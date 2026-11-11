# Model/provider adapters — plug-and-play without magical capabilities

## Duplex provider is LIVE
The voice provider is the live conversational participant, not the coordinator. It must be replaceable. The product goal requires live spoken dialogue with interruption handling; do not train a custom duplex system.

## Capability negotiation
At connection time, provider adapter reports whether it supports:
- bidirectional low-latency audio
- speaker/turn IDs
- partial transcript text + timing
- final transcript text + timing
- interruption/cancel events
- tool/event injection during ongoing voice session
- text/semantic context updates during speech
- session resumption and telemetry

Don't make provider-specific claims without a tested adapter. If a full-duplex provider gives no usable partial transcript, a parallel streaming ASR can be evaluated, but dual streams are **observations to reconcile**, not competing topic authorities. If neither is available, show only non-semantic live UI reactions until confirmed utterance events arrive. A consumer chat voice UI is not equivalent to an accessible developer API.

## Where LiveKit fits
Optional media transport and agent orchestration; NOT a model and NOT required for initial local event/canvas test. Use when it actually reduces work for the chosen voice provider. Consider provider-native session SDK first for fewer hops; compare on interruption events, timing, and cost.

## Decider interface
Method: propose(observationWindow, frontierSnapshot, rendererCapabilities) → action proposals or NEEDS_PLAN. Must not generate new unrestricted semantic concepts. Candidate types can include a decision model, small structured-output/tool-calling model, or deterministic baseline. The code doesn't depend on model-specific response format.

Models discussed: Jev, Holo and other sub-billion options are *evaluation candidates*, not verified superior choices. Their speed, multilingual accuracy, structured output and local compute suitability need direct testing. Do not invent benchmark results or assume a computer-use model's screenshot capability helps on this API.

## Planner interface
Method: extend(conversationEvidence, currentGraph, frontierInterest, capabilities) → versioned candidate concept graph and visual recipes. Can be another LLM alongside a duplex provider, especially if that provider cannot expose internal reasoning. Its latency does not block rendering. Budget and rate limit planner calls. Use aggressive coalescing/debouncing, NOT a call per transcript token.

## Multilingual-first design
Use language-independent concept IDs plus tagged surface forms (ja-JP/th-TH/en-US examples). ASR uncertainty and code switching must be represented; don't translate everything to English then overwrite distinctions. Pinyin-like Thai romanization can be a presentation concern, not an inference assumption. Track language switching and correctable spans. Test with languages unlike English.

## Adapter matrix to complete during preflight
| Provider/model | Live audio | Partial transcript | Interrupt event | Context injection | Local? | Actual tested? |
|---|---|---|---|---|---|---|
| Candidate duplex provider | TBD | TBD | TBD | TBD | TBD | NO |
| Candidate fast decider | N/A | N/A | N/A | N/A | TBD | NO |
| Deterministic stub | N/A | Input fixtures | Simulated | State snapshots | YES | NOT YET |

No keys, provider credentials, or audio recordings should be stored in public Atlas.
