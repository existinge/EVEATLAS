# ATLAS LOOP — Agent Orchestration

**State: implemented local foundation, external model adapters NOT wired.** Do not mistake an accepted review CLI entry for proof that Codex executed.

## Architecture
An objective produces a validated dependency graph; worker dispatch produces artifacts; deterministic checks accept/reject output; retry and budget policies bound work; final state ALWAYS waits for Codex. SQLite persists tasks, runs, events, approval requests and review receipts under `private/`.

Primary file: `tools/atlas_loop.py`. It uses standard-library Python only and is separate from the existing Signal Desk ingestion pipeline.

## Currently implemented
- SQLite-backed run/task/event state
- DAG validation, dependency-aware scheduling, bounded attempts
- Deterministic local fixture worker
- Restricted opt-in unittest command worker
- Output contract verification
- Pause, resume, cancel commands
- Explicit approval records
- Mandatory `AWAITING_FINAL_REVIEW` state and Codex-only reviewer label
- Status JSON, model preferences and provider stubs that FAIL CLOSED

## Not implemented yet
- Real Codex invocation and authenticated review receipt (CLI review is **manual attestation only**, not cryptographic identity verification)
- DeepSeek or Gemini credentials, supported endpoint integration and measured prices
- Jev/TypeSafe adapter or decisions
- Autonomous generation of repair instructions and automatic worker reassignment
- Crash-safe external job reconciliation, true concurrent DAG scheduling
- Background worker service, notifications, Mission Control web UI
- Enforced process sandboxing for arbitrary source code, complete monetary accounting

## Manual local demonstration
```bash
python tools/atlas_loop.py --db private/atlas-loop.sqlite3 start examples/atlas-loop-plan.json
python tools/atlas_loop.py --db private/atlas-loop.sqlite3 tick RUN_ID
python tools/atlas_loop.py --db private/atlas-loop.sqlite3 tick RUN_ID
python tools/atlas_loop.py --db private/atlas-loop.sqlite3 status RUN_ID
```
The sample run stops in `AWAITING_FINAL_REVIEW`. Only after a real review, manually record its result with `review RUN_ID approved --evidence "reference to actual Codex findings"`. This command is not itself proof Codex ran.

## Model policy
DeepSeek Flash: default proposed implementation; Gemini Flash: proposed planning and alternative; Codex: mandatory independent final reviewer. Exact versions, official identifiers, authentication and available quotas must be verified before activation. If Codex unavailable, remain awaiting review. Optional Jev: decisions only, NEVER authoritative permission granting.

## Next integration gate
Develop supported provider adapters with explicit credentials outside Git, actual invocation receipts, timeout/cancel handling, per-run cost reservations and verified Codex review. Require an independent multi-worker fail/repair/pass integration test. No autonomous publishing, spending or production operations.

## Security warning
`--allow-commands` is meant only for trusted plans; passing Python tests to a subprocess is NOT sandboxing. Run only in isolated authorized workspaces. Never execute untrusted repository code on a machine with sensitive credentials.
