# Shared space protocol v0.1 — normative draft

This contract is **proposed**. It is not implemented or benchmarked. Use this spec to generate schemas, validators, tests and source interfaces in T01. If a revision is needed, document it in DECISIONS.md and require a compatible migration.

## Separation
Event stream is append-only evidence about what happened or was proposed. Materialized state is the latest validated snapshot. An event is NOT a command merely because it was emitted by a model. Only coordinator-generated SCENE_COMMITTED alters authoritative canvas state.

## Minimum event envelope

~~~json
{
  "schemaVersion": "0.1",
  "eventId": "evt-0001",
  "sessionId": "s-demo",
  "turnId": "turn-01",
  "kind": "OBSERVATION_PARTIAL",
  "source": "stt",
  "topicEpoch": 1,
  "observationRevision": 4,
  "semanticRevision": 2,
  "sceneRevision": 7,
  "emittedAtMs": 2400,
  "correlationId": "obs-4",
  "payload": {
    "languageTag": "ja-JP",
    "text": "次の電車に",
    "isFinal": false
  }
}
~~~

Times use milliseconds relative to a session monotonic origin inside a single machine trace; wall-clock timestamps are metadata only. Revisions are integers local to a session and are independently incremented by the named authority. A separate global monotonically increasing append sequence is assigned by the store. Never compare timestamps across machines without clock correlation.

## Event kinds / writer authorities
- OBSERVATION_PARTIAL, OBSERVATION_FINAL, OBSERVATION_CORRECTION: provider/STT adapter; advisory until confirmed.
- USER_ACTION, USER_INTERRUPT: UI/voice adapter; interrupt immediately invalidates speculative actions in old turn/observation scope.
- PLAN_PROPOSED, PLAN_COMMITTED: planner proposes; state coordinator validates and commits semantic revision.
- DECIDER_PROPOSAL, DECIDER_UNCERTAIN, FRONTIER_INTEREST: decider advisory; cannot directly mutate canonical scene or semantic plan.
- SCENE_PROVISIONAL, SCENE_COMMITTED, SCENE_REVERTED: coordinator-owned.
- RENDER_ACK, RENDER_ERROR: renderer telemetry, not semantic authority.
- TOPIC_EPOCH_ADVANCED: coordinator-owned on confirmed topic or explicit human change.
- PROVIDER_CAPABILITY, PROVIDER_ERROR: adapter-owned.

## State snapshot outline

~~~json
{
  "sessionId": "s-demo",
  "topicEpoch": 1,
  "observationRevision": 4,
  "semanticRevision": 2,
  "sceneRevision": 7,
  "activeConceptId": "travel.train.board",
  "conversationLanguages": ["ja-JP", "en-US"],
  "frontier": ["travel.train.ticket", "travel.train.platform"],
  "concepts": {},
  "visualObjects": {},
  "permissions": {},
  "pendingProposals": [],
  "lastCommittedEventId": "evt-0000"
}
~~~

## Concept node
Required: id (stable and language-neutral), labelByLanguage (BCP47 keys, optional per-language), relationships (typed edges with sources), visualRecipeId, allowedActions, status [prepared|active|retired], planRevision, expiresAtSessionMs. Concept IDs are pointers, NOT cross-language equivalence claims. Preserve untranslated/polysemous distinctions and text spans.

## Visual proposal
Required: id, correlationId, topicEpoch, observationRevision, semanticRevision, targetObjectIds, actionType, parameters, confidence (0..1 or null when uncalibrated), evidenceEventIds, reversible, expiresAtSessionMs.
Permitted actionTypes in v0.1: show, hide, emphasize, deEmphasize, connect, move, layout, setParameter, revealHint, transitionRecipe, clearProvisional. The renderer decides actual animation paths.

## Stoplight states
GREEN: authorized and fresh; stable visual actions permitted.
YELLOW: ambiguous or partial; permit only local reversible non-deceptive emphasis/hints. No new factual labels or irreversible object deletion.
RED: stale, conflicting, unsupported action or ungrounded concept; reject and possibly request PLAN_REFRESH.

Stoplight is a deterministic policy over authorizations, evidence state, and confidence calibration. Never treat raw probability alone as sufficient permission.

## Safety invariants
I1. Only validated coordinator commits change authoritative scene.
I2. No decider proposal creates unplanned concept meaning or changes an object's semantic identity.
I3. A proposal with non-current topicEpoch is rejected.
I4. Proposals referencing a revoked semanticRevision or expired plan cannot commit.
I5. OBSERVATION_CORRECTION revokes dependent provisional mutations (via correlation/evidence linkage).
I6. A new topic never inherits old action permissions by accident.
I7. Duplicate event IDs or duplicate committed proposal IDs are idempotent.
I8. Log human-visible what-was-shown vs what-was-predicted separately.
I9. Renderer execution is not blocked by pending LLM/decider futures.
I10. A missing semantic match yields safe HOLD/NEEDS_PLAN, not hallucinated canvas content.

## Concurrency mechanics
One in-memory state store for first prototype. Deliver each event to subscriber queues with bounded size and coalescing of high-frequency nonfinal transcripts; never drop USER_INTERRUPT, TOPIC_EPOCH_ADVANCED, or SCENE_COMMITTED. Commit state via serial reducer, no shared mutable objects from model adapters. Version compare+commit must be atomic; optimistic checks only, no semantic model call in commit path. Record event log for deterministic replay. Distinguish stale source events (observations) from stale action commits.

## Failure/recovery
If provider goes silent: keep speaking status and existing stable visuals, not invented new hints. If planner lags: decider navigates current valid frontier, while unrecognized concepts trigger NEEDS_PLAN and a neutral placeholder. If renderer fails: state remains authoritative and RENDER_ERROR is recorded. If event replay mismatch: block integration stage, fix reducer before adding models.

See fixtures/ for intentionally minimal sample data; acceptance tests are in GATES.md.
