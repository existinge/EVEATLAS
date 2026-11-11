// coordinator.ts — T02 deterministic stoplight coordinator.
//
// Gate P2: "receives fast-decider proposals, validates them against canonical
// semantic state, and commits only authorized scene actions."
//
// Layering
// --------
// * `validateProposal(proposal, snapshot)` is a PURE function. It classifies a
//   DECIDER_PROPOSAL against the canonical materialized state into
//   GREEN (commit) / YELLOW (reversible preview) / RED (reject), and records a
//   deterministic reasons[] so callers can always explain the decision.
// * `Coordinator` wraps a `SharedStore`. It is the ONLY authority that may turn
//   a proposal into a committed scene action: it synthesizes SCENE_COMMITTED
//   envelopes itself (source "coordinator") and refuses any externally supplied
//   SCENE_COMMITTED / SCENE_PROVISIONAL that was not previously granted by it.
//   The underlying P1 reducer remains untouched so replay determinism and the
//   16 P1 gates are preserved; the coordinator is an authority layer on top.
//
// Stoplight policy (deterministic, no model, no wall-clock authority)
//   RED    — any hard failure: stale topic epoch, stale/revoked semantic
//            revision (plan advanced past the proposal or branch retired),
//            expired concept permission, invalid/unknown object id, unsupported
//            or non-permitted action, proposal already expired, stale or
//            semantically incompatible evidence. RED proposals never reach the
//            reducer, so canonical sceneRevision is untouched.
//   GREEN  — no hard failures AND the evidence is *authoritative complete*:
//            every evidence event resolves to a live (non-superseded) final
//            observation whose matched concept equals the target object's
//            concept, at the proposal's own topic epoch. The coordinator
//            authorizes a real SCENE_COMMITTED.
//   YELLOW — no hard failures, but evidence is *incomplete* (absent, partial,
//            or unmatched) or the action is a preview-grade emphasis/hint.
//            Only reversible preview-grade actions are allowed; the coordinator
//            stages a SCENE_PROVISIONAL plus a local preview, never a commit
//            and never a factual label.

import { performance } from "node:perf_hooks";
import { SchemaViolation, parseEnvelope, SCHEMA_VERSION } from "./schema.ts";
import { PERMITTED_ACTION_TYPES, type ActionType, type MaterializedState, type SeedSnapshot, type Stoplight } from "./state.ts";
import { SharedStore } from "./store.ts";
import type { Envelope } from "./schema.ts";
import type { IngestOutcome } from "./store.ts";

/** Preview-grade, reversible, non-factual actions a YELLOW proposal may stage. */
export const PREVIEW_ACTION_TYPES: readonly string[] = ["emphasize", "deEmphasize", "revealHint"];

export interface StoplightDecision {
  status: Stoplight;
  /** Machine-readable reason codes (empty for a clean GREEN/YELLOW). */
  reasons: string[];
  /** Human-readable explanation of each reason. */
  details: string[];
  /** What the coordinator is allowed to do with this proposal. */
  authority: "commit" | "preview" | "none";
  /** Wall-clock cost of the pure check only (never model inference). */
  latencyMs: number;
}

export interface RejectRecord {
  proposalId: string;
  reasons: string[];
  atSceneRevision: number;
  atEmittedAtMs: number;
}

export interface PreviewEntry {
  proposalId: string;
  actionType: string;
  targetObjectIds: string[];
  parameters: Record<string, unknown>;
  stagedAtMs: number;
  sourceEventId: string;
}

export interface CoordinatorOutcome extends IngestOutcome {
  decision?: StoplightDecision;
  /** sceneRevision observed just before / just after this ingestion. */
  sceneBefore: number;
  sceneAfter: number;
}

// ---------------------------------------------------------------------------
// Pure validation
// ---------------------------------------------------------------------------

interface ProposalLike {
  topicEpoch: number;
  semanticRevision: number;
  emittedAtMs: number;
  payload: {
    proposalId: string;
    targetObjectIds: string[];
    actionType: string;
    parameters?: Record<string, unknown>;
    evidenceEventIds: string[];
    reversible: boolean;
    expiresAtSessionMs: number;
  };
}

/**
 * Pure stoplight classifier. Never mutates `snapshot` — SharedStore hands out
 * frozen clones, so this is reusable for replay without side effects.
 */
