---
project: Japanese Splat City v3
status: execution-runbook
milestone: S0
owner: ATLAS
updated: 2026-11-10
authority: human-approved scope only
---

# JPSv3 — S0: REAL Gaussian Splat, No Greybox (Agent-Locked Runbook)

> **Definition of success:** A REAL, nonprocedural Gaussian-splat asset loads locally in a browser, with provenance recorded, an evidence screenshot, stable frame timing, and (only after the rendering gate passes) the existing JPSv3 player walking on a collision floor. The first gate is not a complete Japanese street. Do not confuse a working renderer, a reconstructed Japanese street, and final production fidelity.

## 0. Read this first: absolute boundaries

**Hard prohibitions**
- No Three.js procedural buildings, roads, façade factories, canvas texture painting, primitive-box substitutions, or fake 2D background panoramas presented as a splat.
- No changing the game engine from Three.js to PlayCanvas without a separate architecture approval. PlayCanvas/SuperSplat are **tools for asset inspection/conversion**, not authorization to migrate JPSv3.
- No quietly reducing the visual-quality goal, replacing the requested asset with an unrelated geometry city, or claiming 120 FPS without measurement.
- No Google Street View scraping, unlicensed captures, credentialed API bypasses, or republication of research-only datasets.
- No deleting production modules until a working replacement is verified, tests pass, and rollback is possible.
- No touching quests, journal, inspectables, saves, settings, or existing movement behavior beyond the minimal verified interface needed for S0.
- No independent creative expansion, HDR experiment, trainer swap, dependencies beyond those authorized, or parallel agents editing the same files.
- Never state an MCP tool was invoked, a screenshot was viewed, a dataset was downloaded, a GPU benchmark passed, or a scene is street-level without actual evidence.

**Allowed:** inspect repository; create an isolated feature branch; introduce one splat-loader adapter; add a tiny Rapier static floor if absent; test; document artifact metadata; use local SuperSplat editor; run a single legitimate reconstruction after approval of dataset/licensing and environment.

**Nonnegotiable STOP rules:** If repo is unidentified, asset license is unknown, browser integration conflicts with the current engine, tool APIs differ from docs, or real environment cannot be observed, mark **BLOCKED** with exact evidence. Never improvise around a gate.

## 1. Canonical ownership and hierarchy

- **Human:** approves architecture changes, dataset licensing risks, publication, expenses, merging, and major scope.
- **ATLAS coordinator / Antigravity:** scope and acceptance criteria; reviews proof and decides pass/fail. Does not self-approve code.
- **OpenCode:** mechanical handoff, timestamped polling, single writer/relay, evidence collection, state persistence, deduplication. Do not allow it to reinterpret requirements.
- **DeepSeek:** narrowly scoped implementation only; no redesign, no uncontrolled research, no new rendering path.
- **SuperSplat:** editing/conversion. WebMCP availability is experimental; UI/manual path is acceptable and must be stated.
- **PlayCanvas Editor MCP:** OPTIONAL prototyping lane. It is not the runtime for JPSv3 without approval.

**Repo truth:** Git commits + real files + tests + browser evidence. Chat messages are not proof. ATLAS markdown is intent, not proof of a running IDE.

### Suggested JPSv3 repository structure (adapt after inspection; do not create blindly)

```text
docs/jpsv3/s0/
  RUN_LOG.md               # dated commands, outputs, blockers, metrics
  ASSET_PROVENANCE.md      # creator, license, URL, download date, SHA256, restrictions
  QUALITY_GATE.md          # approved/rejected visual measurements
  HANDOFF.md               # exact next action and owner
  captures/               # screenshots as permitted by repo size/privacy policy
src/world/SplatWorld.ts     # isolated viewer adapter
public/assets/splats/      # only redistributed assets if license permits
```

**Git policy:** Do not commit downloaded research-only images, restricted training captures, huge PLYs, checkpoints, credentials, or private local paths. Prefer a manifest and a hash. Use Git LFS or object storage only after owner approval.

