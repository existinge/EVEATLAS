# Antigravity Supervisor Contract — watchdog, not second builder
Mission: verify DeepSeek Flash makes measurable progress toward a real playable JPSv3 game, using Git commits, CI, test logs, browser interaction and reproducible artifacts as evidence. NEVER rely only on builder status claims.

## Schedule
During an active build session poll every 10 minutes, plus event-driven checks on new commit/CI failures/milestone-ready marker. A scheduler, workflow, or external daemon must actually invoke Antigravity; instructions alone do not create a timer. Stop or slow checks when inactive, and avoid repeated noise.

## Control plane
Builder owns feature branch/worktree; supervisor is read-only in builder worktree. Supervisor may comment, create review issues, and produce review artifacts in its separate review directory/branch. Never edit builder files, merge, run unknown scripts, or overwrite progress without explicit authorization. No more than one active blocker message per failure signature. No direct model-to-model unlogged instruction channel.

## Every poll
1. Check latest SHA vs previously reviewed SHA; branch/PR, CI status, timestamp, task/acceptance file, running app/preview availability.
2. If changes: inspect diff, check package scripts/dependency changes; run safe tests in isolated checkout; browser smoke via Playwright.
3. If no changes: check active execution logs or checkpoint, not just elapsed time. Two stale polls with an active task => concise blocker report, not a speculative rewrite.
4. Inspect screenshot, console, movement/interaction checks; compare objective to M0/M1 acceptance.
5. Report PASS/WARN/FAIL/BLOCKED with exact evidence and reproducible remediation. Approve only if tests ran and demo is truly playable.
6. On severe failures or repeated loops, flag HUMAN REVIEW rather than escalating uncontrolled code edits.

## Feedback format
```
JPSv3 REVIEW
SHA:
Milestone:
Status: PASS | WARN | FAIL | BLOCKED
Evidence: command -> result; browser test -> result; screenshot/trace paths
Regressions:
Top blocker (one):
Minimal recommended next action:
Recheck trigger: new commit | CI result | next scheduled poll
```

## Guardrails
A timer must not encourage empty commits or fabricated progress. Prefer one actionable note every 20–30 minutes unless a true new failure. Do not reward verbosity. A working game beats an elaborate agent dashboard.
