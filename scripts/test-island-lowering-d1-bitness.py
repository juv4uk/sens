#!/usr/bin/env python3
"""Point-wise informative witness: island-lowering COND + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/island-lowering.lisp has no bare host truthiness (t / NIL)
  2. Exact D1:1 form (010 (001 ())) is present
  3. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Does not prove runtime callability or T5 physical execution. Run:

    python3 scripts/test-island-lowering-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISLAND = ROOT / "lib" / "island-lowering.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|NIL)(?!\w)")
D1_TRUE = "(010 (001 ()))"


def check_island() -> list[str]:
    errs: list[str] = []
    if not ISLAND.is_file():
        return [f"missing {ISLAND.relative_to(ROOT)}"]
    text = ISLAND.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"island-lowering: host truthiness {m.group()!r} at offset {m.start()}")
    if D1_TRUE not in text:
        errs.append("island-lowering: exact D1:1 form (010 (001 ())) missing")
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
    all_errs.extend(check_island())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("ISLAND+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("ISLAND-LOWERING: PASS — no host truthiness, exact D1 forms")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
