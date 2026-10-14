# ATLAS LOOP — Agent Orchestration

**State: implemented local foundation; one opt-in OpenClaw gateway provider (off by default, tested only against a fake gateway). Direct Gemini/Codex/DeepSeek adapters NOT wired.** Do not mistake an accepted review CLI entry for proof that Codex executed.

## Architecture
An objective produces a validated dependency graph; worker dispatch produces artifacts; deterministic checks accept/reject output; retry and budget policies bound work; final state ALWAYS waits for Codex. SQLite persists tasks, runs, events, approval requests and review receipts under `private/`.

Primary file: `tools/atlas_loop.py`. It uses standard-library Python only and is separate from the existing Signal Desk ingestion pipeline.

## Currently implemented
- SQLite-backed run/task/event state
- DAG validation, dependency-aware scheduling, bounded attempts
- Deterministic local fixture worker
- Restricted opt-in unittest command worker
- Output contract verification
- Exponential retry backoff (`next_attempt_at`), retry cap ends in `FAILED`
- `atlas_brain` retry advice: repeated identical failure switches to an alternate available worker or fails closed; critical cost incidents block the run
- `run` command: ticks on one DB connection until complete/awaiting review/blocked/paused/cancelled/failed, sleeping until the next backoff deadline, capped by `--max-ticks` and `--max-seconds`
- Pause, resume, cancel with validated status transitions (cannot resume CANCELLED/COMPLETE/FAILED)
- Explicit approval records
- Mandatory `AWAITING_FINAL_REVIEW` state and Codex-only reviewer label
- Status JSON; Gemini/Codex stubs FAIL CLOSED (registered unavailable)
- Opt-in OpenClaw gateway provider (`tools/atlas_providers.py`), see below

## Not implemented yet
- Real Codex invocation and authenticated review receipt (CLI review is **manual attestation only**, not cryptographic identity verification)
- Any live model call: the OpenClaw path is untested end-to-end (fake gateway only)
- Jev/TypeSafe adapter or decisions
- Autonomous generation of repair instructions (reassignment only among available registered workers)
- Crash-safe external job reconciliation, true concurrent DAG scheduling
- Background worker service, notifications, Mission Control web UI
- Enforced process sandboxing for arbitrary source code, complete monetary accounting

## Manual local demonstration
```bash
python tools/atlas_loop.py --db private/atlas-loop.sqlite3 start examples/atlas-loop-plan.json
python tools/atlas_loop.py --db private/atlas-loop.sqlite3 run RUN_ID --max-ticks 100 --max-seconds 300
# paid, opt-in (env configured as above):
# python tools/atlas_loop.py --db private/atlas-loop.sqlite3 run RUN_ID --enable-openclaw
python tools/atlas_loop.py --db private/atlas-loop.sqlite3 status RUN_ID
```
The sample run stops in `AWAITING_FINAL_REVIEW`. Only after a real review, manually record its result with `review RUN_ID approved --evidence "reference to actual Codex findings"`. This command is not itself proof Codex ran.

## OpenClaw gateway provider (opt-in)
ATLAS calls models only through a local OpenClaw gateway. It holds a **scoped gateway token, never model provider keys**. The gateway owns the provider credentials and routes the requested model, e.g. a DeepSeek model.

Off unless `ATLAS_ENABLE_OPENCLAW=1` or `--enable-openclaw` is passed to `tick`/`run`. When enabled, all of these are required, or the CLI refuses to start:

| Variable | Meaning |
|---|---|
| `ATLAS_OPENCLAW_URL` | Gateway base URL, intended `http://127.0.0.1:<gateway-port>`. No default port is assumed. Plain HTTP is accepted only for loopback |
| `ATLAS_OPENCLAW_TOKEN` | Scoped bearer token for the gateway, from the environment only, never committed |
| `ATLAS_OPENCLAW_MODEL` | Model name passed through to the gateway unchanged |
| `ATLAS_OPENCLAW_INPUT_USD_PER_MTOK` / `ATLAS_OPENCLAW_OUTPUT_USD_PER_MTOK` | Verified prices for that model. They bound the reservation and price reported usage. Never assumed in code |

Request: `POST <ATLAS_OPENCLAW_URL>/v1/chat/completions`, OpenAI-style, non-streaming, `Authorization: Bearer <token>`. Task shape: `{"worker": "openclaw", "acceptance": {"prompt": "...", "max_tokens": 512, "contains": "..."}}`.

Per paid dispatch, in order:
1. **Uncertain charges:** an unreconciled `uncertain` charge blocks the run.
2. **Approval:** the first paid task requests a `paid_dispatch:openclaw` approval (level `external`) and the run waits in `AWAITING_APPROVAL`. One approval covers this run's paid calls, still capped by its budget. A denial fails the task with no call.
3. **Routing/budget:** `atlas_brain.choose_worker` routes only when the estimated maximum cost fits the available budget; otherwise the run is `BLOCKED`.
4. **Reserve:** `atlas_treasurer.reserve` holds the upper bound (prompt chars + 64 as input tokens, plus `max_tokens`).
5. **Call** the gateway.
6. **Settle:**
   - If the gateway returns `usage.prompt_tokens`/`completion_tokens`, the charge is settled as `gateway_metered` from those counts and the configured prices.
   - **If usage is missing, the hold is marked `uncertain` and the cost is not guessed.** A human settles or releases it with the treasurer CLI, and further paid dispatch stays blocked until then.
   - A 4xx releases the hold. A timeout, connection error or 5xx marks it `uncertain`.

Tests use `FakeProvider` and a fake gateway opener. No test makes network calls.

### Verified vs. unverified (before any live use)
- **Verified by EveClaw:** the OpenClaw gateway runs in local mode, bound to loopback, with token auth.
- **Not confirmed:** the gateway port, and whether the `/v1/chat/completions` endpoint is enabled.
- **Required end-to-end check before the first live call:**
  - the endpoint works
  - the token's auth scope is limited to what ATLAS needs
  - requests are attributed to ATLAS in the gateway
  - the gateway reports usage that matches the provider's billing

  Run it with a small `--budget` and explicit approval.

### CI note
The Atlas Loop workflow path filters do not yet include `tools/atlas_providers.py` or `tests/test_atlas_providers.py`, so changes to only those files may not trigger that workflow. The broader `EVEATLAS checks` workflow still runs the full suite on every PR. Updating `.github/workflows/atlas-loop-checks.yml` must be done manually by someone whose GitHub token has `workflow` scope; agents here must not modify workflow files.

## Model policy
DeepSeek Flash: default proposed implementation; Gemini Flash: proposed planning and alternative; Codex: mandatory independent final reviewer. Exact versions, official identifiers, authentication and available quotas must be verified before activation. If Codex unavailable, remain awaiting review. Optional Jev: decisions only, NEVER authoritative permission granting.

## Next integration gate
Develop supported provider adapters with explicit credentials outside Git, actual invocation receipts, timeout/cancel handling, per-run cost reservations and verified Codex review. Require an independent multi-worker fail/repair/pass integration test. No autonomous publishing, spending or production operations.

## Security warning
`--allow-commands` is meant only for trusted plans; passing Python tests to a subprocess is NOT sandboxing. Run only in isolated authorized workspaces. Never execute untrusted repository code on a machine with sensitive credentials.
