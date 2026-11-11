// SharedStore: one in-memory authority with an append-only event log, a
// deterministic reducer, subscriber queues with coalescing + never-drop, and a
// deterministic canonical snapshot + commit ID.
//
// Concurrency policy (PROTOCOL.md / ARCHITECTURE.md):
//  - serial reducer commit (no external side effects off the critical path);
//  - bounded subscriber queues; high-frequency non-final transcripts coalesce;
//  - USER_INTERRUPT / TOPIC_EPOCH_ADVANCED / SCENE_COMMITTED are never dropped.

import { createHash } from "node:crypto";
import {
  type Envelope,
  type EventKind,
  parseEnvelope,
  envelopeFingerprint,
  SchemaViolation,
  CRITICAL_KINDS,
} from "./schema.ts";
import {
  type MaterializedState,
  type SeedSnapshot,
  type SubscriberDelivery,
  cloneState,
  freezeState,
} from "./state.ts";
import { reduceState, type ApplyOutcome } from "./reducer.ts";
import { canonicalJson } from "./canonical.ts";

export type IngestOutcome =
  | { status: "applied"; kind: EventKind }
  | { status: "rejected"; reason: string; detail: string }
  | { status: "skipped-duplicate"; detail: string }
  | { status: "schema-invalid"; error: string };

export interface LogEntry {
  seq: number;
  eventId: string;
  kind: string;
  outcome: "applied" | "rejected" | "skipped-duplicate" | "schema-invalid";
  detail: string;
  // Full validated envelope surface (present for any event that passed
  // parseEnvelope) so the canonical log is self-replayable and authorship
  // (e.g. source === "coordinator") survives. P1 summary consumers read only
  // seq/eventId/kind/outcome/detail; distinct events still dedupe on eventId.
  schemaVersion?: number;
  sessionId?: string;
  turnId?: string;
  source?: string;
  topicEpoch?: number;
  observationRevision?: number;
  semanticRevision?: number;
  sceneRevision?: number;
  emittedAtMs?: number;
  correlationId?: string;
  payload?: Record<string, unknown>;
}

export interface Subscriber {
  id: number;
  queue: SubscriberDelivery[];
  capacity: number;
  dropped: number;
  coalesced: number;
}

/** Pure bounded-queue offer with coalescing + never-drop policy. */
export function offerToQueue(
  queue: SubscriberDelivery[],
  incoming: SubscriberDelivery,
  capacity: number,
): { queue: SubscriberDelivery[]; dropped: boolean; coalesced: boolean } {
  const isCritical = CRITICAL_KINDS.has(incoming.causedByKind);
  const isCoalescible =
    incoming.causedByKind === "OBSERVATION_PARTIAL" &&
    !incoming.isFinal &&
    queue.length > 0;

  if (isCoalescible) {
    const tail = queue[queue.length - 1];
    if (
      tail.causedByKind === "OBSERVATION_PARTIAL" &&
      !tail.isFinal &&
      tail.correlationId === incoming.correlationId &&
      tail.languageTag === incoming.languageTag
    ) {
      const next = queue.slice();
      next[next.length - 1] = { ...tail, seq: incoming.seq, snapshotRevision: incoming.snapshotRevision };
      return { queue: next, dropped: false, coalesced: true };
    }
  }

  // Critical kinds can never be dropped: evict the oldest non-critical entry
  // to make room rather than losing the important signal.
  if (queue.length >= capacity) {
    if (isCritical) {
      const firstNonCritical = queue.findIndex((d) => !CRITICAL_KINDS.has(d.causedByKind));
      if (firstNonCritical !== -1) {
        const next = queue.slice();
        next.splice(firstNonCritical, 1);
        next.push(incoming);
        return { queue: next, dropped: true, coalesced: false };
      }
      // All critical already; allow bounded overrun to preserve every critical item.
      return { queue: [...queue, incoming], dropped: false, coalesced: false };
    }
    // Non-critical overflow: drop the oldest (bounded queue).
    return { queue: [...queue.slice(1), incoming], dropped: true, coalesced: false };
  }
  return { queue: [...queue, incoming], dropped: false, coalesced: false };
}

// ---------------------------------------------------------------------------
// Initial state
// ---------------------------------------------------------------------------

