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

## Watchlist (all UNVERIFIED here)
Qwen 3.5 9B class (~5 GB Q4, reported strong for tool use); Gemma 4 E2B (smaller/faster fallback); a ≤12B MoE coder; MLX-served variants of the above via mlx-lm/LM Studio.

## Runtime
`~/.gemini/antigravity/scratch/local-llm-runtime/localllm.py` (Mac-local utility, not a source of truth): Ollama tuning, keep-awake, memory/swap/thermal watchdog. Not yet started on this Mac as of this note.

Related: [[03-Architecture/Source of Truth]], [[04-Operations/Model Cost and Cache Policy]], [[02-Agents/Skills/cost-aware-routing]], [[04-Operations/Mac Antigravity Node Handoff]].
