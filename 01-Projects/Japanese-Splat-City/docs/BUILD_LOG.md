# Build log

Chronological record of milestone work, evidence, and fixes.

| Date | Milestone | Change | Evidence |
| ---- | --------- | ------ | -------- |
| 2026-11-05 | M0 | Scaffolded Vite + TypeScript + Three.js project; engine core (`Game`, `SceneManager`), initial street placeholder, README/AGENTS/docs, Vitest smoke test | `npm install` (three 0.187.0, vite 7.3.7, vitest 5.1.0, typescript 5.9.3); `npm run typecheck` OK; `npm test` 2/2 passed; `npm run build` OK (525.91 kB js bundle); `npm run dev` served and transformed all entry modules without errors |
| 2026-11-05 | M1 | First-person exploration: pure-simulation `PlayerController` (physics, input-free, node-testable), WASD + pointer-lock mouse look, sprint/jump, axis-separated AABB collision with no-tunnel guarantees, gravity/grounding, `buildStreetWorld()` colliders + 8-building street, R reset-player, Esc pause + quality settings overlay | `npm run typecheck` OK; `npm test` 19/19 passed (smoke + player suites: movement, mouse look, collision stop/slide/no-tunnel, bounds clamp, gravity/jump, reset); `npm run build` OK (534.36 kB js bundle); dev server served `/` + compiled `/src/main.ts` module graph (HTTP 200) |

> **M1 browser note:** headless Edge could not produce a screenshot on this host —
> `--virtual-time-budget` hangs on a continuously-animating `requestAnimationFrame`
> scene and CDP remote debugging is refused by the machine policy (`RemoteDebuggingAllowed=false`),
> so render-evidence for M1 relies on the unit tests + production build + module-serving
> check; a visual pass is revisited at M8.
