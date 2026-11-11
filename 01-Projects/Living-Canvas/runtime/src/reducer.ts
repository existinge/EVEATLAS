// Deterministic reducer: event → materialized state transition.
//
// Invariants implemented here (PROTOCOL.md safety invariants I1–I10):
//  - I1  only coordinator SCENE_COMMITTED mutates the authoritative scene;
//  - I2  decider proposals are advisory, held in pendingProposals (provisional);
//  - I3  actions/proposals from a non-current topicEpoch are rejected (diagnostic);
//  - I4  a revoked semanticRevision or expired plan cannot commit (checked here);
//  - I5  an observation correction revokes dependent provisional proposals;
//  - I6  a topic epoch advance clears provisional/needsPlan of the old topic;
//  - I7  duplicate event/proposal IDs are idempotent (handled in store + reducer);
//  - I8  the log shows applied vs rejected separately (outcomes, not silent);
//  - I9  the renderer is not blocked: telemetry only, no LLM dependency;
//  - I10 unknown/multilingual-only input → safe NEEDS_PLAN, never hallucinated.

import {
  type Envelope,
  type EventKind,
  KIND_META,
} from "./schema.ts";
import {
  type MaterializedState,
  type VisualProposal,
  type CommittedSceneAction,
  type ObservationRecord,
  type NeedsPlan,
  type Stoplight,
  type ActionType,
  PERMITTED_ACTION_TYPES,
} from "./state.ts";
import { cloneState } from "./state.ts";

export type RejectReason =
  | "stale-epoch"
  | "epoch-not-advancing"
  | "unknown-kind"
  | "invalid-proposal"
  | "invalid-target"
  | "action-not-permitted"
  | "not-reversible-by-decider"
  | "no-valid-source"
  | "expired-proposal"
  | "proposal-already-committed"
  | "duplicate-pending-proposal"
  | "session-monotonicity"
  | "internal";

export type ApplyOutcome =
  | { status: "applied"; kind: EventKind }
  | { status: "rejected"; reason: RejectReason; detail: string }
  | { status: "skipped-duplicate"; reason: "duplicate-event-id" | "duplicate-pending-proposal" | "proposal-already-committed" };

function rejected(reason: RejectReason, detail: string): ApplyOutcome {
  return { status: "rejected", reason, detail };
}

/**
 * Reduce one envelope into a clone of `state`. Never mutates the incoming
 * `state` object (pure), which keeps replayed runs deterministic.
 */
