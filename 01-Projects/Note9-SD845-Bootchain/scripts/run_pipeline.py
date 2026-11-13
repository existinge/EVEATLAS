#!/usr/bin/env python3
"""run_pipeline.py — orchestrator for the Note9-SD845 bootchain diff pipeline.

Stages (docs/02): export (Ghidra headless) → align → delta md/json → report.

Per-rev export:
  python scripts/run_pipeline.py export --comp tz --bin firmware/extracted/r9/tz.mbn --rev r9
Diff two exports:
  python scripts/run_pipeline.py diff --comp tz --r7 analysis/export/tz-r7.json --r9 analysis/export/tz-r9.json

JSON-native between stages.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # Note9-SD845-Bootchain/
EXPORT = ROOT / "analysis" / "export"
MODULES = ROOT / "analysis" / "modules"


def run(cmd: list[str]) -> int:
    print("+", " ".join(str(c) for c in cmd))
    return subprocess.call(cmd, cwd=ROOT)


def cmd_export(args) -> int:
    EXPORT.mkdir(parents=True, exist_ok=True)
    export_json = EXPORT / f"{args.comp}-{args.rev}.json"
    rc = run(["powershell", "-ExecutionPolicy", "Bypass", "-File",
              str(ROOT / "scripts/ghidra/run_headless.ps1"),
              "-Bin", args.bin, "-Rev", args.rev, "-Comp", args.comp,
              "-OutDir", str(EXPORT)])
    if rc != 0 or not export_json.exists():
        print("ERROR: export stage failed", file=sys.stderr)
        return 1
    print(f"export ready: {export_json} ({export_json.stat().st_size} bytes)")
    return 0


def cmd_diff(args) -> int:
    MODULES.mkdir(parents=True, exist_ok=True)
    out_json = EXPORT / f"{args.comp}-delta.json"
    out_md = MODULES / f"{args.comp}-rev7-vs-rev9.md"
    rc = run([sys.executable, str(ROOT / "scripts/diff/diff_functions.py"),
              "--comp", args.comp, "--r7", args.r7, "--r9", args.r9,
              "--out-json", str(out_json), "--out-md", str(out_md)])
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SDM845 bootchain rev7-vs-rev9 pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pe = sub.add_parser("export", help="run Ghidra headless export for one binary")
    pe.add_argument("--comp", required=True)
    pe.add_argument("--bin", required=True, help="path to ELF/MBN for this rev")
    pe.add_argument("--rev", required=True, choices=("r7", "r9"))

    pd = sub.add_parser("diff", help="align two exports and emit delta JSON + MD")
    pd.add_argument("--comp", required=True)
    pd.add_argument("--r7", required=True)
    pd.add_argument("--r9", required=True)

    args = ap.parse_args(argv)
    return cmd_export(args) if args.cmd == "export" else cmd_diff(args)


if __name__ == "__main__":
    sys.exit(main())