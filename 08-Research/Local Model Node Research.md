# Local Model Node — Research & Selection Policy

Date: 2026-10-12. Hardware: MacBook Air M4, 16 GB unified memory, fanless, ~16 GB free disk.
Purpose: stop wasting resources on local models/harnesses that don't fit, and give ATLAS a repeatable way to evaluate new ones. Evidence labels: **MEASURED** (run on this Mac), **REPORTED** (web-search summaries, unverified against primary sources — treat as hypotheses), **INFERENCE**.

## Measured on this Mac
| Model | Params / quant | Decode | Prefill | Cold load |
|---|---|---|---|---|
| `qwen2.5-coder:14b` | 14.8B dense, Q4_K_M | 9.4 tok/s | 25 tok/s | 67 s |
| `gemma4:latest` | 8.0B total (E4B-class), Q4_K_M | **27.3 tok/s** | 50 tok/s | 18 s |

Caveats: single short prompt, 4K ctx, cold load while swap was ~2.6→8.8 GB. Prefill is noisy. Re-measure with `tools/local_model_bench.py` before relying on these.

## Findings
1. **Decode speed is bandwidth-bound** (INFERENCE, consistent with measurements): tok/s ≈ bandwidth ÷ bytes read per token. A dense 14B (~9 GB) is slow; fewer *active* parameters is what makes `gemma4` fast.
2. **`gemma4:latest` here is the E4B edge variant** (MEASURED: 8.0B listed; REPORTED: ~4.5B effective via Per-Layer Embeddings, 128K ctx, Apache 2.0, tools + thinking + vision + audio capability flags). Best current fit on this machine.
3. **MoE helps speed, not memory** (REPORTED): all expert weights must be resident. Gemma 4 26B-A4B (~4B active) and Qwen 30B-A3B-class models need ~16–18 GB at Q4 → **do not fit** 16 GB. A 12B MoE at ~8 GB Q4 would (REPORTED, e.g. JetBrains Mellum) — unverified.
4. **Qwen 3.6 27B dense: rejected** for this node — ~16–20 GB at Q4 (REPORTED) exceeds the usable GPU budget (~10–11 GB default wired limit) and would decode ~4–5 tok/s (INFERENCE). Reconsider only on ≥32 GB hardware.
5. **Practical budget on 16 GB:** ~9–11 GB for model + KV cache after macOS and apps (REPORTED). Ceiling ≈ 14B dense at Q4 with small context — usable for occasional "think harder" jobs, not as a worker default.
6. **Engines (REPORTED):** MLX is typically ~15–25% faster decode on Apple Silicon; llama.cpp/Ollama is often better at prefill and is the most convenient (OpenAI-compatible API). Ollama ≥0.20-era builds may include optional MLX paths. **Untested here** — worth a head-to-head with the bench tool before switching engines.
7. **Harness lessons for small models (REPORTED, aligns with ATLAS):** constrain tool surface per step; trim/fold old tool output; set context explicitly (default 4K truncates agent loops); use native chat templates; preserve/strip reasoning tokens consistently; use schema-constrained decoding for tool args where available; keep deterministic validation outside the model.
8. **Speculative decoding** (REPORTED) may help but adds memory for a draft model; low priority on 16 GB.

## Policy for ATLAS (proposed — needs an ADR + human approval, not yet in [[05-Decisions/Decision Log]])
- **Role:** the Mac local node is a cheap worker (classification, extraction, drafting, summarization, tool-call practice). Never the executive brain, never self-reviewer. Final review stays GPT/Codex-class ([[04-Operations/Review Gate]]).
- **One resident model at a time**; default `gemma4:latest`; the 14B is opt-in.
- **Admission test before adopting any new local model/engine** (run `tools/local_model_bench.py`, log the row in this note or a dated results file):
  1. Fits: model + KV at target ctx ≤ ~9 GB, swap growth < 1 GB during run.
  2. Speed: decode ≥ 15 tok/s for worker use (≥ 25 preferred for interactive).
  3. Capability: tools flag + passes a small tool-call/JSON-validity task set; quality spot-check against a cloud model.
  4. Cost: download size vs free disk; no paid API used.
- **Treasurer integration:** local runs cost \$0 API but consume time/energy/thermal budget — log tok/s and load time per run alongside cloud spend; watchdog events (memory/swap/thermal unloads) are escalation signals.
- **Re-check cadence:** review new releases monthly or when a candidate is claimed to fit ≤ ~10 GB; do not chase every release.

## Watchlist
Superseded by the 2026-10-12 availability survey below (that survey is based on the live Ollama library; speeds still UNMEASURED here).

## Runtime
`~/.gemini/antigravity/scratch/local-llm-runtime/localllm.py` (Mac-local utility, not a source of truth): Ollama tuning, keep-awake, memory/swap/thermal watchdog. Not yet started on this Mac as of this note.

Related: [[03-Architecture/Source of Truth]], [[04-Operations/Model Cost and Cache Policy]], [[02-Agents/Skills/cost-aware-routing]], [[04-Operations/Mac Antigravity Node Handoff]].