export function validateProposal(proposal: ProposalLike, snapshot: Readonly<MaterializedState>): StoplightDecision {
  const t0 = performance.now();
  const reasons: string[] = [];
  const details: string[] = [];
  const push = (reason: string, detail: string) => {
    reasons.push(reason);
    details.push(detail);
  };

  const actionType = proposal.payload.actionType;
  const targetIds = proposal.payload.targetObjectIds;

  // -- freshness of the proposal itself -------------------------------------
  if (proposal.topicEpoch !== snapshot.topicEpoch) {
    push("stale-epoch", `proposal carries topicEpoch ${proposal.topicEpoch}, current is ${snapshot.topicEpoch}`);
  }
  if (proposal.semanticRevision < snapshot.semanticRevision) {
    push("stale-semantic-revision", `proposal carries semanticRevision ${proposal.semanticRevision}, current is ${snapshot.semanticRevision}`);
  }
  if (proposal.payload.expiresAtSessionMs <= proposal.emittedAtMs) {
    push("expired-proposal", `proposal born at ${proposal.emittedAtMs} already past its own expiry ${proposal.payload.expiresAtSessionMs}`);
  }
  if (proposal.payload.expiresAtSessionMs <= snapshot.sessionMonotonicMs) {
    push("expired-proposal", `proposal expiry ${proposal.payload.expiresAtSessionMs} is not later than current session time ${snapshot.sessionMonotonicMs}`);
  }

  // -- action must be one we know --------------------------------------------
  if (!(PERMITTED_ACTION_TYPES as readonly string[]).includes(actionType)) {
    push("unsupported-action", `actionType "${actionType}" is not in the permitted set`);
  }

  // -- every target must exist, be eligible, and permit the action ------------
  const targetConcepts = new Set<string>();
  for (const objId of targetIds) {
    const obj = snapshot.visualObjects[objId];
    if (!obj) {
      push("invalid-object-id", `target object "${objId}" does not exist on the canvas`);
      continue;
    }
    const concept = snapshot.concepts[obj.conceptId];
    if (!concept) {
      push("unknown-concept", `object "${objId}" references unknown concept "${obj.conceptId}"`);
      continue;
    }
    // concept nodes are keyed by id; the map key (== obj.conceptId) is the id.
    targetConcepts.add(obj.conceptId);

    if (proposal.semanticRevision < concept.planRevision) {
      push("revoked-plan", `concept ${obj.conceptId} plan advanced to revision ${concept.planRevision}; proposal still at ${proposal.semanticRevision}`);
    } else if (concept.status === "retired") {
      push("revoked-plan", `concept ${obj.conceptId} is retired (${concept.status})`);
    } else if (concept.status !== "active") {
      push("ineligible-branch", `concept ${obj.conceptId} status "${concept.status}" is not active`);
    }
    if (concept.expiresAtSessionMs < proposal.emittedAtMs) {
      push("expired-permission", `concept ${obj.conceptId} permission expired at ${concept.expiresAtSessionMs} before proposal time ${proposal.emittedAtMs}`);
    }
    const allowed = snapshot.permissions[obj.conceptId] ?? [];
    if (!allowed.includes(actionType)) {
      push("action-not-permitted", `action "${actionType}" not permitted on concept ${obj.conceptId}`);
    }
  }

  // -- evidence must be live and semantically compatible ----------------------
  let confirming = 0;      // live observations matching a target concept
  let finalConfirming = 0; // ...that are also final (authoritative)
  for (const evId of proposal.payload.evidenceEventIds) {
    const corr = snapshot.observationByEventId[evId];
    const rec = corr ? snapshot.observations[corr] : undefined;
    if (!rec) {
      push("stale-evidence", `evidence event ${evId} is superseded or unknown`);
      continue;
    }
    if ((rec.topicEpoch ?? undefined) !== undefined && rec.topicEpoch !== proposal.topicEpoch) {
      push("stale-evidence", `evidence event ${evId} belongs to epoch ${rec.topicEpoch}, proposal to ${proposal.topicEpoch}`);
      continue;
    }
    if (rec.matchedConceptId == null) {
      // Unmatched evidence: incomplete (never a hard failure, never authority).
      continue;
    }
    if (!targetConcepts.has(rec.matchedConceptId)) {
      push("incompatible-evidence", `evidence event ${evId} matched concept ${rec.matchedConceptId} which is not among targets [${[...targetConcepts].join(",")}]`);
      continue;
    }
    confirming += 1;
    if (rec.isFinal) finalConfirming += 1;
  }

  const latencyMs = performance.now() - t0;

  const hard = reasons.length > 0;
  if (hard) {
    return { status: "RED", reasons, details, authority: "none", latencyMs };
  }

  // Evidence completeness drives GREEN vs YELLOW. Authoritative requires every
  // evidence slot to be live & final & matching (finalConfirming reflects
  // matching-and-final; requiring non-empty so no-evidence is never GREEN).
  const authoritativeComplete = proposal.payload.evidenceEventIds.length > 0 && finalConfirming === proposal.payload.evidenceEventIds.length;

  if (authoritativeComplete && proposal.payload.reversible) {
    return { status: "GREEN", reasons, details, authority: "commit", latencyMs };
  }
  if (proposal.payload.reversible && PREVIEW_ACTION_TYPES.includes(actionType)) {
    return { status: "YELLOW", reasons, details, authority: "preview", latencyMs };
  }
  // Eligible but neither a complete-authoritative commit nor a reversible
  // preview: cannot be acted on by a decider.
  reasons.push(proposal.payload.reversible ? "preview-only-action" : "not-reversible-by-decider");
  details.push(
    proposal.payload.reversible
      ? `action "${actionType}" is not preview-grade (${PREVIEW_ACTION_TYPES.join("|")}) and evidence is not authoritative`
      : `non-reversible proposal cannot be applied by a decider`,
  );
  return { status: "RED", reasons, details, authority: "none", latencyMs };
}

