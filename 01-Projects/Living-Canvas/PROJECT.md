# Living Canvas — Project record

Status: researching / specification approved for agent review; implementation unverified
Owner: user
Last updated: 2026-11-11
Atlas role: independent domain R&D project; no changes to Atlas execution authority

## Problem
Existing AI visual interfaces commonly follow a turn-based input → model → redraw pattern. For learning, particularly multilingual speaking practice, visual explanation and spoken dialogue should coexist continuously, without the graphics loop waiting for complete reasoning turns.

## Desired outcome
A living visual workspace that depicts what a conversational model is discussing, anticipates relevant relationships, allows responsive but safe visual exploration, and responds to hesitation, correction, interruption, and topic switch. The user describes it as a mind's eye and hive-mind-like collaboration rather than a new chatbot.

## Core model
- Use an existing duplex voice provider; DO NOT build or train a duplex model.
- A planner LLM maintains a rolling branching semantic horizon of available concepts and visual recipes.
- A cheap interchangeable fast decider (Jev-class, Holo-class, alternative, or first a deterministic stub) proposes scoped actions.
- One shared event space carries observations, predictions, plans, and commits asynchronously.
- Deterministic coordinator is the backplate for the canvas, NOT another model.
- tldraw/React draws persistent objects. Motion/SVG animations provide fluidity independent of token generation.
- Fast inference is helpful, but semantic novel-object generation has real latency; do not promise instant creativity.

## Prototype goals
G1: event-driven visual updates while planning proceeds concurrently.
G2: semantic authority and versioning prevent visual drift.
G3: unanticipated language/topic exit is visible and non-misleading, even when planner is late.
G4: swap voice providers and fast deciders without rewriting the canvas.
G5: performance trace distinguishes capture, transcription, model decision, validation, and paint.

## Explicit non-goals
Inventing a new multilingual speech model; autonomous browser clicking to draw; generating photorealistic images every frame; endless hypothetical lesson branching; a prewritten language course as the architecture; automatic production deployment; proving 200 ms end-to-end latency without live measurements.

## Verified vs proposed
Verified external building blocks: tldraw Agent Starter Kit, tldraw editor API, Motion SVG animation, LiveKit Agents framework (see SOURCES.md).
Proposed and NOT built: semantic state protocol, planner, decider adapter, coordinator, media adapter, end-to-end live UI.
Unknown: which provider emits suitably timed transcript/semantic events; which fast model is accurate enough across multiple languages; actual laptop performance; licensing for deployment.

## Constraints
Aim for no infrastructure spend during scripted/local stages. Keep models/provider keys configurable. Public Atlas notes must contain zero personal recordings, credentials or private information. Work on feature branches; review before merge. Keep implementation in repo only when compatible with existing Atlas architecture.

## Next smallest milestone
Complete T00 preflight, then replay a multilingual observation stream through the shared state and a deterministic canvas action without any LLM calls. This is infrastructure proof, not final product proof.

## Links
[[START_HERE]], [[ARCHITECTURE]], [[PROTOCOL]], [[VISUAL_RUNTIME]], [[GATES]], [[ATLAS_HANDOFF]], [[tickets/INDEX]]
