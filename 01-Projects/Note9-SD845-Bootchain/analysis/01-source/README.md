# Source-tree area (analysis/01-source)
Local scratch space for the pipelined analysis of the two acquired bootloader sets.

Hard rules:
- **Nothing binary above this line in git.** `firmware/` is git-ignored; this tree
  holds only notes, listings and derived artifacts with no copyright-bearing content
  copied in (per `.agent/instructions.md` §7).
- Raw/extracted artifacts live under `firmware/` (git-ignored) exactly as
  documented in docs/01 and docs/04; only digests and listings mirror into
  `analysis/manifest/`.
- Never commit firmware, binaries, keys, or device identifiers beyond the public
  model codes (SM-N960U etc.).

Expected contents after execution:
- `r7/` — extraction notes, module listings (names/sizes), aligner inputs for rev 7
- `r9/` — same for rev 9
