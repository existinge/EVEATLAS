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
- All remaining checklist items are gated by the blocker above (implemented/shipped = false, none fabricated).

## Open questions

- Exact URP 17.3.0 acceptance with `org.nesnausk.gaussian-splatting` v2.0.0 (targets 2022.3/URP 17.0; may need feature `renderPassEvent` compatibility path on 17.3) — to confirm on first editor open.
- Direct3D 12 default in ProjectSettings + standalone `-force-d3d12` fallback.
- Licensed street-correct PLY source (provenance record needed before the walk scene uses any real street splat).