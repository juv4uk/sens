#!/usr/bin/env python3
"""Point-wise informative witness: world D1 + domain bitness.

Axiom: width = address = identity.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "lib" / "world.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
# Чинні виконавчі назви є українськими; протокольні дані недоторканні.
REQUIRED_PRIMARY = (
    "(визначити світ-модуль-відомий?",
    "(визначити внутрішній-світ-модуль-відсутній?",
    "(визначити світ-повідомити",
    "(визначити світ-відкликати",
)
LEGACY_BINDING = "(визначити world-module-missing?"


def check_world() -> list[str]:
    errs: list[str] = []
    if not WORLD.is_file():
        return [f"missing {WORLD.relative_to(ROOT)}"]
    text = WORLD.read_text(encoding="utf-8")
    if len(text) < 1000:
        errs.append(f"world: truncated ({len(text)} bytes)")
    for spelling in REQUIRED_PRIMARY:
        if spelling not in text:
            errs.append("world: втрачено українське визначення " + spelling)
    if LEGACY_BINDING in text:
        errs.append("world: лишився старий англомовний дубль")
    if "(за-умовою" not in text or "(хибне?" not in text:
        errs.append("world: немає чинних умов та D1 заперечення")
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
        errs.append(f"D{n}: key width mismatch")
    expected_keys = {format(number, f"0{n}b") for number in range(expect)}
    if set(keys) != expected_keys:
        errs.append(f"D{n}: неточна або повторена доменна адреса")
    return errs


def main() -> int:
    errs: list[str] = []
    errs.extend(check_world())
    for n in range(1, 11):
        errs.extend(check_domain(n))
    if errs:
        print("WORLD+BITNESS: BLOCKED", file=sys.stderr)
        for e in errs:
            print(f"  {e}", file=sys.stderr)
        return 1
    print("WORLD: українську D1-поверхню підтверджено статично; виконання засвідчує SENS")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit")
    print("BITNESS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
