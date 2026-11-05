# Roadmap

Milestone-by-milestone plan (gates must pass in order; each milestone ends with
a commit and a build-log entry).

- [x] **M0 — Bootstrap**: Vite + TypeScript + Three.js, engine core, placeholder
      street, README/AGENTS, dev server + production build verified.
- [x] **M1 — First-person exploration**: player controller (WASD, mouse look +
      pointer lock, sprint, jump), gravity/grounding, AABB collision, basic
      street, reset-player, graphics settings.
- [x] **M2 — Real Gaussian splatting**: integrate a splat renderer, load a
      genuinely-licensed splat, verify it coexists with conventional geometry;
      splat stays visual-only (collision stays geometric).
- [x] **M3 — Japanese street props**: three real gaussian-splat props (apple,
      brass-diya-lantern, concrete-cat) on the walking strips of the shopping
      street — grounded to the M2 ground line and street-facing; splat stays
      visual-only; verified in unit tests, headless-Chrome CDP and pixel diffs.
      *(Remaining M3 decor from the original bullet — signage, convenience-store /
      café zones, vending machines — is future work; lighting became M3.1.)*
- [x] **M3.1 — Street lighting / colorization**: six street lamps flanking the road
      with azure/warm-white bulbs — `bulbColor()` = `setHSL(210, 0.9, 0.72)` within the
      requested 200–220 hue band — shared as an emissive bulb + translucent glass shade
      per lamp, lit by a per-lamp `PointLight`; lamp poles are **real AABB colliders**
      (`Colliders.poles`), so the player collides with them; verified in unit tests and
      headless-Chrome CDP (6 lamps + 6 PointLights live in the scene, zero console errors).
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
