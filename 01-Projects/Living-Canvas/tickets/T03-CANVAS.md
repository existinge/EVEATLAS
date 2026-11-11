# T03 — Persistent reactive canvas

Timebox: 25–40 minutes. Status: NOT STARTED. Depends on: T02/P2.

## Build
Create a browser screen with a tldraw editor and a runtime adapter subscribing ONLY to coordinator-committed scene actions. Implement persistent IDs and at least: show, emphasize, move, connect, revealHint, setParameter and reversible preview. Demonstrate one procedural relationship: isolated node/tree → grouped cluster or tree-to-forest-esque visual change, with pre-authored vector recipe. Avoid claiming newly generated semantic illustration.

Use minimal CSS/SVG transition to start; install Motion if its interpolation is actually needed. Keep a compact debug inspector: topicEpoch, semanticRevision, current branch, latest observation, proposal reason, commit time and render acknowledgement.

## Test gate P3
- Renderer updates existing object IDs rather than deleting/recreating entire canvas per event.
- Valid action on existing object reaches paint.
- Rejected stale action never reaches paint.
- A provisional highlight reverses after correction.
- Transform is smooth while unrelated asynchronous planner promise is intentionally delayed.
- Unknown concept shows neutral placeholder/hint, no invented drawing.
- Capture screen recording or reproducible recorded trace (no personal data).

## Forbidden
Screenshot-and-click computer use, LLM prompt per animation frame, invented visual asset lookup, installing Rive or image generation by default.

## Stop
Return branch/commit and proof, then T04.
