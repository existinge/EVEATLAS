# Scholar intake — DeepSeek free review candidate

Date: 2026-10-15
Scope: ATLAS self-study and practical tooling discovery
Requested by: Eve
Status: intake and advisory handoff; provider research and runtime trial pending

This is a discovery intake for Scholar, authored during documentation setup. It is not a completed Scholar research run, a deployed integration, or proof of model quality.

## Question

Can a free OpenCode DeepSeek connection perform useful bounded reviews while preserving the existing paid OpenRouter workflow?

## Summary

- **verified (repo):** an isolated implementation notice exists on `experiment/deepseek-free-review`; only test documentation was added there during setup.
- **speculative:** separate review sessions could catch useful defects without incremental paid review calls.
- **unverified lead:** the free offer, 200k context, exact quotas, endpoint/tool compatibility, and continued availability need first-hand verification.

## Evidence and sources

| Finding | Label | Source | Date read |
|---|---|---|---|
| Scholar is defined as advisory and may write its own dated reports. | verified in repository documentation; automation not established | [Scholar role](../../02-Agents/Scholar.md), branch `docs/scholar-role`; inspected revision before this workflow addition: blob `43b3f0da4b700a079060ce82cf11c5c0bc93de99` | 2026-10-15 |
| The free review trial has a bounded scope, role aliases, JSON handoff examples, success criteria and rollback. | verified documentation; implementation not run | [Immutable implementation notice](https://github.com/existinge/EVEATLAS/blob/727223d861f9bf27d3d34bfcb15adb73fcc84ce7/04-Operations/Implementation%20Tests/DeepSeek%20Free%20Review%20Structure%20Test.md) | 2026-10-15 |
| Free model access and a 200k window were presented as a discovery lead. | unverified intake; not a verified provider fact | User-supplied lead in the 2026-10-15 task; Scholar must obtain a primary source and timestamped availability evidence | 2026-10-15 |

## ATLAS relevance

Eve wants to retain the paid OpenRouter DeepSeek connection because it already provides useful value. The proposal adds a separately named trial reviewer; it does not replace the current worker or imply that the free model is independently stronger.

This is the kind of actionable discovery Scholar should pursue: find an accessible capability, match it to a real workflow, verify its constraints, propose the smallest test, and learn from observed outcomes.

## Candidate implementation test

[Full notice — explicitly on the experiment branch](https://github.com/existinge/EVEATLAS/blob/experiment/deepseek-free-review/04-Operations/Implementation%20Tests/DeepSeek%20Free%20Review%20Structure%20Test.md)

- Hypothesis: an additional free review pass can catch actionable defects at acceptable latency.
- Baseline: existing workflow; inspect actual configuration before proposing a connection.
- Scope: opt-in review of five bounded non-sensitive tasks, including one seeded defect.
- Limits: $0 incremental provider spending; five minutes per review; one transient retry maximum; end after five reviews or seven days from first verified request.
- Success: at least four reviews complete in time, seeded defect caught, at least one additional useful finding validated, and at least 75% of defect findings validated.
- Stop: any paid fallback, production mutation, credential exposure, or change to existing routing.
- Rollback: stop invoking the optional reviewer; keep the paid workflow as it is.
- Permanent adoption: separate proposal after evidence.

The implementation notice is authoritative for trial details; this report is an intake summary. If details diverge, reconcile explicitly before execution.

## Scholar's next investigation

1. Verify the current free offer from official OpenCode sources and an observed free-route response where available through an authorized operator. Record actual provider/model ID, quotas, context/output limits, compatibility, and relevant terms. Treat social posts as leads.
2. Inspect redacted runtime evidence to identify whether a supported API, OpenCode invocation, or manual bridge is available. Do not assume MCP or screenshot support.
3. Identify one small completed task suitable for review. Separate acceptance criteria and actual validation evidence from the builder's conclusions.
4. Hand the lead a recommendation: test now, blocked pending a named fact, or skip with evidence. Avoid unneeded structural redesign.
5. After the bounded trial, read redacted results and update this report with outcomes and disconfirming evidence.

## Handoff to lead / builder

Objective: evaluate and, where verified feasible, prepare the isolated free-review trial.

Canonical files: [Scholar](../../02-Agents/Scholar.md), [Operating contract](../../AGENTS.md), [Model Cost and Cache Policy](../../04-Operations/Model%20Cost%20and%20Cache%20Policy.md), and the linked implementation notice.

Branches: research and role documentation on `docs/scholar-role`; test notice and any scoped adapter work on `experiment/deepseek-free-review` or a child branch. Neither branch is automatically present on main.

Evidence vs hypotheses: notice existence is verified; provider capabilities, review utility, savings, and runtime integration are untested.

Tools and budget: Scholar reads public sources and redacted repository/runtime evidence and writes its own reports. The Builder owns adapter changes and trial requests under the notice's limits. No new paid integrations or production changes.

Changes so far: documentation only. Tests actually run: none; repository reads confirmed the notice and branch separation. Risks: shared-model blind spots, disappearing free access, stale links/configuration, confusing documentation with deployment.

Next step: Scholar verifies the offer and recommends a concrete free connection method to the lead. This task authorizes documenting and preparing the bounded trial; existing approval gates still govern additional actions.

## Outcome and recommendation

Not measured. Candidate is queued in documentation, not proven delivered to or loaded by a running Grokbot/Scholar. Recommendation: investigate the bounded trial; no permanent routing change.
