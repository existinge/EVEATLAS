# Street-Level 3D Gaussian Splat (or point cloud + images) — Licensed Source Report

**Prepared:** 2026-11-08 (single research pass, timestamped evidence below)
**Project:** `01-Projects/Japanese-Splat-City` — Unity shipped offline Windows game
**Goal:** One **licensed, redistribution-permitted** street-level 3D Gaussian splat (or point-cloud + image set convertible to splat). Japanese shooting-street / shotengai (covered arcade) preferred; any dense urban street acceptable.

---

## 1. The hard license gate

Bundling a capture **inside a shipped, offline Windows game** = **redistribution of the capture** to end users. Therefore:

- ✅ **Allows shipping:** CC0, CC-BY 4.0 / BY-SA, Apache-2.0 (with attribution/notice obligations).
- ❌ **Disqualifies:** **NC** (non-commercial) terms, **research/educational-only** terms, **evaluation-only** terms, **no-dissemination / no-redistribution** terms, **ND** (no-derivatives), and content whose license tag cannot be verified at a primary source.
- ❗ **Does not rescue:** an open-source **viewer/toolkit license** (MIT/AGPL/etc.) does **not** license the underlying capture's content. Only the *content* license matters.

All license claims below were checked against **primary sources** (dataset pages, LICENSE files, READMEs, Hugging Face API metadata, Sketchfab API model end-points) — not aggregator blurbs.

---

## 2. Sources table

