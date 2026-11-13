#!/usr/bin/env python3
"""Provenance: hash-based chain of custody for firmware artifacts (SOP-1).

Records sha256 (and optionally sha1) + size + mtime for every file under a tree,
so binary artifacts can stay git-ignored while their digests remain committed.

Usage:
  python scripts/provenance.py hash-dir firmware/raw/r7 --out firmware/manifest/r7-manifest.json
  python scripts/provenance.py tree-compare firmware/extracted/r7 firmware/extracted/r9

Python 3.8+; stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


def _hash_bytes(path: Path, digest: str = "sha256", buf: int = 1 << 20) -> str:
    h = hashlib.new(digest)
    with path.open("rb") as fh:
        while chunk := fh.read(buf):
            h.update(chunk)
    return h.hexdigest()


def hash_dir(root: Path, out: Path) -> dict:
    files = sorted(p for p in root.rglob("*") if p.is_file())
    entries = []
    for p in files:
        st = p.stat()
        entries.append(
            {
                "rel": p.relative_to(root).as_posix(),
                "sha256": _hash_bytes(p, "sha256"),
                "sha1": _hash_bytes(p, "sha1"),
                "size": st.st_size,
                "mtime": int(st.st_mtime),
            }
        )
    manifest = {"root": root.as_posix(), "entries": entries, "count": len(entries)}
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def tree_compare(a: Path, b: Path, ignore: str = "sha1") -> int:
    """Compare the two manifest-like trees (same names => same sha256)."""
    from hashlib import sha256

    def snapshot(root: Path) -> dict:
        snap = {}
        for p in sorted(root.rglob("*")):
            if p.is_file():
                rel = p.relative_to(root).as_posix()
                snap[rel] = sha256(p.read_bytes()).hexdigest()
        return snap

    sa, sb = snapshot(a), snapshot(b)
    names = sorted(set(sa) | set(sb))
    missing = ["?" if sa.get(n) == sb.get(n) else "! %s" % n for n in names if sa.get(n) != sb.get(n)]
    real_diff = [n for n in names if (sa.get(n) is not None) != (sb.get(n) is not None) or sa.get(n) != sb.get(n)]
    for n in real_diff:
        print(f"DIFF {n}: {sa.get(n, '<missing>')} vs {sb.get(n, '<missing>')}")
    print(f"{len(names)} files compared; {len(real_diff)} differences.")
    return 1 if real_diff else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Firmware provenance chain-of-custody")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_h = sub.add_parser("hash-dir", help="hash every file under a tree into a JSON manifest")
    p_h.add_argument("root", type=Path)
    p_h.add_argument("--out", type=Path, default=None)

    p_c = sub.add_parser("tree-compare", help="compare two extracted trees (r7 vs r9)")
    p_c.add_argument("a", type=Path)
    p_c.add_argument("b", type=Path)

    args = ap.parse_args(argv)
    if args.cmd == "hash-dir":
        m = hash_dir(args.root, args.out)
        print(f"manifested {m['count']} files under {m['root']}")
        return 0
    if args.cmd == "tree-compare":
        return tree_compare(args.a, args.b)
    return 2


if __name__ == "__main__":
    sys.exit(main())