## Availability survey — 2026-10-12 (source: ollama.com/library and per-model pages; sizes as listed, speeds NOT measured here)

### Fits a 16 GB Mac (≤ ~9 GB)
| Model | Size | Notes (from library description) |
|---|---|---|
| `lfm2.5:8b` | 5.2 GB | LFM2.5-8B-A1B, edge MoE (~1B active) "built for fast, reliable tool calling on consumer hardware" — top candidate for worker speed |
| `granite4.2:8b` / `:3b` | 5.3 / 2.2 GB | IBM, Apache 2.0; tool use, thinking, structured JSON output, RAG |
| `ornith-1.5:9b` | 6.6 GB | self-improvement-trained family; capability unverified |
| `tev1:4b` / `:0.8b` | 4.5 / ~1 GB | **decision model** (fast typed classification) |
| `laya` (421M / 322M multilingual, MLX fp16) | tiny | **decision model**, ModernBERT-large based, "typed-decisions" variant; MLX-only tags |
| `nimble:9b` | 9.3 GB | 9B decision model; borderline on 16 GB |
| `gemma4:latest` (installed) | 9.6 GB | measured 27.3 tok/s |

### Does NOT fit 16 GB (all-experts-resident rule)
`qwen3.8:27b` 18 GB; `muse-glimmer:30b` (Meta, 30B always-on agents) 18 GB; `north-mini-code-1.0` (Cohere, 30B-A3B coder) ~19 GB; `laguna-xs-2.1` (33B-A3B) ~20 GB q4; `nemotron-3.5-lightning:30b` (30B-A3B) 23 GB; `ornith-1.5:35b` 23 GB; `clef-flash:9b` 11 GB. These are the "frontier of local agents" in the library but need ≥ 32 GB. On this Mac they are for reference only.
Note: the earlier "Qwen 3.6 27B" question maps to `qwen3.8:27b` (18 GB) in today's library; `qwen3.6` tags were not checked.
`glm-5.3-flash` appears only as a `:cloud` tag — Ollama cloud models are remote (spend/privacy implications, not local).

### Frontier techniques for a base 16 GB Apple Silicon machine (REPORTED, unverified here)
- **Decision models** (new class): one forward pass, no generated tokens, calibrated probabilities. Matches Eve Lab's JEV pattern (typed judgments). Local `laya`/`tev1` could take high-volume classification/routing/triage off paid gateways at \$0 — HYPOTHESIS, needs a quality comparison against current JEV outputs before any routing change.
- **MLX-format tags** now ship in Ollama (`:27b-mlx`, `laya` MLX-only); MLX decode reportedly 15–25% faster. Test `gemma4`/`lfm2.5` GGUF vs MLX with `tools/local_model_bench.py`.
- **Native multi-token prediction** (MLX stack, e.g. MTPLX) reported 1.6–2.2x decode speedup; separate draft-model speculative decoding reportedly backfires on llama.cpp/Metal.
- **KV-cache compression** (TurboQuant-style, 3–4 bit) reported 3–5x smaller KV; community MLX implementations only. Current cheap win already applied: `OLLAMA_KV_CACHE_TYPE=q8_0`.
- **Neural Engine is not the LLM path**; stay on GPU/Metal.
- **Harness QoL (REPORTED):** Pi agent (minimal prompt, live llama.cpp model switching), OpenCode (client/server daemon, router tiers fast/medium/heavy), Aider, Cline; all use an OpenAI-compatible endpoint, so the Mac node can serve them via `http://<mac>:11434/v1`. Tiered routing (small local for file reading/grep/classification → heavier/cloud only when needed) mirrors [[02-Agents/Skills/cost-aware-routing]].

### Proposed next measurements (each needs a download; ask the human first)
1. `lfm2.5:8b` and `granite4.2:8b` through `tools/local_model_bench.py` vs `gemma4` (speed + JSON smoke).
2. `laya:421m-typed-decisions-mlx-fp16` and `tev1:4b` on a labelled sample of real JEV-style judgments; compare agreement with existing outputs.
3. GGUF vs MLX tag of the same model.

## Benchmark results — 2026-10-12 (MEASURED on MacBook Air M4 16 GB; raw rows in `data/local_model_bench.jsonl`)
Single run each, 4K ctx, 200 generated tokens, temperature 0, via `tools/local_model_bench.py`. Models were pulled, tested and removed (disk is tight).

| Model | Decode tok/s | Prefill tok/s | Load s | JSON smoke | Swap Δ GB |
|---|---|---|---|---|---|
| `lfm2.5:8b` (5.2 GB) | **75.4** | 96.9 | 1.4 | **FAIL** | 0.0 |
| `granite4.2:8b` (5.3 GB) | 17.9 | 137.8 | 1.1 | pass | 0.0 |
| `gemma4:latest` (9.6 GB) | 26.7 | 123.3 | 16.5 | pass | +3.3 |

Reading (INFERENCE, n=1): `lfm2.5:8b` is ~2.8x faster than `gemma4` and fits with no swap growth, but failed the JSON smoke test; the failure cause is undetermined (see diagnosis below). `granite4.2:8b` is slower than `gemma4` here but reliable on JSON and light on memory. `gemma4` is the strongest all-rounder installed but is the only one that pushed the machine into swap.

