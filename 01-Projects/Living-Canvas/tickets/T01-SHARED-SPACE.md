# T01 — Shared workspace reducer + event replay

Timebox: 20–30 minutes after preflight. Status: NOT STARTED. Depends on: T00/P0.

## Build
Implement a TypeScript shared-state core with append-only events, session/epoch/revision scoping, reducer-owned materialized state, bounded subscriptions, and replay from fixtures. Define discriminated union event types and runtime schema checks. Use in-memory state first. The canonical current scene is separate from speculative predictions.

## Protocol source
../PROTOCOL.md; ../fixtures/seed-concepts.json; ../fixtures/sample-events.jsonl.
Deliver event bus, reducer, fixture runner and test. Prioritize exact reproducibility; no background database/server.

## Test gate P1
- Run same fixture twice → byte-equivalent normalized final scene state.
- Duplicate event ID cannot create duplicate changes.
- Events have independently versioned observation/semantic/scene revisions.
- Unknown kind and malformed JSON produce errors, not silent acceptance.
- Late event for old topic epoch cannot mutate current scene.
- High-frequency provisional observations can coalesce; committed/interrupt events are never dropped.
- Unrecognized multilingual concept remains represented as UNKNOWN/NEEDS_PLAN, not falsely classified.

## Out of scope
LLMs, voice, tldraw rendering, probabilistic model confidence benchmarks, external persistence.

## Stop
When P1 passes, report the actual files, commands/test output, known gaps and recommend T02. Do not immediately implement T02.
