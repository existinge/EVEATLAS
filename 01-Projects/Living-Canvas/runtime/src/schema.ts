// Event envelope + per-kind payload validation, per PROTOCOL.md v0.1.
//
// The envelope is the protocol's min event shape. Validation is strict and
// reject-with-diagnostic, never silent (Gate P1): unknown kinds and malformed
// envelopes produce errors.

export const SCHEMA_VERSION = "0.1" as const;
export type SchemaVersion = typeof SCHEMA_VERSION;

export const EVENT_KINDS = [
  "OBSERVATION_PARTIAL", "OBSERVATION_FINAL", "OBSERVATION_CORRECTION",
  "USER_ACTION", "USER_INTERRUPT",
  "PLAN_PROPOSED", "PLAN_COMMITTED",
  "DECIDER_PROPOSAL", "DECIDER_UNCERTAIN", "FRONTIER_INTEREST",
  "SCENE_PROVISIONAL", "SCENE_COMMITTED", "SCENE_REVERTED",
  "RENDER_ACK", "RENDER_ERROR",
  "TOPIC_EPOCH_ADVANCED",
  "PROVIDER_CAPABILITY", "PROVIDER_ERROR",
] as const;

export type EventKind = (typeof EVENT_KINDS)[number];

/** Kinds that must never be dropped by bounded/coalescing queues (concurrency policy). */
export const CRITICAL_KINDS: ReadonlySet<EventKind> = new Set<EventKind>([
  "USER_INTERRUPT",
  "TOPIC_EPOCH_ADVANCED",
  "SCENE_COMMITTED",
]);

export interface Envelope {
  schemaVersion: SchemaVersion;
  eventId: string;
  sessionId: string;
  turnId: string;
  kind: EventKind;
  source: string;
  topicEpoch: number;
  observationRevision: number;
  semanticRevision: number;
  sceneRevision: number;
  emittedAtMs: number;
  correlationId: string;
  payload: Record<string, unknown>;
}

export class SchemaViolation extends Error {
  readonly violations: string[];
  constructor(violations: string[]) {
    super("[schema] " + violations.join("; "));
    this.name = "SchemaViolation";
    this.violations = violations;
  }
}

// ---------------------------------------------------------------------------
// Primitive checks
// ---------------------------------------------------------------------------

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function isNonEmptyString(v: unknown): v is string {
  return typeof v === "string" && v.length > 0;
}

function isFiniteNumber(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}

function isNonNegativeInt(v: unknown): v is number {
  return isFiniteNumber(v) && Number.isInteger(v) && v >= 0;
}

function isStringArray(v: unknown): v is string[] {
  return Array.isArray(v) && v.every((x) => isNonEmptyString(x));
}

// ---------------------------------------------------------------------------
// Per-kind payload validators (protocol v0.1)
// ---------------------------------------------------------------------------

type PayloadValidator = (payload: Record<string, unknown>, errors: string[]) => void;

const V_OBSERVATION: PayloadValidator = (p, e) => {
  if (!isNonEmptyString(p.languageTag)) e.push("payload.languageTag must be a non-empty string");
  if (typeof p.text !== "string") e.push("payload.text must be a string");
  if (typeof p.isFinal !== "boolean") e.push("payload.isFinal must be a boolean");
};

const V_CORRECTION: PayloadValidator = (p, e) => {
  if (!isNonEmptyString(p.languageTag)) e.push("payload.languageTag must be a non-empty string");
  if (typeof p.text !== "string") e.push("payload.text must be a string");
  if (typeof p.isFinal !== "boolean") e.push("payload.isFinal must be a boolean");
  if (!Array.isArray(p.supersedes) || !p.supersedes.every((x) => isNonEmptyString(x))) {
    e.push("payload.supersedes must be a string array");
  }
};

const V_USER_INTERRUPT: PayloadValidator = (p, e) => {
  if (p.reason !== undefined && typeof p.reason !== "string") e.push("payload.reason must be a string");
};

const V_USER_ACTION: PayloadValidator = (p, e) => {
  if (!isNonEmptyString(p.actionType)) e.push("payload.actionType must be a non-empty string");
  if (!isStringArray(p.targetObjectIds)) e.push("payload.targetObjectIds must be a string array");
};

const V_DECIDER_PROPOSAL: PayloadValidator = (p, e) => {
  if (!isNonEmptyString(p.proposalId)) e.push("payload.proposalId must be a non-empty string");
  if (!isStringArray(p.targetObjectIds)) e.push("payload.targetObjectIds must be a string array");
  if (!isNonEmptyString(p.actionType)) e.push("payload.actionType must be a non-empty string");
  if (p.confidence !== null && !isFiniteNumber(p.confidence)) {
    e.push("payload.confidence must be a finite number or null");
  }
  if (!isStringArray(p.evidenceEventIds)) e.push("payload.evidenceEventIds must be a string array");
  if (typeof p.reversible !== "boolean") e.push("payload.reversible must be a boolean");
  if (!isFiniteNumber(p.expiresAtSessionMs)) e.push("payload.expiresAtSessionMs must be a finite number");
  if (p.parameters !== undefined && !isPlainObject(p.parameters)) e.push("payload.parameters must be an object");
};

