# Architecture — shared semantic pipeline

## Data flow (concurrent, not an inference chain)

~~~text
 microphone/audio ──→ duplex voice provider ──→ spoken response
       │                         │
       ├──→ optional timed STT ──┤ observations (partial/final, corrections)
       │                         ▼
       └────────────────→ shared event stream ←── canvas/user interactions
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
          concept planner (LLM)           fast decider
          expands branch graph            scores approved actions
                    │                           │
                    ▼                           ▼
           versioned semantic state    proposed action events
                    └────────────┬──────────────┘
                                 ▼
                     deterministic coordinator
                    validates epoch / revision /
                     permissions / object IDs
                                 ▼
                       committed scene actions
                                 ▼
                      tldraw + SVG / Motion
                                 │
                        actual-state feedback
                                 └────→ event stream
~~~

## Roles and truth
**Duplex adapter** owns bidirectional conversation media and emits whatever observable timestamps, transcripts, speaker/turn and interruption events its provider actually supports. Never fabricate partial transcript capability.

**Semantic planner** is the primary authority on topic, instructional intent, concept identity, valid relationships, branch readiness, visual recipes, and semantic permissions. It may be a separate LLM sidecar if the duplex provider cannot expose state. It does NOT drive frame-by-frame animation.

**Fast decider** consumes incremental observations and a compact eligible frontier. It returns ranked, typed action proposals; it is not required to understand raw pixels, speak, create arbitrary scenes, or be Jev specifically. When it encounters an unknown concept, emit NEEDS_PLAN, not a confident fabrication.

**Shared workspace** comprises event stream and versioned materialized state. It is the pipeline's coordination surface, not another language model. State is scoped by session, topic epoch, semantic revision, and scene revision; updates have provenance.

**Coordinator** is deterministic application code. It checks authorization and staleness and commits allowable mutations. It can let provisional non-semantic previews through, but never establishes novel semantics. Should be colocated with the state store/scene runtime for low latency.

**Renderer** receives restricted, validated scene actions. tldraw renders shapes and persistent objects; procedural SVG/Motion makes position/opacity/shape transitions smooth. Graphics can run at display refresh speed regardless of how frequently either model proposes actions.

## Provider policy

The planner, duplex adapter and local decider are independent of one another and outside the renderer's critical path. Prefer a supported existing frontier subscription for reasoning and a verified free developer tier for duplex. The offline core runs without provider credentials. OpenRouter is opt-in, and exhaustion of a free tier or subscription quota falls back to local or fixture behavior. See [provider policy](VOICE_AND_MODELS.md#provider-policy).

## Authority ladder
1. Human actions and explicit correction supersede model speculation.
2. Confirmed conversation transcript/context and planner-issued semantic snapshots establish what concepts mean.
3. Fast decider proposes transitions only inside authorized semantic envelopes.
4. Canvas applies committed scene instructions; canvas state is a feedback observation, not a semantic ground truth.
5. Provisional suggestions are labelled and reversible; low confidence is not permission to invent.

## Rolling horizon / highway model
Planner prebuilds a small frontier of likely next branches (not a complete curriculum); each branch has: stable concept ID, source evidence, language surface forms, visual recipe, action whitelist, confidence/readiness, version, expiry, and candidate exits. Decider sees the current frontier, not the entire latent tree. It can rank exits. Planner expands high-interest exits while decider acts inside existing permissions. Unplanned exit triggers a neutral transition and planner update, not an unrelated image.

Use bounded breadth/depth and TTL; trim cold branches. The first experiment can try breadth 3, depth 2 but these are tuning parameters, not locked architecture.

## The real bottlenecks
- Raw voice model throughput and decider throughput are NOT directly comparable: speech endpointing, partial ASR, transport, inference and paint have different clocks.
- A provider that exposes only final transcripts cannot support true mid-utterance semantic reactions through transcripts; an explicit parallel ASR or other permitted semantic event feed may be necessary.
- Decider speed is insufficient if it selects the wrong concept. Measure both latency and semantic error.
- Rendering is fast once geometry/recipes are available; creating novel semantic illustrations is slower and must be asynchronous.
- Inference and canvas must never await one another on the hot path.

## Concurrency policy
Use per-session event order, monotonic local sequencing, and idempotent commits. Epoch advances on confirmed topic reset; stale proposals cannot mutate the new scene. Planner produces versioned snapshots; decider captures the version it used. Human interrupt yields immediate cancellation of pending speculative transitions and a fresh observation revision. Late proposals may be logged but not applied.

## Domain-general architecture
Language learning is the high-value evaluation lane: Japanese/Thai/English code-switch, kanji, pronunciation, grammar, diagrams. The shared primitives are generic enough for math, programming and abstract conceptual explanation. Do not bake JLPT level, specific words, or a lesson into the protocol.
