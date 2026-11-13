#!/usr/bin/env python3
"""Self-test for diff_functions alignment (SOP-4 reproducibility).

Keeps synthetic fixtures inline so the aligner can be verified with no binaries
and no network. Run: python scripts/test/test_diff_functions.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from diff import diff_functions as df  # noqa: E402

R7 = {
    "image": {"file": "fixture-r7", "rev": "r7", "base": 0x400000},
    "functions": [
        {"name": "memcmp_digest", "addr": 0x401000, "size": 64, "blocks": 5,
         "mnemonics": {"ldr": 8, "cmp": 4, "mul": 1}, "calls": ["memcpy"]},
        {"name": "rpmb_rollback_check", "addr": 0x401080, "size": 120, "blocks": 9,
         "mnemonics": {"ldr": 14, "cmp": 6, "bl": 3}, "calls": ["rpmb_read", "memcmp_digest"]},
        {"name": "replaced_func", "addr": 0x4010F8, "size": 40, "blocks": 4,
         "mnemonics": {"add": 4, "ldr": 3}, "calls": []},
    ],
}

R9 = {
    "image": {"file": "fixture-r9", "rev": "r9", "base": 0x400000},
    "functions": [
        {"name": "memcmp_digest", "addr": 0x401000, "size": 64, "blocks": 5,
         "mnemonics": {"ldr": 8, "cmp": 4, "mul": 1}, "calls": ["memcpy"]},
        {"name": "rpmb_rollback_check", "addr": 0x401094, "size": 132, "blocks": 10,
         "mnemonics": {"ldr": 14, "cmp": 8, "bl": 3}, "calls": ["rpmb_read", "memcmp_digest"]},
        {"name": "new_verify_patch", "addr": 0x401118, "size": 96, "blocks": 7,
         "mnemonics": {"ldr": 10, "cmp": 5, "bl": 2}, "calls": ["memcmp_digest"]},
    ],
}


def main() -> int:
    failures = []

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        p7 = td / "r7.json"
        p9 = td / "r9.json"
        p9.write_text(json.dumps(R9), encoding="utf-8")
        p7.write_text(json.dumps(R7), encoding="utf-8")

        rows = df.align(R7["functions"], R9["functions"])
        by_name = {r["name"]: r for r in rows}
        for r in rows:
            r["verdict"] = df.verdict(r)

        expect = {
            "memcmp_digest": ("exact-size-name", "same"),
            "rpmb_rollback_check": ("name-win", "changed"),
            "replaced_func": ("unmatched-r7", "unmatched-r7"),
            "new_verify_patch": ("added-r9", "added-r9"),
        }
        for name, (kind, verdict) in expect.items():
            r = by_name.get(name)
            if r is None:
                failures.append(f"{name}: missing from aligned rows")
            elif (r["kind"], r["verdict"]) != (kind, verdict):
                failures.append(f"{name}: got {(r['kind'], r['verdict'])}, want {(kind, verdict)}")

        d_rbb = by_name["rpmb_rollback_check"]
        if (d_rbb["dsize"], d_rbb["dva"]) != (12, 20):
            failures.append(f"rpmb_rollback_check delta wrong: {d_rbb['dsize']=} {d_rbb['dva']=}")

        totals = {
            "same": sum(1 for r in rows if r["verdict"] == "same"),
            "changed": sum(1 for r in rows if r["verdict"] == "changed"),
            "added": sum(1 for r in rows if r["kind"] == "added-r9"),
            "unmatched": sum(1 for r in rows if r["kind"] == "unmatched-r7"),
        }
        if totals != {"same": 1, "changed": 1, "added": 1, "unmatched": 1}:
            failures.append(f"totals wrong: {totals}")

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        return 1
    print("OK — aligner self-test passed (same=1 changed=1 added=1 unmatched=1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())