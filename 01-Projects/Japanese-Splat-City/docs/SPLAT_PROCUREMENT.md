# SPLAT_PROCUREMENT — licensed street-correct Gaussian splat

Full primary-source research: `docs/SPLAT-SOURCE-REPORT.md` (2026-11-08, verbatim
license quotes, per-candidate verification, verification-walls section).

Hard gate (shipping = redistribution): **CC0 / CC-BY / BY-SA / Apache pass; ANY
non-commercial, research-only, no-dissemination, ND, or unverifiable license
disqualifies.** An open-source viewer/toolkit license (MIT/AGPL…) never licenses
captured content.

## Candidates (verified, condensed)

| # | Source | License | Street-level? | Direct splat? | Verdict |
|---|---|---|---|---|---|
| 1 | HF `Voxel51/gaussian_splatting` | Apache-2.0 (self-declared; re-verify in-repo LICENSE before ship) | ✅ real outdoor (`truck`, `train`) | ✅ **pre-trained 3DGS PLY** | ✅ PASS |
| 2 | Sketchfab *Back Street Alley Photogrammetry Scan* | CC-BY 4.0 (API) | ✅ street alley | ❌ mesh → own conversion | ✅ PASS |
| 3 | Sketchfab *Old Broad Street Arcade Entrance* | CC-BY 4.0 (API) | ✅ covered arcade entrance (closest shotengai form factor) | ❌ mesh → own conversion | ✅ PASS |
| 4 | Mapillary imagery + own reconstruction | CC-BY-SA 4.0 (ShareAlike derivative) | ✅ **only route to a real Japanese street** | images → own COLMAP/3DGS | ⚠️ PASS w/ ShareAlike |
| — | SS3DM, 3D_Street_View, SceneSplat-49K, MatrixCity, ScanNet++, Mill-19/Block-NeRF, UrbanScene3D, Sketchfab 居酒屋, GSV-scraped sets | NC / research-only / no-dissemination / GSV ToS | — | — | ❌ DISQUALIFIED |

## Top-3 recommendation (research verdict)

1. **Voxel51/gaussian_splatting** — only verified redistribution-permitted,
   already-trained 3DGS PLYs (`truck`, `train`); no conversion work.
2. **Back Street Alley Photogrammetry Scan** — CC-BY, real alley, mesh→splat.
3. **Old Broad Street Arcade Entrance** — CC-BY, real covered arcade (London).

**Bottom line from research:** no redistributable capture of an actual Japanese
street/shotengai exists in any indexed licensed form. Japanese candidates are all
NC, stylized, single-wall, or GSV-ToS-breaching.

## Selection decision (M1 anchor)

- **Adopt #1 `Voxel51/gaussian_splatting`, scene `train` @ iteration 30000, as the
  Milestone-1 renderer anchor** (proves splat-in-URP/DX12; content is not Japanese
  and not an arcade — acceptable for M1 renderer-proof, documented as such).
- **DONE 2026-11-08:** payload downloaded to `.tools/splat-source/`
  (`Voxel51-gaussian_splatting-train-iteration30000.ply`, 266,542,260 B) and
  SHA256-verified **exactly against the HF LFS oid**
  (`a4c1906ce0256f5cb2255aa078d18b468dc01d8604f6eda1aaf22b235147a7a1`) — byte-for-byte
  match with what Hugging Face serves. License record committed under
  `LICENSE/Voxel51-gaussian_splatting/` (canonical Apache-2.0 text, dataset card
  front-matter, HF API metadata, NOTICE with caveats + obligations).
- **Verified caveat (report §3 (a), now resolved as documented):** the dataset repo
  contains **no in-repo LICENSE file**; the Apache-2.0 tag rests on the uploader's
  card front-matter + HF API `cardData.license`, captured as evidence in the LICENSE
  folder. Kept as M1 anchor (declaration is primary-source-verifiable; Apache-2.0
  has no NC restriction). `truck` (510 MB) retained as the heavier alternative.
- **Next gate:** the PLY enters the scene only after the Unity license resolves
  (deploy + import into `Assets/GaussianSplats/` under StreamingAssets, notice
  mirrored beside the payload per NOTICE.md obligations).
- Japanese shotengai content is deferred and gated on the Mapillary CC-BY-SA
  self-reconstruction path (ShareAlike acceptance) or a commissioned capture.
- Attribution/notice obligations for whichever item ships are preserved in an
  in-game + repo credits note (CC-BY/Apache requirement).
