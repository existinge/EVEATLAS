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
- No build artifacts, player, or frames — none claimed.

## Offline-player acceptance checks (deferred — require a build)

- [ ] Packaged Win64 Mono player launches with editor closed and no Unity Hub.
- [ ] No browser / webview / localhost / DeepSeek / MCP dependency at runtime.
- [ ] GPU, resolution, splat count, per-process fps and player-log recorded (target RTX 2080 Ti, 60 fps @ 1080p provisional).
- [ ] Four evidence frames: spawn, junction, service bend, rejoin.
- [ ] Direct3D 12 active; URP "Compatibility Mode" OFF.
- [ ] Walk proof: 60–90 m covered main arcade + narrow bending service lane, two connections, rejoin landmarks.
- [ ] Japanese signage present; font + asset provenance recorded.