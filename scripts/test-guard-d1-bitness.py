#!/usr/bin/env python3
"""Point-wise informative witness: guard PredicateBit + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/guard.lisp has no bare host truthiness (t / NIL)
  2. Current executable D1 values come from Ukrainian ATOM(QUOTE NIL/non-NIL)
  3. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Does not prove runtime callability or T5 physical execution. Run:

    python3 scripts/test-guard-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "lib" / "guard.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|NIL)(?!\w)")
D1_TRUE = "(атом? (як-є ()))"
D1_FALSE = "(атом? (як-є (())))"


def check_guard() -> list[str]:
    errs: list[str] = []
    if not GUARD.is_file():
        return [f"missing {GUARD.relative_to(ROOT)}"]
    text = GUARD.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"guard: host truthiness {m.group()!r} at offset {m.start()}")
    active = "\n".join(line for line in text.splitlines()
                       if not line.lstrip().startswith(";"))
    if D1_TRUE not in active or D1_FALSE not in active:
        errs.append("guard: executable D1 true/false predicate witnesses missing")
    if re.search(r"(?<![\w-])(?:так|ні)(?![\w-])", active):
        errs.append("guard: unbound D1 truth name in executable Lisp")
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
    all_errs.extend(check_guard())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("GUARD+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("GUARD: PASS — no host truthiness, exact D1 forms")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