export function reduceState(state: MaterializedState, evt: Envelope): { state: MaterializedState; outcome: ApplyOutcome } {
  const s = cloneState(state);
  s.stats.total += 1;

  // -- kind existence -------------------------------------------------------
  if (!KIND_META[evt.kind]) {
    const detail = `unknown event kind "${evt.kind}"`;
    s.diagnostics.push(`rejected event#${evt.eventId}: ${detail}`);
    s.stats.rejected += 1;
    return { state: s, outcome: rejected("unknown-kind", detail) };
  }

  // -- monotonic session-relative clock ------------------------------------
  if (evt.emittedAtMs < s.sessionMonotonicMs) {
    const detail = `emittedAtMs ${evt.emittedAtMs} < current sessionMonotonicMs ${s.sessionMonotonicMs}`;
    s.diagnostics.push(`rejected event#${evt.eventId}: ${detail}`);
    s.stats.rejected += 1;
    return { state: s, outcome: rejected("session-monotonicity", detail) };
  }
  s.sessionMonotonicMs = evt.emittedAtMs;

  // -- duplicate proposal ID handling --------------------------------------
  const propId = (evt.payload as { proposalId?: unknown })?.proposalId;
  if (typeof propId === "string") {
    // The "pending" check applies only to events that *author* a pending
    // proposal (DECIDER_PROPOSAL). SCENE_COMMITTED and SCENE_PROVISIONAL
    // legitimately target a pending proposal: the coordinator authors the
    // DECIDER_PROPOSAL first (creating the pending entry) and then a
    // SCENE_* event for the same proposalId, so those must not be treated as
    // duplicates here. Their genuine re-stages are caught below (committed /
    // provisional action already present).
    if (evt.kind === "DECIDER_PROPOSAL" && s.pendingProposals.some((p) => p.id === propId)) {
      s.stats.skippedDuplicate += 1;
      return { state: s, outcome: { status: "skipped-duplicate", reason: "duplicate-pending-proposal" } };
    }
    // Re-authoring / re-staging an already-committed proposal is a duplicate.
    // SCENE_REVERTED legitimately targets a committed action, so it is
    // excluded. A distinct SCENE_COMMITTED for an already-committed proposal is
    // also not a duplicate at this layer (the exact synthesized commit dedupes
    // on eventId in the store); applyCommittedScene classifies it: idempotent
    // skip-duplicate when the commitment is already present in the scene,
    // no-valid-source when the proposal never existed here.
    if (evt.kind !== "SCENE_REVERTED" && evt.kind !== "SCENE_COMMITTED" && s.committedSceneActions.some((a) => a.proposalId === propId)) {
      s.stats.skippedDuplicate += 1;
      return { state: s, outcome: { status: "skipped-duplicate", reason: "proposal-already-committed" } };
    }
    if (evt.kind === "SCENE_PROVISIONAL" && s.provisionalSceneActions.some((a) => a.proposalId === propId)) {
      s.stats.skippedDuplicate += 1;
      return { state: s, outcome: { status: "skipped-duplicate", reason: "duplicate-pending-proposal" } };
    }
  }

  // -- revision stream bookkeeping -------------------------------------------
  // Advance the stream's revision to the max seen by authors of that stream
  // (events that "use" a revision but don't author it do not bump it).
  const stream = KIND_META[evt.kind].stream;
  if (stream === "obs" && evt.kind !== "USER_INTERRUPT" && evt.kind !== "USER_ACTION") {
    s.observationRevision = Math.max(s.observationRevision, evt.observationRevision);
  } else if (stream === "obs" && evt.kind === "USER_INTERRUPT") {
    s.observationRevision = Math.max(s.observationRevision, evt.observationRevision);
  } else if (stream === "sem") {
    s.semanticRevision = Math.max(s.semanticRevision, evt.semanticRevision);
  } else if (stream === "scene") {
    s.sceneRevision = Math.max(s.sceneRevision, evt.sceneRevision);
  }
  // TOPIC_EPOCH_ADVANCED authors topicEpoch (handled below); carries no reviews.

  // -- epoch gating (I3) ------------------------------------------------------
  // Actions/proposals from a non-current epoch are rejected with diagnostics.
  // Purely-observational events are evidence and accepted but tagged with the
  // epoch they belong to, so they can never mutate the current scene either.
  const epochGated: ReadonlySet<EventKind> = new Set<EventKind>([
    "DECIDER_PROPOSAL", "DECIDER_UNCERTAIN", "PLAN_PROPOSED", "PLAN_COMMITTED",
    "SCENE_PROVISIONAL", "SCENE_COMMITTED", "SCENE_REVERTED",
    "USER_ACTION", "FRONTIER_INTEREST",
  ]);
  if (epochGated.has(evt.kind) && evt.topicEpoch !== s.topicEpoch) {
    const detail = `event#${evt.eventId} for topicEpoch ${evt.topicEpoch} while current is ${s.topicEpoch}; rejected before mutation`;
    s.diagnostics.push(detail);
    s.stats.rejected += 1;
    return { state: s, outcome: rejected("stale-epoch", detail) };
  }

  // -- reducer per kind -------------------------------------------------------
  let applied = false;

  switch (evt.kind) {
    case "OBSERVATION_PARTIAL":
    case "OBSERVATION_FINAL": {
      recordObservation(s, evt, evt.kind === "OBSERVATION_FINAL");
      applied = true;
      break;
    }
    case "OBSERVATION_CORRECTION": {
      applyCorrection(s, evt);
      applied = true;
      break;
    }
    case "USER_INTERRUPT": {
      // Highest-priority non-authoritative signal: clear leftover speculative
      // actions/proposals; committed scene actions stay (coordinator reverts).
      const cleared = s.pendingProposals.length + s.provisionalSceneActions.length;
      s.pendingProposals = [];
      s.provisionalSceneActions = [];
      s.stats.interrupts += 1;
      s.diagnostics.push(`event#${evt.eventId} USER_INTERRUPT cleared ${cleared} speculative action(s)`);
      applied = true;
      // observation revision bumped above (stream === obs)
      break;
    }
    case "USER_ACTION": {
      // Advisory; the core records it but grants no scene authority.
      s.userActions = s.userActions ?? [];
      s.userActions.push({
        eventId: evt.eventId,
        actionType: evt.payload.actionType as string,
        targetObjectIds: evt.payload.targetObjectIds as string[],
        correlationId: evt.correlationId,
      });
      applied = true;
      break;
    }
    case "DECIDER_PROPOSAL": {
      const r = applyProposal(s, evt);
      applied = r.status === "applied";
      break;
    }
    case "DECIDER_UNCERTAIN": {
      applyUncertain(s, evt);
      applied = true;
      break;
    }
    case "PLAN_PROPOSED": {
      const conceptId = evt.payload.conceptId as string;
      s.tentativePlans = s.tentativePlans ?? [];
      s.tentativePlans.push({ conceptId, sourceEventId: evt.eventId, topicEpoch: evt.topicEpoch });
      s.diagnostics.push(`event#${evt.eventId} PLAN_PROPOSED for ${conceptId} (not authoritative until committed)`);
      applied = true;
      break;
    }
    case "PLAN_COMMITTED": {
      const conceptId = evt.payload.conceptId as string;
      if (s.concepts[conceptId]) {
        const planRevision = typeof evt.payload.planRevision === "number" ? evt.payload.planRevision : undefined;
        if (planRevision !== undefined) s.concepts[conceptId].planRevision = planRevision;
      } else {
        // A coordinator may introduce the concept node on commit.
        s.concepts[conceptId] = {
          conceptId,
          labelByLanguage: {},
          relationships: [],
          visualRecipeId: "",
          allowedActions: [],
          status: "prepared",
          planRevision: typeof evt.payload.planRevision === "number" ? evt.payload.planRevision : 1,
          expiresAtSessionMs: Number.MAX_SAFE_INTEGER,
        };
        s.permissions[conceptId] = [];
        if (!s.frontier.includes(conceptId)) s.frontier.push(conceptId);
      }
      s.semanticRevision = Math.max(s.semanticRevision, evt.semanticRevision);
      s.diagnostics.push(`event#${evt.eventId} PLAN_COMMITTED applied for ${conceptId}`);
      applied = true;
      break;
    }
    case "FRONTIER_INTEREST": {
      s.frontierInterest = s.frontierInterest ?? [];
      s.frontierInterest.push({ conceptId: (evt.payload as { conceptId?: unknown })?.conceptId ?? null, sourceEventId: evt.eventId });
      applied = true;
      break;
    }
    case "SCENE_PROVISIONAL": {
      const r = applyProvisionalScene(s, evt);
      applied = r.status === "applied";
      if (r.status !== "applied") return { state: s, outcome: r };
      break;
    }
    case "SCENE_COMMITTED": {
      const r = applyCommittedScene(s, evt);
      if (r.status !== "applied") return { state: s, outcome: r };
      applied = true;
      break;
    }
    case "SCENE_REVERTED": {
      const r = applySceneRevert(s, evt);
      applied = r.status === "applied";
      if (r.status !== "applied") return { state: s, outcome: r };
      break;
    }
    case "TOPIC_EPOCH_ADVANCED": {
      const r = applyEpochAdvance(s, evt);
      return { state: s, outcome: r };
    }
    case "RENDER_ACK": {
      s.telemetry.renderAcks += 1;
      s.telemetry.lastRenderAckEventId = evt.eventId;
      applied = true;
      break;
    }
    case "RENDER_ERROR": {
      s.telemetry.renderErrors += 1;
      s.diagnostics.push(`event#${evt.eventId} RENDER_ERROR: ${String(evt.payload.message ?? "")}`);
      applied = true;
      break;
    }
    case "PROVIDER_CAPABILITY": {
      const cap = (evt.payload as { capability?: unknown })?.capability;
      if (typeof cap === "string" && !s.telemetry.providerCapabilities.includes(cap)) {
        s.telemetry.providerCapabilities.push(cap);
      }
      applied = true;
      break;
    }
    case "PROVIDER_ERROR": {
      s.telemetry.providerErrors.push(String(evt.payload.message));
      s.diagnostics.push(`event#${evt.eventId} PROVIDER_ERROR: ${String(evt.payload.message)}`);
      applied = true;
      break;
    }
    default: {
      const detail = `unhandled kind ${evt.kind}`;
      s.diagnostics.push(`rejected event#${evt.eventId}: ${detail}`);
      s.stats.rejected += 1;
      return { state: s, outcome: rejected("internal", detail) };
    }
  }

  if (applied) {
    s.appliedEventIds.push(evt.eventId);
    s.stats.applied += 1;
    return { state: s, outcome: { status: "applied", kind: evt.kind } };
  }
  s.stats.rejected += 1;
  return { state: s, outcome: rejected("internal", "no application rule") };
}

