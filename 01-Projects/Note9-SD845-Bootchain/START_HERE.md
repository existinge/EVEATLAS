# START HERE — Note9-SD845 Bootchain R&D

**Tracked project** · vault: `01-Projects/` · status: framework scaffold (phase 1)

Independent technical research: reverse-engineering the Samsung Galaxy Note 9
(SM-N960*, SDM845) secure-boot trust chain by **binary diffing the unlockable
**Revision 7** bootloader against the patched **Revision 9**.

> Scope & legality: public-model research on our own/archived hardware. No
> proprietary blobs, keys, or leaked binaries are committed to this repo — only
> methodology, scripts, digests, and derived symbols/offsets/hypotheses.

## Start here

1. Read the operating contract first: [`.agent/instructions.md`](.agent/instructions.md)
   (persona, research questions, REA-style harness, output standards, provenance).
2. Roadmap docs:
   - [docs/01-firmware-extraction.md](docs/01-firmware-extraction.md) — Odin/ELF/MBN extraction runbook (+ `analysis/manifest/` layout)
   - [docs/02-ghidra-bindiff-pipeline.md](docs/02-ghidra-bindiff-pipeline.md) — Ghidra headless + aligner design
   - [docs/03-vulnerability-triage.md](docs/03-vulnerability-triage.md) — validation-gap triage plan
   - [docs/04-acquisition.md](docs/04-acquisition.md) — verified acquisition runbook (rev identification, sources, two-owner hashing)
   - [docs/05-environment.md](docs/05-environment.md) — environment & toolchain plan (Ghidra/JDK, BinDiff, pip extras)
3. Scripts: `scripts/run_pipeline.py` (export|diff), `scripts/provenance.py`
   (hash-dir|tree-compare), `scripts/diff/diff_functions.py` (aligner),
   `scripts/ghidra/` (headless export), `scripts/test/` (self-tests).

## Status

- [x] Framework scaffold & pipeline scripts (phase 1)
- [ ] Odin packages located + sha256 manifest (phase 2)
- [ ] Extraction → `firmware/extracted/{r7,r9}/`
- [ ] Ghidra headless exports → `analysis/export/<comp>-r<rev>.json`
- [ ] Per-module delta reports → `analysis/modules/<comp>-rev7-vs-rev9.md`
- [ ] Validation-gap findings (triage tiers T1–T4) → `analysis/claims-ledger.md`

## Answered so far

Nothing claimed yet — evidence-first. Findings only appear with a repro snippet,
per `.agent/instructions.md` §6–7.