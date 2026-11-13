# 04 — Firmware acquisition runbook

Status: runbook (phase 2). Evidence captured 2026-11-13 via Firecrawl search+scrape;
working copies of the scraped pages live **outside** this repo (see §7). Nothing here
claims a sha256 or a download URL that we have not observed ourselves. Anything marked
**verify-at-execution** must be re-checked before first use.

## 1. Objective

Obtain exactly **two** stock Samsung packages for the Note 9 **SM-N960U** (Snapdragon
SDM845, USA): a **revision-7** build and a **revision-9** build, per the phase-1 mandate.
Only the BL (bootloader) partition content is in scope: `xbl.elf`, `abl.elf`, `tz.mbn`,
`hyp.elf`, `rpm.mbn`, `pmic.elf` as present in the BL image.

Hard rules:
- **Static analysis only — no flashing.** We never write these images to a device.
- **Exactly two rev sets** (`r7/`, `r9/`). A third build introduces trust-on-first-use
  ambiguity and is out of scope.
- No firmware files, images, or binaries enter git (§7 of the manifest; `.gitignore`).

## 2. Revision identification (verified convention)

Samsung firmware version strings encode the bootloader revision as the **digit between
the build-type letters and the feature tag**: `N960U<CCC><REV><TAG>`.

Observed samples (two independent sources, 2026-11-13):

