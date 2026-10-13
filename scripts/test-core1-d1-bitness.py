#!/usr/bin/env python3
"""Point-wise informative witness: core1 PredicateBit + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/core1.lisp has no bare host truthiness (T / NIL as carriers)
  2. Exact D1:1 form (010 (001 ())) is present
  3. C1-ADMITTED-SID-VALUEP has no duplicate SID arms
  4. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Does not prove runtime callability or T5 physical execution. Run:

    python3 scripts/test-core1-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE1 = ROOT / "lib" / "core1.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
# Bare T or NIL as atoms (not inside longer words)
HOST = re.compile(r"(?<!\w)(T|NIL)(?!\w)")
D1_TRUE = "(010 (001 ()))"
SID_ARM = re.compile(r"\(101\s+VALUE\s+([01]+)\)")


def check_core1() -> list[str]:
    errs: list[str] = []
    if not CORE1.is_file():
        return [f"missing {CORE1.relative_to(ROOT)}"]
    text = CORE1.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"core1: host truthiness {m.group()!r} at offset {m.start()}")
    if D1_TRUE not in text:
        errs.append("core1: exact D1:1 form (010 (001 ())) missing")
    # duplicate admitted SID arms
    sids = SID_ARM.findall(text)
    seen = set()
    for s in sids:
        if s in seen:
            errs.append(f"core1: duplicate admitted SID arm {s}")
        seen.add(s)
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
    all_errs.extend(check_core1())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("CORE1+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("CORE1: PASS — no host T/NIL, exact D1 forms, unique SIDs")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
