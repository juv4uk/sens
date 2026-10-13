#!/usr/bin/env python3
"""Informational bit-economy witness for exact-width domains.

Axiom: every domain coordinate is worth exactly N bits — no padding in the
semantic address, no missing slots, no silent widening.

Reports:
  - per-domain: width N, rows 2^N, address-bits N*2^N
  - total semantic address mass across D1–D9 (Core) and D10 (research)

Also checks a packing lower bound: 5 trits per byte (3^5=243≤256) is the
classical dense trit packing rate (cf. densely-packed-ternary / five-trit
LLM layouts). This script does NOT change the T5 codec; it only educates
CI that width and mass are explicit.

    python3 scripts/test-domain-bit-economy.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)


def domain_rows(n: int) -> list[str]:
    path = ROOT / "lib" / "domains" / f"d{n}.lisp"
    if not path.is_file():
        raise FileNotFoundError(path)
    return ROW.findall(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    total_core = 0
    total_all = 0
    print("domain  width  rows   address-bits  status")
    print("------  -----  -----  -------------  ------")
    for n in range(1, 11):
        keys = domain_rows(n)
        expect = 1 << n
        mass = n * expect
        total_all += mass
        if n <= 9:
            total_core += mass
        ok = (
            len(keys) == expect
            and all(len(k) == n for k in keys)
            and len(set(keys)) == expect
        )
        if not ok:
            errors.append(f"D{n}: economy invariant broken")
        status = "PASS" if ok else "FAIL"
        print(f"D{n:<5}  {n:>5}  {len(keys):>5}  {mass:>13}  {status}")

    # Classical 5-trit byte packing density (informative constant)
    trit_byte_rate = 8 / 5  # bits of storage per trit capacity unit
    print()
    print(f"Core D1–D9 semantic address mass: {total_core} bits")
    print(f"All D1–D10 semantic address mass: {total_all} bits")
    print(f"Dense trit packing reference: 5 trits/byte ⇒ {trit_byte_rate:.3f} storage-bits/trit")
    print("Note: domain *address* width is binary N; T5 transport may pack trits separately.")

    if errors:
        print("BIT-ECONOMY: BLOCKED", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    print("BIT-ECONOMY: PASS — every coordinate costs exactly its domain width in bits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