// ---------------------------------------------------------------------------
// Kind handlers
// ---------------------------------------------------------------------------

function recordObservation(s: MaterializedState, evt: Envelope, isFinal: boolean): void {
  const payload = evt.payload as { languageTag: string; text: string };
  const lang = payload.languageTag;
  const text = payload.text;
  const matched = matchConceptLabel(s, lang, text);

  const rec: ObservationRecord = {
    correlationId: evt.correlationId,
    languageTag: lang,
    text,
    isFinal,
    topicEpoch: evt.topicEpoch,
    matchedConceptId: matched?.conceptId ?? null,
    matchedLabel: matched?.label ?? null,
    sourceEventId: evt.eventId,
  };
  s.observations[evt.correlationId] = rec;
  s.observationByEventId[evt.eventId] = evt.correlationId;
  if (!s.conversationLanguages.includes(lang)) s.conversationLanguages.push(lang);
  s.diagnostics.push(
    `event#${evt.eventId} observed "${text}"@${lang} -> ${matched ? `matched advisory ${matched.conceptId}` : "no semantic match (may NEEDS_PLAN)"}`,
  );
}

function applyCorrection(s: MaterializedState, evt: Envelope): void {
  const payload = evt.payload as { languageTag: string; text: string; isFinal: boolean; supersedes: string[] };
  const supersedes = payload.supersedes ?? [];
  const lang = payload.languageTag;

  // If this correction supersedes a previous observation, remove that record
  // and revoke any dependent provisional proposals (I5).
  for (const oldEventId of supersedes) {
    const oldCorr = s.observationByEventId[oldEventId];
    if (oldCorr && s.observations[oldCorr]) {
      delete s.observations[oldCorr];
      delete s.observationByEventId[oldEventId];
    }
    const dependent = s.pendingProposals.filter(
      (p) => p.evidenceEventIds.includes(oldEventId) || p.sourceEventId === oldEventId,
    );
    for (const p of dependent) {
      p.status = "revoked";
      s.diagnostics.push(`correction event#${evt.eventId} revoked dependent provisional proposal ${p.id}`);
    }
    s.pendingProposals = s.pendingProposals.filter((p) => p.status !== "revoked");
  }

  // Correction provides the confirmed text.
  const matched = matchConceptLabel(s, lang, payload.text);
  s.observations[evt.correlationId] = {
    correlationId: evt.correlationId,
    languageTag: lang,
    text: payload.text,
    isFinal: payload.isFinal,
    topicEpoch: evt.topicEpoch,
    matchedConceptId: matched?.conceptId ?? null,
    matchedLabel: matched?.label ?? null,
    sourceEventId: evt.eventId,
  };
  s.observationByEventId[evt.eventId] = evt.correlationId;
  if (!s.conversationLanguages.includes(lang)) s.conversationLanguages.push(lang);
  s.diagnostics.push(
    `event#${evt.eventId} correction "${payload.text}"@${lang} supersedes ${supersedes.join(",")}; provisional proposals revoked`,
  );
}

