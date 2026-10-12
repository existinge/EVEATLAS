# Mac Antigravity Node — Context Checkpoint & Handoff

Generated: 2026-10-12 by Antigravity on the MacBook (read-only discovery pass, then this note). Status labels are honest: PLANNED / PARTIAL / IMPLEMENTED / RUNNING / BROKEN / UNKNOWN. Evidence column = what was actually inspected or run.

## Objective
Make the MacBook a competent builder/execution node in the EVE/ATLAS loop without creating a parallel system. "Join the Atlas loop" should start by reading this note, [[AGENTS]], [[03-Architecture/Source of Truth]], [[04-Operations/Review Gate]].

## Role split (canonical, from existing docs + intent)
- **Eve/EveClaw** — executive: goals, strategy, delegation, user comms. Final authority.
- **ATLAS** — execution control plane (task state, dispatch, retries, checkpoints, validation, review, approval gates, DONE determination).
- **Antigravity (this Mac)** — builder/execution worker per [[02-Agents/Agent Registry]]: branches, tests, PR proposals. No deploys, publishing, spending or outreach without human approval.
- **Independent reviewer (GPT/Codex-class)** — final critical review; builder never self-approves ([[04-Operations/Review Gate]]).
- **Treasurer** — deterministic cost accounting, code not an LLM.

## Component status (verified on this Mac)
| Component | Status | Evidence |
|---|---|---|
| EVEATLAS vault (Obsidian+Git) | IMPLEMENTED | cloned `existinge/EVEATLAS`; `tools/atlas.py audit` = 0 issues; 13 unit tests pass |
| Vault hygiene / diff review (`tools/atlas.py`) | IMPLEMENTED | NOT an execution control plane despite the name |
| Signal Desk (`tools/signal_desk.py`) | PARTIAL | offline ingest only; no live adapters/scheduling (per its own docs) |
| Opportunity Engine tooling | PARTIAL | tiny tools + templates |
| **ATLAS execution control plane** (task graph, dispatcher, state machine, retries, checkpoints, DONE gate) | **MISSING** | no code or docs found in EVEATLAS, `saveme`, rAIdar, job-email-agent, or on-disk dirs. Only conceptual descriptions exist |
| Review gate | PARTIAL (documented process) | policy in [[04-Operations/Review Gate]] + `atlas.py review` diff helper; no automated reviewer dispatch |
| Handoff schema | PARTIAL (prose contract) | field list in [[AGENTS]] and [[02-Agents/Skills/context-handoff]]; no machine-readable schema in EVEATLAS |
| Machine-readable state/handoff precedent | IMPLEMENTED (other repo) | private repo `existinge/saveme` ("Eve Lab"): `01_STATE/*.yaml/jsonl`, `ADVISOR_HANDOFF.md`, zod schemas (`src/schemas`), `src/state/*`; 282 tests pass on this Mac |
| Treasurer / budget | PARTIAL | Eve Lab: `06_MODELS/model_costs.csv`, `AUTONOMY_ENVELOPES.yaml` (model_spending sprint limit/warning, fail-closed), `src/governance/policy.ts`, `src/ledgers`. EVEATLAS only has policy text ([[04-Operations/Model Cost and Cache Policy]]). Not wired to ATLAS dispatch. Prompt caching: not verified |
| Model routing | PARTIAL | Eve Lab `06_MODELS/provider_registry.yaml` (capability-based workers: deterministic, JEV, primary_flash/DeepSeek, advisor) + workload YAMLs; routing by measured performance is aspirational |
| OpenClaw / EveClaw runtime | UNKNOWN on Mac | no `openclaw` binary or files here (expected on the PC) |
| Hermes agent (`~/.hermes`) | PARTIAL/idle | job-search persona, local Ollama `gemma4` default, no cron, no sessions/memories; not part of ATLAS |
| Codex (`~/.codex`) | PARTIAL | config present, model set, Computer Use + browser plugins enabled; `codex` CLI not on PATH |
| Local inference (paired worker + decider) | IMPLEMENTED & RUNNING | `local-node/`: `lfm2.5:8b` (75.5 tok/s, native tools) + `tev1:0.8b` (134 ms typed decider) on sidecar Ollama 0.40.3; both resident in 16 GB RAM; smoke test PASS (`NODE OK`); see `local-node/INSTRUCTIONS.md` |
| Skills | PARTIAL | EVEATLAS `02-Agents/Skills/*.md` (6, docs only, not wired to agents); rAIdar `.agents/skills`; Antigravity workspace skills unrelated (SpiFun, shopper-pair) |
| Polaris | UNKNOWN | no artifacts found on this Mac or in accessible repos |
| Hopecore Job Engine | UNKNOWN here | only related: `existinge/job-email-agent` (Outlook/Graph classifier, public); no pipeline code for research→draft→review→send |
| Dynamic skill discovery / learnings feedback | MISSING | nothing found |

## Source-of-truth hierarchy (as found)
1. EVEATLAS markdown = intent/decisions/evidence (ADR-001).
2. Code + tests + CI = implementation truth.
3. Private bookkeeping = financial truth (not in public vault).
4. Agent memory = cache, never authority.
Local clone on this Mac: `~/Documents/EVEATLAS` (origin `existinge/EVEATLAS`). `~/Documents/Obsidian Vault` is an empty stub — **not** canonical; do not use.

## Contradictions / drift
- Name collision: `tools/atlas.py` is vault hygiene, not ATLAS the control plane.
- Eve Lab hierarchy (Eve → advisory ChatGPT → primary model → JEV → code) differs from the loop model (Eve → ATLAS → workers → GPT/Codex reviewer). Reconcile by mapping, don't replace: Eve Lab's deterministic governance/state/ledger layer is the best reusable base for ATLAS state + Treasurer.
- Eve Lab's primary model (DeepSeek via Vercel AI Gateway) vs local-Ollama defaults in Hermes: only the former is the cheap-worker pattern in the canonical docs.
- Caching/cost savings documented as objectives, not observed.
- Hermes SOUL persona overlaps job-engine intent; not integrated.

## Decisions already made
ADR-001..004 in [[05-Decisions/Decision Log]]. Drafts are not launches; external actions need explicit human approval.

## Constraints
Public repo: no secrets, tokens, private data. Branch/PR for agent changes. No paid API use for context work (none spent in this pass). No deletions of unclear files.

## Failed attempts / notes
- Sandbox blocked home-directory listing until broader access was granted; searched with read-only `find`/`grep` and the authenticated `gh` CLI (`repo` scope).
- No ATLAS or Polaris material located; those likely live on the Windows PC (`C:\Users\exist\Documents\EVEATLAS`) / OpenClaw host, or only in chat history. **Check that PC clone/branches for ATLAS code before building anything.**

## Review state
Not yet independently reviewed. This note is an unreviewed hypothesis-grade summary until a GPT/Codex-class reviewer checks it ([[02-Agents/Skills/adversarial-review]]).

## Next recommended action (single highest value)
Locate the actual ATLAS control-plane implementation on the PC/OpenClaw host (or confirm it does not exist). If absent, define a minimal machine-readable ATLAS task packet + state file *by extending Eve Lab's existing schemas/ledger/envelopes* (via ADR + PR + independent review), then expose it to this Mac. Do not build a new orchestrator first.

## Dependencies
Access to the PC EVEATLAS clone/OpenClaw workspace; reviewer channel to a GPT/Codex-class model; decision on whether Eve Lab (`saveme`) becomes ATLAS's state/Treasurer substrate.

## Budget
Spent: \$0 (no paid APIs used). Eve Lab model_spending envelope: \$1.00 sprint limit, expires 2026-10-31.
