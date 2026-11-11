# Agent dispatch — T01 after P0 review

Repository: https://github.com/existinge/EVEATLAS

Feature branch: feat/living-canvas-project-pack

Entry point: [START_HERE.md](START_HERE.md)

Review [T00 evidence](worklogs/T00.md) and check the tracked GitHub handoff for P0 acceptance before coding. If acceptance is absent, record the review outcome or blocker and leave T01 pending.

After P0 acceptance, fetch the feature branch and work on its current tip. Read root AGENTS.md, [the protocol](PROTOCOL.md), [the gates](GATES.md), [fixture expectations](fixtures/README.md) and [T01](tickets/T01-SHARED-SPACE.md). Before editing, record the branch and commit, intended files, acceptance test and stop condition.

Implement T01 only. Use TypeScript and lightweight local test tooling. Record proposals separately from committed scene state. Keep renderer scaffolding, provider SDKs, credentials, network inference and coordinator validation outside T01. See [provider policy](VOICE_AND_MODELS.md#provider-policy) for later tickets.

Run real tests and return the branch and commit, changed files, commands and pass/fail output, actual vs simulated behavior, unresolved issues and next cursor. Stop at P1 for review. No merge or deployment.
