# Japanese Splat City — 日本語スプラットシティ

An interactive 3D exploration demo for learning Japanese vocabulary while walking
through a *商店街* (shopping street). The scene combines conventional Three.js
geometry with real Gaussian splat content, and it teaches vocabulary through
in-world discovery instead of flashcards.

Built inside the EVEATLAS vault at `01-Projects/Japanese-Splat-City`.

## Quick start

Requires Node.js 20+ and npm.

```sh
cd 01-Projects/Japanese-Splat-City
npm install
npm run dev
```

Open the printed URL (default <http://localhost:5173>).

- **WASD** — walk · **Mouse** — look around (click to lock the pointer)
- **Shift** — sprint · **Space** — jump · **R** — reset position · **Esc** — pause menu
- Interactions (E), pointer-lock toggling and the notebook arrive with milestones M4/M5

## Commands

| Command            | Purpose                                  |
| ------------------ | ---------------------------------------- |
| `npm run dev`      | Development server with hot reload       |
| `npm run build`    | Type-check (`tsc --noEmit`) then bundle  |
| `npm run typecheck`| Type-check only                         |
| `npm run preview`  | Serve the production build locally       |
| `npm test`         | Run the automated test suite (Vitest)    |

## Milestones

| #  | Name                               | Status |
| -- | ---------------------------------- | ------ |
| M0 | Bootstrap Vite + TypeScript + Three.js | ✅ |
| M1 | First-person exploration           | ✅ |
| M2 | Real Gaussian splat rendering      | ⏳ |
| M3 | Japanese shopping street           | ⏳ |
| M4 | Interactable environment           | ⏳ |
| M5 | Vocabulary learning                | ⏳ |
| M6 | Missions                           | ⏳ |
| M7 | Persistence & quality of life      | ⏳ |
| M8 | Verification & polish              | ⏳ |

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Asset sources & licenses](docs/ASSETS.md)
- [Build log](docs/BUILD_LOG.md)
- [Test report](docs/TEST_REPORT.md)
- [Roadmap](docs/ROADMAP.md)

## Troubleshooting

**Windows: `npm run build` / `npm run dev` fail with `open ...\Temp\esbuild-<hash>: Access is denied.`**

An antivirus/security heuristic on some Windows machines blocks large random-named
writes under the system temp dir, which breaks esbuild's large-input file path.
Direct `npm test` / `npm run typecheck` are unaffected. Workaround — point the
temp dir at a writable project-local folder for the command:

```sh
# PowerShell
$env:TMP="$PWD\.esbuild-tmp"; $env:TEMP="$env:TMP"; npm run build

# CMD
set TMP=%CD%\.esbuild-tmp && set TEMP=%TMP% && npm run build
```

The output `dist/` or `.esbuild-tmp/` folders are gitignored.

## License & assets

Code is part of the public EVEATLAS vault. Every third-party asset used in this
project is listed with its license in [docs/ASSETS.md](docs/ASSETS.md); nothing
is included unless its license permits redistribution.
