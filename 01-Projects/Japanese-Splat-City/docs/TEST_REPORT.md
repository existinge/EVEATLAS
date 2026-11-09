# TEST_REPORT — Japanese Splat City (Native Windows walk)

Status of Milestone 1 acceptance evidence on this host. All results are from runs actually
executed here. Nothing fabricated; anything not executed is recorded as not-done.

## Environment acceptance tests (executed)

| # | Test | Command / evidence | Result |
|---|---|---|---|
| T1 | Editor installed | `Editor/Unity.exe` present; `FileVersion 6000.3.28.9373741`, `ProductVersion 6000.3.28f1_8f082d2fe476` | **PASS** |
| T2 | Installer SHA256 | `UnitySetup64-6000.3.28f1.exe` = `8197A37DEAD5597AD3A919B2293FDC9EA525BE3390FC745319A089406641E68B` | **PASS** |
| T3 | Windows Mono support bundled | `PlaybackEngines/WindowsStandaloneSupport` present | **PASS** |
| T4 | URP family pinned for 6000.3.28f1 | BuiltInPackages `package.json`: universal **17.3.0**, core **17.3.0**, shadergraph **17.3.0**, universal-config **17.0.3** | **PASS** (see BUILD_LOG correction) |
| T5 | Splat renderer vendored | `native/Packages/org.nesnausk.gaussian-splatting/package.json` = v2.0.0, MIT (76 files, 268 925 B) | **PASS** |
| T6 | Project scaffold | `native/ProjectSettings/ProjectVersion.txt` = `6000.3.28f1 (8f082d2fe476)` | **PASS** |
| T7 | Editor start / import / compile | attempted `Unity.exe -batchmode -quit` open | **FAIL — environment** |
| T8 | Licensing probe: `--showContext` / `--showRemoteEntitlements --debug` | dies at logging bootstrap: `UnauthorizedAccessException: Access to the path 'C:\Users\exist\AppData\Local\Unity' is denied` (`.tools/lic-ctx-*`,`lic-remote-*`) | **FAIL — environment** |
| T9 | Root discriminator (control) | `cmd.exe` child writes `%LOCALAPPDATA%\Unity` successfully | **PASS** (proves binary-identity confinement of third-party exes, not a path ACL) |
| T10 | LicensingCclient gateway | `Unity.Licensing.Client.exe` never creates the `LicenseClient-<user>` pipe; no entitlement; no Hub/account/ULF on machine | **FAIL (no license, confined)** |

## Offline pre-staging checks (executed — outside Unity, no license needed)

