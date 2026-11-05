# Build log

Chronological record of milestone work, evidence, and fixes.

| Date | Milestone | Change | Evidence |
| ---- | --------- | ------ | -------- |
| 2026-11-05 | M0 | Scaffolded Vite + TypeScript + Three.js project; engine core (`Game`, `SceneManager`), initial street placeholder, README/AGENTS/docs, Vitest smoke test | `npm install` (three 0.187.0, vite 7.3.7, vitest 5.1.0, typescript 5.9.3); `npm run typecheck` OK; `npm test` 2/2 passed; `npm run build` OK (525.91 kB js bundle); `npm run dev` served and transformed all entry modules without errors |
| 2026-11-05 | M1 | First-person exploration: pure-simulation `PlayerController` (physics, input-free, node-testable), WASD + pointer-lock mouse look, sprint/jump, axis-separated AABB collision with no-tunnel guarantees, gravity/grounding, `buildStreetWorld()` colliders + 8-building street, R reset-player, Esc pause + quality settings overlay | `npm run typecheck` OK; `npm test` 19/19 passed (smoke + player suites: movement, mouse look, collision stop/slide/no-tunnel, bounds clamp, gravity/jump, reset); `npm run build` OK (534.36 kB js bundle); dev server served `/` + compiled `/src/main.ts` module graph (HTTP 200) |
| 2026-11-05 | M2 | Integrated `@mkkellogg/gaussian-splats-3d@0.4.7` class-based Viewer into `Game.ts`: non-blocking `addSplatScene()` of a genuinely-licensed monument splat (`carved-bull-head.ksplat` — CC0 Poly Haven "Bull Head" by Tina, splat baked by Innerscene, attribution in `public/assets/licenses/README.md`) at `monumentPosition()` (`[-0.035, 3.024, -0.2065]`, scale 7, rests on ground), `RenderMode.Always`, `sharedMemoryForWorkers:false`, external renderer/camera/controls, depth-composited street→splat each frame and disposed in order; splat stays **visual-only** — collision uses matching AABB pushed through `monumentFootprint()` into `buildStreetWorld` (raw bounds, no double padding); PlayerController axis-resolver fix (snap against pre-move adjacent axis; boxes entered only by this frame's move are skipped — fixes sideways slide past the monument); inline SVG favicon (removes 404 console noise) | `npm run typecheck` OK; `npm test` 21/21 passed; `npm run build` OK (790.50 kB js bundle, gzip 201.91 kB); headless-Chrome CDP proof on dev **and** prod servers: `viewer.getSceneCount()==1`, `isLoadingOrUnloading()==false`, zero console/page errors; two-pass pixel diff vs. ksplat-aborted baseline = 9,753 px difference in a 128×186 bbox, centroid (637.8, 351.4) vs. screen center (640, 360) — the monument renders dead-ahead of spawn, resting on the street, identically in dev and prod |
| 2026-11-05 | M2-fix | Removed stray `bull-curl.bin` duplicate (SHA-256 identical to the ksplat); gitignored harness scratch `.firecrawl/` and local evidence `docs/evidence/` | `git status` clean of both; duplicate confirmed via `Get-FileHash` match before deletion |

> **M2 browser note (supersedes the M1 note's tools):** system Chrome at
> `C:\Program Files\Google\Chrome\Application\chrome.exe` **does** honor CDP on this
> host (`--headless=new --remote-debugging-port`), so visual browser evidence is
> produced with headless Chrome (Edge is the one blocked by machine policy). M2
> evidence includes screenshots and the pixel-diff described above; the M1
> render-visual pass is revisited at M8 with the same tooling.
