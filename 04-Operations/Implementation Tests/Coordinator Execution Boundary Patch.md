# Coordinator Execution Boundary — Structure Test
Date: 2026-10-15
Status: proposed implementation contract; documentation only; NOT deployed or technically enforced.
Base: feat/atlas-loop-runtime @ d2213b5a1dc3086ec9c388040781b02ca4d8e641.
Trial branch: experiment/coordinator-boundary-audit. Do not merge into main or change live credentials as part of this documentation patch.

## Problem and intended behavior
When a worker handoff fails, the coordinator can currently become the implementation worker instead. That hides a broken loop and spends coordinator tokens on execution. Require explicit task ownership, role-scoped tools and bounded routing. A failed dispatch must produce a visible blocked state or an authorized bounded retry, never an unrecorded coordinator takeover.

A restriction belongs to a role/session identity, not a model brand. GPT may be a coordinator, explicitly assigned worker, or independent reviewer under distinct credentials and permissions. The coordinator must not grant itself worker permissions or create an elevated identity to bypass a failed handoff.

## Trial permission matrix
| Role | Permitted | Withheld |
|---|---|---|
| Coordinator | Read scoped repo files, diffs, logs and task state; propose plans; request dispatch through Atlas; report verified results | General shell, computer control, product source edits, direct provider fallback calls, self-assignment as worker, approval/review forgery |
| Assigned worker | Execute the specific task in an isolated workspace through granted tools; publish artifacts and receipts | Changing routing, permissions, budget or approval policy; claiming independent review of its own work |
| Independent reviewer | Inspect actual revision/artifacts/tests under a separate authenticated identity and submit findings | Builder self-approval; overriding authorization |
| Operator | Assign roles, approve permitted actions, set budgets and explicit exceptions | No implicit authorization inferred from silence |

The coordinator can work with the repository: read and analyze anything within scope. If enabled, it may write task briefs, status and research notes only through a dedicated path-scoped API that records the task ID. No general GitHub write token, shell, or unrestricted file writer belongs in that coordinator session: those can bypass path limits. Product code and runtime/config changes go to an assigned builder on a branch. If the narrow notes API is absent, submit a proposed note through Atlas rather than silently using broader tools.

This does not remove computer access from separate direct-use GPT sessions outside Atlas. An intentional GPT worker is allowed only when the operator explicitly assigns its task, capabilities and budget.

## Runtime enforcement to implement
1. Separate coordinator, worker, reviewer and human identities. Enforce tool allowlists outside model prompts. Authenticate at the dispatch boundary; reject forbidden execution even when requested in natural language.
2. Atlas owns task IDs, selected worker, allowed capabilities, route/model, attempts and state. Every execution and fallback must reference an authorized task and attempt.
3. On unavailable/invalid handoff: persist reason, retry within an explicit cap or BLOCK. Never substitute coordinator execution. Worker reassignment is restricted to configured routes and budget; escalation proposes an exception but does not grant it.
4. Pass dependency artifacts explicitly: resolve upstream output by task ID/revision, validate size/type and include artifact references or bounded content in the downstream packet. Dependency order alone is insufficient.
5. Require task-specific acceptance criteria. Reject empty checks for real work. Content substring tests alone do not establish successful code, files, rendering or source-backed research.
6. Final engineering completion needs an actual independent review execution bound to task IDs, revision and artifact digest. A reviewer label or CLI evidence string is not authentication. Manual attestation remains visibly distinct and must not impersonate automated review.
7. Claims need expiring leases, atomic ownership and idempotency keys. After restart, reconcile in-flight remote executions before retrying; unknown dispatch outcome must not create duplicate work.
8. Service hosting must be explicit: supervised process, durable private state, health/last-progress signal and recovery policy. A manually invoked bounded run command is not deployment evidence.
9. Record usage for coordinator and workers separately. Use reservations and per-task/run caps for metered calls; monitor coordinator reasoning caps. Unknown billable cost blocks further paid dispatch pending reconciliation. Subscription allowance and token-dollar accounting are different meters; never invent a conversion.
10. Use event-driven waiting or bounded deterministic polling. Do not repeatedly ask the coordinator model whether a worker is done.

