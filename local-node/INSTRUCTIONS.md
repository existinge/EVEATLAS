# Local Node Packet — worker + decider pair

**Schema:** `atlas.local-node/1` · machine-readable twin: [`node.json`](node.json) · evidence: [[08-Research/Local Model Node Research]] · status of this Mac: [[04-Operations/Mac Antigravity Node Handoff]]

## What this is
A reusable, git-cloneable local inference node for a 16 GB Apple Silicon Mac. Two models, one sidecar Ollama server on `127.0.0.1:11435`:

| Part | Model | Role | Endpoint |
|---|---|---|---|
| Worker | `lfm2.5:8b` (5.2 GB, ~1B active params, ~70–77 tok/s measured) | cheap drafting / extraction / tool-call practice | `/v1/chat/completions`, `/api/chat` (native tools) |
| Decider | `tev1:0.8b` (0.8 GB, ~134 ms median measured) | typed routing / classification / go-no-go probabilities, zero generated tokens | `/v1/systemone` (JEV-compatible) |

Where it sits in ATLAS: a **cheap worker pool** under Eve/ATLAS. It is not the executive brain, not a reviewer, and not an approval authority. Cloud/GPT-class review remains the final critic ([[04-Operations/Review Gate]]); deterministic code owns approval gates and money ([[AGENTS]]).

## Join the node (agent checklist)
1. `git clone https://github.com/existinge/EVEATLAS.git && cd EVEATLAS/local-node` (use the PR/branch that contains this folder until it is merged).
2. Read `node.json` (boundaries, limits, guard). Do not change models or ports without a recorded decision.
3. `./setup.sh` — checks RAM/disk, installs a pinned sidecar Ollama only if none ≥ 0.40 exists (never touches an installed Ollama app), pulls both models (~6 GB).
4. `python3 localnode.py start` — starts the server with tuned env, preloads decider then worker, keeps the Mac awake, launches the guard.
5. `python3 smoke_test.py` — must print `NODE OK`. If not, report the failing line; do not proceed to real work.
6. Use via `client.py`: `work(prompt, tools=...)` and `decide(state, questions)`.
7. Stop: `python3 localnode.py stop`.

## Operating rules
- **Worker output is a draft.** Anything consequential needs independent review before it counts as done.
- **Thinking worker:** `lfm2.5:8b` always emits a `<think>` block; `client.work()` budgets ≥1500 output tokens. A small `num_predict` returns empty content.
- **Decider is advisory.** Probabilities are uncalibrated against real data here (author-labelled smoke test, n=16). Never let a decider alone approve outreach, submissions, spending or deletions. Prefer `tev1:4b` (set in `node.json`, ~4.4 GB) when accuracy matters and memory allows.
- **Guard:** if free memory < 10% or swap *grows* > 1.5 GB over the start baseline for ~15 s, the guard unloads the **worker** and keeps the decider, then notifies. Recover with `python3 localnode.py ensure` once pressure clears. (Judged by swap growth, not absolute use — macOS retains old swap.)
- **One resident pair only.** No third model loaded alongside; no parallel requests (`NUM_PARALLEL=1`).
- **Privacy:** loopback only; no secrets or private data in prompts that get logged to Git; logs live in `~/.localnode`, outside the repo.
- **Cost:** \$0 API spend. Log latency/tok/s and guard trips as Treasurer inputs.

## Task-packet pattern (how Eve/ATLAS should delegate here)
Include per [[AGENTS]] handoff: objective, canonical files, branch, allowed tools, budget, expected output schema, validation step, reviewer, next step. For the node specifically also state: which side is used (`worker` or `decider`), the question schema for deciders, and the token budget for the worker.

```text
route:    decider  -> choice question (2-24 options) -> pick destination + probabilities
gate:     decider  -> noul question                  -> go/no-go probability (advisory; policy code decides)
draft:    worker   -> chat/tools, >=1500 tokens      -> DRAFT, flagged unreviewed
review:   NOT here -> GPT/Codex-class independent reviewer
```

## Known limits (honest status)
| Item | Status |
|---|---|
| Server + both models + smoke test on the build machine | **VERIFIED PASS (2026-10-12)** |
| Worker answer/code quality | **UNMEASURED** (speed + tool-call only) |
| Decider quality (`tev1:0.8b`) | PARTIAL: classify 9/12, needs_reply 7/12, gate 3/4 on a tiny set; 4B was 12/12, 11/12, 3/4 |
| Adapter from Eve Lab's JEV worker to `/v1/systemone` | MISSING |
| Decider calibration vs real JEV outputs | UNMEASURED |
| Non-Apple-Silicon / <16 GB hosts | UNSUPPORTED (setup warns/exits) |

## Verification log
**Run date:** 2026-10-12 on MacBook Air M4 (16 GB unified memory, macOS arm64)
```text
PASS - both models resident | loaded=['tev1:0.8b', 'lfm2.5:8b']
PASS - worker native tool call | 75.5 tok/s, call={'index': 0, 'name': 'search', 'arguments': {'query': 'current weather in Paris'}}
PASS - decider typed decision | rejection p=1.00
PASS - memory snapshot (informational) | total = 7168.00M  used = 5554.62M  free = 1613.38M  (encrypted)

NODE OK
```
Both `lfm2.5:8b` (via `llamacpp` runner) and `tev1:0.8b` (via `mlx` runner) remain resident concurrently on port 11435. Free RAM remained at ~22% with no swap growth.
