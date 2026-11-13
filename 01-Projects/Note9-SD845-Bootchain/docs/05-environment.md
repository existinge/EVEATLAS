# 05 — Environment & toolchain plan

Status: plan (phase 2). Nothing here is installed yet; this is the decision record and
runbook for the local RE environment.

## 1. Python runtime

- **Interpreter (current):** `C:\Users\exist\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe`.
  Bundles numpy, pandas, python-docx, python-pptx, openpyxl, Pillow, lxml, XlsxWriter.
- The aligner (`scripts/diff/diff_functions.py`) and provenance CLI (`scripts/provenance.py`)
  are **stdlib-only** and run on any Python 3.
- **Controlled env:** create `scripts/.venv` (git-ignored via root `.gitignore` rule
  `.venv/`) before installing optional extras; never pollute the shared runtime.

## 2. Optional analysis extras — absent today

| Package     | Purpose                                                         | Install                       | Status  |
|-------------|-----------------------------------------------------------------|-------------------------------|---------|
| `lief`      | ELF/MBN header + segment parsing without Ghidra                 | `pip install lief`            | absent  |
| `capstone`  | Light disassembly: mnemonic histograms, noise filters           | `pip install capstone`        | absent  |
| `z3-solver` | Constraint checks on candidate logic (e.g., rollback-counter)   | `pip install z3-solver`       | absent  |
| `angr`      | Heavy symbolic execution — optional, slow                       | `pip install angr` (skip now) | absent  |

Install lazily per task; **pin the version you actually installed** back into
`scripts/requirements.txt`, and record it in the report reproducibility header.
After install, smoke-test with `python -c "import lief, capstone, z3"`.

## 3. Ghidra headless

- Local install required (not pip-installable). Set `GHIDRA_HOME` (wrapper:
  `scripts/ghidra/run_headless.ps1`, see docs/02).
- **JDK:** current Ghidra releases require JDK 17+ (verify the release notes of the
  exact Ghidra build you install — JDK 11 no longer suffices for recent versions).
- Export contract: `scripts/ghidra/ExportFunctions.java` → JSON per binary into
  `analysis/export/` (git-ignored for `*.json`? No — export JSON is git-ignored;
  fixtures and diffs live in analysis/; see docs/02).

## 4. BinDiff (independent cross-check aligner)

- BinDiff aligns two binaries' functions; **recent BinDiff releases support Ghidra**
  exports — verify version-specific support at install time (BinDiff 5.x/6.x notes).
  BinDiff is free for open-source/research use per Google's terms — verify at install.
- Use: run after our aligner on the same rev7/rev9 pair; report agreement/disagreement
  in the reproducibility header of each module report (docs/02 §header).
- Alternatives if unavailable: `radiff2` (radare2/rizin), Diaphora (IDA-only),
  manual structural pass inside Ghidra.

## 5. Expected payload shape — drives tool choices

- `xbl.elf`, `abl.elf`: ELF; symbols are usually retained → **symbol-anchored**
  alignment first (exact-name priority in `diff_functions.py`).
- `tz.mbn`, `hyp.mbn`: Qualcomm MBN containers (ELF inside) → **stripped**;
  structural matching and reload-address math matter; `lief` can parse the ELF
  inside the MBN once extracted. (No `rpm.mbn` exists in this BL block.)
- `pmic.elf`: small; treat as supporting evidence, not a primary diff target.

## 6. Environment provenance

Record in every report header (Output Standard §6): Ghidra version, JDK version,
BinDiff version, Python version, pip extras with versions. A tool line like
`Ghidra 11.3 (JDK 21) + BinDiff 9` is only meaningful with the exact builds recorded.
