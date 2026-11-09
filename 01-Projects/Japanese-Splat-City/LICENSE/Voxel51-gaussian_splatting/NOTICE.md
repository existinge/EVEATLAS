# Notice — Voxel51 / gaussian_splatting dataset (M1 renderer anchor)

**Asset:** `FO_dataset/train/point_cloud/iteration_30000/point_cloud.ply`
(3D Gaussian Splatting reconstruction, scene "train", iteration 30000)

**Source:** https://huggingface.co/datasets/Voxel51/gaussian_splatting
(dataset author per card: Paula Ramos; uploaded by Voxel51)

**License declaration — verified at primary source on 2026-11-08:**
`license: apache-2.0` appears in:
1. the dataset-card front matter (`dataset-card.md` in this folder), and
2. the Hugging Face API `cardData.license` field
   (`hf-api-metadata.json` in this folder; `tags` also contain
   `license:apache-2.0`).

**Caveats (recorded honestly, per gate rule "no unverifiable license tags"):**
- The declaration is made by the uploader on the dataset card. There is **no
  `LICENSE` file inside the dataset repository** (repo tree verified 2026-11-08:
  only README.md, .gitattributes, FO_dataset/ and FO_dataset/*/point_cloud/*).
  The tag therefore rests on the uploader's card declaration, not on an
  in-repo license text. Passed for M1 because the declaration is
  primary-source-verifiable and Apache-2.0 is non-copyleft with no
  non-commercial restriction; this caveat is rechecked before any release.
- Underlying photography is from the Mip-NeRF360 / 3D Gaussian Splatting
  research datasets; see `docs/SPLAT-SOURCE-REPORT.md` for the surrounding
  analysis of the train/truck scene lineage.

**Obligations we keep (Apache-2.0 §4):**
- A copy of the license text ships with any distribution that includes the
  splat payload (`apache-2.0.txt` in this folder, mirrored inside the packaged
  `StreamingAssets/` beside the `point_cloud.ply`).
- This NOTICE (name, source URL, license) ships in the packaged game's
  credits/README and in-repo.
- No modifications to the PLY are claimed; if converted/processed later, the
  modified form remains under Apache-2.0 with this notice preserved.
- We do **not** claim to be the dataset author.

**Payload (not in git, kept in `.tools/splat-source/`):**
- File: `Voxel51-gaussian_splatting-train-iteration30000.ply`
- Expected SHA256 (HF LFS oid): `a4c1906ce0256f5cb2255aa078d18b468dc01d8604f6eda1aaf22b235147a7a1`
- Size (HF tree metadata): 266,542,260 bytes
