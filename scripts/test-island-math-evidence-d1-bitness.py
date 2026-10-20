#!/usr/bin/env python3
"""Перевірка перенесення історичного SID8 PLUS до точної D5 української проєкції.

Аксіома: старий SID8 і чинний D8 з однаковими бітами — різні сутності.
Checks:
  1. lib/island-math-evidence.lisp has no bare host truthiness (t / T / NIL)
  2. Сучасний оператор додавання перевіряється за ратифікованою D5:01010 додати
  3. Authority / mechanism-source surface paths present
  4. Чотири executor-свідки і чотири механізми мають правильну назву додати
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
UKR_HEAD = "додати"
MECHANISMS = ROOT / "lib" / "function-table-mechanisms.lisp"
REQUIRED = (
    "island-math-evidence/1",
    "lib/surface/semantic-registry.lisp",
    "lib/function-table-mechanisms.lisp",
    "common-lisp",
    "prolog",
    "clips",
    "datalog",
    UKR_HEAD,
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
    # Перевіряємо тільки чинний ратифікований D5; історія сід8 лишається в Git.
    d5 = ROOT / "lib" / "domains" / "d5.lisp"
    if not d5.is_file() or not re.search(
        r"^\s*\(01010\s+\(ук [^)]*\)\s+\(укр додати\)",
        d5.read_text(encoding="utf-8"), re.MULTILINE
    ):
        errs.append("island-math-evidence: D5:01010 Ukrainian authority missing")

    islands = {"common-lisp", "prolog", "clips", "datalog"}
    witnessed = re.findall(
        r"^\s*\(([^()\s]+)\s+(common-lisp|prolog|clips|datalog)\s+execution-witness\b",
        text, re.MULTILINE
    )
    expected = {(UKR_HEAD, name) for name in islands}
    if len(witnessed) != 4 or set(witnessed) != expected:
        errs.append(f"island-math-evidence: D5 add witnesses mismatch: {witnessed!r}")
    if not MECHANISMS.is_file():
        errs.append("island-math-evidence: mechanism source missing")
    else:
        mechanisms = re.findall(
            r"^\s*\(([^()\s]+)\s+(common-lisp|prolog|clips|datalog)\s+bounded-exact-add\)",
            MECHANISMS.read_text(encoding="utf-8"), re.MULTILINE
        )
        if len(mechanisms) != 4 or set(mechanisms) != expected:
            errs.append(f"island-math-evidence: D5 add mechanisms mismatch: {mechanisms!r}")
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
        print("ISLAND-MATH-EVIDENCE+BITNESS: FAIL", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("ISLAND-MATH-EVIDENCE: PASS — D5:01010 додати; 4 witness/mechanism routes")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
