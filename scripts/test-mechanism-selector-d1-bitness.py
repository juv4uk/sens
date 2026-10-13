#!/usr/bin/env python3
"""Point-wise informative witness for mechanism-selector + domain bitness.

Axiom: binary key width IS the domain address.
Checks:
  1. lib/mechanism-selector.lisp has no duplicate consecutive EQ arms
     of the form ((101 X Y) ...) ((101 X Y) ...)
  2. No bare host truthiness tokens t / NIL as predicate carriers
  3. Fallback uses exact D1:1 form (010 (001 ()))
  4. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

This does not prove runtime callability. Run:

    python3 scripts/test-mechanism-selector-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEL = ROOT / "lib" / "mechanism-selector.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
DUP_EQ = re.compile(
    r"\(\s*\(101\s+[^)]+\)\s+[^)]*\)\s*\(\s*\(101\s+[^)]+\)\s+[^)]*\)",
    re.MULTILINE,
)
HOST_T = re.compile(r"\b(t|NIL)\b")
D1_TRUE = "(010 (001 ()))"


def check_selector() -> list[str]:
    errs: list[str] = []
    if not SEL.is_file():
        return [f"missing {SEL.relative_to(ROOT)}"]
    text = SEL.read_text(encoding="utf-8")
    if DUP_EQ.search(text):
        errs.append("mechanism-selector: consecutive duplicate EQ arms still present")
    if HOST_T.search(text):
        errs.append("mechanism-selector: host truthiness token (t/NIL) found")
    if D1_TRUE not in text:
        errs.append("mechanism-selector: exact D1:1 form (010 (001 ())) missing")
    # count binary call-heads roughly
    heads = re.findall(r"\(([01]{1,10})\b", text)
    if not heads:
        errs.append("mechanism-selector: no binary call-heads found")
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
    all_errs.extend(check_selector())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("SELECTOR+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("SELECTOR: PASS — no duplicate EQ, exact D1 forms")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