const V_DECIDER_UNCERTAIN: PayloadValidator = (p, e) => {
  if (!isNonEmptyString(p.reason)) e.push("payload.reason must be a non-empty string");
  if (p.text !== undefined && typeof p.text !== "string") e.push("payload.text must be a string");
  if (p.languageTag !== undefined && !isNonEmptyString(p.languageTag)) {
    e.push("payload.languageTag must be a non-empty string");
  }
};

const V_PLAN: PayloadValidator = (p, e) => {
  if (!isNonEmptyString(p.conceptId)) e.push("payload.conceptId must be a non-empty string");
  if (p.planRevision !== undefined && !isNonNegativeInt(p.planRevision)) {
    e.push("payload.planRevision must be a non-negative integer");
  }
};

const V_SCENE_COMMIT: PayloadValidator = (p, e) => {
  if (!isNonEmptyString(p.proposalId)) e.push("payload.proposalId must be a non-empty string");
  if (!isStringArray(p.targetObjectIds)) e.push("payload.targetObjectIds must be a string array");
  if (!isNonEmptyString(p.actionType)) e.push("payload.actionType must be a non-empty string");
  if (typeof p.reversible !== "boolean") e.push("payload.reversible must be a boolean");
  if (p.parameters !== undefined && !isPlainObject(p.parameters)) e.push("payload.parameters must be an object");
  if (p.correlationId !== undefined && !isNonEmptyString(p.correlationId)) {
    e.push("payload.correlationId must be a non-empty string");
  }
};

const V_SCENE_REVERT: PayloadValidator = (p, e) => {
  if (p.proposalId !== undefined && !isNonEmptyString(p.proposalId)) {
    e.push("payload.proposalId must be a non-empty string");
  }
  if (p.correlationId !== undefined && !isNonEmptyString(p.correlationId)) {
    e.push("payload.correlationId must be a non-empty string");
  }
};

const V_EPOCH_ADVANCE: PayloadValidator = (p, e) => {
  if (p.reason !== undefined && typeof p.reason !== "string") e.push("payload.reason must be a string");
  if (p.languageTag !== undefined && !isNonEmptyString(p.languageTag)) {
    e.push("payload.languageTag must be a non-empty string");
  }
};

const V_RENDER_ERR: PayloadValidator = (p, e) => {
  if (p.message !== undefined && typeof p.message !== "string") e.push("payload.message must be a string");
};

const V_PROVIDER_ERR: PayloadValidator = (p, e) => {
  if (!isNonEmptyString(p.message)) e.push("payload.message must be a non-empty string");
};

const V_EMPTY: PayloadValidator = () => {};

const KIND_META: Record<EventKind, { stream: "obs" | "sem" | "scene" | "topic" | "none"; validator: PayloadValidator }> = {
  OBSERVATION_PARTIAL: { stream: "obs", validator: V_OBSERVATION },
  OBSERVATION_FINAL: { stream: "obs", validator: V_OBSERVATION },
  OBSERVATION_CORRECTION: { stream: "obs", validator: V_CORRECTION },
  USER_ACTION: { stream: "obs", validator: V_USER_ACTION },
  USER_INTERRUPT: { stream: "obs", validator: V_USER_INTERRUPT },
  PLAN_PROPOSED: { stream: "sem", validator: V_PLAN },
  PLAN_COMMITTED: { stream: "sem", validator: V_PLAN },
  DECIDER_PROPOSAL: { stream: "none", validator: V_DECIDER_PROPOSAL },
  DECIDER_UNCERTAIN: { stream: "none", validator: V_DECIDER_UNCERTAIN },
  FRONTIER_INTEREST: { stream: "none", validator: V_EMPTY },
  SCENE_PROVISIONAL: { stream: "scene", validator: V_SCENE_COMMIT },
  SCENE_COMMITTED: { stream: "scene", validator: V_SCENE_COMMIT },
  SCENE_REVERTED: { stream: "scene", validator: V_SCENE_REVERT },
  RENDER_ACK: { stream: "none", validator: V_EMPTY },
  RENDER_ERROR: { stream: "none", validator: V_RENDER_ERR },
  TOPIC_EPOCH_ADVANCED: { stream: "topic", validator: V_EPOCH_ADVANCE },
  PROVIDER_CAPABILITY: { stream: "none", validator: V_EMPTY },
  PROVIDER_ERROR: { stream: "none", validator: V_PROVIDER_ERR },
};

