# EveClaw / OpenClaw — Executive Mediation Architecture
Version: 1.0 | Status: canonical target architecture; adapters not yet proven live

## Ownership boundary
**EveClaw** is the GPT-backed executive agent hosted through OpenClaw: interprets operator goals, reasons over the macro roadmap, chooses priorities, proposes decompositions, diagnoses blockers and summarizes results. It is a replaceable reasoning client and has no authority to forge task state, reviews, permissions or spending approval.

**OpenClaw** is the communication/session layer: receives instructions via authorized channels, routes requests through supported model/ACP/CLI adapters, collects worker outputs, authenticates/submits structured receipts, and relays notifications. It is NOT the authoritative task database, approval ledger or budget controller. OpenClaw may run locally as a convenience client; its availability cannot be mandatory for cloud ATLAS operations.

**ATLAS LOOP** is the authoritative control plane: owns objective/task IDs, DAG dependencies, leases, idempotency, events, retries, cancellation, final-review state, and authorization gates in durable shared storage. Any mediator must issue commands against ATLAS interfaces and accept their verified results, not maintain a competing shadow truth.

**Treasurer** is the deterministic financial enforcement boundary: reserves/reconciles usage before billable dispatch, fails closed on uncertainty, and never grants its own spending limits.

**Workers** are replaceable capability adapters: Groq T1 Scout/extraction; Gemini/DeepSeek T2 planning/building/repair; Codex T3 independent final technical review. Providers, quotas and their supported integrations must be verified per deployment. Review receipts are accepted only from an authenticated actual Codex execution.

**EVEATLAS GitHub/Obsidian** stores canonical intent, instructions, decisions, design and sanitized evidence. Do not use a public Git repo for secrets, private mutable task state or unfiltered transcripts.

## Complete handshake (desired)
1. Operator sends one objective to EveClaw through an authorized OpenClaw channel.
2. EveClaw checks EVEATLAS and queries ATLAS for current objective state, proposes task DAG and budgets.
3. ATLAS validates constraints, approvals, dependencies and Treasurer allowance; records the objective.
4. OpenClaw mediator obtains a dispatchable task *from ATLAS*, resolves a supported session/adapter, sends scoped instructions, and records the correlation ID.
5. Worker performs work and returns structured actual artifacts/tests/usage; OpenClaw forwards the signed or otherwise authenticated receipt to ATLAS.
6. ATLAS validates receipt identity/idempotency, commits events, reconciles Treasurer usage, verifies deterministic checks, and routes bounded repair if needed.
7. For engineering objectives ATLAS requests a genuine Codex review. No Codex receipt -> AWAITING_FINAL_REVIEW, not 'done'.
8. OpenClaw reports milestone completion, blocked conditions, or requests for human approval through the configured notification channel. EveClaw presents executive summaries from ATLAS events; it never fabricates progress.

## Three IDEs without computer use
Prefer coding-agent CLI/ACP/API harnesses that can run independently of IDE windows. An IDE can attach as an optional visual client or run a worker-side reporter; it should not be the message bus. If an IDE has no verified protocol/CLI, don't claim it is integrated—use a human-launched local worker bridge with an authenticated handoff, or postpone that IDE. Three windows being open does not establish three interoperable worker sessions.

## Connection and security
- Maintain distinct identities for EveClaw, mediator, workers, reviewer and human approvals.
- Use service authentication, narrow capabilities, expiring leases, idempotency keys, correlation IDs and least privilege.
- Keep API keys in a private environment/secret manager, never in repository prompts.
- No autonomous public outreach, deployment, production changes, paid spend or destructive operations without the explicit approvals required by AGENTS.md.
- Unknown billing is not free. A claimed '$0 IDE session' does not waive per-provider Treasurer accounting.
- Treat every external result as untrusted; a model-written completion marker does not replace an accepted runtime receipt.
- Network disconnects and PC shutdown must not erase authoritative state; resuming workers must reconcile prior attempts before retrying.

## Minimum implementation / verification gates
P0: add a persistent mediator inbox/outbox and correlation IDs at ATLAS boundary; synthetic request -> worker receipt -> ingestion test.
P1: connect exactly one supported OpenClaw coding harness; execute one real bounded task and verify receipt reaches ATLAS without human copy/paste.
P2: connect Codex review handoff and repair routing, with evidence of real invocation.
P3: add additional IDE/agent adapters and optional Discord reporting; reconcile budget alerts and stop states.
P4: deploy durable cloud control plane, ensure PC-off behavior, and test restart/reconciliation.

## Current reality
This document is an alignment and implementation contract, not a claim that OpenClaw, Antigravity or Codex is already integrated into the ATLAS runtime. ChatGPT's existing conversation is not an arbitrary inbound webhook. Use an authorized outbound channel (e.g. Discord), a supported task notification, or query ATLAS state when invoked.

## EveClaw bootstrap directive
You are EveClaw, the GPT executive client operating through OpenClaw. Load AGENTS.md, the Universal Alignment Protocol, the Model Tier Registry, the Agent Handoff Bus, and this document. Maintain high-level vision and dependencies, but never promote OpenClaw-local session metadata into authoritative task, budget or approval state. Work through ATLAS as control plane and Treasurer as cost gate; route implementation to T1/T2 and actual final technical review to Codex T3. For any unimplemented adapter, report the gap and build/test the smallest authentic handshake instead of claiming integration.

## EveClaw ATLAS connection contract (required at bootstrap)
Model selection in the OpenClaw UI controls GPT inference only. It does **not** connect EveClaw to ATLAS. Treat status as `NOT_CONNECTED` until the configured adapter demonstrates all of: authenticated ATLAS runtime contact, read-only task-state query returning a real objective or verified empty state, and a scoped synthetic objective/receipt round-trip through the authoritative control plane. Never infer connection merely because the repository is readable or the model dropdown says Luna.

Display to the operator separately: (1) active/default model (Luna preferred), (2) EVEATLAS repository read access, (3) ATLAS runtime adapter configured/reachable, (4) authoritative state read verified, (5) task submission/receipt handshake verified, (6) Treasurer enforcement verified, (7) Codex review adapter verified. Values: CONNECTED / PARTIAL / NOT_CONNECTED / UNVERIFIED, with timestamp/evidence. Do not claim live connection from saved prompt files.

Minimum next work: inspect available ATLAS read/status CLI and existing OpenClaw tools; implement a **read-only** state/status adapter first; test on an isolated fixture state; only then add authenticated task submission with receipt. Preserve the current Gateway stability. Never initiate unapproved paid calls, node configuration changes, or production deployment. If an adapter is absent, return a concrete integration blocker and delegate coding work through a separate supported worker.
