# Plan — Japanese Splat City

**Single source of truth for milestone status, staging, and the two-codebase
register.** No other document may carry a milestone status table; README,
ARCHITECTURE, BUILD_LOG and TEST_REPORT link here. See §Consistency rules.

- **Current milestone:** M5 done + verified, **uncommitted** (staging item S0).
- **Last full verification:** 2026-11-09 — `npm run typecheck` clean,
  `npm test` 77/77 (6 files), `npm run build` OK (812.42 kB js / 208.89 kB gzip).
- **Host tooling facts (2026-11-09, re-proven):** headless verification uses
  system **Chrome** CDP (`--headless=new`); **Edge** CDP is blocked by machine
  policy. `npm run build`/`dev` require the project-local temp override
  (`TMP/TEMP = .tmp-esbuild`) — the system-temp esbuild write is still denied on
  this host (build fails with `Access is denied.` without it). Node 24 / npm 11
  are in use; README requires Node 20+.

## Milestone ledger

Statuses live only here. A status change must land in the same commit as its
`BUILD_LOG.md` row and `TEST_REPORT.md` section.

| # | Name | Status | Evidence |
| --- | --- | --- | --- |
| M0 | Bootstrap Vite + TypeScript + Three.js | ✅ done | BUILD_LOG M0; TEST_REPORT M0 |
| M1 | First-person exploration | ✅ done | BUILD_LOG M1; TEST_REPORT M1 (visual sweep queued → M8) |
| M2 | Real Gaussian splat rendering | ✅ done (superseded in part by M2-fix) | BUILD_LOG M2/M2-cleanup/M2-fix; TEST_REPORT M2/M2-fix |
| M3 | Japanese street props (apple, diya lantern, cat) | ✅ done | BUILD_LOG M3; TEST_REPORT M3 (leftovers → S1) |
| M3.1 | Street lighting / colorization | ✅ done | BUILD_LOG M3.1; TEST_REPORT M3.1 |
| M4 | Interactable environment | ✅ done | BUILD_LOG M4; TEST_REPORT M4 |
| M5 | Vocabulary learning | ✅ done + verified — **uncommitted** | BUILD_LOG M5 row (working tree); TEST_REPORT M5; re-verified 2026-11-09 |
| M6 | Missions | ⏸ staged (S3) | — |
| M7 | Persistence & QoL | ⏸ staged (S4) | — |
| M8 | Verification & polish | ⏸ staged (S5) | — |

## Staging area

Flow: `staged → current → verified-done` (or `dropped`, with reason).
- **staged** — entry lists origin, scope, and any blocker.
- **current** — at most one item at a time.
- **verified-done** — requires all four, in the same change: (1) `typecheck` +
  `test` + `build` green at that commit, (2) `BUILD_LOG.md` row, (3)
  `TEST_REPORT.md` section, (4) this ledger updated.

