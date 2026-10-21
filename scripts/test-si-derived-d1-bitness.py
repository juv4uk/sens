#!/usr/bin/env python3
"""Point-wise informative witness: si-derived exact composition + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/si-derived.lisp has no bare host truthiness (t / T / NIL)
  2. No decimal approximation literals (no floating-point forms)
  3. Reuses SI defining constants and exact multiply/divide surface
  4. All seven derived constants present
  5. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Run:
    python3 scripts/test-si-derived-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SI_D = ROOT / "lib" / "si-derived.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|T|NIL)(?!\w)")
FLOAT = re.compile(r"\d+\.\d+")
REQUIRED = (
    "сі:стала-фарадея",
    "сі:молярна-газова-стала",
    "сі:стала-джозефсона",
    "сі:стала-фон-клітцинга",
    "сі:квант-магнітного-потоку",
    "сі:квант-електричної-провідності",
    "сі:молярна-стала-планка",
    "сі:стала-авогадро",
    "сі:елементарний-заряд",
    "сі:стала-больцмана",
    "сі:стала-планка",
)


def check_si_derived() -> list[str]:
    errs: list[str] = []
    if not SI_D.is_file():
        return [f"missing {SI_D.relative_to(ROOT)}"]
    text = SI_D.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"si-derived: host truthiness {m.group()!r} at offset {m.start()}")
    for m in FLOAT.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"si-derived: decimal approximation {m.group()!r}")
    for fn in REQUIRED:
        if fn not in text:
            errs.append(f"si-derived: required surface missing: {fn}")
    # Справжні числові токени у виконуваних формах не можна
    # підміняти бездоменним десятковим значенням. Коментарі не є кодом.
    executable = "\\n".join(
        line.split(";", 1)[0] for line in text.splitlines()
    )
    if re.search(r"(?<![\\w:])2(?=[\\s)])", executable):
        errs.append("si-derived: RAW_NUMERIC_OPERAND_D24: знайдено сирий множник 2")
    expected_double = (
        "(визначити сі:подвоєний-заряд\\n"
        "  (додати сі:елементарний-заряд сі:елементарний-заряд))"
    )
    if expected_double not in executable:
        errs.append("si-derived: точне додавання заряду відсутнє")
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
    all_errs.extend(check_si_derived())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("SI-DERIVED+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("SI-DERIVED: PASS — exact rational composition, SI surface reuse")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
