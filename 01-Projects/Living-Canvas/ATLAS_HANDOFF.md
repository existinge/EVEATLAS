# ATLAS handoff packet — Living Canvas

Project: [[PROJECT]]
Feature branch: feat/living-canvas-project-pack
Status: T00 complete, P0 acceptance pending, implementation unstarted
Review: see the T00 evidence and the tracked GitHub handoff for P0 acceptance
Last updated: 2026-11-11
Budget: $0 incremental inference by default. T01–T03 run offline. Use supported subscription workflows first for reasoning and a verified free developer tier first for duplex. OpenRouter is optional and disabled by default. Any paid experiment requires explicit opt-in and a cost cap.
Dependencies: Node/npm and the existing Atlas tests were verified. TypeScript tooling belongs to T01, and the browser renderer belongs to T03.
Agent execution authority: follow repository AGENTS.md; no autonomous extra agent manager, production deployment, purchases, public outreach, or major architecture deviation.

## Deliverable inventory
[[START_HERE]], [[PROJECT]], [[ARCHITECTURE]], [[PROTOCOL]], [[VISUAL_RUNTIME]], [[VOICE_AND_MODELS]], [[GATES]], [[DECISIONS_AND_RISKS]], [[SOURCES]], [[tickets/INDEX]], fixtures.

## Current factual state
[T00 evidence](worklogs/T00.md) records the original local commit, clean-branch audit and 17 passing Atlas tests. The renderer and provider behavior remain untested. The tldraw production-license decision is open.

## Next action

After P0 acceptance, dispatch [T01 only](AGENT_DISPATCH.md). Build and test the offline reducer and replay harness, then stop at P1. Follow the [provider policy](VOICE_AND_MODELS.md#provider-policy) for later tickets.

## Agent handoff template
- Outcome:
- Working branch and commit:
- Files changed:
- Tests/commands ACTUALLY run + output:
- Demonstrated functionality (real/simulated):
- Observed latency and hardware or NOT MEASURED:
- API/provider verification:
- Deviations / needed decisions:
- Risks/credentials exposure check:
- Reviewer state:
- Next ticket + exact command:
- Stop condition and rollback:
