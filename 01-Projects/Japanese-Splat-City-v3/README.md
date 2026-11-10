# Japanese Splat City v3 (JPSv3)
Status: reboot specification, NOT a playable build.
Mission: browser-first immersive Japanese learning through realistic interactions in a walkable Japanese street and konbini. Learner: high N4 toward N3; Japanese-first, optional English rescue rail and optional furigana; learning via context, not endless quizzes.

## Core decision
TypeScript strict + Vite + Three.js + Spark Gaussian splats + Rapier physics + optional React HUD. First playable must work with simple mesh placeholders if no splat is ready. Meshes/colliders handle interaction and physics; splats mainly provide scenery. Never put per-frame simulation in React. No live LLM requirement for basic gameplay.

First vertical slice: enter play mode, WASD/mouse-look movement, street, store, 3 interactable product objects, Japanese request for tea and onigiri, cashier interaction, mission completion, progress saved after reload.

## Governance
Read [AGENT_CONTRACT.md](./AGENT_CONTRACT.md), [SUPERVISOR.md](./SUPERVISOR.md), [RESOURCES.md](./RESOURCES.md). Also obey repository root AGENTS.md. Builder: DeepSeek Flash. Independent review: Antigravity monitoring agent. Work in separate branches/worktrees; avoid shared dirty working tree. Changes land only with passing build, tests and browser verification. Artifact/screenshots and actual commits are evidence; agent self-reports are not.

## Atlas integration
Atlas holds decisions and governance; put implementation in a dedicated game workspace or repo with a backlink here. Before migration, inventory any prior Unity files/workspace elsewhere; this Atlas main branch had no JPSv3 source in 01-Projects at audit time.

## Milestones and acceptance
M0: reproducible starter, lockfile, npm scripts, test runner, one browser page, movement and pointer-lock fallback.
M1: simple street/convenience store, collision, a mission, Japanese interaction, keyboard and mouse playability, save reload.
M2: integrate one licensed splat in place of environment mesh; maintain collision and interaction; fallback remains functional.
M3: polish, vocabulary/mastery, performance instrumentation and accessibility.
Milestone blocked unless tested with automated browser input (not only compile) and screenshot/trace evidence. Aim 60 FPS on target desktop, but measure and report rather than claim.
