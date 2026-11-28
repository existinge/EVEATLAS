# TYGER full-duplex speech controller — Scholar research handoff
Date: 2026-10-17
Status: Candidate / investigation only; NOT deployed
Owner lanes: Scholar (research), EveClaw (architecture), Builder (future optional prototype), independent reviewer (approval)

## Opportunity
Explore [NineNineSix TYGER](https://huggingface.co/nineninesix/tyger), mentioned in [this post](https://x.com/defoemark/status/2111306095591670263), as a speech turn-taking/interruptibility controller for EVECLAW. The post claims concurrent monitoring of microphone and TTS playback, decisions every 80 ms (speak/yield/backchannel), and compatibility with different LLM/TTS systems. These are *claims to verify*, not performance guarantees. 80 ms decision frames are not 80 ms end-to-end latency.

## Desired boundary
mic + outbound TTS playback reference -> speech turn-taking decision -> cancel/pause/yield/resume and backchannel event handling -> OpenClaw voice session. Preserve existing remote LLM routing, Mem0/ATLAS data, ElevenLabs cloned voice, and execution/approval boundaries. This is not a replacement for reasoning models, STT or TTS. Verify that dedicated VAD or audio gating remains necessary in real conditions; do not assume the claim 'no VAD' is proven.

## IMPORTANT hosting change
User plans to move the local OpenClaw/EVECLAW host OFF their Windows gaming PC because of performance impact, ONTO their MacBook. Migration has NOT happened. Do not deploy, benchmark as target, or provision TYGER on the Windows PC. Hardware specifications of the MacBook (CPU, memory, Apple Silicon generation, macOS) and current migration state must be confirmed before any feasibility claim. Mac GPU/Metal/MLX/MPS compatibility of the isolated controller is unknown; do not port assumptions from RTX 2080 Ti/CUDA. The optional local OpenClaw host must not become a required dependency of ATLAS cloud runtime.

## Scholar assignment: evidence-gated investigation
1. Read exact upstream TYGER model card, code, license(s), weights, software dependencies and any custom-code / remote-code execution risks. Record SHA/release/date.
2. Distinguish small standalone speech decision controller from larger end-to-end TYGER S2S demo and enumerate each one's RAM/VRAM/CPU/GPU demand. Avoid unverified parameter/memory numbers.
3. Confirm standalone inference API: expected incoming PCM format, sample rate, playback-reference/echo handling, inference cadence, outputs, thresholds and ability to pause/cancel TTS safely.
4. Research Apple Silicon macOS inference paths and fallback routes (Core ML, MLX, MPS, CPU) if supported; estimate rather than assert until benchmarked.
5. Evaluate duplex performance using interruptions, overlapping speech, thoughtful pauses, backchannels, music/game sounds, speaker feedback/echo, mic mute and noisy environments. Include English-language limitations and multilingual alternative routing.
6. Compare against lighter VAD + endpointing + STT approaches; include latency, false barge-in, missed interruption, sustained utilization and setup complexity.
7. Propose isolation as optional feature with explicit flags, rollback, CPU/memory budgets and idle suspend so gaming PC is unaffected.
8. Produce evidence-linked findings in Scholar's source watchlist and dated macro/micro system-map patch note. Keep uncertain conclusions marked UNVERIFIED.

## Acceptance / gate
No live installation, secret transfer, host migration, continuous mic collection, automatic approval or production changes on the basis of this note. First deliver architecture options, migration-aware feasibility assessment and a minimal isolated benchmark design; require independent review before integration.
