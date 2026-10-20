#!/usr/bin/env python3
"""Легка перевірка українського добору механізмів та адрес доменів Д1–Д10.

Перевіряються лише визначення Lisp і точні координати таблиць.
Цей скрипт не обчислює семантику СЕНС, не запускає важких ранерів.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEL = ROOT / "lib" / "mechanism-selector.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
DUP_EQ = re.compile(
    r"\(\s*\(101\s+[^)]+\)\s+[^)]*\)\s*\(\s*\(101\s+[^)]+\)\s+[^)]*\)",
    re.MULTILINE,
)
HOST_T = re.compile(r"\b(t|NIL)\b")
UKRAINIAN_SELECTOR = "(визначити вибрати-механізм"


def check_selector() -> list[str]:
    errs: list[str] = []
    if not SEL.is_file():
        return [f"missing {SEL.relative_to(ROOT)}"]
    text = SEL.read_text(encoding="utf-8")
    if DUP_EQ.search(text):
        errs.append("mechanism-selector: consecutive duplicate EQ arms still present")
    if HOST_T.search(text):
        errs.append("mechanism-selector: host truthiness token (t/NIL) found")
    if UKRAINIAN_SELECTOR not in text:
        errs.append("немає українського визначення вибрати-механізм")
    if "(третє маршрут)" not in text:
        errs.append("відсутній точний селектор Д5 третього поля")
    if re.search(r"(?m)^\(визначити\s+mechanism-", text):
        errs.append("виявлено застарілі англомовні визначення")
    if re.search(r"\(([01]{3,10})(?=[\s(])", text):
        errs.append("викличні голови не мають української проєкції")
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
    all_errs.extend(check_selector())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("SELECTOR+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("ДОБІР: українська поверхня підтверджена статично; виконання СЕНС не перевірено")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
