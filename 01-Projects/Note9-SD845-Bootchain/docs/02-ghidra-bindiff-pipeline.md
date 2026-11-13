# 02 — Ghidra Headless + BinDiff Pipeline

Status: runbook (phase 2)
Relates to: `.agent/instructions.md` §4/§5; output standards §6

---

## 1. Goal

Produce a reproducible, JSON-native pipeline: load each component → analyze headless
→ export function/CFG/constant data → align rev7 vs rev9 → emit delta tables.

```
scripts/run_pipeline.py (orchestrator)
  → scripts/ghidra/run_headless.ps1   (analyzeHeadless per binary → <proj>/<img>.gpr)
  → scripts/ghidra/ExportFunctions.java  (final-analysis export → JSON)
  → scripts/diff/diff_functions.py    (align + delta + similarity → JSON + .md)
  → analysis/modules/<component>-rev7-vs-rev9.md
```

## 2. Stage pipeline

### Stage A — import & analyze (per binary)
Run `analyzeHeadless` once per binary with `-import` + `-postScript
ExportFunctions.java`. Use consistent analyzer options **across both revisions**,
or delta tables are meaningless. Record the exact CLI (tool versions + flags) in the
report reproducibility header.

Deliberate library-noise handling: keep the auto-analysis default, then filter at
export/diff time by symbol table + section origin (UEFI/vector tables, LK sections),
so library noise is *excluded from the delta* rather than baked into the project.

### Stage B — export (JSON contract)
`ExportFunctions.java` writes per-image JSON:

```json
{
  "image": {"file": "...", "sha256": "...", "base": 4194304},
  "functions": [
    {
      "name": "csr_wait_for_dbl",
      "addr": 4212456, "size": 48,
      "mnemonics": {"ldr": 6, "str": 2, "bl": 1, "stp": 3},
      "constants": [4198392],
      "calls": ["api_mem_get_pool"],
      "callsites": 3, "blocks": 4
    }
  ]
}
```
This contract is the single source of truth for every downstream stage and for AI
review (SOP-4).

### Stage C — alignment (rev7 vs rev9)
`diff_functions.py` matches functions in priority order:
1. identical `(size, name)` pairs, then
2. nearest-name matches within an address-window, then
3. structural similarity (mnemonic histogram cosine + call-import vector), allowing
   renamed/inlined functions to bind.
Emits `Δva`, `Δsize`, and a **diff signature** = per-function
`(added|removed|changed-blocks|same)`.

### Stage D — BinDiff cross-check
BinDiff (bindiff CLI / Ghidra integration via `Analyzedb`) is used as a **second,
independent aligner** for security-critical modules to validate the Python alignment.
Each module report records the matching engine used and any disagreements.

## 3. Reproducible runbook

```powershell
# per component (example: tz)
python scripts/run_pipeline.py --comp tz --rev r7 --bin firmware/extracted/r7/tz.mbn
python scripts/run_pipeline.py --comp tz --rev r9 --bin firmware/extracted/r9/tz.mbn
python scripts/diff/diff_functions.py --comp tz --r7 analysis/export/tz-r7.json --r9 analysis/export/tz-r9.json
# → writes analysis/modules/tz-rev7-vs-rev9.md + analysis/export/*.json
```

## 4. Output contract

- `analysis/export/<comp>-r<rev>.json` — machine-readable (committed for small comps,
  otherwise recorded as hashes in a committed index).
- `analysis/modules/<comp>-rev7-vs-rev9.md` — human review artifact per instructions §6.
- Every report header embeds tool versions (Ghidra, JDK, bindiff, python) + CLI flags.