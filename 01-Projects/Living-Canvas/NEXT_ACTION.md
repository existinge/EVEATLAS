# Next action / resume cursor

Date: 2026-11-11

T00 is complete. The [preflight evidence review](worklogs/T00.md) records the clean-branch baseline and the open tldraw production-license decision. P0 acceptance is pending reviewer signoff.

1. Record P0 acceptance or a specific blocker in the tracked GitHub handoff.
2. After acceptance, take [T01 — Shared Workspace](tickets/T01-SHARED-SPACE.md) only on the existing feature branch.
3. Build the offline TypeScript event log, reducer and deterministic replay harness. Run [the e1–e8 fixture](fixtures/sample-events.jsonl) against [its expected outcomes](fixtures/README.md).
4. Report the commit, changed files, exact test commands and results, and any gaps. Stop at Gate P1 for review.

T01 uses local fixtures and needs no model, voice service, credentials or graphics SDK. T02 and later require separate dispatch.