function matchConceptLabel(s: MaterializedState, lang: string, text: string): { conceptId: string; label: string } | null {
  const normalized = text.trim().toLowerCase();
  if (normalized.length === 0) return null;
  for (const [conceptId, concept] of Object.entries(s.concepts)) {
    if (!concept.labelByLanguage || !concept.labelByLanguage[lang]) continue;
    const label = concept.labelByLanguage[lang];
    if (label.toLowerCase() === normalized) return { conceptId, label };
  }
  return null;
}

function stoplightForProposal(proposal: { reversible: boolean; confidence: number | null; isAuthoritative: boolean }): Stoplight {
  if (proposal.isAuthoritative) return "GREEN";
  if (!proposal.reversible) return "RED";
  return "YELLOW";
}

function applyProposal(s: MaterializedState, evt: Envelope): ApplyOutcome {
  const payload = evt.payload as {
    proposalId: string;
    targetObjectIds: string[];
    actionType: string;
    parameters?: Record<string, unknown>;
    confidence: number | null;
    evidenceEventIds: string[];
    reversible: boolean;
    expiresAtSessionMs: number;
  };

  const actionType = payload.actionType as ActionType;
  if (!(PERMITTED_ACTION_TYPES as readonly string[]).includes(actionType as string)) {
    const detail = `event#${evt.eventId} actionType "${actionType}" not in permitted set`;
    s.diagnostics.push(detail);
    s.stats.rejected += 1;
    return rejected("action-not-permitted", detail);
  }

  // Every target must exist in the canvas and allow the action (per concept
  // authority; permission derived from seed allowedActions).
  for (const objId of payload.targetObjectIds) {
    const obj = s.visualObjects[objId];
    if (!obj) {
      const detail = `event#${evt.eventId} target object "${objId}" does not exist`;
      s.diagnostics.push(detail);
      s.stats.rejected += 1;
      return rejected("invalid-target", detail);
    }
    const allowed = s.permissions[obj.conceptId] ?? [];
    if (!allowed.includes(actionType as string)) {
      const detail = `event#${evt.eventId} action "${actionType}" not permitted on concept ${obj.conceptId}`;
      s.diagnostics.push(detail);
      s.stats.rejected += 1;
      return rejected("action-not-permitted", detail);
    }
  }

  // Non-reversible advisory proposals are refused (decider has no commit authority).
  if (!payload.reversible) {
    const detail = `event#${evt.eventId} decider proposed non-reversible action; requires coordinator commit`;
    s.diagnostics.push(detail);
    s.stats.rejected += 1;
    return rejected("not-reversible-by-decider", detail);
  }

  const proposal: VisualProposal = {
    id: payload.proposalId,
    correlationId: evt.correlationId,
    topicEpoch: evt.topicEpoch,
    observationRevision: evt.observationRevision,
    semanticRevision: evt.semanticRevision,
    targetObjectIds: payload.targetObjectIds,
    actionType,
    parameters: payload.parameters ?? {},
    confidence: payload.confidence,
    evidenceEventIds: payload.evidenceEventIds,
    reversible: payload.reversible,
    expiresAtSessionMs: payload.expiresAtSessionMs,
    createdAtMs: evt.emittedAtMs,
    status: "pending",
    stoplight: stoplightForProposal({ reversible: payload.reversible, confidence: payload.confidence, isAuthoritative: false }),
    sourceEventId: evt.eventId,
  };
  s.pendingProposals.push(proposal);
  s.diagnostics.push(
    `event#${evt.eventId} DECIDER_PROPOSAL ${payload.proposalId} held as provisional ${proposal.stoplight} (NOT committed; mutable only by coordinator)`,
  );
  return { status: "applied", kind: evt.kind };
}