| # | Candidate | License (primary source) | Redistribute in shipped game? | Format | Content | Link | Download |
|---|-----------|--------------------------|------------------------------|--------|---------|------|----------|
| 1 | **Voxel51 `gaussian_splatting`** (Hugging Face) | `apache-2.0` declared on HF card (HF API `cardData.license`); verify the in-repo LICENSE file before shipping | ✅ **PASS** (Apache-2.0 permits redistribution w/ notice+attribution) | **Real pre-trained 3DGS PLYs** (`point_cloud/iteration_30000/point_cloud.ply`) + source images | Real outdoor street-level scenes **`truck`**, **`train`**, plus `drjohnson`, `playroom`; outdoor industrial/street-corner scale | https://huggingface.co/datasets/Voxel51/gaussian_splatting | Direct download via HF repo / API |
| 2 | Sketchfab — *Back Street Alley Photogrammetry Scan* | **CC-BY 4.0** (`license.label` from Sketchfab API) | ✅ **PASS** (CC-BY: redistribute with attribution) | Photogrammetry **mesh** (→ convert to splat yourself) | Real outdoor street alley | https://sketchfab.com/3d-models/back-street-alley-photogrammetry-scan-0c930d5c8aa54036a97d520615c72195 | Via model web page download |
| 3 | Sketchfab — *Old Broad Street Arcade Entrance* | **CC-BY 4.0** (Sketchfab API) | ✅ **PASS** | Photogrammetry **mesh** | **Covered arcade entrance** (closest shotengai-like form factor) — London, not Japan | https://sketchfab.com/3d-models/old-broad-street-arcade-entrance-337c2696b719429586c0782841ed5ea8 | Via model web page download |
| 4 | Mapillary imagery (+ **own** reconstruction) | **CC-BY-SA 4.0** (Mapillary terms) | ⚠️ **PASS with caveat** — **ShareAlike**: derivatives (your capture + reconstruction) must ship under CC-BY-SA; attribution required | Images + your own poses → own splat | **Only viable route to an actual Japanese shooting street / shotengai** (Japan is heavily covered) | https://www.mapillary.com/ | Via Mapillary web/API |
| 5 | Poly Haven | **CC0** ("You can redistribute them… even in a product you sell") | ✅ PASS | HDRIs / props / textures | **No street captures** — unsuitable content | https://polyhaven.com/license | polyhaven.com |
| 6 | Marcel Padilla *Gaussian Splat Objects Dataset* | Scanned items **CC-BY 4.0** per-object | ✅ PASS (scanned items) | Real scanned 3DGS `.ply` + `splatset` package | **Objects, not streets** — unsuitable for a street scene | https://marcelpadilla.com/Gaussian_Splat_Object_Dataset/ | GitHub `marcelpadilla/splats` |
| 7 | SS3DM (NeurIPS 2024) | **License conflict:** abstract claims "CC BY 4.0"; **but** repo `LICENSE.txt` = no-redistribution + non-commercial, and HF card = `cc-by-nc-nd-4.0`. Strictest terms control | ❌ **DISQUALIFIED** (NC + no-distribute + ND per actual data license) | Synthetic 3D meshes + depth | *Synthetic* street-view surface reconstruction (rendered, not a real capture) | https://github.com/THU-LYJ-Lab/SS3DM-Benchmark | Google Drive / HF |
| 8 | *3D Street View* (Amir Zamir / Stanford ECCV'16) | Repo LICENSE = **non-commercial only + "do not distribute this dataset or modified versions"**; content is **Google Street View** imagery | ❌ **DISQUALIFIED** (NC + no-distribution + GSV ToS breach) | Images + 6DOF poses + city 3D models | 25M GSV images / 8 cities — no Japanese city | https://github.com/amir32002/3D_Street_View | — |
| 9 | SceneSplat-49K (`GaussianWorld/scene_splat_49k`) | `cc-by-nc-4.0` (HF API) | ❌ NC | 3DGS splats | 26.12B gaussians / 22.4M RGB frames | https://huggingface.co/datasets/GaussianWorld/scene_splat_49k | gated |
| 10 | MatrixCity (Urban matrices) | **CC-BY-NC-4.0** (repo LICENSE) | ❌ NC | NeRF trainset / split | Synthetic urban aerial+street | https://github.com/lzhnb/MatrixCity | — |
| 11 | ScanNet++ | ToU: **non-commercial, research & educational use only** | ❌ research-only | RGB-D + poses | Indoor | https://github.com/ScanNet-Dataset-Creators | — |
| 12 | Mill-19 / Block-NeRF | **Waymo Open Dataset Terms**: non-commercial (def. line 38) + "Dataset Community Distribution Only" (line 56) + additional restrictions (line 70) | ❌ NC + restricted distribution | NeRF model | Industrial Google campus — not a shopping street | https://waymo.com/open/terms/ | — |
| 13 | UrbanScene3D | LICENSE: **non-commercial + "not for dissemination"** | ❌ | Mesh / image sets | Synthetic + real aerial urban | https://github.com/Liu-Debug/UrbanScene3D | — |
| 14 | `everettshen/StreetView360AtoZ` (HF) | `mit` tag, **but** content = images **scraped from Google Street View** → redistribution breaches Google ToS; no poses | ❌ (ToS breach / no reconstruction) | Equirectangular panoramas only | Random GSV views, no poses → not splattable anyway | https://huggingface.co/datasets/everettshen/StreetView360AtoZ | — |
| 15 | UCF GMCP Geolocalization "Google Street View" (62k images) | Research dataset of GSV imagery — no redistribution grant; GSV ToS issue | ❌ | Images | GSV panoramas split into side views | https://www.crcv.ucf.edu/data/GMCP_Geolocalization/ | research request |
| 16 | Stanford 2D-3D-S | Unverifiable — site served HTTP 503 during pass; no license text retrievable | ⚠️ **UNVERIFIED** | Images+poses | Indoor+outdoor | http://buildingparser.stanford.edu/dataset.html | — |
| 17 | InCommon (TUM) | Host dead/unreachable; no license text found | ⚠️ **UNVERIFIED / presumed dead** | RGB-D + poses | Indoor rooms | (no live host found) | — |
| 18 | "5K Street View" (Yang et al.) | **No licensed dataset found under this exact name.** Nearest indexed items are GSV-scraped image sets (fail GSV gate) | ⚠️ **NOT FOUND** | — | — | — | — |
| 19 | "VS-360" | **No single licensed dataset found under this name.** Closest results = GSV-scraped image sets (see #14/#15) | ⚠️ **NOT FOUND** | — | — | — | — |
| 20 | `keijiro-tk/splat-data` (HF) | HF API returns **401 (gated)**; card license not readable | ⚠️ **GATED / unverifiable** | 3DGS test splats | small test scenes | https://huggingface.co/datasets/keijiro-tk/splat-data | gated |
| 21 | OpenSplat | **AGPLv3 = toolkit code license only, not a content license**; no licensed capture dataset | ❌ not a capture | Toolkit | — | https://github.com/WebODM/OpenSplat | — |
| 22 | Polycam marketplace / explore | ToS reviewed (2025-04-25); governs service use, **no permissive redistribution license for downloaded third-party content found** | ❌ no license found | — | — | https://poly.cam/legal/terms-of-service | — |
| 23 | Scaniverse / Niantic Spatial | No primary redistribution terms found (ToS URL 404s; platform is enterprise/paid "Reconstruction"); gallery items lack explicit redistribution licenses | ❌ no license found | — | — | scaniverse.com / nianticspatial.com | — |
| 24 | Sketchfab — *Japanese tavern 居酒屋* | **CC-BY-NC** (API) | ❌ NC | mesh | Japanese bar alley | (Sketchfab search) | — |
| 25 | Sketchfab — *Street art at Morimoto Noren store* | CC-BY (API), but a single **shutter/wall**, not a street | ⚠️ not a street | mesh | Tokyo storefront wall | https://sketchfab.com/3d-models/street-art-at-morimoto-noren-store-d5bcfcbcbbae48868c9710339ce79358 | via page |
| 26 | Sketchfab — *Elevator in Berlin (Realities.io)* | CC-BY (API) | ✅ PASS (license) | mesh | **Interior**, not street | https://sketchfab.com/3d-models/elevator-in-berlin-realitiesio-7c759a68446c4bf3b109bfa9cea974ae | via page |

**Not re-listed as rows but also checked:** Sketchfab *Western Street Set Photogrametry* (CC-BY but 1872 faces + Western), *Shotengai-Maple Room* (stylized game asset), *japanese streets SENDAI* (Stylized/Steam-screenshot), *Japanese Street Section A* (manual 3ds Max) — all fail the "real street capture" content bar. ShapeSplat (Objaverse/ShapeNet-derived gaussian splats for classification, objects-only, not street).

---

## 3. Top-3 recommendations

**#1 — Hugging Face `Voxel51/gaussian_splatting` (Apache-2.0) — the only verified, redistribution-permitted, *already-trained 3DGS* found.**
- Published as a Hugging Face dataset with `license: apache-2.0` (read via HF API on retrieval). Contains trained gaussian `point_cloud/iteration_30000/point_cloud.ply` files **plus** source images, i.e., genuine 3DGS splats in exactly the format you need — no mesh→splat conversion required. Scenes include **`truck`** and **`train`** which are real street-level outdoor captures (industrial corner / yard scale, not a shopping arcade).
- *Caveats:* (a) the Apache-2.0 tag is self-declared by the uploader — before shipping, read the dataset's in-repo LICENSE file and (SAFER) contact Voxel51 for a written confirmation; (b) content is **not Japanese** and not a covered arcade; (c) scenes are small street-corner/lot scale, so it satisfies "dense street" only loosely.
- Why it still wins: it is the **only real permissive 3DGS splat** (not a mesh, not NC, not gated) on the entire candidate list.

**#2 — Sketchfab *Back Street Alley Photogrammetry Scan* (CC-BY 4.0).**
- A real photogrammetry scan of an **outdoor street alley**; Sketchfab API reports `license: Attribution 4.0 International`. CC-BY permits redistribution inside a shipped product as long as **attribution is provided** (e.g., an in-game credits line / README credits — extract the exact attribution string from the model's `meta.json` on download).
- *Caveat:* ships as a **mesh**, not a splat; you must generate a point cloud / splat yourself (e.g., sample + splat pipeline). Effort is modest and the license is rock-solid.

**#3 — Sketchfab *Old Broad Street Arcade Entrance* (CC-BY 4.0).**
- The **best "shotengai-like" form factor found anywhere**: a real photogrammetry capture of a covered arcade entrance, CC-BY. Same mesh→splat conversion needed. It is London, not Japan, so the signage won't be Japanese — but it is the closest licensed *arcade* geometry available.

**Honorable / strategic: Mapillary + own reconstruction (CC-BY-SA).** If the brief genuinely requires a **Japanese** shopping street, the only route that clears the license gate is to **reconstruct it yourself** from Mapillary's **CC-BY-SA**-licensed street imagery (pick poses → COLMAP/3DGS → splat). ShareAlike means the resulting capture ships under CC-BY-SA (attribution + same license), which your team should be willing to accept; verify attribution-source handling before committing. No canned, permissive, Japanese street capture exists in any form we located.

---

## 4. The Japanese shotengai reality check (bottom line)

After primary-source verification of **every named candidate** plus broader searches, **no redistributable (non-NC) 3DGS / NeRF / point-cloud+images capture of an actual Japanese street or shotengai exists** in any indexed, licensed form today. The Japanese candidates found are either NC-licensed (居酒屋), stylized art assets, single walls/shutters, or GSV-derived images whose redistribution breaches Google's ToS. The realistic paths are:

1. **Ship a non-Japanese licensed capture** (recommendation #1/#2/#3) as placeholder/prototype now, or
2. **Self-capture or self-reconstruct** (Mapillary CC-BY-SA route, or your own phone/LiDAR capture of an agreed street — fully clean), or
3. **Commission/vendor an agreed street capture** you hold copyright to.

---

## 5. Primary-source evidence quotes (verbatim)

- **Voxel51 HF card** — `license=apache-2.0`, `tags=… license:apache-2.0 … arxiv:2308.04079` (HF API, retrieved during pass). Files confirm `point_cloud/iteration_30000/point_cloud.ply` per scene.
- **Stanford 3D Street View LICENSE** — *"freely available … for non-commercial purposes … 3. That you do not distribute this dataset or modified versions … 4. That you may not use the dataset or any derivative work for commercial purposes …"* (repo `LICENSE`, master).
- **SS3DM LICENSE.txt** — *"you do not distribute this dataset or modified versions … you may not use the dataset or any derivative work for commercial purposes"* AND HF example card `license=cc-by-nc-nd-4.0` — directly **contradicts** the paper abstract's "CC BY 4.0" claim (that attribution applies to the paper/website, not the data distribution). Strictest terms govern.
- **Poly Haven** — *"You can redistribute them… even in a product you sell"* (CC0, polyhaven.com/license).
- **Mapillary** — imagery is licensed **CC-BY-SA 4.0** (Mapillary terms site).
- **Waymo Open Dataset Terms** (also governing Mill-19/Block-NeRF) — non-commercial definition (terms line 38), "Dataset Community Distribution Only" (line 56), additional restrictions (line 70).
- **Marcel Padilla dataset page** — *"Scanned: CC-BY-4.0. Use them for anything, credit Marcel Padilla."*
- **OpenSplat README** — *"The code in this repository … is licensed under the AGPLv3"* (toolkit only; no capture content).

**Google Street View ToS note:** several image sets (Stanford/GMCP, StreetView360AtoZ) are mass-downloads of Google Street View. Even where a downstream tag (e.g., MIT) exists, redistributing GSV imagery violates Google's terms of use — a separate, decisive gate independent of the dataset's own license tag.

---

## 6. Verification walls / unresolved

- **2D-3D-S (Stanford)**: `http://buildingparser.stanford.edu/dataset.html` returned HTTP 503 throughout the pass; Firecrawl tunnel failed → license unverified.
- **InCommon (TUM)**: no live host; presumed dead.
- **"5K Street View" / "VS-360"**: no dataset under those exact names found; likely conflations with GSV-scraped image sets.
- **`keijiro-tk/splat-data`**: HF API 401 — gated; license unreadable.
- **Sketchfab `/v3/models/{uid}/download`** endpoint returned 401 (auth-required); downloads are done from the public model page, which carries the CC-BY label — noted for whoever performs the download.
- **Polycam / Scaniverse (Niantic)**: no permissive redistribution terms for downloadable third-party content are published where we could verify them.