# URP + WalkMain Scene Import — offline-capable vs. first-licensed-run split

Status: **authored, uncompiled, review-by-first-import** (round 7). Everything below is
implemented in code under `native/` but is compiled and executed for the first time by the
first licensed editor run.

## Why a "first import" step exists at all

A fresh clone of `feat/japanese-splat-city-native` deliberately contains **no** compiled
Unity artifacts: no `Library/`, no `Assets/Settings/`, no `.unity` scene file, and no
`GaussianSplatData` ScriptableObject. Those artifacts must be produced by the Unity editor
itself — and the editor will not run on this authoring host (no Unity entitlement, and
binary-identity confinement blocks the licensing client even with a valid `.ulf`). So every
scene/project artifact is instead **authored procedurally by an idempotent editor tool**
that runs on the very first successful import, from self-contained C# that needs no Unity
compile to review.

The flip side, stated plainly: none of this has been compiled, executed, or rendered.
The first licensed run is the compile gate **and** the acceptance test.

## What is committed (offline-capable, this branch)

- `native/Assets/Editor/ProjectAuthor.cs` — the whole authoring step, idempotent:
  1. URP pipeline assets under `Assets/Settings/`: `JSC-URP-Renderer.asset`
     (`UniversalRendererData`) + `JSC-URP.asset` (`UniversalRenderPipelineAsset`, default
     renderer wired, depth texture on).
  2. The vendored splat package's `GaussianSplatURPFeature` is `internal` — added to the
     renderer by reflection (type `GaussianSplatting.Runtime.GaussianSplatURPFeature,
     GaussianSplatting`). No manual `GS_ENABLE_URP` define: the package asmdef declares a
     versionDefine for URP, and URP 17.3.0 is pinned in `native/Packages/manifest.json`.
     The tool **fails loudly** if that type is missing — that means the package didn't
     compile with the define, i.e. a real import problem, not a silent skip.
  3. `GraphicsSettings.defaultRenderPipeline = JSC-URP.asset` + URP global-settings
     registration (reflection over internal `UniversalRenderPipelineGlobalSettings.Ensure()`
     + `GraphicsSettings.RegisterRenderPipelineSettings<T>`; best-effort with warning).
  4. `Assets/Scenes/WalkMain.unity` with exactly the minimal root set:
     - `BlockBuilder` (buildOnAwake, includeEvidenceGates, arcadeLength 72) — owns geometry
       **and** the player rig (BlockBuilder.BuildPlayer); the composer must not duplicate
       player objects.
     - `EvidenceDriver` — adds `Tooling.FpsAndCapture` to the rig at runtime.
     - `SplatAnchor` — top-level empty GO carrying `GaussianSplatRenderer` with
       `m_SourcePath = "M1Anchor_train.ply"`; `BlockBuilder.PlaceSplatAnchor` finds it by
       name and positions it at `(0, 1.1, 76)`.
     - `Global Volume (Fog)` — VolumeProfile with a Fog override (component and float param
       resolved by name; version-tolerant, non-fatal if absent).
  5. Registers `WalkMain.unity` in `EditorBuildSettings.scenes` — the gate
     `PlayerBuilder.Build` relies on.
- `native/Assets/Editor/PlayerBuilder.cs` — now calls `ProjectAuthor.Run()` at the head of
  `Build()`, then enforces the scene gate + IL2CPP backend + Win64 build.
- `native/Build.ps1` — four-step pipeline (see below), verified PowerShell-parse-clean on
  this host.
- `native/Assets/Scripts/{Block,Player,Tooling}/…` — runtime scene builder, FPS controller,
  gates, capture driver (drafted earlier rounds, same first-import review applies).

## The split: what runs offline vs. what requires the first licensed run

| Step | Offline (this host) | First licensed run |
| --- | --- | --- |
| Splat payload staged into `Assets/StreamingAssets/` | ✔ `Build.ps1 [1/4]` (SHA256-verified; `.ply` gitignored) | no-op (already staged) |
| URP pipeline assets + features | authored source only | created by `ProjectAuthor.Run()` (step 1) |
| WalkMain scene + build-settings entry | authored source only | created by `ProjectAuthor.Run()` (steps 4–5) |
| Package compile + shader compile | ✘ impossible (no editor) | `Build.ps1 [2/4]` headless import |
| Player build (IL2CPP Win64) | ✘ impossible | `Build.ps1 [3/4]` via `PlayerBuilder.Build` |
| Packaged run + evidence + URP acceptance | ✘ impossible | `Build.ps1 [4/4]` + frame capture |

Nothing on this branch claims URP runtime acceptance, a rendered frame, or a compiled
IL2CPP payload. Those markers are added to `docs/BUILD_LOG.md`/`docs/TEST_REPORT.md` only
from actual first-run evidence.

## Exact first-licensed-run procedure

1. Drop `Unity_v5.x.ulf` into `.tools\licensing\` (see `docs/ACTIVATION.md`), ensure the
   editor `6000.3.28f1` sits at `$EditorRoot`, and the SHA-verified payload at
   `$SplatSource` (defaults point at `.tools\splat-source\…train-iteration30000.ply`).
2. From `native/`: `.\Build.ps1 -ImportOnly` — stages the splat (SHA check), then headless
   import: ProjectAuthor creates URP + scene + build-settings entry; package shaders
   compile. Inspect `logs\import-*.log` for the `[ProjectAuthor]` lines and any errors
   (open questions below).
3. `.\Build.ps1` — build (IL2CPP enforced) + packaged offline run with `-force-d3d12` +
   `Player.log` archive; then capture the four evidence frames (spawn / junction /
   servicebend / rejoin) and record GPU, resolution, fps and frame times per
   `docs/TEST_REPORT.md`.

Expected-good `[ProjectAuthor]` log lines (from code): `URP global settings registered`,
`created + saved Assets/Scenes/WalkMain.unity…`, `EditorBuildSettings.scenes += …`.
Expected-good player line: `[BlockBuilder] …` build messages and zero splat-load errors.

## Open questions to confirm on first run

- URP 17.3.0 acceptance with `org.nesnausk.gaussian-splatting` v2.0.0 (packaged against
  URP 17.0): primarily the splat feature's `renderPassEvent` + URP 17.3 internal API drift;
  if the feature silently fails to inject, the renderer must fall back to the package's
  documented 17.0 compatibility path.
- `GraphicsSettings.defaultRenderPipeline` + global-settings map injection on a truly fresh
  project (the `Ensure()`/`Register` path) — if the map behaves differently, URP falls
  back to Built-in with an editor warning; the fallback is detectable in the import log.
- Fog component assembly location on 17.3 (`FindFogType` candidates) — non-fatal, logged.
- DX12 default vs. `-force-d3d12` at runtime on the RTX 2080 Ti host.
