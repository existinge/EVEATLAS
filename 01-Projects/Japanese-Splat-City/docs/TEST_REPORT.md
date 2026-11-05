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

## M2 — Gaussian-splat street monument

- [x] `npm run typecheck` passes — `tsc --noEmit` clean, strict
- [x] `npm test` passes — Vitest 21/21 over `tests/smoke.test.ts` + `tests/player.test.ts`
  (new: monument footprint present in `buildStreetWorld()` as collider index 8; monument near-
  face stops forward travel at the street; sideways slide past the monument is fixed — the
  pre-move adjacent axis is used for snap, and a box whose band is entered only by the current
  frame's move is skipped; far-edge clamp at `bounds.minZ + 0.38`)
- [x] `npm run build` produces a production bundle — `dist/` emitted (JS 790.50 kB / gzip 201.91 kB)
- [x] Playable game unaffected by splat load — `addSplatScene()` is fire-and-forget; the game
  loop starts immediately; the viewer composites after the street pass each frame
- [x] Splat genuinely loads and renders (headless Chrome CDP, dev server + prod preview):
  - `window.__splatCityGame.viewer.getSceneCount() === 1`, `isLoadingOrUnloading() === false`,
    WebGL 2.0 context live — no page errors; console shows **zero** errors/warnings on the
    prod pass (favicon 404 removed via inline SVG data URI)
  - Baseline pass with the `.ksplat` request aborted: `getSceneCount() === 0`, only the
    expected `Failed to fetch` / `ERR_FAILED` noise → the captured delta is the splat, not
    street variance (same deterministic street renders in both passes)
  - `pngjs` pixel diff (1280×720): 9,753 px differ (1.06 % of frame) in a connected 128×186
    bbox, centroid (637.8, 351.4) vs. screen center (640, 360) — the monument renders dead-ahead
    of the spawn camera (yaw 0 → −Z) with its bottom edge at the street ground line;
    **identical numbers in dev and prod runs** (`docs/evidence/m2-splat.png` vs
    `docs/evidence/m2-baseline.png`, local only)
- [x] Collision stays AABB — splat is visual-only; `monumentFootprint()` pushes raw
  `(bounds − center) · scale` bounds into `buildStreetWorld()` (no double radius padding);
  controller pads at query time
- [x] Attribution committed — `public/assets/licenses/README.md` documents CC0 license +
  Poly Haven "Bull Head" by Tina + Innerscene baking provenance

> **Tooling note:** this pass was produced with system **Chrome** (`--headless=new`,
> CDP honored on this host); Edge remains blocked by machine policy.