## 2. Exact source-of-truth links (verify at use time)

| Role | Canonical URL | Use / limitation |
|---|---|---|
| Public minimal test Gaussian | https://raw.githubusercontent.com/willeastcott/assets/main/biker.ply | Official SuperSplat docs' sample URL; inspect license before redistribution; use for throwaway local viewer test only |
| SuperSplat editor | https://superspl.at/editor | Import real PLY, cleanup, align; preserve .ssproj; export PLY/SOG |
| SuperSplat import/export | https://developer.playcanvas.com/user-manual/supersplat/editor/import-export/ | Verified formats: PLY/SOG/SPLAT/SPZ; KSPLAT import-only |
| SuperSplat getting started | https://developer.playcanvas.com/user-manual/supersplat/getting-started/ | Manual UI procedure; no upload required for editing |
| SuperSplat WebMCP contract | https://github.com/playcanvas/supersplat/blob/main/docs/webmcp.md | Browser-native, **not** PlayCanvas port 52000; test discovery first |
| SplatTransform CLI | https://developer.playcanvas.com/user-manual/splat-transform/ | Local PLY → SOG conversion and inspection |
| Nerfstudio install | https://docs.nerf.studio/quickstart/installation.html | GPU/CUDA environment; follow exact supported versions |
| Nerfstudio custom data | https://docs.nerf.studio/quickstart/custom_dataset.html | Images/video and 360° conversion |
| Splatfacto training/export | https://docs.nerf.studio/nerfology/methods/splat.html | 3DGS trainer; typical ~6GB VRAM; big mode ~12GB (2080 Ti 11GB is NOT the big-mode target) |
| Japanese street research data | https://www.vision.is.tohoku.ac.jp/?page_id=1115&lang=en | Kamaishi/Takata camera-pose sequences; **research-only**, copyright retained; not automatically reusable in a shipped game |
| Reference fidelity | https://superspl.at/scene/13b9a601 | Ceramic Studio visual reference, NOT permission to copy its capture or distribute it |
| T&T fallback research benchmark | https://www.tanksandtemples.org/download/ | Outdoor multi-view capture; **noncommercial** use |
| HDR+ RAW preprocessing examples | https://hdrplusdata.org/dataset.html | CC BY-SA RAW burst samples; NOT a coherent walkable street capture |
| CC0 environment HDRI | https://polyhaven.com/hdris/streets-town | Environment lighting, not reconstructable multi-location street parallax |

**Source hierarchy:** source download/owner documentation > maintained official implementation docs > community guide > model claim. Record what is verified, inferred, or unknown.

## 3. Phase A: make an existing REAL splat visible (S0-A)

### A1. Preflight — read-only

Execute in JPSv3 root, recording outputs in RUN_LOG:
```powershell
git status --short
git rev-parse --show-toplevel
git rev-parse --short HEAD
node --version
npm --version
Get-ChildItem package.json, src, public -ErrorAction SilentlyContinue
npm ls three @mkkellogg/gaussian-splats-3d @dimforge/rapier3d-compat --depth=0
nvidia-smi
```
If a command is missing, log it. If project is dirty, do not reset, stash or discard another agent's edits without authorization. Confirm existing bundler, current camera, renderer, resize loop, pointer-lock and PlayerController lifecycle before proposing integration edits.

### A2. Fetch sample with audit; do not imply redistribution rights

