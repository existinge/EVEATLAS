#!/usr/bin/env python3
"""whole_file_diff.py — localize differing byte spans between two firmware files.

Companion to the block-level alignment: the block export only covers executable
PT_LOAD segments, so a file whose sha256 differs may still have byte-identical
executable content (e.g. signature trailers, headers, non-exec segments).
This tool prints coarse differing spans so that distinction is explicit.

Usage:
    python scripts/diff/whole_file_diff.py A B [--span 0x1000]

stdout: file lengths, total differing bytes, and each differing span
(start, end, length) as hex, capped at SPAN_CAP spans.
"""
from __future__ import annotations

import argparse
from pathlib import Path

SPAN_CAP = 32


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("a", type=Path)
    ap.add_argument("b", type=Path)
    ap.add_argument("--span", type=lambda v: int(v, 0), default=0x1000,
                    help="coalesce differing bytes closer than this gap (default 0x1000)")
    args = ap.parse_args()

    A, B = args.a.read_bytes(), args.b.read_bytes()
    print(f"A {args.a}: {len(A)} bytes  sha256={__import__('hashlib').sha256(A).hexdigest()}")
    print(f"B {args.b}: {len(B)} bytes  sha256={__import__('hashlib').sha256(B).hexdigest()}")

    n = min(len(A), len(B))
    diff_bytes = sum(1 for i in range(n) if A[i] != B[i])
    diff_bytes += abs(len(A) - len(B))  # length delta counts as differing
    print(f"differing bytes (incl. length delta): {diff_bytes}")

    spans = []  # (start, stop)
    for i in range(n):
        if A[i] != B[i]:
            if spans and i - spans[-1][1] <= args.span:
                spans[-1] = (spans[-1][0], i + 1)
            else:
                spans.append((i, i + 1))
    if len(A) != len(B):
        if spans and (n - spans[-1][1]) <= args.span:
            spans[-1] = (spans[-1][0], max(len(A), len(B)))
        else:
            spans.append((n, max(len(A), len(B))))

    print(f"differing spans: {len(spans)}")
    for s, e in spans[:SPAN_CAP]:
        print(f"  0x{s:08x}-0x{e:08x}  len 0x{e - s:x} ({e - s} bytes)")
    if len(spans) > SPAN_CAP:
        print(f"  ... {len(spans) - SPAN_CAP} more spans suppressed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
