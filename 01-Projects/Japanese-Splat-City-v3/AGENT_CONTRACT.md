# DeepSeek Flash — JPSv3 Builder Contract
Read root `AGENTS.md` plus JPSv3 `README.md`, `PRODUCT_CHARTER.md`, `SUPERVISOR.md`, `RESOURCES.md`. Product charter supersedes the previous personal N4–N3 learner assumption and overrides fixed tea/onigiri shopping as the sole definition of the game.

## Primary role
Implement a game. Never use the time budget on architecture documents while the playable build is absent. Build M0 first, then M1. Verify existing Unity workspace before migration, but do not delay a working browser prototype indefinitely.

## Nonnegotiable engineering
- Strict TS + Vite + Three.js + Rapier. Spark only after core controls/gameplay work. React for HUD only; game loop outside React.
- Clean scripts: dev, typecheck, lint, test, build, e2e. Lockfile committed; documented version and license for assets.
- Play mode: user-gesture activation, focus, pointer lock when supported, fallback when not, keyboard maps by code, release on blur/visibility change, prevent page scrolling only while game active. Escape exits without trapping user; no OS shortcut hijacking.
- Scene: physics/colliders separate from splats; accessible interactions and inspectability; authored deterministic quest data; versioned persistent save.
- Language: no founder-level assumption; a configurable support system with selectable display/audio options; contextual comprehensible Japanese; opt-in translations; distinguish exposure from evidence of mastery; no arbitrary JLPT gating.
- Gameplay: free exploration and purposeful interactions; a journal/photo mechanism is optional inspiration from Shashingo, but the unique value is consequences and deeper language use. Do not clone copyrighted elements.
- Work on own branch/worktree. Commit small runnable slices. Antigravity is read-only supervisor and cannot self-approve builder output.
- No secret commits or arbitrary execution of skill packs. Check all dependency API compatibility and licenses.

## M0 gate
Can enter a scene, walk and look, collide with obstacles, exit/re-enter play mode, and survive blur/reload without stuck movement. Run all scripts and Playwright with real keyboard/mouse. Record evidence.
## M1 gate
Can wander to shop, inspect/observe several objects, see authentic Japanese labels with configurable aid, perform a context-dependent interaction with an NPC or object, complete/recover from a misunderstanding, and reload into consistent state. Test novice and proficient configuration paths; no hardcoded founder level or arbitrary forced quiz.
## Review/handoff
Provide SHA, runnable commands/URL, true test status, screenshot/trace, changed files, known defects and next smallest action. Mark NOT RUN instead of fake success. Do not advance past red failures. Two failed repairs -> reproducible blocker report. Supervisor evidence is independent, not permission for uncontrolled rewrites.
