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
│   ├── r7/   N960U...<rev7>.tar.md5
│   └── r9/   N960U...<rev9>.tar.md5
├── extracted/
│   ├── r7/
│   │   ├── xbl.elf            # SDM845 primary bootloader (SBL2-class / UEFI)
│   │   ├── abl.elf            # Little-Kernel aboot (Android Boot Loader)
│   │   ├── tz.mbn             # TrustZone OS (secure monitor/world)
│   │   ├── hyp.elf, rpm.mbn, pmic.elf
│   │   └── ...
│   └── r9/   (mirror)
└── README.md                  # what/why/how-to-reproduce (local only)

analysis/manifest/              # COMMITTED: sha256 + metadata per build (provenance.py)
├── r7-manifest.json
└── r9-manifest.json
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
2. Un-tar to `firmware/raw/<rev>/`. Expect `BL_*`, `AP_*`, `CP_*`, `CSC_*` blocks;
   the BL (bootloader) block contains `xbl.elf`, `abl.elf`, `tz.mbn`, and friends.
3. For each ELF payload record: image type, entry point, program headers, and the
   **target load address** (from the ELF or the loader table). Addresses later are
   reported as image-relative + image-base-relative deltas (see instructions §6).
4. For MBN payloads (`tz.mbn`, `rpm.mbn`): note MBN magic/header (Qualcomm secure
   MBN / standard MBN), document format before disassembly.
5. Write `analysis/manifest/<rev>-manifest.json` (via `scripts/provenance.py`) with
   every digest + the fields above.

## 4. Reproducible runbook

```powershell
# 1. record raw digests
python scripts/provenance.py hash-dir firmware/raw/r7 --out analysis/manifest/r7-manifest.json
python scripts/provenance.py hash-dir firmware/raw/r9 --out analysis/manifest/r9-manifest.json

# 2. extract (during setup only; binaries stay git-ignored)
#    (extraction helper documented here once finalized)

# 3. confirm per-component tree parity
python scripts/provenance.py tree-compare firmware/extracted/r7 firmware/extracted/r9
```