export { KIND_META };

// ---------------------------------------------------------------------------
// Envelope parsing
// ---------------------------------------------------------------------------

/**
 * Strict, non-silent envelope validation. Throws SchemaViolation on any
 * violation (unknown kind, missing/wrong-typed fields, malformed payload).
 */
export function parseEnvelope(raw: unknown): Envelope {
  const errors: string[] = [];
  if (!isPlainObject(raw)) {
    // Strict schema validation surfaces errors, never silent. A raw JSON
    // string / number / null / boolean is schema-invalid before any field
    // access; the message must be pushed into `errors` (not passed as
    // `fail`'s optional Envelope value) so SchemaViolation is thrown.
    errors.push("event must be a JSON object");
    return fail(errors);
  }

  const r = raw as Record<string, unknown>;

  if (r.schemaVersion !== SCHEMA_VERSION) errors.push(`schemaVersion must be "${SCHEMA_VERSION}"`);
  const kind = r.kind as EventKind;
  if (typeof kind !== "string" || !(EVENT_KINDS as readonly string[]).includes(kind)) {
    errors.push(`unknown event kind: ${String(r.kind)}`);
  }
  if (!isNonEmptyString(r.eventId)) errors.push("eventId must be a non-empty string");
  if (!isNonEmptyString(r.sessionId)) errors.push("sessionId must be a non-empty string");
  if (!isNonEmptyString(r.turnId)) errors.push("turnId must be a non-empty string");
  if (!isNonEmptyString(r.source)) errors.push("source must be a non-empty string");
  if (!isNonEmptyString(r.correlationId)) errors.push("correlationId must be a non-empty string");
  if (!isNonNegativeInt(r.topicEpoch)) errors.push("topicEpoch must be a non-negative integer");
  if (!isNonNegativeInt(r.observationRevision)) errors.push("observationRevision must be a non-negative integer");
  if (!isNonNegativeInt(r.semanticRevision)) errors.push("semanticRevision must be a non-negative integer");
  if (!isNonNegativeInt(r.sceneRevision)) errors.push("sceneRevision must be a non-negative integer");
  if (!isFiniteNumber(r.emittedAtMs) || r.emittedAtMs < 0) {
    errors.push("emittedAtMs must be a non-negative finite number");
  }
  if (!isPlainObject(r.payload)) errors.push("payload must be an object");

  if (errors.length > 0) return fail(errors);

  const payload = r.payload as Record<string, unknown>;
  if (typeof kind === "string" && (EVENT_KINDS as readonly string[]).includes(kind)) {
    KIND_META[kind as EventKind].validator(payload, errors);
  }
  return fail(errors, {
    schemaVersion: SCHEMA_VERSION,
    eventId: r.eventId as string,
    sessionId: r.sessionId as string,
    turnId: r.turnId as string,
    kind: kind as EventKind,
    source: r.source as string,
    topicEpoch: r.topicEpoch as number,
    observationRevision: r.observationRevision as number,
    semanticRevision: r.semanticRevision as number,
    sceneRevision: r.sceneRevision as number,
    emittedAtMs: r.emittedAtMs as number,
    correlationId: r.correlationId as string,
    payload,
  });
}

function fail(errors: string[], value?: Envelope): Envelope {
  if (errors.length > 0) throw new SchemaViolation(errors);
  return value as Envelope;
}

/** Canonical (deterministic) JSON of one envelope, used for duplicate detection. */
export function envelopeFingerprint(evt: Envelope): string {
  // Re-serialize the envelope in a stable shape.
  const t = evt;
  const ordered: Record<string, unknown> = {
    schemaVersion: t.schemaVersion,
    eventId: t.eventId,
    sessionId: t.sessionId,
    turnId: t.turnId,
    kind: t.kind,
    source: t.source,
    topicEpoch: t.topicEpoch,
    observationRevision: t.observationRevision,
    semanticRevision: t.semanticRevision,
    sceneRevision: t.sceneRevision,
    emittedAtMs: t.emittedAtMs,
    correlationId: t.correlationId,
    payload: t.payload,
  };
  return canonicalizeForFingerprint(ordered);
}

function canonicalizeForFingerprint(value: unknown): string {
  if (Array.isArray(value)) return "[" + value.map(canonicalizeForFingerprint).join(",") + "]";
  if (value !== null && typeof value === "object") {
    const src = value as Record<string, unknown>;
    return "{" + Object.keys(src).sort().map((k) => JSON.stringify(k) + ":" + canonicalizeForFingerprint(src[k])).join(",") + "}";
  }
  return JSON.stringify(value);
}