// ---------------------------------------------------------------------------
// Coordinator
// ---------------------------------------------------------------------------

export interface CoordinatorOptions {
  previewCapacity?: number;
  debugEvents?: boolean;
}

export class Coordinator {
  private store: SharedStore;
  readonly previewCapacity: number;
  readonly debugEvents: boolean;
  private previewsByProposal = new Map<string, PreviewEntry>();
  /** proposalId -> granted commit fingerprint (targets+action+epoch). */
  private grantedCommits = new Map<string, { targetsKey: string; actionType: string; topicEpoch: number }>();
  private stagedPreviews = new Set<string>();
  private committedByCoordinator = new Set<string>();
  readonly rejectLog: RejectRecord[] = [];
  readonly latencies = {
    /** time spent in the pure stoplight check per proposal. */
    stoplight: [] as number[],
    /** wall-clock time from proposal ingest to SCENE_COMMITTED applied. */
    commit: [] as number[],
    /** wall-clock time from proposal ingest to SCENE_PROVISIONAL staged. */
    previewStage: [] as number[],
    /** simple forwards that touch no coordinator logic. */
    forward: [] as number[],
  };

  constructor(seed: SeedSnapshot, opts: CoordinatorOptions = {}) {
    this.store = new SharedStore(seed);
    this.previewCapacity = opts.previewCapacity ?? 16;
    this.debugEvents = opts.debugEvents ?? false;
  }

  getState(): MaterializedState {
    return this.store.getState();
  }

  getLog() {
    return this.store.getLog();
  }

  /** Cached median helper for the report. */
  median(samples: number[]): number {
    if (samples.length === 0) return 0;
    const sorted = [...samples].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 === 1 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  }

  latencyReport() {
    const l = this.latencies;
    const summarize = (name: keyof typeof l, samples: number[]) => ({
      hop: name,
      n: samples.length,
      medianMs: Number(this.median(samples).toFixed(3)),
      p95Ms: samples.length
        ? Number([...samples].sort((a, b) => a - b)[Math.max(0, Math.ceil(0.95 * samples.length) - 1)].toFixed(3))
        : 0,
      maxMs: samples.length ? Number(Math.max(...samples).toFixed(3)) : 0,
    });
    return [summarize("stoplight", l.stoplight), summarize("commit", l.commit), summarize("previewStage", l.previewStage), summarize("forward", l.forward)];
  }

  ingest(raw: unknown): CoordinatorOutcome {
    let evt: Envelope;
    try {
      evt = parseEnvelope(raw);
    } catch (err) {
      const error = err instanceof SchemaViolation ? err.message : String(err);
      return { status: "schema-invalid", error, sceneBefore: 0, sceneAfter: 0 };
    }
    const sceneBefore = this.store.getState().sceneRevision;
    let out: IngestOutcome;

    switch (evt.kind) {
      case "DECIDER_PROPOSAL":
        out = this.propose(evt);
        break;
      case "SCENE_COMMITTED":
        out = this.externalCommit(evt);
        break;
      case "SCENE_PROVISIONAL":
        out = this.externalProvisional(evt);
        break;
      case "SCENE_REVERTED":
        out = this.externalRevert(evt);
        break;
      case "USER_INTERRUPT":
        out = this.interrupt(evt);
        break;
      case "USER_ACTION":
        out = this.userAction(evt);
        break;
      case "TOPIC_EPOCH_ADVANCED":
        out = this.epochAdvance(evt);
        break;
      default:
        out = this.forward(evt);
        break;
    }

    const sceneAfter = this.store.getState().sceneRevision;
    if (this.debugEvents) {
      // eslint-disable-next-line no-console
      console.log(`[coordinator] ${evt.kind}#${evt.eventId} -> ${out.status}${"decision" in (out as { decision?: unknown }) && (out as { decision?: StoplightDecision }).decision ? ` ${(out as { decision: StoplightDecision }).decision.status}/${(out as { decision: StoplightDecision }).decision.authority}` : ""}`);
    }
    return { ...out, sceneBefore, sceneAfter };
  }

