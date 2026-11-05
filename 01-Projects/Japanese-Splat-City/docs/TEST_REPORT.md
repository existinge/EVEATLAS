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

## M2-fix — Monument transform correction + boot fix (supersedes the M2 transform claims)

The M2 row above documents the original integration; the placement it claimed was
wrong (bull floating at `y = 3.024`) and the multi-splat boot crashed. Both are fixed
here and re-verified end-to-end:

- [x] `npm run typecheck` passes — `tsc --noEmit` clean, strict
- [x] `npm test` passes — Vitest 28/28 (new `tests/street-props.test.ts` adds 7 prop/ground
  suites, incl. M2 grounding invariants re-asserted in unit form)
- [x] `npm run build` passes — `dist/` emitted (JS 791.82 kB / gzip 202.39 kB)
- [x] Ground truth transform — `rotation` on the splat scene is a **quaternion**: the
  Innerscene bake is Y-down, so the file's `maxY` end is the base slab; the bull is
  vertically flipped with the unit Z-flip `[0,0,1,0]` and grounded with
  `position.y = +boundsMax.y·scale` (`worldMinY` of every splat ≈ 0). No Euler
  `[0,0,Math.PI]` and no `−boundsMin.y·scale` anywhere.
- [x] Boot crash fixed — four synchronous `viewer.addSplatScene()` calls collided with the
  viewer's internal load/unload state (`Cannot add splat scene while another load or unload
  is already in progress`); all loads now go through a promise chain (`queueSplatScene`).
- [x] Headless-Chrome CDP verification (dev server, fresh page):
  - `window.__splatCityGame` exists; canvas 1264×705; WebGL 2.0 context live
  - `viewer.getSceneCount() === 4` (bull + 3 props), `isLoadingOrUnloading() === false`
  - every scene's `position`/`quaternion`/`scale`/`splatCount` matches the expectations
    below to ≤ 2e-3 (bull 200,000 splats)
  - zero uncaught exceptions, zero `console.error`, zero viewer log errors, zero failed
    splat requests; all 4 splat assets return HTTP 200
- [x] Pixel evidence (`docs/evidence/m3-bull.png` vs `m3-bull-nosplat.png`, splats hidden
  via `viewer.splatMesh.visible=false`): 5.26 % of frame changed, meanAbsDiff 4.495 in a
  601×379 bbox at (238, 180) — the bull renders dead-ahead of spawn, large and upright
  (horns-up), resting on the street ground line

## M3 — Japanese street props (apple, brass-diya-lantern, concrete-cat)

- [x] `npm run typecheck` passes — `tsc --noEmit` clean, strict
- [x] `npm test` passes — Vitest 28/28; `tests/street-props.test.ts` asserts: exactly the
  three milestone props are registered (a `wine-barrel` asset is **excluded** by name and
  the count check fails if added); each prop's computed worldMinY ≈ 0 (M2 ground line);
  both flip quaternions are unit length; the cat's X-flip `[1,0,0,0]` cancels its
  file-space −Z-facing head so it faces the street (+Z) like the Z-flipped apple/lantern;
  props sit on road strips, clearing the monument footprint and the ±1 m spawn corridor,
  pairwise non-overlapping
- [x] `npm run build` passes — same bundle as M2-fix row
- [x] Headless-Chrome CDP (same harness as M2-fix): 4 scenes loaded with exact expected
  transforms; no console errors on any pass; all three prop assets HTTP 200

  | scene | position | quaternion | scale | splatCount |
  |-------|----------|------------|-------|------------|
  | bull (M2) | `[-0.035, 0.0301, -0.2065]` | `[0,0,1,0]` | `[7,7,7]` | 200,000 |
  | apple | `[2.5, 0.15, 3.4994]` | `[0,0,1,0]` | `[0.6,0.6,0.6]` | 36,313 |
  | brass-diya-lantern | `[-2.506, 0.0048, 1.4928]` | `[0,0,1,0]` | `[1.2,1.2,1.2]` | 150,000 |
  | concrete-cat | `[2.603, 0.0015, -3.0375]` | `[1,0,0,0]` | `[1.5,1.5,1.5]` | 150,000 |
- [x] Pixel evidence (`docs/evidence/m3-*.png`, splats-hidden baselines via
  `splatMesh.visible=false`):
  - **stability**: same view 1 s apart → meanAbsDiff 0, 0.00 % changed (diff noise floor)
  - **default view coverage** vs. nosplat: meanAbsDiff 2.824, 4.96 % changed, full-frame
    bbox — the whole street scene differs as expected
  - **cat wide** (from spawn): 0.22 % changed in a 39×79 bbox — the cat is small at 2.5 m
  - **cat close-up** (camera 1.7 m away): 0.59 % changed (5,260 px) in a **centered 61×126
    bbox** (18 % of frame height — the statue's true proportions), 6,048 unique colors vs
    777 with splats hidden; ≥ 0.00 % noise floor ⇒ rendered at the expected screen
    position and size, facing the camera (street-facing +Z)
- [x] Playability — player spawn `(0, 0, 8)` field of view contains bull + apple + lantern;
  cat requires a short walk south; all props are visual-only (no collision changes), so
  the player can walk past them; no path is blocked

> **Tooling note (extends the M2 note):** headless Chrome CDP (system Chrome, Edge blocked)
> is the visual-verification harness for M2-fix and M3; the M1 render-visual sweep remains
> queued for M8 but the tooling it will use is proven here.

## M3.1 — Street lighting / colorization

- [x] `npm run typecheck` passes — `tsc --noEmit` clean, strict
- [x] `npm test` passes — Vitest **37/37** (4 files); new `tests/lamp-colorization.test.ts` asserts:
  - bulb colorization: `bulbColor()` returns `setHSL` hue ∈ [209, 211], saturation > 0.8,
    lightness > 0.6 (azure/cyan "warm white" in the requested 200–220 band)
  - placement: all 6 `STREET_LAMPS` sit on the sidewalk strip (x = ±4.3, between
    `sidewalkInner`/`sidewalkOuter`) and inside `STREET.bounds`
  - clearance: lamp poles clear every building base, the monument footprint and every
    `STREET_PROPS` footprint; the spawn corridor `(0, 8)` is pole-free
  - colliders: `Colliders.poles` has 6 entries matching each lamp's x/z within ±
    `LAMP_POLE_HALF`, and the poles are mutually disjoint
  - collision: walking from `(5.8, 0, 11)` toward lamp `west-mid` (4.3, 11) is stopped
    flush at x ∈ [4.75, 4.85] (`4.3 + LAMP_POLE_HALF.x + 0.38`), so the player cannot walk
    through a pole; with the pole removed from the world the player reaches x < 4.3
  - scene wiring: the `ShoppingStreet` group contains exactly 6 `PointLight`s and ≥ 6
    emissive (`emissiveIntensity > 1`) materials whose hue ≈ `BULB_HUE` (210)
- [x] `npm run build` passes — `dist/` emitted (JS ~793.61 kB / CSS 4.91 kB /
  `index.html` 0.83 kB), built with the workspace-local `.tmp-esbuild` TMP override
- [x] Headless-Chrome CDP (dev server `http://127.0.0.1:5173/`, same harness as M2-fix):
  - app boots, `window.__splatCityGame` present, canvas 1264×705
  - live scene traversal: **6 `PointLight`s** and **6 emissive bulbs**, every bulb at
    **hue 210 / s 0.9 / l 0.72 / intensity 2.4** — the exact `bulbColor()` spec
  - zero uncaught exceptions, zero `console.error`, zero log-level errors
- [x] Pixel evidence (`docs/evidence/m31-*.png`): `street-corridor`, `lamp-closeup` and
  `spawn-view` screenshots decode as non-blank, well-exposed frames (average 88–110,
  10–22 % bright pixels, 27–36 % colored pixels); the close-up is cool/azure-dominant
  (blue 108 > red 94), consistent with the azure bulbs against the `0x9ec8e8` sky
- [x] No splat provenance change — lighting is procedural Three.js geometry; every
  splat asset still carries CC0 attribution per `public/assets/licenses/README.md`
- [~] Apples/props are unlit by the lamps from range (`PointLight.distance = 10` is a
  deliberate, documented scope limit); the glow is on the lamp bulbs and shades
  themselves rather than a full scene relight