| # | Item | State | Origin / notes | Blocker |
| --- | --- | --- | --- | --- |
| S0 | Commit the M5 working tree (Game.ts, main.css, InteractionHud.ts, MenuOverlay.ts, src/content/, src/systems/, VocabularyNotebook.ts, learning.test.ts, BUILD_LOG M5 row) | **current** | audit F8 — verified code exists only in the working tree; commit on the feature branch | none |
| S1 | M3 leftovers: signage, convenience-store/café zones, vending machines | staged | ROADMAP M3 note (pre-merge); needs design decisions + licensed assets | asset decisions |
| S2 | Doc-consistency sweep after S0 lands | staged | audit 2026-11-09 (this file, TEST_REPORT M5, ARCHITECTURE rewrite) | S0 |
| S3 | M6 — Missions: three missions, state machines, tests; `systems/MissionSystem.ts`, `content/missions.ts`, `dialogue.ts`, `ui/MissionTracker.ts` are *planned* names, not existing code | staged | original roadmap; ARCHITECTURE aspirational modules map here | S0 |
| S4 | M7 — Persistence & QoL: localStorage progress under one namespaced key with schema version + reset (LearningSystem deliberately does not persist; M7 owns it), controls help, optional speech synthesis | staged | ARCHITECTURE invariant; LearningSystem.ts header comment | S0 |
| S5 | M8 — Verification & polish: full test pass, **incl. the queued M1 visual sweep** (headless-Chrome CDP, tooling proven at M2), docs, handoff | staged | TEST_REPORT M1 `[~]` note; M2 tooling note | S3, S4 |
| S6 | `public/assets/splats/m3/wine-barrel.ksplat` — adopt (later milestone + ASSETS.md row) or delete | staged, decision pending | on disk, untracked, undocumented; BUILD_LOG M3 excluded it from M3 | human decision |
| S7 | Native side-track resume decision | staged | EVEATLAS-native `native/` project is a fully specified drop (editor 6000.3.28f1, URP 17.3.0, vendored GaussianSplatting, `native/Build.ps1`); headless import/license blocked on this host | Unity Personal `.ulf` on an unconfined host — see native `docs/ACTIVATION.md` |
| S8 | Deferred procured assets: Sketchfab Back Street Alley (CC-BY), Sketchfab Old Broad Street Arcade (CC-BY), Mapillary + own COLMAP/3DGS (CC-BY-SA) | staged | native `docs/SPLAT_PROCUREMENT.md` top-3 (candidates #2–#4); no redistributable capture of a real Japanese street exists (per that research) | S7 / native direction |

## Cross-codebase register

Two codebases, planned as one here:

| Codebase | Path | Role | Status | Own logs |
| --- | --- | --- | --- | --- |
| Web | `EVEATLAS/01-Projects/Japanese-Splat-City/` | **canonical**, actively developed | M0–M5 done (M5 uncommitted, S0) | `docs/BUILD_LOG.md`, `docs/TEST_REPORT.md` |
| Native (Unity) | `EVEATLAS-native/01-Projects/Japanese-Splat-City/` | side-track — renderer/URP proof, walk gate | compile gated on Unity license (S7); splat payload staged + SHA-verified outside git | native `docs/BUILD_LOG.md`, `docs/TEST_REPORT.md` |

Shared anchors: the native M1 anchor splat
(`Voxel51-gaussian_splatting-train-iteration30000.ply`, SHA256
`A4C1906C…47A7A1`, byte-verified 2026-11-09) and the web `docs/ASSETS.md`
license policy (CC0/CC-BY/BY-SA/Apache only for shipping).

## Consistency rules

1. **One fact, one home.** Milestone status appears only in the ledger above.
   README points here instead of carrying a table; no second status table may
   appear anywhere.
2. **ARCHITECTURE mirrors `src/`.** `docs/ARCHITECTURE.md` describes only files
   that exist; planned modules live in the staging table, never as phantom
   paths in the module tree.
3. **BUILD_LOG and TEST_REPORT are append-only evidence**, organized by
   milestone id; they never restate status, only evidence.
4. **Scratch hygiene.** Project-root scratch (`scratch-m3.html`,
   `.scratch-m3-parse/`, `.tmp-esbuild/`, `.firecrawl/`, `dev-server*.log`) is
   gitignored and classified: `.tmp-esbuild/` is **load-bearing** (the
   documented TMP workaround target); `.firecrawl/` holds the browser
   verification scripts (`m4-verify.mjs`, `m5-verify.mjs`); `dev-server.err.log`
   documents the EBUSY crash that motivated the `vite.config.ts` watch ignores.
   Nothing is deleted without a decision row here.
5. **Evidence visibility.** `docs/evidence/*.png` are local-only by design
   (gitignored); claims that depend on them must say so.

## Audit notes (2026-11-09)

Recorded so the drift history survives the fix:

- F1 README:40-48 showed M2–M8 ⏳ while M0–M5 were verified — fixed by replacing
  the table with a link here (README edit, same change).
- F2 ARCHITECTURE described ~60% non-existent modules — rewritten to the real
  `src/` tree; aspirational names moved to S3/S4 staging.
- F3 TEST_REPORT M1 "[~] browser capture impossible" was Edge-specific and
  superseded in-writing by the Chrome-CDP tooling note (TEST_REPORT M2);
  Chrome CDP remains the working harness today.
- F4 Root scratch correctly ignored (git check-ignore verified); vault-root
  `.firecrawl/` was **not** covered by any ignore — fixed in the vault root
  `.gitignore` (one line, outside this project dir, approved 2026-11-09).
- F5 Splat staging flows match their docs: web splats in git under
  `public/assets/splats/`; native payload SHA-pinned in `native/Build.ps1`,
  staged into `Assets/StreamingAssets/` (PLY gitignored), verified on disk.
- F6 Native side-track was absent from all web planning — fixed by the
  cross-codebase register above and S7/S8.
- F7 Command agreement verified: `package.json` scripts = README Commands =
  AGENTS.md verification commands. Disagreements were documentation-shape only
  (F1/F2); README's stale "arrive with M4/M5" controls line fixed.
- F8 M5 uncommitted — tracked as S0.
- F9 wine-barrel.ksplat orphan — tracked as S6.
- F10 evidence local-only — stated in rule 5.
