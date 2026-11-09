# ASSET_PROVENANCE — Japanese Splat City

Every shipped asset in the native project must carry a provenance record before it enters
the packaged player. Rule: **nothing unlicensed or undocumented ships** (AGENTS.md quality
contract; licensing caution for street splats).

## Status board

| Asset | Status | License | Source / URL | Proven (file hash) |
|---|---|---|---|---|
| M1 splat anchor (`truck` or `train` scene, Voxel51 HF dataset) | PENDING download (do not ship until license text + hash recorded) | Apache-2.0 (self-declared; re-verify in-repo LICENSE) | https://huggingface.co/datasets/Voxel51/gaussian_splatting | — |
| Japanese shotengai capture | DEFERRED (no redistributable capture exists; Mapillary CC-BY-SA self-reconstruction or commission) | — | see docs/SPLAT_PROCUREMENT.md | — |

## Rules

1. **Street Gaussian splat** (the one renderer anchor): must be a licensed exemplary
   capture with the license text saved into this repo (LICENSE/*.txt + URL). A sample
   PLY/SPZ proves the pipeline only, not the art. See `docs/SPLAT_PROCUREMENT.md`.
2. **Japanese signage textures** (hiragana/katakana/kanji): rasterize from a
   license-checked font (e.g. Noto Sans JP, OFL) — record font name/version + license
   file here. No screenshots of proprietary assets.
3. **Architecture kit** (bays/shutters/sign rails/canopies): authored in-editor from
   primitives/procedural meshes; no third-party model imports.
4. Generated/finalized textures and their sources of truth (SVG/font) stay in the repo;
   large binaries (`*.ply`, `*.spz`, `*.png` beyond a few MB) stay out of git and are
   produced by repeatable tooling with records here.

## Japanese fonts (pending)

- Candidate: Noto Sans JP (SIL OFL) — offline install + rasterization script
  (`native/Tools/rasterize-jp-text.ps1`, TBD when the editor exists).
