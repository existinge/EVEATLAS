# Roadmap

Milestone-by-milestone plan (gates must pass in order; each milestone ends with
a commit and a build-log entry).

- [x] **M0 — Bootstrap**: Vite + TypeScript + Three.js, engine core, placeholder
      street, README/AGENTS, dev server + production build verified.
- [x] **M1 — First-person exploration**: player controller (WASD, mouse look +
      pointer lock, sprint, jump), gravity/grounding, AABB collision, basic
      street, reset-player, graphics settings.
- [ ] **M2 — Real Gaussian splatting**: integrate a splat renderer, load a
      genuinely-licensed splat, verify it coexists with conventional geometry;
      splat stays visual-only (collision stays geometric).
- [ ] **M3 — Japanese shopping street**: storefronts, sidewalks, signage,
      convenience store area, café area, vending machines, lighting, collision;
      all destinations reachable.
- [ ] **M4 — Interactable environment**: targeting, E interactions, contextual
      UI, registration system, ≥12 interactive objects with Japanese labels.
- [ ] **M5 — Vocabulary learning**: typed schema, N4–N3 content, discovery
      events, notebook, encountered-words tracking; no English→Japanese
      translation quizzes.
- [ ] **M6 — Missions**: three playable missions with state machines and
      automated tests.
- [ ] **M7 — Persistence & QoL**: localStorage progress, reset option,
      pause/settings, controls help, speech synthesis (optional).
- [ ] **M8 — Verification & polish**: full test pass, browser verification,
      docs, commit, handoff.
