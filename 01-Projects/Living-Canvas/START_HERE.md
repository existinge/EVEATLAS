# START HERE — Living Canvas (Atlas agent entry point)

> Status: SPECIFICATION PACK, NOT A WORKING APPLICATION. Last assembled: 2026-11-11.
> Canonical home: existinge/EVEATLAS / 01-Projects/Living-Canvas.
> This project belongs to the existing Atlas loop. Do not create Atlas v2, a second planning silo, or an autonomous manager.

## Mission, in one paragraph
Build a low-cost, open-source, provider-pluggable real-time visual companion to full-duplex AI conversation: the AI's mind's eye made visible. A conversational model speaks; an asynchronous semantic planner prepares a bounded, rolling concept horizon; a low-latency interchangeable decider proposes small canvas actions; a deterministic coordinator validates them against shared state; a graphics runtime draws and animates continuously. The domain example is multilingual language learning, but the runtime must be domain-general.

## Before you write code
1. Read repository-root AGENTS.md, 03-Architecture/Source of Truth.md, this file, PROJECT.md, ARCHITECTURE.md, PROTOCOL.md, VISUAL_RUNTIME.md, and GATES.md.
2. Read [NEXT_ACTION.md](NEXT_ACTION.md), [the provider policy](VOICE_AND_MODELS.md#provider-policy), and only the active ticket. Check existing code, tools and tests.
3. Work in a scoped feature branch/PR from the existing Atlas repository. Keep a separate implementation workspace (subfolder or linked repo) only if the existing vault explicitly delegates it; Atlas owns the durable specification.
4. Run the Atlas baseline audit and tests before changes: python tools/atlas.py audit ; python -m unittest discover -s tests -v. Record actual output.
5. Do not copy this spec into a second independent authority system. Never commit credentials or private conversation recordings.

## Current dispatch

[T00 evidence](worklogs/T00.md) is available for review. After P0 acceptance is recorded in [GitHub issue #9](https://github.com/existinge/EVEATLAS/issues/9), execute [T01](tickets/T01-SHARED-SPACE.md) only. Use local TypeScript and fixtures with zero inference cost. Stop at P1 and return test evidence. See [AGENT_DISPATCH.md](AGENT_DISPATCH.md).

T02 through T07 remain individually gated. T03 uses a minimal programmable tldraw Editor integration. Keep the [tldraw Editor API example](https://tldraw.dev/examples/api) as a reference for that ticket.

## Agent handoff response — mandatory
Report: actual branch/commit; changed files; commands run + result; state of runtime vs simulation; measured latencies (or not measured); architecture deviations; blockers; next ticket; exact next agent instruction. See ATLAS_HANDOFF.md.

## Non-negotiable
If the implementation becomes a chatbot that redraws only after full responses, a script of fixed visual scenes, a computer-use clicking agent, or a second LLM adjudicating every frame, STOP. Those do not prove the concept.
