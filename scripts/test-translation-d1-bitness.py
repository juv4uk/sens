#!/usr/bin/env python3
"""Point-wise informative witness: translation PredicateBit + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/translation.lisp has no bare host truthiness (t / T / NIL)
  2. D1:YES is the ratified exact 1-bit українська projection «так»
  3. Reuses knowledge validators (knowledge-proper-list?, knowledge-clause-valid?)
  4. Key translation surface present
  5. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Does not prove runtime callability or T5 physical execution. Run:

    python3 scripts/test-translation-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANS = ROOT / "lib" / "translation.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|T|NIL)(?!\w)")
D1_TRUE = "(1 (ук так) (укр так)"
REQUIRED = (
    "статус-запису-перекладу-коректний?",
    "вид-кандидата-перекладу-коректний?",
    "структура-обгортки-перекладу-коректна?",
    "переклад-перевірка",
    "переклад-допустимий?",
    "правильно-структурований-список-знань?",
    "клауза-бази-знань-коректна?",
    "ціль-бази-знань-коректна?",
    "рішення-на-основі-огляду-перекладу-й-поради",
)


def check_translation() -> list[str]:
    errs: list[str] = []
    if not TRANS.is_file():
        return [f"missing {TRANS.relative_to(ROOT)}"]
    text = TRANS.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"translation: host truthiness {m.group()!r} at offset {m.start()}")
    d1_source = (ROOT / "lib" / "domains" / "d1.lisp").read_text(encoding="utf-8")
    if D1_TRUE not in d1_source or "так" not in text:
        errs.append("translation: D1:YES exact 1-bit Ukrainian projection missing")
    if "#d1:" in text:
        errs.append("translation: forbidden historical textual D1 literal")
    for fn in REQUIRED:
        if fn not in text:
            errs.append(f"translation: required surface missing: {fn}")
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
    all_errs.extend(check_translation())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("TRANSLATION+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("TRANSLATION: PASS — no host truthiness, exact D1, knowledge reuse")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
