# AGENTS — Japanese Splat City

Project-level operating notes for agents (and humans) working inside
`01-Projects/Japanese-Splat-City`. The vault-wide contract in
`/AGENTS.md` always applies and takes precedence.

## Scope

- All project work stays inside this directory. Do **not** edit the BL Engine,
  research ops, core agent framework, or unrelated projects.
- Do not rewrite existing ATLAS contracts or the Projects Index sections that
  belong to other projects.

## Implementation rules

- Evidence first: every milestone must produce a testable result and a log entry
  in `docs/BUILD_LOG.md`; claims of success must be backed by the test report in
  `docs/TEST_REPORT.md`.
- No fabricated implementations: if a dependency fails, investigate and fix it,
  or document the limitation honestly.
- Commit meaningful per-milestone changes on the feature branch; never merge to
  `main` without human approval.
- No secrets, credentials, private data or large build artifacts in commits
  (this repository is public).
- Milestone status lives **only** in `docs/PLAN.md` (ledger + staging). A status
  change must land in the same change as its `BUILD_LOG.md` row and
  `TEST_REPORT.md` section. README and ARCHITECTURE link to the plan; ARCHITECTURE
  describes only files that exist in `src/` — planned modules go to the staging
  table, never into the module tree.

## Verification commands

```sh
npm run typecheck   # strict TypeScript check
npm test           # unit / integration tests (Vitest)
npm run build      # production build
npm run dev        # local dev server
```

Browser verification uses a local dev server plus headless browser screenshots
and console-error inspection before milestone sign-off.

## Handoff

Include: objective, branch, exact changes, commands, evidence (tests run,
screenshots, console output), known limitations, and next step.