**System warning:** after the runs, swap was 9.5 of 10.0 GB used (encrypted, ~0.75 GB free). Memory pressure from other applications — not these models — is the dominant constraint; fix it (quit apps / restart) before drawing conclusions or running a resident model.

Not yet done: decision-model tests (`laya`, `tev1`), GGUF vs MLX comparison, JSON-failure diagnosis for `lfm2.5`.

### `lfm2.5:8b` diagnosis (MEASURED, n=5 prompts; same day)
- The earlier "JSON FAIL" was a **test artifact**: with `format=json` the model returned valid JSON but invented its own schema (`weather`/`params`) instead of the one in the prompt — an instruction-following miss on an ad-hoc schema, not a broken output format.
- **Native tool calling (Ollama `tools` API): 5/5 correct** (right tool, right argument; correctly made no call for a plain arithmetic question), ~70–77 tok/s sustained, identical with `think` true/false.
- **Caveat — reasoning:** the model emits a `<think>` block before answering; `think:false` did not change token counts or suppress it on this Ollama build (0.33.2). Budget `num_predict` generously (a 120-token cap returned empty content because thinking consumed it). Reasoning inflates latency per answer even at 75 tok/s.
- **Not yet evaluated:** answer/code quality (my 300-token probe was consumed by the thinking preamble), long-context behaviour, multi-turn agent loops. Speed + tool-call correctness alone do not make it a good worker.
- Benchmark tool updated: the schema-strict JSON check was replaced with a native tool-call check (`tool_ok`).
- Status: model left installed (5.2 GB) for further evaluation.

## Decision-model (decider) tests — 2026-10-12 (MEASURED, tiny smoke set; `tools/decider_eval.py`)
**Discovery:** Ollama ≥0.35/0.40 exposes `POST /v1/systemone`, explicitly "follows TypeSafe's Jev API" (state + up to 64 typed questions: `choice` / `noul` (true-false probability) / `score` (rubric)). Eve Lab's JEV worker (`typesafe-ai/jev`, see `provider_registry.yaml`) uses the same concept via the Vercel AI Gateway, so a local decider is a plausible drop-in *at the interface level*. Not yet verified against Eve Lab's actual wrapper (`src/jev/gateway.ts` maps the gateway evaluation-model protocol, not `/v1/systemone`) — an adapter would be required.
Setup: the installed Ollama app (0.33.2) is too old; the official 0.40.3 binary runs as a **sidecar** on port 11435 (`~/.localllm/ollama-0.40.3`), sharing the model store. The installed app was not modified.

Test: 12 job-application emails (5-way `choice` + `needs_reply` true/false, no criteria text) and 4 agent-step policy gates (go/no-go). Author-written labels; very small n; question wording not tuned.

| Model | Size | Classify | Needs reply | Gate | Median latency | License |
|---|---|---|---|---|---|---|
| `laya` (ModernBERT-large, 421M) | 0.85 GB | 10/12 | 5/12 | 2/4 | **63 ms** | Apache 2.0 |
| `tev1:0.8b` | 0.8 GB | 9/12 | 7/12 | 3/4 | 134 ms | dataset/training scripts MIT |
| `tev1:4b` | 4.4 GB | **12/12** | **11/12** | 3/4 | 794 ms | see model page |

Observations (INFERENCE from n=16):
- Output is probabilities with **zero generated tokens**; `tev1:4b` was far more confident/discriminating (e.g. 0.997 on a clear interview request vs laya 0.54).
- `laya` is fastest but weakest on my *custom* labels; it is fine-tuned on email triage/safety/intent/fact-check and has a **512-token context** — long emails must be truncated. Its `needs_reply` result (5/12) is no better than chance here, partly because my question had no criteria.
- All three misjudged "read the local tracker and summarize" as unsafe (p≈0.1–0.3): gates are conservative — acceptable direction for an approval gate, but it shows decider outputs must be validated before they gate anything. Deterministic policy code remains authoritative ([[00-Atlas/Home]], approval gates in [[AGENTS]]).
- Calibration and agreement with real JEV outputs are **unmeasured**. ECE figures on model pages are vendor-reported.

Other open decision models on the Ollama library (not tested): `nimble:9b` (Bespoke Labs, Qwen3.5-9B base, Apache 2.0, 9.3 GB, needs Ollama ≥0.35), `clef-flash:9b` (Cloudflare, multimodal, 11 GB, Apache 2.0) and the larger `clef` — all too heavy to keep resident alongside a worker on 16 GB. Liquid AI `d1-3B` / `d1-omni-600M` were reported by web search but were not seen in the Ollama library and are unverified.

Proposed pattern (needs ADR + approval): worker model (`gemma4` or `lfm2.5:8b`) does generation; a resident decider (`tev1:4b`, or `tev1:0.8b`/`laya` where latency matters) does typed routing/classification/gating; strong cloud reviewer remains the final critic. Treasurer logs decider calls as \$0 API cost with latency.