export function createInitialState(seed: SeedSnapshot): MaterializedState {
  const concepts = cloneState(seed.concepts);
  const frontier = seed.frontier ? [...seed.frontier] : [];
  const visualObjects = cloneState(seed.visualObjects);
  const permissions: Record<string, string[]> = {};
  const conversationLanguages = new Set<string>();
  for (const [id, node] of Object.entries(seed.concepts)) {
    permissions[id] = node.allowedActions ? [...node.allowedActions] : [];
    for (const lang of Object.keys(node.labelByLanguage ?? {})) conversationLanguages.add(lang);
  }
  return {
    schemaVersion: "0.1",
    sessionId: seed.sessionId,
    topicEpoch: seed.topicEpoch ?? 1,
    observationRevision: 0,
    semanticRevision: seed.semanticRevision ?? 1,
    sceneRevision: 0,
    activeConceptId: null,
    conversationLanguages: [...conversationLanguages].sort(),
    frontier,
    concepts,
    visualObjects,
    permissions,
    pendingProposals: [],
    provisionalSceneActions: [],
    committedSceneActions: [],
    needsPlan: [],
    observations: {},
    observationByEventId: {},
    lastCommittedEventId: null,
    commitCount: 0,
    sessionMonotonicMs: 0,
    telemetry: {
      renderAcks: 0,
      lastRenderAckEventId: null,
      renderErrors: 0,
      providerCapabilities: [],
      providerErrors: [],
    },
    stats: {
      total: 0,
      applied: 0,
      rejected: 0,
      skippedDuplicate: 0,
      interrupts: 0,
      epochAdvances: 0,
      coalesced: 0,
      droppedOldest: 0,
    },
    diagnostics: [],
    appliedEventIds: [],
  };
}

// ---------------------------------------------------------------------------
// SharedStore
// ---------------------------------------------------------------------------

export class SharedStore {
  private state: MaterializedState;
  private log: LogEntry[] = [];
  private seq = 0;
  private appliedFingerprints = new Map<string, string>();
  private subscribers: Subscriber[] = [];
  private nextSubscriberId = 1;

  constructor(seed: SeedSnapshot) {
    this.state = createInitialState(seed);
  }

  getState(): Readonly<MaterializedState> {
    return freezeState(cloneState(this.state));
  }

  getLog(): readonly LogEntry[] {
    return this.log.map((e) => ({ ...e }));
  }

  /** Strict ingestion. Throws SchemaViolation only when `strict` is true. */
  ingest(raw: unknown, opts?: { strict?: boolean }): IngestOutcome {
    let evt: Envelope;
    try {
      evt = parseEnvelope(raw);
    } catch (err) {
      const message = err instanceof SchemaViolation ? err.message : String(err);
      if (opts?.strict) throw err;
      this.log.push({ seq: this.nextSeq(), eventId: "(invalid)", kind: "(invalid)", outcome: "schema-invalid", detail: message });
      this.recordRejectedDiag(message);
      return { status: "schema-invalid", error: message };
    }

    // Session-scoping.
    if (evt.sessionId !== this.state.sessionId) {
      const detail = `event#${evt.eventId} sessionId "${evt.sessionId}" != store session "${this.state.sessionId}"`;
      this.log.push(this.logEntry(this.nextSeq(), evt.eventId, evt.kind, "rejected", detail, evt));
      this.recordRejectedDiag(detail);
      return { status: "rejected", reason: "session-mismatch", detail };
    }

    // Duplicate-ID idempotency (I7).
    if (this.appliedFingerprints.has(evt.eventId)) {
      if (this.appliedFingerprints.get(evt.eventId) !== envelopeFingerprint(evt)) {
        const detail = `event#${evt.eventId} repeated with differing content (id conflict)`;
        this.log.push(this.logEntry(this.nextSeq(), evt.eventId, evt.kind, "rejected", detail, evt));
        this.recordRejectedDiag(detail);
        return { status: "rejected", reason: "id-conflict", detail };
      }
      this.log.push(this.logEntry(this.nextSeq(), evt.eventId, evt.kind, "skipped-duplicate", "duplicate eventId; applied once", evt));
      this.state.stats.skippedDuplicate += 1;
      return { status: "skipped-duplicate", detail: "duplicate eventId; applied once" };
    }

    const { state: next, outcome } = reduceState(this.state, evt);

    if (outcome.status === "applied") {
      this.appliedFingerprints.set(evt.eventId, envelopeFingerprint(evt));
      this.log.push(this.logEntry(this.nextSeq(), evt.eventId, evt.kind, "applied", outcome.kind, evt));
      if (next.stats.total !== this.state.stats.total + 1) {
        // keep consistency; reduceState already incremented once
      }
    } else if (outcome.status === "rejected") {
      this.log.push(this.logEntry(this.nextSeq(), evt.eventId, evt.kind, "rejected", outcome.detail, evt));
    } else {
      this.log.push(this.logEntry(this.nextSeq(), evt.eventId, evt.kind, "skipped-duplicate", String(outcome.reason), evt));
    }

    this.state = next;
    if (outcome.status === "applied") {
      this.deliverToSubscribers(outcome.kind, evt);
    }
    return outcome;
  }

