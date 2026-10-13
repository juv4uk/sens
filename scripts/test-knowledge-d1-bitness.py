#!/usr/bin/env python3
"""Point-wise informative witness: knowledge D1 + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/knowledge.lisp has no bare host truthiness in COND else (001 t)
  2. Exact D1:1 form (010 (001 ())) is present
  3. Key surface present (tell-knowledge, module-clauses-now, reason-in)
  4. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Run:
    python3 scripts/test-knowledge-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOW = ROOT / "lib" / "knowledge.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST_T = "(1110 (001 t)"
D1_TRUE = "(010 (001 ()))"
REQUIRED = (
    "tell-knowledge",
    "module-clauses-now",
    "reason-in",
    "*knowledge-journal*",
    "check-conflict",
)


def check_knowledge() -> list[str]:
    errs: list[str] = []
    if not KNOW.is_file():
        return [f"missing {KNOW.relative_to(ROOT)}"]
    text = KNOW.read_text(encoding="utf-8")
    if len(text) < 1000:
        errs.append(f"knowledge: file too small ({len(text)} bytes) — run restore-knowledge-d1.py")
    if HOST_T in text:
        errs.append("knowledge: host COND else (1110 (001 t) still present")
    if D1_TRUE not in text:
        errs.append("knowledge: exact D1:1 form (010 (001 ())) missing")
    for fn in REQUIRED:
        if fn not in text:
            errs.append(f"knowledge: required surface missing: {fn}")
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
    all_errs.extend(check_knowledge())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("KNOWLEDGE+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("KNOWLEDGE: PASS — no host COND t, exact D1, surface intact")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
