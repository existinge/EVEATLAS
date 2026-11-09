# ASSET_PROVENANCE — Japanese Splat City

Every shipped asset in the native project must carry a provenance record before it enters
the packaged player. Rule: **nothing unlicensed or undocumented ships** (AGENTS.md quality
contract; licensing caution for street splats).

## Status board

| Asset | Status | License | Source / URL | Proven (file hash) |
|---|---|---|---|---|
| M1 splat anchor — `train` scene @ 30k iterations (Voxel51 HF) | **DOWNLOADED + SHA256-verified 2026-11-08** (payload in `.tools/splat-source/`, outside git); deploy into scene gated on Unity license | Apache-2.0 (card front-matter + HF API `cardData.license`; **no in-repo LICENSE file** — caveat recorded in LICENSE/Voxel51-gaussian_splatting/NOTICE.md) | https://huggingface.co/datasets/Voxel51/gaussian_splatting | SHA256 `a4c1906c…47a7a1` (matches HF LFS oid; 266,542,260 B) |
| Japanese signage font — Noto Sans CJK JP Regular | **DOWNLOADED + SHA256-verified 2026-11-08** (payload `.tools/font-source/`, outside git); OFL + NOTICE committed under `LICENSE/NotoSansJP/`; rasterization script `native/Tools/rasterize-jp-text.ps1` TBD when editor exists | **SIL OFL 1.1** — bundling in the offline game permitted; must ship OFL text + attribution with the font | https://github.com/notofonts/noto-cjk (`Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf`) | SHA256 `68A3FC98…75B5` (OTF, 16 467 736 B); OFL `6A73F954…E2BF2` |
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

## Signage font — RESOLVED (Noto Sans CJK JP, SIL OFL 1.1)

- Candidate adopted: **Noto Sans CJK JP Regular** (covered above in the status board).
- OFL 1.1 full text committed: `LICENSE/NotoSansJP/OFL-1.1.txt`; record: `LICENSE/NotoSansJP/NOTICE.md`.
- Packaged player must ship the OTF + OFL + NOTICE next to the executable, and the
  in-game credits must name the Noto CJK project (see NOTICE.md).