function applyUncertain(s: MaterializedState, evt: Envelope): ApplyOutcome {
  const payload = evt.payload as { reason?: string; text?: string; languageTag?: string };
  const reason = payload.reason ?? "NEEDS_PLAN";
  const text = payload.text ?? "";
  // Resolve the languageTag from the referenced observation when not explicit.
  let languageTag: string | null = payload.languageTag ?? null;
  if (languageTag === null) {
    const obs = s.observations[evt.correlationId];
    if (obs) languageTag = obs.languageTag;
  }
  if (languageTag === null && text) {
    for (const rec of Object.values(s.observations)) {
      if (rec.text === text) { languageTag = rec.languageTag; break; }
    }
  }
  const entry: NeedsPlan = {
    correlationId: evt.correlationId,
    text,
    languageTag,
    topicEpoch: evt.topicEpoch,
    reason,
    sourceEventId: evt.eventId,
  };
  s.needsPlan.push(entry);
  if (!s.conversationLanguages.includes(languageTag ?? "")) {
    if (languageTag && languageTag.length > 0) s.conversationLanguages.push(languageTag);
  }
  s.diagnostics.push(
    `event#${evt.eventId} DECIDER_UNCERTAIN (${reason}) -> NEEDS_PLAN for "${text}"@${languageTag ?? "?"}; no scene mutation (I10)`,
  );
  return { status: "applied", kind: evt.kind };
}

