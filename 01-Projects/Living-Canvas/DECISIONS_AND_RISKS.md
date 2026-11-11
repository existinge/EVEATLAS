# Decisions, hypotheses and open risks

## Locked design decisions (for this draft, subject to review)
D01: Canonical notes live inside existing EVEATLAS/Obsidian under 01-Projects; don't fork authority.
D02: A full-duplex provider is the live conversational model. No custom duplex training.
D03: Shared state and event pipeline are central, not point-to-point synchronous agent calls.
D04: Coordinator is deterministic code with atomic commits and bounded permissions.
D05: Fast decider is swappable; no Jev-specific API shape or computer-use dependency.
D06: Canvas uses reusable mathematical/procedural rendering, not a visual generator for every frame.
D07: Long-horizon planner maintains a bounded branching frontier; unexpected exits degrade gracefully.
D08: Multilingual by design, use concept IDs and tagged language representations.
D09: Human correction overrides speculative model output. No semantic invention on low confidence.
D10: Test a complete interaction, not disconnected demos. Each code ticket is independently gated.

## Hypotheses requiring measurement
H01: Small decision models can handle action selection within <150 ms after eligible observations on target machine.
H02: Rolling frontier permits most meaningful in-context transitions without waiting for a planner call.
H03: Persistent SVG and tldraw objects support smooth conceptual transformations enough for mind's-eye immersion.
H04: At least one affordable duplex API exposes events adequate for interruptions and semantic synchronization.
H05: Forwarding decider interest signals to planner improves next-branch readiness relative to planner alone.

## Critical threats / mitigations
R01 Semantically confident error → deterministic action whitelist, abstain/hold, human correction.
R02 Voice events unavailable or delayed → capabilities negotiation, optional parallel ASR, degrade honestly.
R03 Concept-tree explosion → bounded frontier, TTL, active-interest pruning, versioned cache.
R04 Async races → epoch+revision+correlation validation, single serial reducer, deterministic replay.
R05 Visual hallucination → no arbitrary factual objects unless semantically authorized, neutral fallback.
R06 Multi-language collapse → preserve source language, ambiguity, polysemy and transcript provenance.
R07 Agent scope drift → ticket fences, tests and review; don't silently swap to canned slides or click bots.
R08 Cost creep → deterministic local baseline, planner coalescing, no paid services before approval.
R09 License drift → verify tldraw license for chosen distribution/use; do not assume full SDK is MIT just because starter templates are.
R10 Overengineering → first 60 min aim for one production-shaped loop; no Redis, event broker, microservices or vector DB until measured need.
R11 Fast but meaningless screen updates → measure semantic correctness and human-perceived relevance, not fps alone.

## Deferred decisions
- Exact duplex provider, ASR strategy, decider candidate and hardware benchmarking.
- tldraw starter vs minimal React/tldraw editor integration (choose by preflight).
- Planner model, low-level image generation/asset-generation, Rive, backend persistence, distributed runtime.
- License/distribution of independent runtime; open-source project intent does not override upstream licenses.

## Explicit anti-patterns
A giant prompt that tries to implement all features; re-rendering on LLM final response; deriving semantic authority from decider confidence; decider operating via screenshot-and-click; separate state silos between planner and renderer; false timing claims.