  // -- internal helpers -------------------------------------------------------

  private forward(evt: Envelope): IngestOutcome {
    const t0 = performance.now();
    const out = this.store.ingest(evt);
    this.latencies.forward.push(performance.now() - t0);
    return out;
  }

  private syncPreviewsFromState() {
    const state = this.store.getState();
    const seen = new Set(state.provisionalSceneActions.map((a) => a.proposalId));
    const next = new Map<string, PreviewEntry>();
    for (const [pid, entry] of this.previewsByProposal) {
      if (seen.has(pid)) next.set(pid, entry);
    }
    this.previewsByProposal = next;
    this.stagedPreviews = new Set(next.keys());
  }

  private envelopeFor(kind: string, evt: Envelope, proposalId: string, over: Record<string, unknown>): Envelope {
    const payload = {
      proposalId,
      targetObjectIds: over.targetObjectIds as string[],
      actionType: over.actionType as string,
      parameters: over.parameters as Record<string, unknown> | undefined,
      reversible: over.reversible as boolean,
      ...(over.correlationId !== undefined ? { correlationId: over.correlationId as string } : {}),
    };
    return {
      schemaVersion: SCHEMA_VERSION,
      sessionId: evt.sessionId,
      eventId: over.eventId as string,
      kind,
      topicEpoch: over.topicEpoch as number,
      observationRevision: evt.observationRevision,
      semanticRevision: evt.semanticRevision,
      sceneRevision: (over.sceneRevision as number) ?? evt.sceneRevision,
      correlationId: (over.correlationId as string) ?? evt.correlationId,
      turnId: evt.turnId,
      source: "coordinator",
      emittedAtMs: over.emittedAtMs as number,
      payload,
    } as Envelope;
  }

  // -- DECIDER_PROPOSAL -------------------------------------------------------

  private propose(evt: Envelope): IngestOutcome {
    const snapshot = this.store.getState();
    const decision = validateProposal(evt, snapshot);
    this.latencies.stoplight.push(decision.latencyMs);

    if (decision.status === "RED") {
      const proposalId = (evt.payload as { proposalId: string }).proposalId;
      this.rejectLog.push({ proposalId, reasons: decision.reasons, atSceneRevision: snapshot.sceneRevision, atEmittedAtMs: evt.emittedAtMs });
      return { status: "rejected", reason: decision.reasons[0], detail: decision.details.join("; ") };
    }

    if (decision.status === "GREEN") {
      return this.commitOnAuthority(evt, decision);
    }

    // YELLOW — stage a reversible provisional preview (never a commit).
    return this.stageProvisional(evt, decision);
  }

  private commitOnAuthority(evt: Envelope, decision: StoplightDecision): IngestOutcome {
    const t0 = performance.now();
    const payload = evt.payload as {
      proposalId: string;
      targetObjectIds: string[];
      actionType: string;
      parameters?: Record<string, unknown>;
      reversible: boolean;
    };
    // 1. Author the proposal into canonical state (held pending).
    const propOut = this.store.ingest(evt);
    if (propOut.status !== "applied") {
      return { status: "rejected", reason: propOut.status === "rejected" ? propOut.reason : propOut.status, detail: `failed to stage GREEN proposal: ${propOut.status}` };
    }
    const snapshot = this.store.getState();
    // 2. Grant authority and emit the SCENE_COMMITTED we alone are authorized to author.
    const targetsKey = payload.targetObjectIds.join(",");
    this.grantedCommits.set(payload.proposalId, { targetsKey, actionType: payload.actionType, topicEpoch: evt.topicEpoch });
    const commitEnvelope = this.envelopeFor("SCENE_COMMITTED", evt, payload.proposalId, {
      eventId: `volition-${payload.proposalId}`,
      targetObjectIds: payload.targetObjectIds,
      actionType: payload.actionType,
      parameters: payload.parameters,
      reversible: payload.reversible,
      correlationId: evt.correlationId,
      topicEpoch: evt.topicEpoch,
      sceneRevision: snapshot.sceneRevision,
      emittedAtMs: snapshot.sessionMonotonicMs,
    });
    const commitOut = this.store.ingest(commitEnvelope);
    this.latencies.commit.push(performance.now() - t0);
    if (commitOut.status === "applied") {
      this.committedByCoordinator.add(payload.proposalId);
      return { status: "applied", kind: "SCENE_COMMITTED" as const, decision };
    }
    // Should be unreachable (validated against the same synchronous state), but
    // never fabricate success: drop authority and surface the real reason.
    this.grantedCommits.delete(payload.proposalId);
    return { status: "rejected", reason: commitOut.status === "rejected" ? commitOut.reason : commitOut.status, detail: `coordinator commit refused: ${commitOut.status}`, decision };
  }

