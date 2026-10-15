# Implementation structure test: DeepSeek free review

Date: 2026-10-15
Status: documented; not configured, connected, or tested
Branch: `experiment/deepseek-free-review`
Owner: Eve; execution handoff to the existing Atlas coordinator / builder
Scope: isolated, reversible experiment. This notice does not amend the Agent Registry, production routing, review authority, or Model Cost and Cache Policy.

## Intent and reason

Keep the existing paid DeepSeek connection through OpenRouter in its current role. Eve reports that it already produces useful work for little money and intends to continue funding it. Test whether a separate free DeepSeek V4.1 Flash connection through OpenCode adds useful review capacity.

Both connections may serve the same model family. Names identify the provider and assignment, not two different intelligence levels. Confirm the actual model IDs and versions before comparing them.

| Experiment alias | Connection | Assignment |
|---|---|---|
| DeepSeek Main / `ds-main-openrouter` | Existing paid OpenRouter connection | Existing work, unchanged |
| DeepSeek Review / `ds-review-opencode-free` | Free OpenCode offering, if verified usable | On-demand review of a bounded completed task |

A separate session can challenge an implementation without sharing its entire reasoning history. It is still the same model family and may repeat the same mistakes. This is an additional review pass; it does not replace Atlas's independent review requirements, GPT review where already required, or human signoff.

The reported 200k context window is a per-request capacity, not a verified total free-token allowance. It is adequate in principle for focused reviews with relevant files and evidence. Exact quotas, availability, supported tool calls, endpoint compatibility, privacy terms, and duration of the free offer remain unverified here.

## Structure and isolation

- Keep all experiment documentation and redacted results in this folder on this branch.
- Read the current runtime configuration before proposing any adapter. Do not assume Atlas has a particular queue, API, or OpenCode bridge.
- Use an explicit per-task opt-in to select the experimental reviewer. Do not make it a default route or add it to startup.
- Keep provider identity, credential references, model ID, and role alias separate in logs. Never label results only "DeepSeek."
- Preserve paid OpenRouter configuration, existing budgets, role assignments, and approval gates.
- Run the reviewer in a separate session and disposable checkout. It may inspect supplied files and execute permitted local validation; it cannot change the main checkout, approve its own work, merge, publish, or deploy.
- If free access fails, preserve the task as pending or unavailable and let the existing workflow continue according to its existing rules. Never silently fall back to a paid endpoint or skip a required review.
- No new paid calls, subscriptions, top-ups, or production configuration changes are authorized by this notice.

## Small trial

Hypothesis: a free review pass can find actionable defects or missing verification with acceptable delay and without extra paid review calls.

Trial window: up to seven days after the first verified request, ending sooner after five bounded reviews. Use non-sensitive tasks with explicit acceptance criteria. Include at least one disposable example with a deliberately introduced defect that is not disclosed to the reviewer.

Limits: $0 incremental provider spend; one review attempt and at most one transient-error retry per task; five-minute wall-clock ceiling per review. A coordinator can cancel a slow attempt. Start with compact packets, targeting at most 30k input tokens and reserving response capacity; split oversized work rather than filling 200k.

Before trial requests, the builder must verify that the chosen route is the free model, identify the current model ID and free limits, and check that the permitted connection supports the needed access. Record these facts with timestamped official links or observed responses. Do not copy unverified social-media setup commands into production.

Pre-registered thresholds:
- Proceed to a further trial only if at least four of five reviews complete within the ceiling, the seeded defect is caught, at least one additional actionable issue or missing check is validated, and at least 75% of reported defect findings are validated.
- Any paid fallback, production mutation, credential exposure, or alteration of the existing route stops the trial immediately.
- If completed reviews produce no useful findings, or limits make the route unreliable, recommend iterate or stop. Inconclusive evidence is not success.
- Findings are adjudicated using reproduction, requirements, and tests; unresolved findings remain unresolved. A model's confidence is not validation.

Record completion rate, elapsed time, input/output tokens where observable, provider errors, findings accepted/rejected/unresolved, seeded-defect detection, and additional coordinator effort. Compare any available baseline honestly; do not claim measured savings without equivalent observed paid-review cost. Existing builder spending is outside this $0 incremental experiment and retains its existing authorization.

## Agent handoff

### Handoff to the implementing agent

Objective: prepare a reversible, opt-in free review adapter or manual bridge, then execute the bounded trial if a verified free route is available.

