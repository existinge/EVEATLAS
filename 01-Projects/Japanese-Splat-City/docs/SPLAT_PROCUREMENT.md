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

- **Adopt #1 `Voxel51/gaussian_splatting`, scene `truck` or `train`, as the
  Milestone-1 renderer anchor** (proves splat-in-URP/DX12; content is not Japanese
  and not an arcade — acceptable for M1 renderer-proof, documented as such).
- Before the PLY enters any build: download to `.tools/` (outside repo), record
  SHA256 + the in-repo LICENSE file under `LICENSE/` + capture URL in
  `docs/ASSET_PROVENANCE.md`. Verify the Apache-2.0 tag in the dataset's own
  LICENSE file (self-declared by uploader; report §3 caveat (a)).
- Japanese shotengai content is deferred and gated on the Mapillary CC-BY-SA
  self-reconstruction path (ShareAlike acceptance) or a commissioned capture.
- Attribution/notice obligations for whichever item ships are preserved in an
  in-game + repo credits note (CC-BY/Apache requirement).
