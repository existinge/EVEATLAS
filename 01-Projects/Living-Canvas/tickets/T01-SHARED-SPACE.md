# T01 — Shared workspace reducer + event replay

Timebox: 20–30 minutes after preflight. Status: NOT STARTED. Depends on: recorded T00/P0 acceptance.

## Build
Implement a TypeScript shared-state core with append-only events, session/epoch/revision scoping, reducer-owned materialized state, bounded subscriptions, and replay from fixtures. Define discriminated union event types and runtime schema checks. Use in-memory state first. Store DECIDER_PROPOSAL as provisional data. Applying it must never commit a scene action. T02 owns coordinator validation.

## Protocol source
Read [PROTOCOL.md](../PROTOCOL.md), [seed concepts](../fixtures/seed-concepts.json), [events e1–e8](../fixtures/sample-events.jsonl) and [fixture expectations](../fixtures/README.md).
Deliver event bus, reducer, fixture runner and test. Prioritize exact reproducibility; no background database/server.

## Test gate P1
- Run same fixture twice → byte-equivalent normalized final scene state.
- Duplicate event IDs cannot append duplicate entries or apply duplicate changes.
- Replay covers all e1–e8 expectations, including proposal invalidation, interruption, epoch advance, stale rejection, preserved Thai text and NEEDS_PLAN.
- Events have independently versioned observation/semantic/scene revisions.
- Unknown kind and malformed JSON produce errors, not silent acceptance.
- Late event for old topic epoch cannot mutate current scene.
- High-frequency provisional observations can coalesce; committed/interrupt events are never dropped.
- Unrecognized multilingual concept remains represented as UNKNOWN/NEEDS_PLAN, not falsely classified.

## Out of scope
Use TypeScript and lightweight local test tooling only. Provider calls/SDKs, credentials, voice, React, Vite, tldraw, external persistence and T02 coordinator work are outside this ticket.

## Stop
When P1 passes, report the actual files, commands/test output, known gaps and recommend T02. Do not immediately implement T02.
