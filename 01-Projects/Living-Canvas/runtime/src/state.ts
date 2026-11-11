// Materialized shared-state model (PROTOCOL.md "State snapshot outline").
//
// The materialized state is the latest validated snapshot derived from the
// seed + appended events. It is reducer-owned and deterministic. Advisory
// decider proposals live in `pendingProposals` (provisional) and only a
// coordinator SCENE_COMMITTED moves anything into `committedSceneActions`.

export const SCHEMA_VERSION = "0.1";

export type ConceptStatus = "prepared" | "active" | "retired";

export interface ConceptNode {
  conceptId: string;
  labelByLanguage: Record<string, string>;
  relationships: { type: string; target: string; source?: string }[];
  visualRecipeId: string;
  allowedActions: string[];
  status: ConceptStatus;
  planRevision: number;
  expiresAtSessionMs: number;
}

export interface VisualObject {
  objectId: string;
  conceptId: string;
  recipeId: string;
  position: { x: number; y: number };
  attention: number;
}

export type ActionType =
  | "show" | "hide" | "emphasize" | "deEmphasize" | "connect" | "move"
  | "layout" | "setParameter" | "revealHint" | "transitionRecipe" | "clearProvisional";

export const PERMITTED_ACTION_TYPES: readonly ActionType[] = [
  "show", "hide", "emphasize", "deEmphasize", "connect", "move",
  "layout", "setParameter", "revealHint", "transitionRecipe", "clearProvisional",
];

export type Stoplight = "GREEN" | "YELLOW" | "RED";

/** A decider proposal, held provisionally and NOT authoritative (I2). */
export interface VisualProposal {
  id: string;                    // proposalId
  correlationId: string;
  topicEpoch: number;
  observationRevision: number;
  semanticRevision: number;
  targetObjectIds: string[];
  actionType: ActionType;
  parameters: Record<string, unknown>;
  confidence: number | null;
  evidenceEventIds: string[];
  reversible: boolean;
  expiresAtSessionMs: number;
  createdAtMs: number;
  status: "pending" | "revoked";
  stoplight: Stoplight;
  sourceEventId: string;
}

/** Authoritative scene change; only produced by SCENE_COMMITTED (I1). */
export interface CommittedSceneAction {
  actionId: string;
  proposalId: string;
  correlationId: string;
  topicEpoch: number;
  actionType: ActionType;
  targetObjectIds: string[];
  parameters: Record<string, unknown>;
  reversible: boolean;
  sourceEventId: string;
}

/** Coordinator-owned speculative (pre-commit) preview, cleared on interrupt. */
export interface ProvisionalSceneAction {
  actionId: string;
  proposalId: string;
  correlationId: string;
  topicEpoch: number;
  actionType: ActionType;
  targetObjectIds: string[];
  parameters: Record<string, unknown>;
  reversible: boolean;
  sourceEventId: string;
}

/** Advisory observation record (evidence, not truth). */
export interface ObservationRecord {
  correlationId: string;
  languageTag: string;
  text: string;
  isFinal: boolean;
  topicEpoch: number;
  matchedConceptId: string | null;
  matchedLabel: string | null;
  sourceEventId: string;
}

/** I10: a missing semantic match yields a safe HOLD/NEEDS_PLAN record. */
export interface NeedsPlan {
  correlationId: string;
  text: string;
  languageTag: string | null;
  topicEpoch: number;
  reason: string;
  sourceEventId: string;
}

export interface RendererTelemetry {
  renderAcks: number;
  lastRenderAckEventId: string | null;
  renderErrors: number;
  providerCapabilities: string[];
  providerErrors: string[];
}

export interface StoreStats {
  total: number;
  applied: number;
  rejected: number;
  skippedDuplicate: number;
  interrupts: number;
  epochAdvances: number;
  coalesced: number;
  droppedOldest: number;
}

export interface MaterializedState {
  schemaVersion: "0.1";
  sessionId: string;
  topicEpoch: number;
  observationRevision: number;
  semanticRevision: number;
  sceneRevision: number;
  activeConceptId: string | null;
  conversationLanguages: string[];
  frontier: string[];
  concepts: Record<string, ConceptNode>;
  visualObjects: Record<string, VisualObject>;
  permissions: Record<string, string[]>;
  pendingProposals: VisualProposal[];
  provisionalSceneActions: ProvisionalSceneAction[];
  committedSceneActions: CommittedSceneAction[];
  needsPlan: NeedsPlan[];
  observations: Record<string, ObservationRecord>;
  observationByEventId: Record<string, string>;
  lastCommittedEventId: string | null;
  commitCount: number;
  sessionMonotonicMs: number;      // latest emittedAtMs seen (deterministic)
  telemetry: RendererTelemetry;
  stats: StoreStats;
  diagnostics: string[];
  appliedEventIds: string[];       // correlation between snapshot and log
  // Advisory-only collections (log/journal that never mutates the scene).
  userActions?: { eventId: string; actionType: string; targetObjectIds: string[]; correlationId: string }[];
  tentativePlans?: { conceptId: string; sourceEventId: string; topicEpoch: number }[];
  frontierInterest?: { conceptId: string | null; sourceEventId: string }[];
}

/** A queued, coalescible delivery to a subscriber. */
export interface SubscriberDelivery {
  seq: number;
  snapshotRevision: number;
  causedByKind: string;
  eventId: string;
  correlationId: string;
  languageTag: string | null;
  isFinal: boolean;
}

/** Parsed view of fixtures/seed-concepts.json. */
export interface SeedSnapshot {
  schemaVersion: "0.1";
  sessionId: string;
  topicEpoch: number;
  semanticRevision: number;
  frontier: string[];
  concepts: Record<string, ConceptNode>;
  visualObjects: Record<string, VisualObject>;
}

export function cloneState<T>(value: T): T {
  return structuredClone(value);
}

/** Deep-freeze a state so subscribers cannot mutate it. */
export function freezeState(state: MaterializedState): Readonly<MaterializedState> {
  const seen = new WeakSet<object>();
  const freeze = (v: unknown): unknown => {
    if (v !== null && typeof v === "object" && !seen.has(v as object)) {
      seen.add(v as object);
      Object.freeze(v);
      for (const key of Object.keys(v as Record<string, unknown>)) {
        freeze((v as Record<string, unknown>)[key]);
      }
    }
    return v;
  };
  return freeze(state) as Readonly<MaterializedState>;
}