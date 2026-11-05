# Test report

How each milestone gate was verified, with commands and results.

## M0 — Bootstrap

- [x] `npm run typecheck` passes — `tsc --noEmit` clean (TS 5.9.3, strict)
- [x] `npm test` passes — Vitest: 2/2 (street scene builds; street bounds sane)
- [x] `npm run build` produces a production bundle — ok, `dist/` emitted (JS 525.91 kB / gzip 131.51 kB, CSS 3.84 kB)
- [x] Dev server serves the app — `GET /` 200 with `#app` + `/src/main.ts` entry; `GET /src/main.ts`, `/src/engine/Game.ts`, `/src/engine/SceneManager.ts`, `/src/world/ShoppingStreet.ts`, `/src/main.css` all 200 through the Vite transform pipeline; no errors in the server log.

> **Note (Windows only):** this machine's antivirus heuristic denies large random-named writes
> under `%TEMP%`, breaking esbuild's large-input temp-file path. Workaround for `build`/`dev`
> here: `set TMP=%CD%\.esbuild-tmp` (or any writable project-local dir) before the command.
> See README §Troubleshooting.

## M1 — First-person exploration

- [x] `npm run typecheck` passes — `tsc --noEmit` clean, strict
- [x] `npm test` passes — Vitest 19/19 over `tests/smoke.test.ts` + `tests/player.test.ts`:
  - street world: one collider per building footprint matching `BUILDING_BASES` geometry; bounds clamp to `STREET.bounds`; `pointInRect`/`distToRect` helpers on a unit rect
  - movement: forward ~1 s ≈ 3 m toward −Z while staying grounded at y=0; strafe runs perpendicular to the view; sprint covers >1.5 m more per second than walk; camera sits 1.7 above feet and copies pitch/yaw
  - mouse look: pitch clamps at ±(π/2−0.02) both directions; yaw wraps horizontally without affecting pitch
  - collision: stops at the building near-face (x ≥ 4−0.38, never ≥ 4); slides along the face on diagonal approach (z keeps decreasing while x is held); never enters any footprint during a 5 s push around a corner; clamps at the far street edge (z ≥ −46+0.38); no tunneling into a building at 100 ms frames at sprint speed
  - physics: jump leaves the ground (peak ≈ v²/2g ≈ 1.11), lands without sinking and zeroes velocity; grounded players neither sink nor accumulate `velocity.y`
  - reset: returns to spawn (0, 0, 8), yaw 0, pitch 0, zero velocity, grounded
- [x] `npm run build` produces a production bundle — `dist/` emitted (JS 534.36 kB / CSS 3.84 kB)
- [x] Dev server serves and compiles the app — `GET /` 200; `GET /src/main.ts` 200 through the Vite transform (imports `Game.ts` etc.); no Vite server errors in log
- [~] **Headless browser screenshot — NOT captured on this host (documented limitation):**
  `msedge --headless=new --virtual-time-budget` hangs on the continuously-animating
  `requestAnimationFrame` scene, and CDP remote debugging is refused by machine policy
  (`RemoteDebuggingAllowed=false` → port never binds), so no pixel/console capture could be
  produced. The dev server + module-serve probe confirms the app loads and compiles, and the
  simulation is covered by the 19 unit tests. A real-browser visual + console pass is queued
  for M8.
