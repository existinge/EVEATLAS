# Acceptance gates and evidence

Gate status on pack creation: ALL NOT RUN. No runtime is claimed.

## Gate P0 — repository safety
Inspect existing Atlas AGENTS.md / branch, do not overwrite unrelated docs, establish reproducible install, run existing Atlas tests, no secrets committed. Deliver screenshot or logs of actual commands.

## Gate P1 — deterministic replay
Fixture events applied twice produce identical canonical snapshots and commit IDs; duplicated events don't double-apply; order changes are either correctly buffered or rejected with diagnostics. Snapshot and event log share correlation IDs.

## Gate P2 — guarded coordinator
Reject stale epoch, revoked branch, wrong object, wrong semantics and expired proposal. Allow one valid visual emphasis without LLM latency. Interrupt cancels pending provisional changes and leaves stable scene intact.

## Gate P3 — living canvas
Persistent objects update (do not regenerate whole board), both fast parameter modulation and a reversible morph/transform work. Renderer can show a neutral placeholder on unknown concept. Visual loop is not blocked on model/planner futures.

## Gate P4 — actual fast decider
Run the same fixture through deterministic baseline and at least one real fast candidate. Capture p50/p95 and error/confusion on held-out traces, not just demo success. Structured proposals and permissions must be respected. If speed or accuracy poor, report it rather than silently swapping architecture.

## Gate P5 — semantic planning
Planner publishes valid rolling horizon, expands a likely branch, maintains semantic revision, and handles unanticipated jump with a safe HOLD → plan update. Deliberately slow planner must not freeze current canvas.

## Gate P6 — live duplex
Document provider's actual event capability. User can speak, interrupt, correct mid-sentence (if provider signals permit), and visually see an authorized change without waiting for full spoken response. Record limitations honestly when partial words are unavailable.

## Gate P7 — generality + multilingual stress
Test Japanese, Thai and English (including code-switching), domain switch outside language learning, long conversational drift, invalid confidence, repeated speech corrections, provider dropout, empty frontier, and canvas error.

## Measurement protocol
Capture per-event timestamps (monotonic, same clock where possible): mic captured, speech observation emitted, decider start/end, coordinator accepted/rejected, paint acknowledgement. Report median, p95 and maximum for **each hop**, plus semantic correctness and reversal/error counts. Do not compare an audio capture timestamp from a different host as if synchronized.

Initial performance ambitions (NOT promises): after an eligible partial transcript arrives, target decider+coordinator+paint p50 < 150 ms and p95 < 350 ms on target development machine, provided a suitable model. Full mic-to-paint depends on provider and is explicitly measured rather than promised. A smooth animation can last longer than action latency.

## Failure is a valid result
If a candidate has poor multilingual classification, record the confusion and move to another adapter; do not call the architecture proven. A scripted event replay proves the pipeline only, not conversational intelligence or live duplex.
