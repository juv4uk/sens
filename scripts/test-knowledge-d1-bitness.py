#!/usr/bin/env python3
"""Point-wise informative witness: knowledge D1 + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/knowledge.lisp size >= 1000 and no PLACEHOLDER
  2. No host COND else (1110 (001 t)
  3. Current D1 predicates without historical raw literals
  4. Current Ukrainian D1 projection in the domain table
  4. Первинна українська проєкція: повідомити-знання, модуль-клаузи-зараз, міркувати-у
  5. D1–D10 exact-width tables

Run:
    python3 scripts/assemble_knowledge.py   # if needed
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
D1_TRUE_UKR = "(1 (ук так) (укр так)"
D1_GUARDS = ("(за-умовою", "((хибне?", "(порожній?")
REQUIRED = (
    "повідомити-знання",
    "модуль-клаузи-зараз",
    "міркувати-у",
    "журнал-знань",
    "перевірити-конфлікт?",
)


def check_knowledge() -> list[str]:
    errs: list[str] = []
    if not KNOW.is_file():
        return [f"missing {KNOW.relative_to(ROOT)}"]
    text = KNOW.read_text(encoding="utf-8")
    if len(text) < 1000:
        errs.append(
            f"knowledge: truncated ({len(text)} bytes) — "
            "run: python3 scripts/assemble_knowledge.py"
        )
    if "PLACEHOLDER" in text:
        errs.append("knowledge: PLACEHOLDER present — run assemble_knowledge.py")
    if HOST_T in text:
        errs.append("knowledge: host COND else (1110 (001 t) still present")
    for guard in D1_GUARDS:
        if guard not in text:
            errs.append(f"knowledge: current D1 conditional/predicate missing: {guard}")
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
    d1_path = ROOT / "lib" / "domains" / "d1.lisp"
    if not d1_path.is_file():
        all_errs.append("D1: missing current domain table")
    elif D1_TRUE_UKR not in d1_path.read_text(encoding="utf-8"):
        all_errs.append("D1:1 current ук/укр projection так missing")
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("KNOWLEDGE+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("KNOWLEDGE: PASS — full file, no host COND t, Ukrainian D1 projection, surface intact")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
