# 01 — Firmware Extraction & Workspace Layout

Status: runbook (phase 2 of the bootchain research plan)
Target: Samsung Galaxy Note 9 SDM845 (`SM-N960*`), Odin `.tar.md5` packages
Relates to: `.agent/instructions.md` §5 SOP-1; output standards §6

---

## 1. Goal

Turn two public Odin packages (Rev 7 bootloader set and Rev 9 patched set) into a
clean, provenance-tracked, per-component workspace:

```
firmware/                       # GIT-IGNORED, local only (top README explains layout)
├── raw/
│   ├── r7/   r7_N960U1UES7FUA1_drive.zip   # FUS decrypt (single Odin zip per rev)
│   └── r9/   SM-N960U_2_20220723013851_n60buczjuw_fac.zip
├── extracted/                  # per-rev extracted Odin components
│   ├── r7/   BL/  BL_*.tar.md5 + 20 .lz4 modules + 20 decompressed images
│   └── r9/   BL/  BL_*.tar.md5 + 21 .lz4 modules + 20 decompressed images + meta-data/
└── README.md                  # what/why/how-to-reproduce (local only)

analysis/manifest/              # COMMITTED: sha256+sha1+size+mtime per build (provenance.py)
├── r7-manifest-raw.json        # zip digests, before extraction
├── r9-manifest-raw.json
├── r7-manifest-extracted.json  # per-component digests (both .lz4 and decompressed)
└── r9-manifest-extracted.json

analysis/01-source/             # COMMITTED: listings + derived digests only (no binaries)
├── r7/bl-modules.json          # per-module type/size/magic/sha256 + ELF headers
├── r9/bl-modules.json
└── bl-r7-vs-r9-diff.json       # per-module r7↔r9 size/digest comparison
```

`firmware/` (raw + extracted) is **git-ignored**; only the digest manifests under
`analysis/manifest/`, this runbook, and the acquisition record (docs/04) are
committed to the public repo.

## 2. Acquisition & provenance

1. Obtain the official Odin packages from Samsung's distribution channels for the
   target CSC/model (public firmware; document source URL + date).
2. Compute `sha256` of each `.tar.md5` and record in the manifest *before* extraction.
3. Verify the two packages differ only at the expected revision axis (same CSC/model,
   unless the diff objective requires otherwise). Record the bootloader revision
   letter/number shown in the package name or download metadata.

## 3. Extraction steps

1. Verify `.tar.md5` checksum (embedded MD5) — confirms transport integrity.
   (`samloader verify-md5 <file>` returns exit 0 for both revs; verified 2026-11-13.)
2. Un-tar to `firmware/raw/<rev>/`. Expect a FUS zip first; unzip to `BL_*`,
   `AP_*`, `CP_*`, `CSC_*` blocks. **Only `BL_*` is retained for this scope.**
3. The BL block stores every image as **LZ4 frame-compressed** (`.lz4`). Decompress
   with `lz4.frame` from the project `.venv` (python-lz4) into co-located images.
   Original `.lz4` bytes are kept alongside for provenance (both hashed).
4. Classify each decompressed image: `xbl.elf`, `abl.elf`, `pmic.elf` are ELF;
   `tz.mbn`, `hyp.mbn`, `aop.mbn`, etc. are MBNs that are themselves ELF
   (mix of ELF32/ELF64 — the loader's "mbn" type refers to the Qualcomm
   wrapping/container used for Secure World images, independent of ELF class).
   For each ELF payload record: class, image type, entry point, program headers,
   and the **target load address** (first program header / load-base table).
   Addresses later are reported as image-relative + image-base-relative deltas
   (see instructions §6).
5. `scripts/bl_modules.py` writes per-module records (kind, size, magic, sha256 of
   decompressed AND of the `.lz4` bytes, plus ELF headers) to
   `analysis/01-source/<rev>/bl-modules.json`.
6. `scripts/bl_diff.py` compares the two BL trees and writes
   `analysis/01-source/bl-r7-vs-r9-diff.json` (identical vs differing modules).
7. `scripts/provenance.py hash-dir` records sha256+sha1+size+mtime manifests
   (raw zips and extracted trees) into `analysis/manifest/`.

**Observed BL inventory (both revs, 20 decompressed modules):** the in-scope set
is present as `xbl.elf`, `abl.elf`, `tz.mbn` and `pmic.elf`; the hypervisor is
carried as **`hyp.mbn`** (not `hyp.elf` in this build family), and **no `rpm.mbn`
exists** in the BL block for SM-N960U (SDM845 routing/sleep controller firmware is
not shipped as a standalone BL member here). Presence/absence per `bl-modules.json`.

Note: `NON-HLOS.bin` (modem/modem-wifi firmware, RAW, ~59 MB) is also inside the
BL tar but is out of scope for bootchain analysis.

## 4. Reproducible runbook

```powershell
$py = (Resolve-Path '.venv\Scripts\python.exe').Path
Push-Location <project-root>

# 1. record raw (zip) digests, before any manipulation
& $py scripts/provenance.py hash-dir firmware/raw/r7 --out analysis/manifest/r7-manifest-raw.json
& $py scripts/provenance.py hash-dir firmware/raw/r9 --out analysis/manifest/r9-manifest-raw.json

# 2. verify + extract + decompress (walkthrough in docs/01 §3)
#    samloader verify-md5 <BL tar.md5>   (exit 0 for both revs)
#    unzip FUS zip -> tar -x -> lz4.frame decompress each .lz4 (project .venv has python-lz4)

# 3. record per-component digests (original .lz4 AND decompressed images)
& $py scripts/provenance.py hash-dir firmware/extracted/r7 --out analysis/manifest/r7-manifest-extracted.json
& $py scripts/provenance.py hash-dir firmware/extracted/r9 --out analysis/manifest/r9-manifest-extracted.json

# 4. classify modules (ELF/MBN/RAW + ELF32/64 headers, sha256) -> analysis/01-source/<rev>/bl-modules.json
& $py scripts/bl_modules.py <project-root>

# 5. r7↔r9 per-module comparison -> analysis/01-source/bl-r7-vs-r9-diff.json
& $py scripts/bl_diff.py <project-root>
```

Current result (2026-11-13): 20 decompressed BL modules per rev; **every module
differs** between r7 and r9 (xbl.elf 3,124,728 → 3,124,856 bytes; all in-scope ELF
headers structurally identical between revs — a clean diff pair).