  private stageProvisional(evt: Envelope, decision: StoplightDecision): IngestOutcome {
    const t0 = performance.now();
    const payload = evt.payload as {
      proposalId: string;
      targetObjectIds: string[];
      actionType: string;
      parameters?: Record<string, unknown>;
      reversible: boolean;
    };
    const propOut = this.store.ingest(evt);
    if (propOut.status !== "applied") {
      return { status: "rejected", reason: propOut.status === "rejected" ? propOut.reason : propOut.status, detail: `failed to stage YELLOW proposal: ${propOut.status}`, decision };
    }
    const snapshot = this.store.getState();
    this.stagedPreviews.add(payload.proposalId);
    const provisionalEnvelope = this.envelopeFor("SCENE_PROVISIONAL", evt, payload.proposalId, {
      eventId: `provisional-${payload.proposalId}`,
      targetObjectIds: payload.targetObjectIds,
      actionType: payload.actionType,
      parameters: payload.parameters,
      reversible: payload.reversible,
      correlationId: evt.correlationId,
      topicEpoch: evt.topicEpoch,
      sceneRevision: snapshot.sceneRevision,
      emittedAtMs: snapshot.sessionMonotonicMs,
    });
    const provisionalOut = this.store.ingest(provisionalEnvelope);
    this.latencies.previewStage.push(performance.now() - t0);
    if (provisionalOut.status !== "applied") {
      this.stagedPreviews.delete(payload.proposalId);
      return { status: "rejected", reason: provisionalOut.status === "rejected" ? provisionalOut.reason : provisionalOut.status, detail: `provisional staging refused: ${provisionalOut.status}`, decision };
    }
    // Keep the coordinator's bounded preview store in sync with canonical
    // provisional scene actions.
    const entry: PreviewEntry = {
      proposalId: payload.proposalId,
      actionType: payload.actionType,
      targetObjectIds: payload.targetObjectIds,
      parameters: payload.parameters ?? {},
      stagedAtMs: snapshot.sessionMonotonicMs,
      sourceEventId: provisionalEnvelope.eventId,
    };
    this.previewsByProposal.set(payload.proposalId, entry);
    if (this.previewsByProposal.size > this.previewCapacity) {
      const oldest = [...this.previewsByProposal.keys()].shift() as string;
      this.previewsByProposal.delete(oldest);
      this.stagedPreviews.delete(oldest);
    }
    return { status: "applied", kind: "SCENE_PROVISIONAL" as const, decision };
  }

  // -- externally supplied SCENE_* (authority gate) ----------------------------

