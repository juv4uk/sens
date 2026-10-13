#!/usr/bin/env python3
"""Point-wise informative witness: understand COND + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/understand.lisp has no bare host truthiness (t / T / NIL)
  2. Exact D1:1 form (010 (001 ())) is present as fallback
  3. Key surface present (understand / understand-query / strip-article)
  4. Pairs with narrate (structure<->text bridge)
  5. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Does not prove runtime callability or T5 physical execution. Run:

    python3 scripts/test-understand-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UND = ROOT / "lib" / "understand.lisp"
NAR = ROOT / "lib" / "narrate.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|T|NIL)(?!\w)")
D1_TRUE = "(010 (001 ()))"
REQUIRED = (
    "strip-article",
    "understand-is",
    "understand-relation",
    "understand-universal",
    "understand",
    "understand-query",
    "understand-query-is",
    "understand-query-relation",
)


def check_understand() -> list[str]:
    errs: list[str] = []
    if not UND.is_file():
        return [f"missing {UND.relative_to(ROOT)}"]
    text = UND.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"understand: host truthiness {m.group()!r} at offset {m.start()}")
    if D1_TRUE not in text:
        errs.append("understand: exact D1:1 form (010 (001 ())) missing")
    for fn in REQUIRED:
        if fn not in text:
            errs.append(f"understand: required surface missing: {fn}")
    # narrate pair exists (structure <-> text bridge)
    if not NAR.is_file():
        errs.append("understand: pair lib/narrate.lisp missing")
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
    all_errs.extend(check_understand())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("UNDERSTAND+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("UNDERSTAND: PASS — two-field COND, exact D1, narrate pair intact")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