  /** Deterministic canonical snapshot + commit ID (Gate P1). */
  canonicalSnapshot(): { json: string; commitId: string; appliedEventIds: string[] } {
    const json = canonicalJson(this.state);
    const commitId = createHash("sha256")
      .update(json + "\n" + this.state.appliedEventIds.join("\n"))
      .digest("hex");
    return { json, commitId, appliedEventIds: [...this.state.appliedEventIds] };
  }

  subscribe(capacity = 64): { id: number; unsubscribe: () => void } {
    const sub: Subscriber = { id: this.nextSubscriberId++, queue: [], capacity, dropped: 0, coalesced: 0 };
    this.subscribers.push(sub);
    return {
      id: sub.id,
      unsubscribe: () => {
        this.subscribers = this.subscribers.filter((x) => x.id !== sub.id);
      },
    };
  }

  subscriberStats(subscriberId: number): { dropped: number; coalesced: number; length: number } {
    const sub = this.subscribers.find((x) => x.id === subscriberId);
    return sub ? { dropped: sub.dropped, coalesced: sub.coalesced, length: sub.queue.length } : { dropped: 0, coalesced: 0, length: 0 };
  }

  private nextSeq(): number {
    this.seq += 1;
    return this.seq;
  }

  /** Build a canonical-log entry, optionally carrying the full validated
   *  envelope so the log is self-replayable and authorship survives. */
  private logEntry(
    seq: number,
    eventId: string,
    kind: string,
    outcome: LogEntry["outcome"],
    detail: string,
    evt?: Envelope,
  ): LogEntry {
    const entry: LogEntry = { seq, eventId, kind, outcome, detail };
    if (evt) {
      entry.schemaVersion = evt.schemaVersion;
      entry.sessionId = evt.sessionId;
      entry.turnId = evt.turnId;
      entry.source = evt.source;
      entry.topicEpoch = evt.topicEpoch;
      entry.observationRevision = evt.observationRevision;
      entry.semanticRevision = evt.semanticRevision;
      entry.sceneRevision = evt.sceneRevision;
      entry.emittedAtMs = evt.emittedAtMs;
      entry.correlationId = evt.correlationId;
      entry.payload = evt.payload;
    }
    return entry;
  }

  private recordRejectedDiag(detail: string): void {
    this.state.stats.rejected += 1;
    this.state.diagnostics.push(detail);
  }

  private deliverToSubscribers(kind: EventKind, evt: Envelope): void {
    const isFinal = (evt.payload as { isFinal?: boolean })?.isFinal === true;
    for (const sub of this.subscribers) {
      const delivery: SubscriberDelivery = {
        seq: this.state.appliedEventIds.length,
        snapshotRevision: this.state.sessionMonotonicMs,
        causedByKind: kind,
        eventId: evt.eventId,
        correlationId: evt.correlationId,
        languageTag: (evt.payload as { languageTag?: string })?.languageTag ?? null,
        isFinal,
      };
      const res = offerToQueue(sub.queue, delivery, sub.capacity);
      sub.queue = res.queue;
      if (res.coalesced) sub.coalesced += 1;
      if (res.dropped) sub.dropped += 1;
    }
  }
}

export type { ApplyOutcome } from "./reducer.ts";