| # | Test | Command / evidence | Result |
|---|---|---|---|
| T11 | Noto Sans CJK JP font license | SIL OFL 1.1 — permits bundling + offline redistribution with license copy; no ND/NC analog | **PASS** |
| T12 | Font integrity | `NotoSansCJKjp-Regular.otf` SHA256 `68A3FC98…75B5`; OFL `6A73F954…E2BF2`; OTF hash recomputed inside verifier | **PASS** |
| T13 | Signage rasterizer run | `native/Tools/rasterize-jp-text.ps1`: 21 UTF-8 sign texts → 21 `sign-*.png` (32bpp ARGB, AA) + `signs-manifest.json` + proof sheet into `Assets/Resources/Textures/Signs/` (zero-editor-work `Resources.Load`) | **PASS** |
| T14 | No-tofu glyph verification | `verify-font-glyphs.ps1` VERDICT **True**: cmap glyph id > 0 for all 48 unique chars (21 signs, incl. rare `珈`), `GlyphTypeface` family "Noto Sans CJK JP", per-PNG ink fill 7.3–18.4% (≥5% threshold); `font-glyph-report.json` written | **PASS** |
| T15 | Sign texture wiring | `BlockBuilder.ApplySignTexture` (draft, uncompiled): `Resources.Load("Textures/Signs/sign-…")` with aspect-preserving crop + flat-material fallback; 20 storefront slates cycle bays; 商店街 title banner + 入口/出口 door flaps | **DRAFT** (compile pending license) |
| T16 | IL2CPP host prerequisite | VS Build Tools **2022** ver `17.14.37411.7` (`…\2022\BuildTools`, VC x64 14.44.35207) + **2019** ver `16.11.37301.9` (VC x64 14.29.30133) via `vswhere` | **PASS** |
| T17 | URP + scene authoring route | `native/Assets/Editor/ProjectAuthor.cs` (346 l, uncompiled-on-commit, round7 `799d3ff`): `UniversalRendererData` + reflected internal `GaussianSplatURPFeature` (throws if missing), `UniversalRenderPipelineAsset.Create(rd)` w/ camera depth texture, `GraphicsSettings.defaultRenderPipeline` + reflected `RegisterRenderPipelineSettings<T>` (best-effort), Fog `VolumeProfile` via type-name candidates (best-effort), `Assets/Scenes/WalkMain.unity` (BlockBuilder + EvidenceDriver + SplatAnchor `m_SourcePath="M1Anchor_train.ply"` + global Fog Volume) + `EditorBuildSettings` entry; reviewed section-by-section on disk | **DRAFT** (compile pending license) |
| T18 | Build firmware | `native/Build.ps1` 4-step, parse-checked on this host (PS 5.1): [1/4] SHA256-verified PLY (`A4C1906C…47A7A1`, 266,542,260 B) → `Assets/StreamingAssets/M1Anchor_train.ply`, [2/4] headless import, [3/4] `PlayerBuilder.Build` (runs `ProjectAuthor.Run()` first, IL2CPP fail-fast, Lz4HC), [4/4] packaged `-force-d3d12` launch + `Player.log` archived to `logs\` | **DRAFT** (run pending license) |
| T19 | First-licensed-run procedure | `docs/URP_SCENE_IMPORT.md`: offline-capable vs. licensed split, expected-good `[ProjectAuthor]` log lines, open compile risks (URP 17.3 API drift, feature reflection, global-settings injection, fog assembly) | **PASS** (documented) |

## Verdict

**Milestone 1: NOT ACHIEVED on this host — environment blocker, not content blocker.**

The host has no Unity license and third-party executables (Unity editor, LicensingClient, UPM node
child) are denied user-profile writes by the harness' binary-identity confinement; system binaries
write the same paths fine. No approval-based escalation exists in this session, and licensing cannot
be fabricated or bypassed.

**Deliverables produced despite the blocker:**
- Pinned, reproducible Unity project committed on `feat/japanese-splat-city-native`:
  `native/ProjectSettings`, `native/Packages/manifest.json` (URP 17.3.0 family + vendored splat package),
  `.gitignore`, `docs/BUILD_LOG.md`, `docs/TEST_REPORT.md`.
- Verified offline signage pipeline (T11–T15): licensed font, deterministic rasterizer, no-tofu proof,
  runtime texture wiring drafted — the whole block dresses itself on first import with zero editor work.
- IL2CPP build prerequisite confirmed present on this host (T16); build script pins the IL2CPP backend.
- No build artifacts, player, or frames — none claimed.

## Offline-player acceptance checks (deferred — require a build)

- [ ] Packaged Win64 **IL2CPP** player launches with editor closed and no Unity Hub.
- [ ] No browser / webview / localhost / DeepSeek / MCP dependency at runtime.
- [ ] GPU, resolution, splat count, per-process fps and player-log recorded (target RTX 2080 Ti, 60 fps @ 1080p provisional).
- [ ] Four evidence frames: spawn, junction, service bend, rejoin.
- [ ] Direct3D 12 active; URP "Compatibility Mode" OFF.
- [ ] Walk proof: 60–90 m covered main arcade + narrow bending service lane, two connections, rejoin landmarks.
- [ ] Japanese signage present; font + asset provenance recorded.