# T04 — Fast decision model adapter and benchmark

Timebox: 30–45 minutes. Status: NOT STARTED. Depends on: T03/P3.

## Build
Preserve an always-available deterministic baseline. Add one replaceable adapter that maps a bounded observation window and latest authorized concept frontier into typed proposals. Use model response schema validation; no direct renderer access. Choose from candidate deciders only after checking license, inputs, local hardware feasibility and structured action support. A Jev-style decision classifier may require a structured set of candidate labels; do not assume arbitrary open-ended geometry emission.

## Experiments
Replay the SAME held-out fixture across stub and selected model.
Measure queue, inference, validation, and paint separately. Compare incorrect branch selection, abstention, invalid output, stale event handling, and true latency.

## Gate P4
Real model call actually executed and logged on hardware/API, proposal schema valid, bounded actions, planner deliberately stalled without canvas freeze, at least one bad case correctly abstains. If no working model, label P4 blocked; do not declare complete.

## Forbidden
Choosing model based on self-reported 200ms coffee demo, rebuilding a computer use interface, swallowing semantic errors, assuming multilingual competency.

## Stop
Report actual model name/version, hardware, runtime timings, output errors, cost (if any) and next ticket.
