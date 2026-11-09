# BUILD_LOG — Japanese Splat City (Native Windows walk)

Milestone 1 focus: **prove the walk** in a packaged standalone Win64 player.
Splat rendering is the local proof-of-renderer; the walk is the acceptance gate.

## Environment (pinned)

| Item | Value | Proven |
|---|---|---|
| Unity editor | **6000.3.28f1**, shortRevision `8f082d2fe476` | installed + verified (`FileVersion 6000.3.28.9373741`, `ProductVersion 6000.3.28f1_8f082d2fe476`) |
| Editor path | `.tools/unity-editor/6000.3.28f1/Editor/Unity.exe` | exists |
| Installer | `UnitySetup64-6000.3.28f1.exe` (4 208 792 576 B, SHA256 `8197A37D...`) | silently installed, exit 0 |
| Windows Build Support (Mono) | bundled with Win64 editor (`PlaybackEngines/WindowsStandaloneSupport`) | present |
| Render pipeline | **URP 17.3.0** (universal / core / shadergraph), `universal-config 17.0.3` | read from editor BuiltInPackages `package.json` (below) |
| Graphics API (splat paths) | Direct3D 12 (required by GaussianSplatting; DX11 unsupported) | to confirm on first open/build |
| Splat renderer | Aras `UnityGaussianSplatting` **v2.0.0**, MIT, `org.nesnausk.gaussian-splatting` | vendored into `native/Packages/` |
| GaussianSplatURPFeature URPRenderer | on active URP renderer | to confirm |
| URP Render Graph "Compatibility Mode" | **OFF** (required) | to confirm |

### Render-pipeline version evidence (from installed editor, authoritative)

Read from
`.tools/unity-editor/6000.3.28f1/Editor/Data/Resources/PackageManager/BuiltInPackages/*/package.json`:

- `com.unity.render-pipelines.universal` = **17.3.0** — deps: `render-pipelines.core 17.3.0`, `shadergraph 17.3.0`, `render-pipelines.universal-config 17.0.3`
- `com.unity.render-pipelines.core` = **17.3.0** — deps: `burst 1.8.14`, `mathematics 1.3.2`, `ugui 2.0.0`, `collections 2.4.3`
- `com.unity.shadergraph` = **17.3.0**; `com.unity.render-pipelines.universal-config` = **17.0.3** (deps core 17.0.3)
- `com.unity.ugui` = **2.0.0**

> Correction: an earlier note pinned URP at 17.0.3 based on a stale sample `packages-lock` and the
> CHANGELOG's oldest bundled entry. The editor's own `package.json` `version` field is **17.3.0**,
> which supersedes that. We pin the exact bundled versions so an offline editor can resolve them from
> `BuiltInPackages` without the (incomplete) registry mirror. Registry indexes observed from this host
> are partial/stale (`packages.unity.com` returned only pre-17.x versions and 404s for versioned URLs),
> so built-in bundling is our reproducibility source of truth.

### Package pins (in `native/Packages/manifest.json`)

