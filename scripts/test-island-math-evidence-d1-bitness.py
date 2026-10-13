#!/usr/bin/env python3
"""Point-wise informative witness: island-math-evidence SID8 + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/island-math-evidence.lisp has no bare host truthiness (t / T / NIL)
  2. Exact SID 00001100 (8-bit) is present as identity coordinate
  3. Authority / mechanism-source surface paths present
  4. Four executor witnesses share the same SID without a fifth invent
  5. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Run:
    python3 scripts/test-island-math-evidence-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IME = ROOT / "lib" / "island-math-evidence.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|T|NIL)(?!\w)")
SID8 = "00001100"
REQUIRED = (
    "island-math-evidence/1",
    "lib/surface/semantic-registry.lisp",
    "lib/function-table-mechanisms.lisp",
    "common-lisp",
    "prolog",
    "clips",
    "datalog",
    SID8,
)


def check_ime() -> list[str]:
    errs: list[str] = []
    if not IME.is_file():
        return [f"missing {IME.relative_to(ROOT)}"]
    text = IME.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"island-math-evidence: host truthiness {m.group()!r}")
    if SID8 not in text:
        errs.append(f"island-math-evidence: exact SID8 {SID8} missing")
    # SID must be exactly 8 bits in row form
    sid_rows = re.findall(r"\((\d{8})\s+(common-lisp|prolog|clips|datalog)", text)
    if len(sid_rows) != 4:
        errs.append(f"island-math-evidence: expected 4 executor rows, got {len(sid_rows)}")
    for sid, _ex in sid_rows:
        if sid != SID8:
            errs.append(f"island-math-evidence: non-canonical SID {sid}")
        if len(sid) != 8:
            errs.append(f"island-math-evidence: SID width {len(sid)} != 8")
    for fn in REQUIRED:
        if fn not in text:
            errs.append(f"island-math-evidence: required surface missing: {fn}")
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
    all_errs.extend(check_ime())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("ISLAND-MATH-EVIDENCE+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("ISLAND-MATH-EVIDENCE: PASS — exact SID8, 4 witnesses, authority surface")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
