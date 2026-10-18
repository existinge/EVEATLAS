# ATLAS Agent-to-Agent Handoff Bus
Status: contract defined; transport and automatic chat delivery NOT yet implemented.

## Purpose
Stop asking the human to relay Antigravity/Gemini, ATLAS, Treasurer, Codex, and ChatGPT status by hand. Agents exchange durable machine-readable receipts through a trusted runtime. GitHub provides a practical development-time audit trail, NOT a secrets store, live message broker, or direct ChatGPT conversation channel.

## Design
1. Coordinator registers an objective and task ID in the runtime state.
2. The worker claims a task with a lease/idempotency key, executes within permissions, and writes a structured receipt.
3. The runtime verifies schema, revision, authorization and task identity; persists events and artifacts.
4. Treasurer reconciles usage and flags uncertain cost.
5. Verification dispatches a bounded repair or a Codex review request.
6. Codex uses the actual diff and test evidence; never trusts an unverified review label.
7. Agent/UI consumers watch the event stream. Human attention is requested only for permission, budget or unrecoverable blocking states.

## Development transport: GitHub handoffs
Use pull requests, commits and issue/PR comments or a CI artifact to publish **sanitized** task receipts. Each receipt should reference its code revision and evidence artifacts; do not commit raw private logs, credentials, user files, financial records, prompts containing secrets or provider tokens. Development workers may write to a purpose-specific PR and report its link. Prefer existing ATLAS LOOP PR #1 until the coordinator assigns otherwise.

For a simple static handoff, a worker may append a receipt under `handoffs/outbox/<task_id>/<attempt_id>.json` in a working branch, then open/update its PR. This is a proposed path, not currently watched by the runtime. The orchestrator must not infer that a file appearing equals a completed or approved task.

## Required receipt
See `02-Agents/Agent Handoff Receipt.schema.json`. Include event ID, objective/task IDs, worker identity, role/tier, status, timestamp, source revision, artifacts, verification evidence, cost source, next action, and blockers. Include factual execution evidence only; mark unknown token/cost quantities null.

## Required adapters before claiming zero-touch
- Task dispatch / lease / retry service with deterministic ownership and durable state.
- Worker-side reporting hook or CI adapter (Antigravity must be able to publish an actual receipt, not simply print it in the chat window).
- Validation and ingestion endpoint (GitHub polling/webhook for dev, queue/event service for production).
- Authorization and authentication of worker identity and review receipts.
- Subscriber for Codex review handoffs, and structured coordinator updates.
- An outbound user notification channel (e.g. Discord or authorized scheduled ChatGPT task), with an explicit policy for approvals.
- End-to-end tests: worker finishes -> receipt persists -> consumer ingests -> automated review/repair -> notification fires.

## What is and isn't automatic today
Current repo contains local scheduler and test workers; external provider adapters, receipt transport, cloud event bus, and push into an existing ChatGPT conversation are not proven. This chat can read a committed GitHub receipt when actively invoked; it cannot be externally pushed into by arbitrary scripts. Scheduled checks can deliver updates through supported ChatGPT automation delivery, but may not be immediate and must be explicitly configured. Production cloud workflow should not depend on ChatGPT conversation continuity.

## Implementation priority
P0: add worker receipt-writing to existing loop state and tests; prove a synthetic message/consumer exchange.
P1: bridge Antigravity output to a GitHub PR comment or committed sanitized JSON with safe retries.
P2: event ingestion + Codex review/repair routing + notification on final/blocked.
P3: cloud queue and authorized user-facing dashboard/Discord; measured spend, approvals and security.
