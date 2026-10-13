#!/usr/bin/env python3
"""Point-wise informative witness: content-store surface + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/content-store.lisp has no bare host truthiness (t / T / NIL)
  2. Reuses persistent-map Ukrainian aliases and world/knowledge addresses
  3. Key content-store surface present
  4. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Run:
    python3 scripts/test-content-store-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CS = ROOT / "lib" / "content-store.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|T|NIL)(?!\w)")
REQUIRED = (
    "empty-content-store",
    "content-store-put",
    "content-store-get",
    "content-store-contains?",
    "content-store-put-world",
    "content-store-size",
    "map-empty",
    "внутрішня-мапа-вставити",
    "внутрішня-мапа-отримати",
    "внутрішня-мапа-містить",
    "knowledge-content-address",
    "world-content-address",
)


def check_cs() -> list[str]:
    errs: list[str] = []
    if not CS.is_file():
        return [f"missing {CS.relative_to(ROOT)}"]
    text = CS.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";") or line.lstrip().startswith(";;"):
            continue
        errs.append(f"content-store: host truthiness {m.group()!r} at offset {m.start()}")
    for fn in REQUIRED:
        if fn not in text:
            errs.append(f"content-store: required surface missing: {fn}")
    return errs


def check_domain(n: int) -> list[str]:
    path = ROOT / "lib" / "domains" / f"d{n}.lisp"
    errs: list[str] = []
    if not path.is_file():
        return [f"D{n}: missing"]
    keys = ROW.findall(path.read_text(encoding="utf-8"))
    expect = 1 << n
    if len(keys) != expect:
        errs.append(f"D{n}: expected {expect} rows, got {len(keys)}")
    bad = [k for k in keys if len(k) != n]
    if bad:
        errs.append(f"D{n}: key width {len(bad[0])} != {n}")
    if len(set(keys)) != len(keys):
        errs.append(f"D{n}: duplicate coordinates")
    return errs


def main() -> int:
    all_errs: list[str] = []
    all_errs.extend(check_cs())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("CONTENT-STORE+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("CONTENT-STORE: PASS — pure composition over D1 map + world addresses")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