Read first:
- [Operating contract](../../AGENTS.md)
- [Agent Registry](../../02-Agents/Agent%20Registry.md)
- [Model Cost and Cache Policy](../Model%20Cost%20and%20Cache%20Policy.md)
- [Review Gate](../Review%20Gate.md)
- This notice and the current runtime's actual configuration

Work only on this experiment branch or a child branch. First report the proposed connection method and precise files it would affect. Build only the isolated adapter, packet validation, timeout/error handling, and result capture needed for the trial. No canonical role or routing migration is part of the task.

Evidence: Eve wants to preserve the paid OpenRouter workflow; the free connection is an experiment. Hypotheses: review quality, latency, reliability, and quota sufficiency. Runtime connectivity and savings have not been demonstrated.

Allowed tools: read relevant repository files; inspect redacted configuration; isolated local validation; verified free model requests within the limits above. Keep credentials in the existing private secret store. No secrets or private runtime dumps in this public vault.

Next step: inspect the runtime and free-provider capabilities, then propose the smallest working opt-in path. If the integration cannot be verified, record the blocker rather than inventing connectivity.

### Packet format and why

Use versioned JSON for machine handoffs, with this Markdown notice providing human context. Explicit fields prevent confusion between providers, bind findings to a specific code revision, and keep acceptance criteria separate from the builder's claims. Send links plus the relevant contents or tool-accessible files; do not assume the reviewer can access a path merely because it appears in JSON.

Illustrative request (replace placeholders with actual values):

```json
{
  "schema_version": "atlas.review.v1",
  "task_id": "review-001",
  "experiment": "deepseek-free-review",
  "sender": "ds-main-openrouter",
  "recipient": "ds-review-opencode-free",
  "objective": "Check the completed task against its acceptance criteria.",
  "repository": "existinge/EVEATLAS",
  "branch": "experiment/deepseek-free-review",
  "base_commit": "<actual-base-sha>",
  "head_commit": "<actual-reviewed-sha>",
  "acceptance_criteria": ["<observable requirement>"],
  "artifacts": [
    {"path": "<actual-path>", "delivery": "attached-content-or-tool-access"}
  ],
  "diff": "<actual diff or accessible artifact reference>",
  "evidence": [
    {"command": "<command actually run>", "result": "<observed result>"}
  ],
  "unknowns": ["<unverified assumption>"],
  "constraints": {
    "incremental_spend_usd": 0,
    "timeout_seconds": 300,
    "max_transient_retries": 1,
    "workspace": "disposable",
    "allow_main_checkout_writes": false,
    "allow_external_actions": false
  },
  "requested_output": "atlas.review-result.v1"
}
```

A result must identify the actual provider/model and reviewed commit. Findings need a location, concrete impact, and supporting evidence or a proposed reproduction. Clearly distinguish checks actually executed from checks merely suggested.

Illustrative result:

```json
{
  "schema_version": "atlas.review-result.v1",
  "task_id": "review-001",
  "reviewer": "ds-review-opencode-free",
  "provider": "opencode-free",
  "actual_model_id": "<observed-model-id>",
  "reviewed_commit": "<actual-reviewed-sha>",
  "status": "needs_changes",
  "findings": [
    {
      "severity": "medium",
      "location": "<path and line or artifact section>",
      "issue": "<specific defect>",
      "impact": "<what fails and under what condition>",
      "evidence": "<observed evidence or explicitly untested reproduction>",
      "suggested_fix": "<bounded correction>"
    }
  ],
  "checks_run": [],
  "checks_not_run": ["<check and reason>"],
  "limitations": ["<missing information or access>"],
  "next_action": "<specific next step>"
}
```

Allowed result statuses: `needs_changes`, `no_findings`, `blocked`, `unavailable`. "No findings" means none were identified within the stated coverage; it is not merge approval. A coordinator rejects malformed results, mismatched task IDs, and stale commits. Material changes after review require fresh review of the new revision.

The coordinator validates findings, hands valid corrections back to the existing builder, and preserves the result. Avoid endless reviewer/builder loops: after one correction cycle, unresolved disagreements go to the existing reviewer/coordinator route.

## Rollback and decision

Disable the per-task experiment flag or stop invoking the manual bridge. Preserve redacted evidence; remove disposable credentials and local adapters if created solely for this trial. Existing OpenRouter execution remains usable without the experiment.

At the end, write proceed / iterate / stop with observed evidence. Any permanent adoption needs a separate proposal; this branch and notice are not approval for a structural migration.

## Results

Not run. No adapter, model connection, tests, or runtime changes have been performed by creating this notice.