- `com.unity.render-pipelines.universal` = **17.3.0** (transitively pulls core/shadergraph/universal-config)
- `com.unity.burst` = **1.8.14**, `com.unity.collections` = **2.4.3**, `com.unity.mathematics` = **1.3.2** (matched to URP core's deps)
- `org.nesnausk.gaussian-splatting` = **file:Packages/org.nesnausk.gaussian-splatting** (vendored 0.3 MB, MIT, provenance in `LICENSE.md`)

## Milestone status

- [x] Editor installed and verified (won't reinstall).
- [x] Windows Mono standalone support verified (bundled).
- [x] `native/` Unity project scaffolded with pinned editor (`ProjectVersion.txt` 6000.3.28f1; Assets empty).
- [x] URP 17.3.0 family pinned in manifest (evidence above).
- [x] Gaussian Splatting package vendored into `native/Packages/`.
- [ ] First headless/open compile passes (impossible in this environment — see blocker).
- [ ] Block scene: first-person controller, enclosed walking loop, occluder/opaque storefront geometry, collision verified.
- [ ] Packaged Windows Mono player builds from CLI.
- [ ] Packaged player launches offline with editor closed; GPU/resolution/fps/player-log recorded.
- [ ] Four evidence frames from packaged player.

## Environment blocker (decisive — blocks Milestone 1)

The Unity toolchain **cannot run on this host**, for two independent reasons:

1. **No Unity license material anywhere.** No `Unity` folder under `%LOCALAPPDATA%`, no `.ulf`, no
   `Unity_v5.x.alf`, no Unity account/Hub on the machine. The editor is unlicensed and cannot start.

2. **Binary-identity confinement blocks third-party executables at the OS level.** Every Unity
   tool component that actually transitions state is a third-party native binary and is denied
   access to the user profile, regardless of the DSH file policy (which is `danger-full-access`
   globally). System binaries (`powershell`, `cmd`) prove they *can* write the same paths.

Decisive probe (evidence in `.tools/lic-ctx-out/err.txt`, `lic-remote-out/err.txt`): running
`Unity.Licensing.Client.exe --showRemoteEntitlements --debug` dies **at logging bootstrap**, before any
licensing logic:

```
System.UnauthorizedAccessException: Access to the path 'C:\Users\exist\AppData\Local\Unity' is denied.
   at Unity.Licensing.Logging.MinimalLockFileSink..ctor(...)
   ...
   at Unity.Licensing.Client.MainProgram.<Main>d__0.MoveNext()
```

and the FileSystemWatcher on `AppData\Local` fails with `FileNotFoundException: Error reading the
C:\Users\exist\AppData\Local\ directory.` The client never reaches entitlement/network code, so
remote-activation reachability is moot. Same class of failure explains earlier `EPERM mkdir
...\AppData\Local\Temp` from the UPM node child and the editor's fatal `'com.unity.editor.headless'
was not found` (licensing-led abort).

Consequence: **no escalation path exists** in this session (approval prompts are disabled), and the
license-free machine means even an unconfined run has nothing to activate. Milestone 1 cannot be
built here without (a) an actual Unity Personal entitlement and (b) a host/process identity that
third-party binaries may write to the profile. We will not fabricate or bypass licensing.

## Current status

- Editor installed and verified; project scaffolded; URP 17.3.0 family pinned; splat renderer vendored.
- Ready-to-build state is committed so the moment a capable host exists, the walk milestone can start:
  1. `cd native && "<Unity.exe>" -projectPath . -batchmode -quit ...` (headless import/compile)
  2. build the Windows Mono player, run packaged with editor closed, capture the four evidence frames.
- **One-command pipeline drafted and committed** (`native/Build.ps1`): headless import → CLI Win64
  build via `Assets/Editor/PlayerBuilder.cs` (`-executeMethod`) → launch packaged player offline with
  `-force-d3d12` and locate `%LOCALAPPDATA%\LocalLow\EVEATLAS\JapaneseSplatCity\Player.log`.
  Build.ps1 verified: PowerShell parse OK on this host, fail-fast path proven (exit 1 + clear
  message when the editor is missing). PlayerBuilder.cs is a **DRAFT — not yet compiled**, it
  requires first editor import; it fails loudly if `Assets/Scenes/WalkMain.unity` is absent.
- Project identity fixed: `companyName` `DefaultCompany`→`EVEATLAS`, `productName` `native`→
  `JapaneseSplatCity` in `ProjectSettings.asset` (player-log path + exe naming follow).
- All remaining checklist items are gated by the blocker above (implemented/shipped = false, none fabricated).
- Splat procurement research COMPLETE (`docs/SPLAT-SOURCE-REPORT.md`, primary-source license quotes):
  no redistributable Japanese-street capture exists; M1 anchor adopted = HF `Voxel51/gaussian_splatting`
  **`train` scene @ iteration 30000** (Apache-2.0). **Payload DOWNLOADED + SHA256-verified** against the HF
  LFS oid (`a4c1906c…47a7a1`, 266,542,260 B) into `.tools/splat-source/`; license record, dataset-card
  front-matter, HF API metadata, and notices committed under `LICENSE/Voxel51-gaussian_splatting/`
  (incl. the verified caveat: no in-repo LICENSE file — tag rests on uploader's card declaration).
  Japanese shotengai deferred to Mapillary CC-BY-SA self-reconstruction.
- Drafted `native/Assets/Scripts/Tooling/FpsAndCapture.cs` (fps.csv + Screenshots/ capture, NOT compiled)
  and `docs/WALK_DESIGN.md` (block layout, two-connection service lane, four evidence frames).
- **Round 5 (offline pre-stage):** Japanese signage font procured and recorded.
  - `NotoSansCJKjp-Regular.otf` + `OFL-1.1.txt` DOWNLOADED to `.tools/font-source/` (workspace root)
    and SHA256-verified (OTF `68A3FC98…75B5`, OFL `6A73F954…E2BF2`); OFL + NOTICE committed under
    `LICENSE/NotoSansJP/`; status row added to `docs/ASSET_PROVENANCE.md`. SIL OFL 1.1 permits
    bundling in the offline game; the packaged player must ship the OTF + OFL + NOTICE and name the
    Noto CJK project in credits.
  - Block-building scripts drafted (NOT compiled, self-contained, ready for first import):
    - `native/Assets/Scripts/Player/FpsController.cs` — WASD + mouse-look + gravity, CharacterController,
      Esc-lock cursor, `cam` wiring; spawn faces the first lit storefront with the splat anchor ahead.
    - `native/Assets/Scripts/Block/BlockBuilder.cs` — runtime-constructs the whole enclosed block from
      primitives: 4.0 m arcade (length 68 m walkable, room to land in the 60–90 m window), storefront
      bay alternation (lit window / shutter + sign rail + sign panel), far-end glazed street viewport
      for the Gaussian-splat anchor, 2.2 m service lane ring with exactly two connections
      (CONNECTION 1 near start, CONNECTION 2 = rejoin with striped awning + vending nook + café
      windows), canopy + lighting poles, collisions + trigger gates.
    - `native/Assets/Scripts/Block/WaypointGate.cs` / `EvidenceDriver.cs` — trigger frames feed
      FpsAndCapture tags junction / servicebend / rejoin + startup spawn frame.
  - Scene `WalkMain.unity` still requires the first editor import (BlockBuilder + EvidenceDriver +
    SplatAnchor one-off composition); `PlayerBuilder.cs` stays gated on it.
- Awaiting the human-supplied `Unity_v5.x.ulf` (drop path `.tools/licensing/`, walkthrough in `docs/ACTIVATION.md`).
- **Round 6 (offline pre-stage) — Japanese signage pipeline COMPLETE and VERIFIED (no-tofu proof).**
  - `native/Tools/rasterize-jp-text.ps1`: renders 21 UTF-8 sign texts from `sign-texts.tsv` with the
    licensed Noto Sans CJK JP OTF → `native/Assets/Resources/Textures/Signs/` (`sign-*.png`, 32bpp ARGB,
    AA grid-fit, width rounded to a multiple of 4) + `signs-manifest.json` (generator, generatedAtUtc,
    OTF SHA256 `68A3FC98…75B5`, per-entry text) + proof sheet.
  - `native/Tools/verify-font-glyphs.ps1` (**ran to VERDICT: True**): recomputes the OTF SHA256, checks
    `GlyphTypeface` family identity ("Noto Sans CJK JP"), asserts cmap glyph id > 0 for every character
    in the manifest (48 unique glyphs across all 21 signs — no tofu; `HashSet[int]` snapshot avoids the
    PS 5.1 `IDictionary.Contains` overload bind trap), and measures per-PNG ink fill (7.3–18.4%,
    ≥5% threshold). Writes `font-glyph-report.json` next to the textures (committed as evidence).
  - `native/Assets/Scripts/Block/BlockBuilder.cs` now wires sign textures at runtime:
    `ApplySignTexture` loads `Resources` texture `Textures/Signs/sign-{tag}` and applies it with an
    aspect-preserving crop (flat `_matSign` fallback when assets are missing); 20 storefront
    `SignSlates` cycle across bays, the 商店街 arcade-title banner hangs over the far-end viewport,
    and 入口/出口 door flaps mark both connections. Entire block self-dresses on first import —
    zero editor work, keyed to the exact texture names the offline rasterizer emits.
  - **IL2CPP hardening:** `PlayerBuilder.cs` pins `SetScriptingBackend(Standalone, IL2CPP)` with a
    fail-fast guard (splat package refuses Mono). Host prerequisite confirmed via `vswhere`: VS Build
    Tools 2022 ver `17.14.37411.7` (VC x64 14.44.35207) + 2019 ver `16.11.37301.9` (VC x64 14.29.30133)
    at `C:\Program Files (x86)\Microsoft Visual Studio\…` — an IL2CPP Windows build is feasible here
    the moment an entitlement exists. T16 in `docs/TEST_REPORT.md`.
- **Round 7 (offline pre-stage) — first-import authoring is now fully code-driven.**
  - `native/Assets/Editor/ProjectAuthor.cs` **added** (~340 lines, self-contained, uncompiled-on-commit):
    idempotently authors the URP pipeline (`UniversalRendererData` + `UniversalRenderPipelineAsset`
    with depth texture on), injects the vendored splat package's `internal` `GaussianSplatURPFeature`
    into the renderer via reflection (fails loudly if absent), sets
    `GraphicsSettings.defaultRenderPipeline` + URP global-settings registration (reflection,
    best-effort, logged), creates the Fog global volume (version-tolerant), composes
    `Assets/Scenes/WalkMain.unity` (BlockBuilder + EvidenceDriver + SplatAnchor carrying
    `GaussianSplatRenderer` with `m_SourcePath="M1Anchor_train.ply"` + Fog Volume) and registers
    the scene in `EditorBuildSettings.scenes`. See `docs/URP_SCENE_IMPORT.md`.
  - `native/Assets/Editor/PlayerBuilder.cs` now calls `ProjectAuthor.Run()` before its scene gate
    (self-healing on fresh imports); IL2CPP enforcement and fail-fast behavior unchanged.
  - `native/Build.ps1` upgraded to **4 steps**: [1/4] stage the SHA256-verified splat into
    `Assets/StreamingAssets/M1Anchor_train.ply` (266,542,260 B; `*.ply` gitignored, never committed),
    [2/4] headless import (ProjectAuthor runs here), [3/4] IL2CPP Win64 build, [4/4] packaged offline
    run with `-force-d3d12` + Player.log archived to `logs\player-*.log`. Re-parse-checked OK on this
    host (PS 5.1 parser).
  - Splat payload re-verified on disk: SHA256 `A4C1906C…47A7A1` (266,542,260 B) at
    `.tools/splat-source/Voxel51-gaussian_splatting-train-iteration30000.ply` — the file the
    runtime path loads from `StreamingAssets` on a licensed machine.
  - No URP acceptance, rendered frame, or compiled IL2CPP payload is claimed before first-run
    evidence lands in this log. First-import compile risks (URP 17.3 API drift, renderer-feature
    reflection, global-settings injection, fog component assembly) are tracked in
    `docs/URP_SCENE_IMPORT.md`.

## Open questions

- Exact URP 17.3.0 acceptance with `org.nesnausk.gaussian-splatting` v2.0.0 (targets 2022.3/URP 17.0; may need feature `renderPassEvent` compatibility path on 17.3) — to confirm on first editor open.
- Direct3D 12 default in ProjectSettings + standalone `-force-d3d12` fallback.
- Licensed street-correct PLY source — RESOLVED for M1: Voxel51 HF `gaussian_splatting` `truck`/`train`
  (Apache-2.0, already-trained PLY; self-declared tag, re-verify in-repo LICENSE at download). Genuine
  Japanese street capture does not exist under a redistributable license; Mapillary CC-BY-SA
  self-reconstruction is the only clean path (deferred, see `docs/SPLAT_PROCUREMENT.md`).