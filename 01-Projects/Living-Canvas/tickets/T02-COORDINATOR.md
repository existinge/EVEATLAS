# T02 — Deterministic coordinator / stoplight backplate

Timebox: 15–25 minutes. Status: NOT STARTED. Depends on: T01/P1.

## Build
Implement validateProposal(proposal, snapshot) with GREEN/YELLOW/RED and explicit reasons; atomic commit of accepted scene actions; bounded reversible preview store. All logic is local code. Treat semantic proposals from planner as plans that require separate semantic revision commits. The fast decider cannot claim topic authority.

## Mandatory cases
GREEN: eligible branch, existing object, fresh versions and allowed action → commit.
YELLOW: incomplete but eligible evidence → only reversible emphasis/ghost/hint; no factual label added.
RED: stale topic epoch, revoked plan, expired permission, unknown object, unsupported action, incompatible evidence → reject.
USER_INTERRUPT: invalidate outstanding partial-turn proposal, remove provisional visual state, retain stable scene.
USER_ACTION: user overrides provisional suggestion.
Out-of-order plan update cannot regress semantic revision.

## Test gate P2
Produce positive, negative and duplicate-action tests; no model in test loop. A rejected proposal must record why and preserve sceneRevision. A committed proposal increments sceneRevision once and is idempotent.

## Forbidden
Another model for coordination, network hop added to hot path, using naked confidence probability as authority, silently relaxing policy to make tests pass.

## Stop
Complete P2 proof and hand off T03; do not implement canvas yet.
