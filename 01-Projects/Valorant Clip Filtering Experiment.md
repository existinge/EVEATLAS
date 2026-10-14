# Valorant Clip Filtering and Montage — Experiment
Date: 2026-10-14
Status: proposed, not implemented or tested.
User requested this plan be recorded in Atlas. This records intent, not authorization to spend on APIs or process/upload footage.

## Goal
Automatically filter a folder containing hundreds of mixed saved recordings, exclude unwanted random chatter/joke captures, and produce a gameplay clip dump with minimal manual sorting. Do not substitute a kill-only filter for the requested semantic triage.

## Architecture
- Windows PC: OpenClaw coordinates; original clips remain here. Local tools inventory files, extract candidate events, sample frames, transcribe audio, validate edits, and render.
- MacBook Air M4 16 GB: LFM2.5 worker receives compact handoff packets, returns structured labels/timelines/tool requests. TEV1 handles selected closed-choice judgments if it improves measured results.
- Vision-capable main model: evaluates visual evidence when text metadata/transcripts are insufficient. Vision capability of the installed LFM is NOT established.
- PC executes tool requests and returns compact results; no need to transfer full videos to Mac.

## First trial
1. Inventory a small representative batch of 20-30 recordings without modifying originals.
2. Extract transcripts, sampled frames and gameplay-event timestamps using existing tools.
3. Ask the judge to classify each recording: USABLE_GAMEPLAY, UNWANTED_CHATTER_OR_JOKE, UNCERTAIN. Include rationale and evidence timestamps. Missing evidence is uncertainty, not rejection.
4. Initial criteria: prioritize footage suitable for a gameplay compilation; exclude captures whose only content is nonsensical jokes/random chatter. Confirm ambiguous preferences from examples rather than assuming all humor is unwanted.
5. Keep originals and all uncertain items. Save a local manifest; no automatic deletion or publishing.
6. Assemble a preview from usable segments, preserving setup and multikill continuity. User reviews a short preview rather than the entire folder.
7. Cache results by file hash and analysis version; resume without repeating completed work.

## Handoff contract
Input: job ID, clip IDs, durations, event timestamps, transcript snippets, editing criteria, available tool schemas, output schema, retry/time budget.
Output: per-clip labels and evidence, proposed in/out timestamps or timeline, requested actions, unresolved questions.
Use small batches within the configured 8192-token context. Validate all paths, IDs, timestamps and output schemas in code. Model scores are not proof of correctness.

## Local pair: evidence and limits
See [[08-Research/Local Model Node Research]] and local-node/node.json on the Mac handoff branch.
- LFM2.5:8b recorded 75.4 decode tokens/sec; native tool smoke 5/5. Coding quality and long agent loops unmeasured.
- TEV1:0.8b median 134 ms; tiny author-labelled tests: classification 9/12, needs_reply 7/12, gate 3/4.
- TEV1 routing is optional. Deterministic steps should stay in code. Compare LFM alone vs pair before adding per-step judgments.
- No claim of frontier-level capability, reliable humor understanding, or demonstrated end-to-end speedup.

## Candidate building blocks — inspected documentation, not execution-tested
- Crispy: https://github.com/Flowtter/crispy — Valorant highlights, pre/post windows, grouping nearby kills. Does not establish semantic joke filtering.
- Vidai: https://github.com/sageships/vidai — declarative JSON timeline and FFmpeg rendering.
- Beatsyncer: https://github.com/ikequan/beatsyncer — beat-aligned montage tooling.
These are candidate components, not a verified compatible stack. Inspect installation, licenses, Windows support and output quality before adopting. MCP is optional; CLI/API tools are sufficient if the host exposes them.

## Acceptance and comparison
Measure usable-clip precision, missed good clips, uncertain fraction, user corrections, wall time, model calls/tokens, retries and actual API cost. Compare with main-model-only baseline and LFM-only routing on the same labelled sample. Passing JSON does not establish editorial quality.
No numerical success claim until measured. Start with filtering before elaborate effects or GUI automation.

## Boundaries and next step
No clips, transcripts, private conversation content, credentials or LAN details in public Atlas. Store analysis and footage locally. External vision/transcription uploads and paid calls require appropriate authorization.
Next builder action: inspect PC capture format and available local tools, then prepare a dry-run manifest and representative trial. This note does not indicate access to the PC or a running implementation.