## User-facing status contract
Show separately, with timestamps and evidence:
- Repository readable and revision loaded.
- Runtime reachable and authoritative state query successful.
- Worker connected and allowed capabilities.
- Submission/dispatch/receipt round-trip verified.
- Current task owner, attempt and last progress.
- Usage known/unknown, budget remaining and pending approvals.
- Review connected and actual verdict.
- Service running/recovering/stopped.

Use CONNECTED / PARTIAL / NOT_CONNECTED / UNVERIFIED for connections. Do not equate a model dropdown, saved prompt, readable repo, passing fake-provider tests, or an open IDE with a live connection.

## First proof workflow
Use one scoped, read-only inventory job on an explicitly selected local video folder. Record filenames, durations and extraction errors privately; commit only sanitized proof. Do not move/delete clips or claim highlight selection.
1. Operator sends one request through the intended OpenClaw channel.
2. Atlas creates a task; assigned PC worker produces the inventory.
3. A downstream verifier receives the actual artifact and checks file counts, readable durations and errors against the folder snapshot.
4. A separately authenticated real reviewer checks the artifact and evidence; no reviewer connection means awaiting review.
5. Runtime reports the verified outcome without human copy/paste between agents.
6. Restart while work is in progress and verify durable recovery without duplicate execution.

The inventory/verification steps should use deterministic tools where practical. Model calls are not required merely to count files.

## Required failure tests
- Disconnect worker: visible blocked/retry state; zero coordinator execution-tool calls and no substitute provider call.
- Request coordinator source edit or GUI control: tool boundary rejects it; explicit worker assignment is the permitted route.
- Exhaust coordinator/worker budget: stop dispatch, persist reason; no hidden fallback.
- Missing dependency artifact: block downstream task rather than fabricate a summary.
- Empty acceptance checks: reject real task before dispatch.
- Forged Codex label/evidence: cannot produce authenticated completion.
- Crash before/after dispatch: reconcile ownership and remote outcome before retry.
- Two schedulers claim the same task: only one lease succeeds.
- Unknown billable usage: retain uncertainty and block additional paid work.
- Coordinator notes path traversal/source-file write: reject.
- Happy path: actual worker -> actual artifact -> downstream check -> authentic review -> notification.

## Agent handoff packet
Use a versioned structured packet. Example fields:
```json
{
  "schema_version": "1.0",
  "task_id": "assigned-by-atlas",
  "attempt_id": "assigned-by-atlas",
  "role": "worker",
  "objective": "Produce a scoped read-only clip inventory",
  "source_revision": "exact-commit",
  "dependency_artifacts": [],
  "allowed_capabilities": ["read_clip_metadata", "write_scoped_artifact"],
  "forbidden_capabilities": ["delete_clips", "change_policy", "self_approve"],
  "acceptance": ["inventory matches folder snapshot", "extraction errors reported"],
  "budget": {"meter": "configured-meter", "limit": "operator-assigned"},
  "on_dispatch_failure": "block_or_authorized_retry",
  "receipt_destination": "configured-runtime-endpoint"
}
```
A packet is not a connection. The authenticated runtime validates identity, task, revision, permissions and artifact receipt before accepting state changes. Do not place private paths, transcripts or secrets in public handoff examples.

## Ownership and next implementation
Assigned builder: implement narrowly on a working branch; report actual changes and tests.
Independent reviewer: review actual diff and reproduction evidence.
Local operator/PC agent: inspect existing gateway capabilities and supported interfaces; do not disrupt the stable gateway. Apply live permissions only in a separate authorized configuration step.
Scholar: research and verify integration options, limits and alternatives; no builder assignment required.
Grok coordinator: research/coordination/intelligence and explicitly authorized outreach preparation. Sending outreach retains existing authorization gates.

Build in order: identity/tool boundary -> artifact handoff and validation -> authenticated review -> restart ownership -> live PC handshake/service. Prove the smallest path before adding more models or agents.

## Rollback and promotion
This is an isolated structure test, not a permanent role rewrite. No live permissions, model configuration, gateway settings or main files changed by this notice. Discard/close the branch to abandon the proposal. Promotion requires implementation evidence and an explicit deployment decision. Restricting prompts alone is not a passed enforcement test.
