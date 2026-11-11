# Verified technical building blocks and research questions
Research snapshot: 2026-11-11. Links are starting points, not proof the combined system exists.

1. tldraw SDK: https://github.com/tldraw/tldraw — programmable editor and React canvas, includes starter kits.
2. tldraw Agent Starter Kit: https://github.com/tldraw/tldraw/tree/main/templates/agent — example of agent actions on canvas, but chat-based rather than continuous duplex pipeline.
3. tldraw API example: https://tldraw.dev/examples/api — create/update/rotate/move shapes programmatically.
4. Motion SVG animation: https://motion.dev/docs/react-svg-animation — path/shape attribute animations, line drawing, morphing.
5. LiveKit Agents: https://github.com/livekit/agents — real-time voice agent orchestration; optional adapter.
6. LiveKit Agents voice examples: https://github.com/livekit/agents/tree/main/examples/voice_agents — find current provider capabilities, includes examples of realtime/duplex providers; verify against live docs.
7. tldraw licensing: https://tldraw.dev/ — review for current production terms; do not rely only on open GitHub source.

## Research tasks (not assumed facts)
- Identify which actual duplex developer APIs emit partial transcript/timestamps and interruption notifications, and which permit context injection while speaking.
- Benchmark Jev, Holo and other small structured-output deciders against the same multilingual action-selection fixture; no winner preselected.
- Determine which tldraw Starter Kit assumptions block streaming/low-latency event injection.
- Measure paint update overhead on desktop browser under high event frequency.
- License-check tldraw SDK and any model weights used in public distribution.

## Evidence standard
Every claim about model latency, provider capabilities and shipping readiness must include test method, date, version, environment and a link/log. Creator-post benchmark claims are hypotheses, not verified service guarantees.
