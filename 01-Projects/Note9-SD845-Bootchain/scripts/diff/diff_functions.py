#!/usr/bin/env python3
"""diff_functions.py — align rev7 vs rev9 function exports and emit a delta report.

Alignment priority (per docs/02 §2 Stage C):
  1. identical (size, name)
  2. nearest name match within an address window (renamed)
  3. structural similarity (mnemonic histogram cosine + call-vector Jaccard)

Inputs: two ExportFunctions.java JSON exports.
Outputs: --out-json (machine delta) and --out-md (human report per instructions §6).

stdlib + math only.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

ADDR_WINDOW = 0x200000  # renames don't move functions far across a binary


def load(path: str) -> tuple[dict, list]:
    with open(path, encoding="utf-8-sig") as fh:
        d = json.load(fh)
    return d["image"], d["functions"]


def hist_norm(mn: dict) -> dict:
    tot = sum(mn.values()) or 1
    return {k: v / tot for k, v in mn.items()}


def cosine(a: dict, b: dict) -> float:
    va, vb = hist_norm(a), hist_norm(b)
    common = set(va) | set(vb)
    dot = sum(va.get(k, 0.0) * vb.get(k, 0.0) for k in common)
    na = math.sqrt(sum(v * v for v in va.values())) or 1.0
    nb = math.sqrt(sum(v * v for v in vb.values())) or 1.0
    return dot / (na * nb)


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def structural(x: dict, y: dict) -> float:
    """Combine mnemonic cosine + call-vector Jaccard into one similarity score."""
    return 0.6 * cosine(x["mnemonics"], y["mnemonics"]) + 0.4 * jaccard(set(x["calls"]), set(y["calls"]))


def align(r7: list, r9: list) -> list[dict]:
    # Phase 1: exact (size, name)
    r9_by_key = defaultdict(list)
    for f in r9:
        r9_by_key[(f["size"], f["name"])].append(f)

    used = set()
    rows = []
    for f in r7:
        key = (f["size"], f["name"])
        cands = r9_by_key.get(key, [])
        cand = next((c for c in cands if id(c) not in used), None)
        if cand is not None:
            used.add(id(cand))
            rows.append(_row(f, cand, "exact-size-name"))
            continue
        # Phase 2: name only, within address window
        cands2 = [c for c in r9 if c["name"] == f["name"] and abs(c["addr"] - f["addr"]) <= ADDR_WINDOW and id(c) not in used]
        if cands2:
            cand = min(cands2, key=lambda c: abs(c["addr"] - f["addr"]))
            used.add(id(cand))
            rows.append(_row(f, cand, "name-win"))
            continue
        # Phase 3: structural, size-adjacent, not yet used
        cands3 = [c for c in r9 if id(c) not in used and abs(c["size"] - f["size"]) <= max(8, f["size"] // 10)]
        if cands3:
            cand = max(cands3, key=lambda c: structural(f, c))
            rows.append(_row(f, cand, "structural"))
            used.add(id(cand))
            continue
        rows.append(_row(f, None, "unmatched-r7"))
    # leftover r9 = added in r9
    for c in r9:
        if id(c) not in used:
            rows.append(_row(None, c, "added-r9"))
    rows.sort(key=lambda r: r["addr_r7"] if r["addr_r7"] is not None else r["addr_r9"])
    return rows


def _row(x, y, kind) -> dict:
    h7 = x.get("sha256") if x else None
    h9 = y.get("sha256") if y else None
    return {
        "name": (x or y)["name"],
        "kind": kind,
        "addr_r7": x["addr"] if x else None,
        "size_r7": x["size"] if x else None,
        "addr_r9": y["addr"] if y else None,
        "size_r9": y["size"] if y else None,
        "dva": (y["addr"] - x["addr"]) if (x and y) else None,
        "dsize": (y["size"] - x["size"]) if (x and y) else None,
        "sim": round(structural(x, y), 4) if (x and y) else None,
        "sha256_r7": h7, "sha256_r9": h9,
        "sha_match": (h7 == h9) if (h7 is not None and h9 is not None) else None,
    }


def verdict(r: dict) -> str:
    if r["kind"] in ("added-r9", "unmatched-r7"):
        return r["kind"]  # not an aligned pair; label as-is
    # byte-true ground truth: when both sides carry a block sha256, it decides.
    if r["sha_match"] is True:
        return "same"
    if r["sha_match"] is False:
        return "changed"
    # legacy/Ghidra-export fallback (no per-function hashes)
    if r["dva"] == 0 and r["dsize"] == 0:
        return "same"
    if r["dsize"] == 0 and r["sim"] >= 0.99:
        return "moved-unchanged"
    return "changed"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Align rev7/rev9 function exports -> delta")
    ap.add_argument("--comp", required=True, help="component tag, e.g. tz")
    ap.add_argument("--r7", required=True, help="rev7 export json")
    ap.add_argument("--r9", required=True, help="rev9 export json")
    ap.add_argument("--out-json", required=True, help="machine delta json")
    ap.add_argument("--out-md", required=True, help="human report markdown")
    args = ap.parse_args(argv)

    img7, funcs7 = load(args.r7)
    img9, funcs9 = load(args.r9)
    rows = align(funcs7, funcs9)

    for r in rows:
        r["verdict"] = verdict(r)

    total = len(rows)
    changed = [r for r in rows if r["verdict"] == "changed"]
    moved = [r for r in rows if r["verdict"] == "moved-unchanged"]
    added = [r for r in rows if r["kind"] == "added-r9"]
    removed = [r for r in rows if r["kind"] == "unmatched-r7"]

    os.makedirs(Path(args.out_md).parent, exist_ok=True)
    os.makedirs(os.path.dirname(args.out_json) or ".", exist_ok=True)
    summary = {
        "comp": args.comp,
        "image_r7": img7, "image_r9": img9,
        "stats": {
            "total_funcs_r7": len(funcs7), "total_funcs_r9": len(funcs9),
            "aligned": total - len(added) - len(removed),
            "changed": len(changed), "moved_unchanged": len(moved),
            "added_r9": len(added), "removed/unmatched_r7": len(removed),
        },
        "rows": rows,
    }
    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1, ensure_ascii=False)

    # Human report skeleton (findings added per instructions §6 by analyst/AI)
    li = []
    li.append(f"# {args.comp} — rev7 vs rev9 (alignment report)")
    li.append("")
    li.append(f"- `r7`: {img7['file']} sha {img7.get('file','')} rev {img7.get('rev')}")
    li.append(f"- `r9`: {img9['file']} rev {img9.get('rev')}")
    li.append(f"- align: exact={sum(1 for r in rows if r['kind']=='exact-size-name')} "
              f"name-win={sum(1 for r in rows if r['kind']=='name-win')} "
              f"structural={sum(1 for r in rows if r['kind']=='structural')}")
    li.append(f"- stats: changed={len(changed)} moved={len(moved)} added_r9={len(added)} unmatched_r7={len(removed)}")
    li.append("")
    li.append("| function | kind | va_r7 | size_r7 | va_r9 | size_r9 | Δva | Δsize | sim | verdict |")
    li.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows[:200]:
        li.append(f"| {r['name']} | {r['kind']} | {r['addr_r7']} | {r['size_r7']} | "
                  f"{r['addr_r9']} | {r['size_r9']} | {r['dva']} | {r['dsize']} | {r['sim']} | {r['verdict']} |")
    li.append("")
    li.append("> Findings pending: add pseudo-code hypothesis + validation snippet per instructions §6 (4)–(5).")
    with open(args.out_md, "w", encoding="utf-8") as fh:
        fh.write("\n".join(li) + "\n")

    print(f"diff_functions: {total} funcs; changed={len(changed)} added={len(added)} unmatched={len(removed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())