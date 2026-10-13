#!/usr/bin/env python3
"""Point-wise informative witness: quantity.lisp PredicateBit forms + domain bitness.

Axiom: D1 PredicateBit is never a bare Number 1/0.
  D1:1 = (010 (001 ()))          ; ATOM of empty
  D1:0 = (101 (001 (0)) (001 (1))) ; EQ of distinct quoted atoms

Also re-checks that every domain table key is exactly N bits (width = address).

Run:
    python3 scripts/test-quantity-predicate-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Forbidden: bare numeric PredicateBit carriers that caused "got 1" type failures
BARE_FALSE = re.compile(r"\(101\s+1\s+0\)")
BARE_TRUE  = re.compile(r"\(101\s+1\s+1\)")
# Allowed exact forms (must appear at least once after migration)
EXACT_FALSE = re.compile(r"\(101\s+\(001\s+\(0\)\)\s+\(001\s+\(1\)\)\)")
EXACT_TRUE  = re.compile(r"\(010\s+\(001\s+\(\)\)\)")

ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)


def check_quantity() -> list[str]:
    path = ROOT / "lib" / "quantity.lisp"
    errs: list[str] = []
    if not path.is_file():
        return [f"missing {path.relative_to(ROOT)}"]
    text = path.read_text(encoding="utf-8")
    if BARE_FALSE.search(text):
        errs.append("quantity.lisp: still contains bare (101 1 0) PredicateBit")
    if BARE_TRUE.search(text):
        errs.append("quantity.lisp: still contains bare (101 1 1) PredicateBit")
    if not EXACT_FALSE.search(text):
        errs.append("quantity.lisp: missing exact D1:0 form after migration")
    # true form may be used elsewhere; not required inside quantity
    return errs


def check_domains() -> list[str]:
    errs: list[str] = []
    for n in range(1, 11):
        path = ROOT / "lib" / "domains" / f"d{n}.lisp"
        if not path.is_file():
            errs.append(f"D{n}: missing")
            continue
        keys = ROW.findall(path.read_text(encoding="utf-8"))
        expect = 1 << n
        if len(keys) != expect:
            errs.append(f"D{n}: rows {len(keys)} != 2^{n}")
        bad = [k for k in keys if len(k) != n]
        if bad:
            errs.append(f"D{n}: key width {len(bad[0])} != {n}")
        if len(set(keys)) != len(keys):
            errs.append(f"D{n}: duplicate keys")
    return errs


def main() -> int:
    q_errs = check_quantity()
    d_errs = check_domains()
    all_e = q_errs + d_errs

    print("quantity PredicateBit: ", "PASS" if not q_errs else "FAIL")
    for e in q_errs:
        print(f"  {e}")
    print("domain exact-width:   ", "PASS" if not d_errs else "FAIL")
    for e in d_errs:
        print(f"  {e}")

    if all_e:
        print("QUANTITY-BITNESS: BLOCKED", file=sys.stderr)
        return 1
    print("QUANTITY-BITNESS: PASS — exact D1 forms + every domain key width = address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
