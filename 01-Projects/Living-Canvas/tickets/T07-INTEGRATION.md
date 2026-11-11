# T07 — End-to-end multilingual, generality and failure testing

Status: NOT STARTED. Depends on: all earlier gates (or honest blocked report).

## Continuous scenario
Live session: discuss Japanese kanji/tree/forest, ask about a related concept, abruptly pivot to Thai, interrupt and correct a partial phrase, then shift into non-language topic (e.g., a math relationship). Observe semantic and canvas behavior, not just UI smoothness.

## Stress cases
- Long continuous voice conversation without explicit stop/start.
- Branch that planner did not anticipate.
- Delayed planner result arrives after topic reset.
- User changes mind mid-utterance; provisional visual reverted.
- Code switch, low-confidence transcript and polysemous concept.
- Decider returns invalid action or confidently wrong prediction.
- Renderer errors or temporarily disconnects; state recovers via replay.
- Provider drops partial transcript support or voice network fails.
- Double event, out-of-order event, spurious duplicate action.
- Layout remains understandable; reduced motion and visual labels work.

## Gate P7
A reviewed trace proves that speech and canvas are concurrent, fast proposals are semantically bounded, unexpected exits degrade without hallucination, and at least two languages are actually tested. Report baseline vs model comparison; p50/p95 per hop; failed trials; known limitations and reproducible commands.

## Completion semantics
Do not claim that an agent-ready pack or scripted canvas equals a deployed working prototype. An independent reviewer and human signoff are required before merging into main or claiming finished.