function applyProvisionalScene(s: MaterializedState, evt: Envelope): ApplyOutcome {
  const payload = evt.payload as {
    proposalId: string;
    targetObjectIds: string[];
    actionType: string;
    parameters?: Record<string, unknown>;
    reversible: boolean;
    correlationId?: string;
  };
  const matching = s.pendingProposals.find((p) => p.id === payload.proposalId);
  if (!matching) {
    const detail = `event#${evt.eventId} SCENE_PROVISIONAL references unknown proposal ${payload.proposalId}`;
    s.diagnostics.push(detail);
    s.stats.rejected += 1;
    return rejected("no-valid-source", detail);
  }
  s.provisionalSceneActions.push({
    actionId: `provisional-${s.provisionalSceneActions.length + 1}`,
    proposalId: payload.proposalId,
    correlationId: matching.correlationId,
    topicEpoch: evt.topicEpoch,
    actionType: payload.actionType as ActionType,
    targetObjectIds: payload.targetObjectIds,
    parameters: payload.parameters ?? {},
    reversible: payload.reversible,
    sourceEventId: evt.eventId,
  });
  s.diagnostics.push(`event#${evt.eventId} SCENE_PROVISIONAL staged speculative preview; cleared on interrupt`);
  return { status: "applied", kind: evt.kind };
}

