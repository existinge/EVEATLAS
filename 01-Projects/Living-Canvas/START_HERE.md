# START HERE — Living Canvas (Atlas agent entry point)

> Status: SPECIFICATION PACK, NOT A WORKING APPLICATION. Last assembled: 2026-11-11.
> Canonical home: existinge/EVEATLAS / 01-Projects/Living-Canvas.
> This project belongs to the existing Atlas loop. Do not create Atlas v2, a second planning silo, or an autonomous manager.

## Mission, in one paragraph
Build a low-cost, open-source, provider-pluggable real-time visual companion to full-duplex AI conversation: the AI's mind's eye made visible. A conversational model speaks; an asynchronous semantic planner prepares a bounded, rolling concept horizon; a low-latency interchangeable decider proposes small canvas actions; a deterministic coordinator validates them against shared state; a graphics runtime draws and animates continuously. The domain example is multilingual language learning, but the runtime must be domain-general.

## Before you write code
1. Read repository-root AGENTS.md, 03-Architecture/Source of Truth.md, this file, PROJECT.md, ARCHITECTURE.md, PROTOCOL.md, VISUAL_RUNTIME.md, and GATES.md.
2. Read the current ticket in tickets/INDEX.md, then ONLY that ticket. Check existing code, tools, and tests; report what exists instead of assuming.
3. Work in a scoped feature branch/PR from the existing Atlas repository. Keep a separate implementation workspace (subfolder or linked repo) only if the existing vault explicitly delegates it; Atlas owns the durable specification.
4. Run the Atlas baseline audit and tests before changes: python tools/atlas.py audit ; python -m unittest discover -s tests -v. Record actual output.
5. Do not copy this spec into a second independent authority system. Never commit credentials or private conversation recordings.

## Agent order
- FIRST: tickets/T00-PREFLIGHT.md. Verify the actual environment, licenses, starter APIs, provider event capabilities, and build boundaries. No implementation until the assessment is recorded.
- THEN: T01-SHARED-SPACE.md. Make an executable event/state/replay loop.
- Follow T02 through T07, passing every ticket's gate. Don't skip to voice integration for a prettier demo.
- Each task packet includes exact scope, proof, timebox, and stop rules; if blocked, report the failing test and resume cursor.

## First 60-minute target — a vertical slice, not a toy architecture
Within the timebox, attempt T00 and T01, then the smallest portion of T02/T03 that fits. A local observation event should become a versioned proposal, pass deterministic validation, and update a persistent canvas object. If a tldraw integration takes longer, prove the event loop with a stub renderer and name the remaining work. NO claim that real voice, multilingual inference or Jev is connected unless it truly is.

## External code starting point
- tldraw Agent starter source: https://github.com/tldraw/tldraw/tree/main/templates/agent
- tldraw editor API: https://tldraw.dev/examples/api
- Motion SVG documentation: https://motion.dev/docs/react-svg-animation
- Optional LiveKit Agents: https://github.com/livekit/agents

Choose the smallest supported tldraw integration. The agent starter demonstrates AI-manipulated drawing but is NOT a duplex/shared-horizon implementation. Avoid adopting the kit's chat-turn assumptions into the core runtime.

## Agent handoff response — mandatory
Report: actual branch/commit; changed files; commands run + result; state of runtime vs simulation; measured latencies (or not measured); architecture deviations; blockers; next ticket; exact next agent instruction. See ATLAS_HANDOFF.md.

## Non-negotiable
If the implementation becomes a chatbot that redraws only after full responses, a script of fixed visual scenes, a computer-use clicking agent, or a second LLM adjudicating every frame, STOP. Those do not prove the concept.
