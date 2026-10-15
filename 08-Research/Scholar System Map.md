# Scholar — Atlas System Map
Updated: 2026-10-15 (America/New_York)
Evidence baseline: runtime branch feat/atlas-loop-runtime @ d2213b5a1dc3086ec9c388040781b02ca4d8e641; main @ dec45eeebf77a547e32bc6f0a7bfa08d486d4aa4.
Scope: compact orientation; not a claim of live connection. Recheck branch heads and patch notes before relying on this snapshot.

## Macro model
Operator goal -> executive/coordinator proposes work -> Atlas validates and tracks tasks -> assigned workers execute -> deterministic checks and independent review -> verified outcome.
GitHub/Obsidian holds intent, evidence and versioned instructions. Private runtime state holds actual tasks and receipts. OpenClaw is intended to provide sessions/transport; reading the repo does not establish runtime integration.

Present reality: executable local foundation on an unmerged runtime branch, not a demonstrated unattended end-to-end system. 59 offline tests passed in the audit; no live provider or PC deployment was verified. Audit evidence is linked below.

## Micro map
| System | Purpose | Observed status | Main dependency/gap |
|---|---|---|---|
| Vault / AGENTS | Canonical intent and operating rules | Files readable; several branches | Agents must load correct revisions |
| Executive / EveClaw | Goals, planning, coordination | Architecture contract | Authenticated runtime handshake unproven; role registry needs alignment |
| Atlas Loop | SQLite tasks, ordered scheduling, bounded retries/run | Implemented on runtime branch; offline-tested | Service supervision, ownership/recovery and live adapters unfinished |
| Artifact handoffs | Carry worker results into dependent tasks | Ordering exists | Automatic upstream artifact delivery absent in reproduced test |
| OpenClaw adapter | Model request through gateway | Opt-in code, fake-tested | Live endpoint/auth/usage and PC capabilities unverified |
| Workers | Execute scoped work | local fixtures/restricted commands; gateway optional | Direct DeepSeek/Gemini/Codex unavailable in runtime registry |
| Treasurer | Reserve/reconcile paid usage, block uncertainty | Offline-tested deterministic accounting | Verified billing and separate subscription meters |
| Verification/review | Reject bad work and obtain independent review | Basic string checks/manual review label | Vacuous checks and unauthenticated completion reproduced |
| Handoff bus | Durable cross-agent receipts | Contract defined | Authenticated transport/ingestion unimplemented |
| Signal Desk | Ingest/deduplicate reviewed candidates | Offline foundation | No automatic live search or monitoring established |
| Scholar | Self-study, field research, bounded trial advice | Role documented on docs/scholar-role | Running Grokbot loading updates not confirmed |
| Free DeepSeek review | Trial separate free reviewer alongside paid Main | Documentation on experiment branch | Offer, limits, connectivity and real results require verification |
| Coordinator restrictions | Prevent silent GPT execution takeover | Proposed contract on audit patch branch | Permissions/tool allowlists not applied |
| Deployment/notifications | Keep work running and report outcomes | Unverified/not implemented in inspected runtime | Supervised host, health signal, notification adapter |

## Active change pointers
- Runtime foundation: [PR #1](https://github.com/existinge/EVEATLAS/pull/1).
- Scholar role: [PR #2](https://github.com/existinge/EVEATLAS/pull/2).
- [2026-10-15 runtime audit](https://github.com/existinge/EVEATLAS/blob/experiment/coordinator-boundary-audit/08-Research/2026-10-15%20Atlas%20Runtime%20Audit.md).
- [Coordinator boundary proposal](https://github.com/existinge/EVEATLAS/blob/experiment/coordinator-boundary-audit/04-Operations/Implementation%20Tests/Coordinator%20Execution%20Boundary%20Patch.md).
- [Dated implementation handoff](https://github.com/existinge/EVEATLAS/blob/experiment/coordinator-boundary-audit/04-Operations/Implementation%20Tests/2026-10-15%20Coordinator%20Boundaries%20and%20Runtime%20Audit%20Handoff.md).
- [DeepSeek review trial](https://github.com/existinge/EVEATLAS/tree/experiment/deepseek-free-review).

Branch presence is not adoption. References to tests in this map are audit evidence supplied to Scholar, not tests performed by Scholar. Deployment remains UNVERIFIED until independently observed.

## Update contract for every significant patch
The builder supplies a dated macro/micro delta in the patch handoff: purpose, affected components/interfaces, before -> after, dependencies, implementation/test/deployment status, evidence revision, cost/permission implications and next blocker.
A designated maintainer updates this compact map when the patch is accepted. Pending branch proposals stay explicitly pending; do not overwrite deployed-state claims with proposed designs.
Until automatic delivery exists, hand off by explicit branch/PR links and record map refresh as pending/complete. A committed note does not mean a running Scholar received it.
Scholar may read/reconcile the map and propose corrections in its own reports. A builder/maintainer edits this canonical note, preserving Scholar's read-only advisory boundary.
Before each recommendation, Scholar checks the latest relevant patch notes and heads. If freshness is uncertain, mark it stale/unverified and verify the affected system before making adoption claims. No permanent polling loop or whole-vault reread is required.

## Required impact paragraph in Scholar recommendations
Name: the Atlas need; affected systems/interfaces; current baseline/status; proposed change; prerequisites; expected benefit as a hypothesis; cost/permission implications; bounded test and rollback; evidence required for promotion.
This lets Scholar search for useful building blocks while understanding what they would connect to or change.
