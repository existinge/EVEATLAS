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
