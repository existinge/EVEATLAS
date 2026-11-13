# Source-tree area (analysis/01-source)

Local scratch space for the pipelined analysis of the two acquired bootloader sets.

## Hard rules
- **Nothing binary above this line in git.** `firmware/` is git-ignored; this tree
  holds only notes, listings and derived artifacts with no copyright-bearing content
  copied in (per `.agent/instructions.md` §7).
- Raw/extracted artifacts live under `firmware/` (git-ignored) exactly as
  documented in docs/01 and docs/04; only digests and listings mirror into
  `analysis/manifest/` and this tree.
- Never commit firmware, binaries, keys, or device identifiers beyond the public
  model codes (SM-N960U etc.).

## Contents

### Per-revision module listings — `r7/bl-modules.json`, `r9/bl-modules.json`
Written by `scripts/bl_modules.py`. One record per **decompressed** BL image:
`name`, `kind` (ELF | MBN | RAW), `size`, `magic`, `sha256` of the decompressed
bytes; for ELF images additionally `class` (ELF32/ELF64), `e_type`, `machine`,
`entry`, program-header summary (`phnum`, each phdr's type/vaddr/paddr/filesz/
memsz/flags). The paired `.lz4` original is hashed separately in
`analysis/manifest/*-extracted.json`.

Classification is **ELF-class aware**: `aboot`/ABL, `aop`, `apdp`, `msadp`,
`cmnlib`, `bksecapp`, `engmode`, `storsec`, `vaultkeeper` and `qupv3fw` are ELF32;
`xbl`, `xbl_config`, `tz`, `hyp`, `devcfg`, `cmnlib64`, `keymaster64` and `pmic`
are ELF64. All MBN-type images are themselves ELF — the `.mbn` extension denotes
the Qualcomm Secure-World container, not a distinct format. `sec.dat` (948 B) is
RAW; `NON-HLOS.bin` (~59 MB) is a RAW modem image, out of bootchain scope.

**Observed BL inventory (both revs, 20 decompressed modules):** the in-scope set is
present as `xbl.elf`, `abl.elf`, `tz.mbn`, `pmic.elf`; the hypervisor ships as
**`hyp.mbn`** (not `hyp.elf`); **no `rpm.mbn`** is present in the SM-N960U BL block
(SDM845 RPM firmware is not a standalone BL member in this build family).

### Revision diff — `bl-r7-vs-r9-diff.json`
Written by `scripts/bl_diff.py`. Per-module r7↔r9 comparison over the decompressed
BL tree (size + sha256 of both decompressed image and `.lz4`). Result: **all 20
modules differ** between revs (0 byte-identical), i.e. a total-firmware refresh
between `N960U1UES7FUA1` (r7) and `N960USQU9FVG2` (r9).