| Version string        | Rev (digit) | Source                                                       |
|-----------------------|-------------|---------------------------------------------------------------|
| `N960USQU9FVG2`       | 9           | [samfrew SM-N960U listing](https://samfrew.com/firmware/model/SM-N960U/upload/Desc/0/10) |
| `N960USQS9FVC5`       | 9           | same listing                                                  |
| `N960USQS9FVC6`       | 9           | same listing                                                  |
| `N960U1UES7FUA1`      | 7           | [XDA [U/U1] Note 9 firmware thread](https://xdaforums.com/t/u-u1-02-2021-fua1-note-9-official-firmware-and-guide-to-convert-to-usa-unlocked.3927478/) |
| `N960U1UES5FTK1`      | 5           | same thread — author labels it **"revision 5 firmware for root"** |
| `N960USQS1CSD1`       | 1           | same thread (2018–2019 era builds)                            |

Corroboration: the XDA author's explicit "revision 5" label on the `...UES5FTK1` build
matches the digit position. **Verify-at-execution:** eye-check the digit position on the
selected packages' version strings against a second sample per rev.

## 3. Candidate package pair

| Slot | Build (rev)           | Version string         | Android | Availability                                          |
|------|-----------------------|------------------------|---------|--------------------------------------------------------|
| r7   | SM-N960U1 (U1, USC)   | `N960U1UES7FUA1`       | 10      | XDA thread (Feb-2021 links) → U1 stock zip in thread   |
| r9   | SM-N960U (carrier)    | `N960USQU9FVG2`        | 10      | samfrew listing (Jul-2022 entry, per-carrier download) |

Both candidates are Android 10 Snapdragon builds two revisions apart — a clean diff
pair for the pipeline (same OS-era toolchain, minimal drift). Final pick happens at
execution after sha256 cross-checks; alternative rev-9 strings can be swapped in
(`N960USQS9FVC5`/`FVC6`).

## 4. Source map (verified 2026-11-13)

| Channel | Role | Notes |
|---------|------|-------|
| [samloader.com](https://samloader.com/) | samloader project site | CLI downloader + Odin tool pages; **verify-at-execution** exact CLI syntax for SM-N960U/CSC codes |
| [samloader.com/odin-tool/](https://samloader.com/odin-tool/) | Odin3 v3.14.4 (Windows), odin4/Heimdall (Linux) reference | Confirms BL/AP/CP/CSC `.tar.md5` slots; warning: flash only "matching model + same/higher binary version" (rev rollback guard) |
| [github.com/axonasif/samsung_root_ota_update](https://github.com/axonasif/samsung_root_ota_update) | Working samloader download workflow | `./startc.sh <csc> <model> <imei>`; `lz4 --rm -dm` decompression step after `tar`; BL partition names incl. `abl.elf`, `tz.mbn` (observed on an S24 example — naming confirms current BL layout conventions) |
| [samfrew.com SM-N960U listing](https://samfrew.com/firmware/model/SM-N960U/upload/Desc/0/10) | Firmware archive index | 235 results for SM-N960U; version strings incl. rev-9 builds; per-carrier download URL pattern `samfrew.com/download/Galaxy__Note9__/<id>/<csc>/<ver>/<csc-ver>` |
| [XDA [U/U1] Note 9 Official Firmware](https://xdaforums.com/t/u-u1-02-2021-fua1-note-9-official-firmware-and-guide-to-convert-to-usa-unlocked.3927478/) | U/U1 firmware + guide | rev-7 (`N960U1UES7FUA1`) and rev-5 (`N960U1UES5FTK1`) U1 stock zips (Google Drive mirrors); drive links are community mirrors → **always sha256 twice** |
| [repair.wiki ODIN guide](https://repair.wiki/w/How_to_use_ODIN_to_flash_firmware_on_Samsung_devices) | Reference guide | Search-result hit, not deep-scraped; **verify-at-execution** before relying on it |

Generic considerations (apply before using any channel):
- **Verify-before-use:** every mirror is community/third-party. Cross-check the same
  build on ≥2 sources; only a matching sha256 from two *independent* observations makes
  a digest trustworthy. Never trust a single page's displayed hash.
- Mirrors (Google Drive, AndroidFileHost, samfrew) may mutate or vanish → archive the
  digest manifests immediately after acquisition (`analysis/manifest/`).
- Ignore all "patched Odin" downloads (they exist in the XDA thread); we never flash,
  so modified flashing tools are out of scope and a supply-chain risk.

## 5. Acquisition procedure (execution phase)

1. **Resolve packages** (owner: @existinge): confirm r7 = `N960U1UES7FUA1` (U1/USC)
   and r9 = `N960USQU9FVG2` (choose carrier CSC; any CSC of the same build works for
   BL extraction) against §3; record where each was obtained.
2. **Download** via samloader CLI (preferred) or browser mirrors, into
   `firmware/raw/r7/` and `firmware/raw/r9/`. Use `samloader -m SM-N960U -r <csc> -s <version> download`
   per the project docs when available (**verify-at-execution** exact flags for this
   model/CSC).
3. **Integrity layer 1:** `.tar.md5` carries an embedded md5 of the `.tar`. Validate:
   - strip the trailing `.md5` and compare `tar` content hash against the embedded sum
     (Odin does this check when flashing; we replicate it statically), and/or
   - compare the published md5 from the source page.
4. **Integrity layer 2 (two-owner rule):** first owner computes sha256 of every raw
   file via `scripts/provenance.py`; a **second person** (different owner) repeats the
   computation from their own download. Both digests must match before extraction.
5. **Record provenance:** `python scripts/provenance.py hash-dir firmware/raw/r7 --out analysis/manifest/r7-manifest.json` (same for r9) and commit the manifests.
6. **Extract:**
   ```powershell
   # raw -> tar
   # .tar.md5 is a tar with a 32-byte md5 trailer; standard tar/7z tools handle it
   tar -xf <pkg>.tar.md5            # yields AP/BL/CP/CSC_*.tar.md5 (Odin image layout)
   # BL image -> components (files inside BL payload are lz4-compressed blobs)
   tar -xf BL_<...>.tar.md5
   lz4 --rm -d <component>.lz4      # e.g. xbl.elf.lz4 -> xbl.elf  (lz4 needed at exec time)
   ```
   Organize per the layout in docs/01: `firmware/extracted/r7/`, `firmware/extracted/r9/`.
7. **Verify module naming** against the expectation table in docs/01 §2; record the
   actual file list (names, sizes) in `analysis/manifest/*-manifest.json`.

## 6. Rollback / TOFU guardrails

- The Odin reference material warns to flash only the same or higher binary version —
  that guardrail is why we pin **two specific revs** and never mix slots across builds.
- If a candidate proves unpickable (dead mirror, mangled hash), fall back **within the
  same rev**: r7 candidates see §3 alternates; r9 alternates: `N960USQS9FVC5`, `FVC6`.
- TOFU rule: no hash enters `analysis/manifest/` until the two-owner cross-check (step 4)
  passes. Digests from a single source are marked `unverified` in the manifest until then.

## 7. Evidence handling

Raw scrape/search outputs used while drafting this runbook are working files under the
DSH workspace (`.firecrawl/`, outside this repo) and are **not committed**. This doc
deliberately embeds only observed facts plus the citation URLs. **verify-at-execution**
items: exact samloader CLI flags for SM-N960U, U1 zips' continued availability, and the
`NS_Rev.ver`-style rollback-window behavior in the OTA path (deferred to the analysis
phase; no live source has been confirmed for it yet).