```powershell
New-Item -ItemType Directory -Force .\local-assets\s0 | Out-Null
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/willeastcott/assets/main/biker.ply' -OutFile '.\local-assets\s0\biker.ply'
Get-Item '.\local-assets\s0\biker.ply' | Select-Object Name,Length
Get-FileHash '.\local-assets\s0\biker.ply' -Algorithm SHA256
```
- If 404, zero bytes, HTML instead of valid splat PLY, or source rights uncertain, stop this acquisition path; choose a demonstrably permitted local test asset, and document its license.
- The biker is a **renderer proof only** (not Japanese street, nor final game's art).
- Keep local-assets untracked unless explicitly licensed and approved. Verify `git status --short`.

### A3. **Prove it in SuperSplat first** (no game code changed)

1. Open https://superspl.at/editor in a WebGPU-capable current Chrome or Edge.
2. File → Import → choose the local `biker.ply` (or authorized alternate).
3. Orbit, zoom, check that depth and parallax exist. Save one screenshot and note exact source and hash.
4. If the sample is bad or invalid, STOP. Do not start coding to compensate for an invalid source.
5. File → Export → **SOG** (for PlayCanvas runtime route) and/or PLY for cross-renderer interchange. Keep the original separately; do not assume SOG is supported by mkkellogg.
6. Record source format, output format, size, SH bands, and SHA256; check an exported file by re-importing it.

**Optional deterministic converter:**
```powershell
npm install -g @playcanvas/splat-transform
splat-transform --version
splat-transform '.\local-assets\s0\biker.ply' '.\local-assets\s0\biker.sog'
```
SOG is a **PlayCanvas** route, not by itself a guaranteed Three.js/mkkellogg input format. For the existing Three.js path, retain `.ply` or convert to a viewer-supported `.splat`/ `.ksplat` only after API verification. Do not fabricate conversion success.

### A4. Pick ONE runtime; do not mix

**Default:** existing JPSv3 Three.js renderer. Inspect current package and @mkkellogg/gaussian-splats-3d package API before writing. Use a `DropInViewer`-style mounted component **only if verified for installed version**. Avoid a second independent WebGL renderer if scene-graph integration is supported; check how viewer is updated/disposed and how render order is affected.

Install only after `npm view @mkkellogg/gaussian-splats-3d version` and documentation review:
```powershell
npm install @mkkellogg/gaussian-splats-3d
```
**Alternative, only with human approval:** PlayCanvas native SOG renderer if switching engines is justified. SuperSplat may edit assets regardless of engine.

**Required `SplatWorld.ts` contract (adapt to actual installed API):**
- `mount(scene, assetUrl, {position, rotation, scale})` returns promise; resolves only after genuine splat load, not merely scene attachment.
- Resolve asset under local `public/assets/splats` only after license approved; otherwise use a local untracked/dev-only static-serving route.
- Validate response/error paths, loading state, progress, camera coordinate convention, dispose/unmount of viewer/resources, and hot reload without duplicates.
- Log asset URL, declared format, GPU timing and render count where available.
- Do **not** create BoxGeometry, PlaneGeometry for visual ground, fake shop signs, canvas scene textures, or fallback mesh scenery.
- If an invisible Rapier floor is needed, it is a physics collider, not a visible procedural ground.

**S0-A pass evidence:**
- Real Gaussian visual in the browser after page load; orbit/move produces valid parallax.
- A source hash, exact tested browser/engine, screenshot, browser console log with no unhandled errors.
- Splat visible after hard reload; no console error; teardown/reload does not leak duplicate viewer.
- Build/test commands with real outputs.
- Explicit status **PASS**, **FAIL**, or **BLOCKED**.

## 4. Phase B: walk the street with invisible Rapier collision (S0-B)

Only start once S0-A PASS. Do not modify PlayerController until reading existing public methods. Required integration:
1. Confirm world up axis Y, camera/player eye height and splat local transform; align visual foot contact to Y=0. Do not assert asset's original ground is at 0.
2. Add static fixed body and **cuboid collider** of an appropriately measured walkable area in `PhysicsWorld` using Rapier's existing patterns. The visual plane remains absent. A simple invisible floor is permitted; building collision is deferred.
3. Confirm capsule feet rest above the collider (not camera origin at Y=0); spawn on a documented flat region.
4. Reconnect existing WASD, mouse look, pointer lock and no-clip prevention without replacing the controller.
5. If asset is a small stationary object (biker), restrict this to a collision smoke-test, NOT a claim that player walks a Japanese street.
6. Keep `src/quest`, `src/journal`, `src/inspectables`, `src/settings`, `src/save` intact. Run existing Vitest + Playwright if present.

**Tests (do not hallucinate passing):**
```powershell
npm run build
npm test -- --run
npx playwright test
```
Run only scripts actually present and supported; if absent, document exactly. Test player stable idle, movement four directions, wall not yet enforced, no fall-through, pointer lock relock, resume after reload, no duplicate physics bodies.

## 5. Phase C: Japanese street capture/reconstruction (separate gate S0-C)

**Critical caveat:** Available research dataset ≠ commercially redistributable game asset. Tohoku explicitly states copyright retained and research use. Get written rights for final shipping, or obtain an explicitly permitted alternative. It is acceptable to use research-only inputs for a permitted noncommercial internal experiment if its terms allow, but do NOT commit them, redistribute derivative splats, or publish a scene without review.

### C1. Asset-selection matrix

For each candidate record: URL, creator, license exact text, allowed derivative/distribution, format, view count, native resolution, camera poses/intrinsics, capture time consistency, pedestrian camera coverage, visible Japanese features, dynamic actors, whether images overlap, download size, expected VRAM, unresolved rights.

Preferred: many overlapping street-level views with geometry-aware camera positions. **HDRI panoramas at one location and 2D Street View screenshots do not supply walkable parallax**.

### C2. Tohoku candidate inspection (NO blind training)

1. Visit the Tohoku page above and read its license statement.
2. Download zip **only if internal research use is permitted in this context**; record file size, hash, date. Do not put in public ATLAS repository.
3. Inspect Kamaishi/Takata, choose `t0` **or** `t1` for one spatially contiguous segment (don't fuse months-apart sequences).
4. Dataset describes 5000x2500 cylindrical panoramic views plus 640x480 perspective derivatives, with pose files and intrinsics. Because Nerfstudio's 360 support expects equirectangular data, **do not label cylindrical panoramas equirectangular** or feed them to the 360 command uncorrected.
5. First try calibrated perspective images and provided extrinsics (convert coordinate systems with a verified transformation, not guessed axes), or separately reproject cylindrical images to calibrated perspective cameras. Check image-to-pose indexing, units, right/left side, orientation, exposure shifts, and repeatable scene overlap.
6. Reproject to multiple perspective views only with accurate camera matrices; scene must have actual camera translation and overlap. A panorama split into views at one position gives no extra translation.
7. Perform pose reprojection/visualization sanity check on a 10–30 frame subset before any expensive training. Record baseline and scale assumptions. The 640x480 derivatives may never meet Ceramic Studio's near-field sharpness: that is an **asset limitation**, not a rendering bug.

### C3. Train only after pose gate and license gate

Use official Nerfstudio instructions and capture installed versions. Prefer an isolated Linux/WSL2 GPU environment if dependencies on Windows prove difficult; do not wipe the existing project environment:
```bash
nvidia-smi
python --version
# Follow https://docs.nerf.studio/quickstart/installation.html
# Install compatible PyTorch/CUDA first per current upstream documentation
pip install nerfstudio
ns-train --help
ns-train splatfacto --help
```

**For ordinary perspective JPG input where no external poses are imported yet**, the official generic preprocessing route is:
```bash
ns-process-data images --data /DATA/street/images --output-dir /DATA/street/processed
```
This invokes an SfM pipeline; it can fail on low-parallax or moving imagery. **If preserving imported calibrated poses**, create valid Nerfstudio-compatible transforms from source calibration through a documented conversion instead; do not rerun image SfM and claim original poses were used.

After dataset passes pose and framing checks:
```bash
ns-train splatfacto --data /DATA/street/processed
# Use the exact config.yml emitted by the training run:
ns-export gaussian-splat --load-config /PATH/TO/config.yml --output-dir /DATA/street/export
```
The `config.yml` location is generated at runtime; never invent its path or claim the command ran.

**GPU guard:** 2080 Ti has 11 GB VRAM. Start with standard splatfacto (docs report ~6 GB typical) and a small segment, not `splatfacto-big` (~12 GB typical). Record peak VRAM, dataset resolution, iterations, training time, CUDA versions, checkpoint hash, output Gaussian count. Training FPS is not gameplay FPS.

### C4. Clean and export

- Import exported **Gaussian** PLY into SuperSplat; ordinary point cloud PLY is not sufficient.
- Orbit near street ground, check sign/window sharpness, holes, floaters, horizon, motion ghosting, street corners; do not use bloom/sharpening to hide defects.
- Save editable `.ssproj` locally, align transforms so chosen walkable ground equals runtime Y=0, export PLY for existing Three.js viewer or SOG for PlayCanvas lane. Preserve original.
- Compare from fixed eye-height camera views (1–3 m proximity) with Ceramic Studio reference; record what fails, not only what looks good.
- Only place redistributable derivatives in `public/assets/splats/` after explicit rights check and size approval.

## 6. Performance + visual acceptance tests

Target desktop: **RTX 2080 Ti**, **1080p**, uncapped, **>=120 FPS** *goal*, with reproducible per-frame measurements (120 FPS = ~8.33 ms/frame). A target is not a promise.

Record:
- GPU, driver, browser, resolution, render scale, display refresh, scene size, Gaussian count, asset bytes, initial load latency.
- FPS distribution (median, p5/p1 or consistent frame-time percentiles) after warmup; capture method/time/sample size.
- GPU vs CPU cost if instrumented, and whether VSync/frame cap was disabled.
- GPU memory before/after, visible region, camera motion path, zoom positions, optional LOD, interaction overhead.
- 5 evidence frames: spawn, 1m sign, storefront, down-street, oblique street corner. Plus motion clip if available.
- Rejection conditions: texture smear at 1–3m, floating splats, large transparency holes, sign text incorrectly asserted as readable, incorrect ground alignment, fall-through, missing browser proof, unlicensed asset, or only still-image evidence.
- Static splat signage may be fuzzy or inaccurate; learning content must come from verified structured data + crisp UI overlay, not guessed OCR.

**Gates:**
- **G0:** clean repo inventory and source/license manifest.
- **G1:** actual external PLY opens in SuperSplat.
- **G2:** actual splat renders inside existing JPSv3 browser, after reload.
- **G3:** original player can walk on Rapier collider without falling.
- **G4:** authorized Japanese street dataset successfully reconstructed, with accurate poses.
- **G5:** Ceramic-quality near-field review passes.
- **G6:** 120 FPS benchmark passes on target GPU.
G1–G3 are S0 functional proof. G4–G6 are later quality/performance gates, not prerequisites to honestly report a minimal working splat.

## 7. Debugging decision tree (no creative detours)

| Symptom | Diagnose ONLY this first | Forbidden substitute |
|---|---|---|
| Blank scene | Network URL/MIME, import format, camera pose, WebGL/WebGPU support, console, loader error | Drawing boxes |
| PLY imported as point cloud | Check Gaussian-specific PLY attributes/SH fields | Rendering colored particles and calling it a splat |
| Flash/flicker | Renderer depth/alpha/order integration, coordinate and alpha conventions | Canvas overlay |
| Scene looks bad near signage | Capture resolution, baseline/overlap, pose error, actual trained detail | Excessive sharpening/bloom |
| Camera falls | Rapier ground collider/spawn capsule and update order | Visible fake road |
| Training OOM | Dataset scale and image downscaling, standard splatfacto, GPU monitoring | Switching to procedural geometry |
| 120 FPS fails | Confirm uncapped measurement, reduce overdraw/LOD only with fidelity comparison | Fake frame reporting or reduced render resolution |
| Research dataset rights unclear | Stop publishing/committing; seek alternative license | Treating public URL as open source |

After **two failed attempts on the same cause**, stop and escalate. No autonomous package/engine migration.

## 8. Required evidence files and report format

Every run ends by updating **only** project-scoped files and linking exact real artifacts:

```markdown
# S0 Run Log — UTC date/time
Repo/branch/commit:
Owner / agent / tool:
Current gate: G0..G6
Status: PASS | FAIL | BLOCKED
Asset: source URL; creator; exact license; permission for game distribution (yes/no/unknown)
SHA256 / size / format:
Commands executed (not planned):
Exit codes and stdout/stderr excerpts:
Browser location and screenshots:
GPU / browser / resolution / FPS (or NOT MEASURED):
Tests actually run:
Files changed:
Risks and unresolved facts:
Next *single* action:
Reviewer signoff: PENDING / APPROVED / REJECTED
```

No success claims from markdown alone. Independent review + user approval before merge/deployment/publication.

## 9. Copy-paste boot prompt: constrain DeepSeek

```text
You are DeepSeek, the S0 implementation worker for Japanese Splat City v3.
Your ONLY authority is this runbook, the verified current JPSv3 source tree, and an explicit one-gate task issued by ATLAS. You are not the architect.

READ FIRST: [ATLAS link to this file]
OBJECTIVE THIS TURN: execute G0, then stop and report. Do not advance to G1 until OpenCode reports reviewer approval.
DO NOT: create any procedural buildings, roads, facades, fake splats, screenshots posing as proof, new architecture, second runtime, random asset search, broad refactoring, or changes to quest/journal/save modules.
DO: inspect repository, detect actual installed APIs, document versions and constraints, assess uncommitted changes, identify exact files for SplatWorld adapter and renderer integration.
RESPONSE FORMAT:
GATE / STATUS / COMMIT / ASSET / COMMANDS+EXIT / FILES CHANGED / EVIDENCE / RISKS / NEXT SINGLE ACTION.
If blocked, report blocker; do not improvise. If two same-class failures occur, STOP.
No progress without evidence. No success claims for unexecuted commands. No self-approval.
```

When ATLAS approves the next gate, change ONLY `OBJECTIVE THIS TURN` to the next gate and provide previous handoff log. Never send 'build the whole beautiful Japanese city' as the implementation assignment.

### OpenCode relay rules

Single relay owns IDE connection. Deduplicate messages by gate+commit+event id, poll only when idle, never type over a running prompt, persist latest accepted gate in a file, and send short status payload to Antigravity. Two stale polls trigger a blocked report, not endless re-prompts. Never declare a test successful based on model prose: require command exit/output and screenshot for visual claims. Antigravity cannot quietly modify gate acceptance while DeepSeek is coding.

## 10. Suggested first session (highest-probability proof)

1. G0: Inspect game repo and freeze interfaces.
2. G1: Download permitted throwaway Gaussian PLY, check hash, **open it in SuperSplat**. If no asset rights for distribution, do not commit it.
3. G2: Integrate isolated real splat loader in existing Three.js scene; display, screenshot, reload.
4. G3: Add existing Rapier floor and controller; smoke test, screenshot, movement evidence.
5. Only AFTER this is proven, begin Tohoku internal research (G4), noting licensing and 640×480 detail ceiling.
6. G5/G6 are separately reviewed; do not assert 'Ceramic quality' based on the initial biker proof.

**Stop state for today:** A functioning real splat viewer in existing game is a valuable S0 result. It is not permission to ship a Japanese street, not evidence of 120 FPS, and not a fidelity pass.

---

## 11. Review checklist for ATLAS coordinator

- [ ] Actual JPSv3 repository and current branch identified
- [ ] No dirty files overwritten; scoped branch used
- [ ] Only approved dependency and adapter changes
- [ ] Data/asset license and download rights recorded
- [ ] Genuine Gaussian PLY confirmed, NOT arbitrary point cloud
- [ ] SuperSplat local import proven
- [ ] Browser import/reload proof attached
- [ ] Physics/player proof attached
- [ ] Original tests run or absence documented
- [ ] No procedural buildings/visual road meshes created
- [ ] No private/restricted assets placed in public EVEATLAS
- [ ] Frame-time benchmark either evidence-backed or "NOT MEASURED"
- [ ] Reviewer outcome + next gate recorded

**Change-control:** Amend this guide through ATLAS review. A worker cannot interpret a failing gate as license to change architecture.
