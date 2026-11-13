#!/usr/bin/env python3
"""Compare r7 vs r9 BL module images (decompressed + lz4) and materialize diff JSON."""
import hashlib
import json
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()


def module_snapshot(rev, subroot="BL"):
    d = os.path.join(ROOT, "firmware", "extracted", rev, subroot)
    snap = {}
    for f in sorted(os.listdir(d)):
        full = os.path.join(d, f)
        if not os.path.isfile(full):
            continue
        with open(full, "rb") as fh:
            snap[f] = {"size": os.path.getsize(full), "sha256": hashlib.sha256(fh.read()).hexdigest()}
    return snap


def compare(rev_a, rev_b, which):
    sa, sb = module_snapshot(rev_a), module_snapshot(rev_b)
    diff = []
    for name in sorted(set(sa) | set(sb)):
        a, b = sa.get(name), sb.get(name)
        if a is None:
            diff.append({"name": name, "status": "absent-in-" + rev_a, "b": b})
        elif b is None:
            diff.append({"name": name, "status": "absent-in-" + rev_b, "a": a})
        elif a["sha256"] != b["sha256"]:
            diff.append({"name": name, "status": "content-differs", "a": a, "b": b})
    identical = [n for n in sorted(set(sa) & set(sb)) if sa[n]["sha256"] == sb[n]["sha256"]]
    out = {
        "which": which,
        "rev_a": rev_a,
        "rev_b": rev_b,
        "files_a": len(sa),
        "files_b": len(sb),
        "identical": identical,
        "differing": diff,
    }
    return out


def main():
    os.makedirs(os.path.join(ROOT, "analysis", "01-source"), exist_ok=True)
    for which, sub in (("decompressed-modules", "BL"),):
        result = compare("r7", "r9", which)
        outpath = os.path.join(ROOT, "analysis", "01-source", "bl-r7-vs-r9-diff.json")
        with open(outpath, "w") as jf:
            json.dump(result, jf, indent=2)
        print("%s: %d identical, %d differing" % (which, len(result["identical"]), len(result["differing"])))
        for d_ in result["differing"]:
            print("  DIFF %s: %s %d -> %s %d" % (
                d_["name"],
                d_.get("a", {}) and result["rev_a"], d_.get("a", {}).get("size", 0),
                d_.get("b", {}) and result["rev_b"], d_.get("b", {}).get("size", 0),
            ))
        print("IDENTICAL:", ", ".join(result["identical"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())