  private externalCommit(evt: Envelope): IngestOutcome {
    const payload = evt.payload as { proposalId: string; targetObjectIds: string[]; actionType: string; reversible: boolean };
    const grant = this.grantedCommits.get(payload.proposalId);
    if (!grant) {
      return {
        status: "rejected",
        reason: "not-coordinator-authoritative",
        detail: `SCENE_COMMITTED for ${payload.proposalId} was not authorized by the coordinator; refusing to bypass authority`,
      };
    }
    if (grant.targetsKey !== payload.targetObjectIds.join(",") || grant.actionType !== payload.actionType) {
      this.grantedCommits.delete(payload.proposalId);
      return {
        status: "rejected",
        reason: "authority-fingerprint-mismatch",
        detail: `SCENE_COMMITTED for ${payload.proposalId} diverges from the granted action; authority revoked`,
      };
    }
    // Authority lineage (I1): the coordinator synthesized exactly one
    // SCENE_COMMITTED per grant. A *distinct* commit event (a new eventId)
    // referencing an already-committed proposal is not that synthesized event,
    // so the coordinator refuses to re-invent a second scene action. The exact
    // synthesized commit is still accepted below as an idempotent replay; the
    // store dedupes it on eventId.
    const state = this.store.getState();
    const alreadyCommitted = state.committedSceneActions.some((a) => a.proposalId === payload.proposalId);
    if (alreadyCommitted && !state.appliedEventIds.includes(evt.eventId)) {
      return {
        status: "rejected",
        reason: "no-valid-source",
        detail: `SCENE_COMMITTED for ${payload.proposalId} references a proposal already committed; refusing to re-invent a second scene action`,
      };
    }
    const out = this.store.ingest(evt);
    if (out.status === "applied") this.committedByCoordinator.add(payload.proposalId);
    return out;
  }

  private externalProvisional(evt: Envelope): IngestOutcome {
    const proposalId = (evt.payload as { proposalId: string }).proposalId;
    if (!this.stagedPreviews.has(proposalId)) {
      return {
        status: "rejected",
        reason: "not-coordinator-authoritative",
        detail: `SCENE_PROVISIONAL for ${proposalId} was not staged by the coordinator; refusing to invent a preview`,
      };
    }
    const out = this.store.ingest(evt);
    this.syncPreviewsFromState();
    return out;
  }

  private externalRevert(evt: Envelope): IngestOutcome {
    const payload = evt.payload as { proposalId?: string; correlationId?: string };
    const snapshot = this.store.getState();
    // Provenance gate: a reversal must reference a real committed action on the
    // current canonical scene. Correlations the coordinator committed are
    // explicitly legitimate reversals; anything else must still resolve.
    const target = snapshot.committedSceneActions.find(
      (a) => (payload.proposalId && a.proposalId === payload.proposalId) || (payload.correlationId && a.correlationId === payload.correlationId),
    );
    if (!target) {
      return { status: "rejected", reason: "no-valid-source", detail: "SCENE_REVERTED references no current committed action" };
    }
    const out = this.store.ingest(evt);
    return out;
  }

  // -- interruption / user override / epoch ------------------------------------

  private interrupt(evt: Envelope): IngestOutcome {
    const out = this.store.ingest(evt);
    // Interrupt invalidates outstanding speculative state: drop staged previews
    // and any yet-uncommitted grants. Committed scene inside the store is
    // already preserved by the reducer.
    this.previewsByProposal.clear();
    this.stagedPreviews.clear();
    const snapshot = this.store.getState();
    for (const [pid] of this.grantedCommits) {
      if (!snapshot.committedSceneActions.some((a) => a.proposalId === pid)) this.grantedCommits.delete(pid);
    }
    return out;
  }

  private userAction(evt: Envelope): IngestOutcome {
    // The user override terminates matching speculative previews (not the
    // committed scene). We forward the advisory USER_ACTION to canonical state
    // and drop any previews that touched the same objects.
    const out = this.store.ingest(evt);
    if (out.status !== "applied") return out;
    const payload = evt.payload as { targetObjectIds?: string[]; conceptId?: string };
    const touched = new Set<string>();
    for (const [pid, entry] of this.previewsByProposal) {
      const overrides =
        (payload.targetObjectIds ?? []).some((oid) => entry.targetObjectIds.includes(oid)) ||
        (payload.conceptId !== undefined &&
          this.store.getState().visualObjects[entry.targetObjectIds[0] ?? ""]?.conceptId === payload.conceptId);
      if (overrides) {
        touched.add(pid);
      }
    }
    for (const pid of touched) {
      this.previewsByProposal.delete(pid);
      this.stagedPreviews.delete(pid);
    }
    if (touched.size > 0 && this.debugEvents) {
      // eslint-disable-next-line no-console
      console.log(`[coordinator] USER_ACTION overrode ${touched.size} staged preview(s)`);
    }
    return out;
  }

  private epochAdvance(evt: Envelope): IngestOutcome {
    const out = this.store.ingest(evt);
    // Old-topic provisional/needsPlan already cleared in canonical state; the
    // coordinator mirrors it for its own preview store.
    this.syncPreviewsFromState();
    const snapshot = this.store.getState();
    for (const [pid] of this.grantedCommits) {
      if (!snapshot.committedSceneActions.some((a) => a.proposalId === pid)) this.grantedCommits.delete(pid);
    }
    return out;
  }
}