function applyCommittedScene(s: MaterializedState, evt: Envelope): ApplyOutcome {
  const payload = evt.payload as {
    proposalId: string;
    targetObjectIds: string[];
    actionType: string;
    parameters?: Record<string, unknown>;
    reversible: boolean;
    correlationId?: string;
  };
  const matching = s.pendingProposals.find((p) => p.id === payload.proposalId);
  if (!matching) {
    // Idempotency (I7): a re-issued SCENE_COMMITTED whose proposalId already
    // produced a committed action is a duplicate of that commitment — skip it,
    // never re-apply. A proposalId that never committed here stays
    // no-valid-source (authority, I1): we must not invent a scene action.
    if (s.committedSceneActions.some((a) => a.proposalId === payload.proposalId)) {
      const detail = `event#${evt.eventId} SCENE_COMMITTED for already-committed proposal ${payload.proposalId}; idempotent skip`;
      s.diagnostics.push(detail);
      s.stats.skippedDuplicate += 1;
      return { status: "skipped-duplicate", reason: "proposal-already-committed", detail };
    }
    const detail = `event#${evt.eventId} SCENE_COMMITTED references no pending proposal ${payload.proposalId}; refusing to invent (I1)`;
    s.diagnostics.push(detail);
    s.stats.rejected += 1;
    return rejected("no-valid-source", detail);
  }
  if (evt.emittedAtMs > matching.expiresAtSessionMs) {
    const detail = `event#${evt.eventId} SCENE_COMMITTED after proposal ${payload.proposalId} expired at ${matching.expiresAtSessionMs}`;
    s.diagnostics.push(detail);
    s.stats.rejected += 1;
    return rejected("expired-proposal", detail);
  }
  const action: CommittedSceneAction = {
    actionId: `act-${s.commitCount + 1}`,
    proposalId: payload.proposalId,
    correlationId: matching.correlationId,
    topicEpoch: evt.topicEpoch,
    actionType: payload.actionType as ActionType,
    targetObjectIds: payload.targetObjectIds,
    parameters: payload.parameters ?? {},
    reversible: payload.reversible,
    sourceEventId: evt.eventId,
  };
  s.committedSceneActions.push(action);
  s.commitCount += 1;
  s.lastCommittedEventId = evt.eventId;
  // Reflect non-destructive parameter application deterministically.
  const params = action.parameters as { attention?: number; x?: number; y?: number };
  if (action.actionType === "emphasize" && typeof params.attention === "number") {
    for (const objId of action.targetObjectIds) {
      const obj = s.visualObjects[objId];
      if (obj) obj.attention = params.attention;
    }
  } else if (action.actionType === "move" && typeof params.x === "number" && typeof params.y === "number") {
    for (const objId of action.targetObjectIds) {
      const obj = s.visualObjects[objId];
      if (obj) { obj.position = { x: params.x, y: params.y }; }
    }
  }
  s.pendingProposals = s.pendingProposals.filter((p) => p.id !== payload.proposalId);
  s.diagnostics.push(`event#${evt.eventId} SCENE_COMMITTED ${action.actionType} on [${action.targetObjectIds.join(",")}] (scene committed)`);
  return { status: "applied", kind: evt.kind };
}

function applySceneRevert(s: MaterializedState, evt: Envelope): ApplyOutcome {
  const payload = evt.payload as { proposalId?: string; correlationId?: string };
  const target = s.committedSceneActions.find((a) => a.proposalId === payload.proposalId || a.correlationId === payload.correlationId);
  if (!target) {
    const detail = `event#${evt.eventId} SCENE_REVERTED references no committed action`;
    s.diagnostics.push(detail);
    s.stats.rejected += 1;
    return rejected("no-valid-source", detail);
  }
  s.committedSceneActions = s.committedSceneActions.filter(
    (a) => a.actionId !== target.actionId,
  );
  s.diagnostics.push(`event#${evt.eventId} SCENE_REVERTED reverted ${target.actionId}`);
  return { status: "applied", kind: evt.kind };
}

function applyEpochAdvance(s: MaterializedState, evt: Envelope): ApplyOutcome {
  const next = evt.topicEpoch;
  if (next <= s.topicEpoch) {
    const detail = `event#${evt.eventId} TOPIC_EPOCH_ADVANCED to ${next} but current is ${s.topicEpoch}; must be > current`;
    s.diagnostics.push(detail);
    s.stats.rejected += 1;
    return rejected("epoch-not-advancing", detail);
  }
  s.topicEpoch = next;
  s.stats.epochAdvances += 1;
  const payload = evt.payload as { languageTag?: string; reason?: string };
  if (payload.languageTag && !s.conversationLanguages.includes(payload.languageTag)) {
    s.conversationLanguages.push(payload.languageTag);
  }
  // I6: new topic never inherits old provisional speculative state.
  const cleared = s.pendingProposals.length + s.provisionalSceneActions.length + s.needsPlan.length;
  s.pendingProposals = [];
  s.provisionalSceneActions = [];
  const currentEpoch = s.topicEpoch;
  const keptNeedsPlan = s.needsPlan.filter((n) => n.topicEpoch === currentEpoch);
  s.needsPlan = [...keptNeedsPlan];
  s.diagnostics.push(
    `event#${evt.eventId} TOPIC_EPOCH_ADVANCED topicEpoch -> ${next} (${String(payload.reason ?? "")}); cleared ${cleared} speculative/provisional/needsPlan of old topic (I6)`,
  );
  s.appliedEventIds.push(evt.eventId);
  s.stats.applied += 1;
  return { status: "applied", kind: evt.kind };
}