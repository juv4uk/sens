#!/usr/bin/env python3
"""Статична перевірка джерела уніфікації й точної ширини доменів.

Семантичний висновок належить виключно СЕНС, а не цьому скрипту.
Адресу об'єкта визначають домен і точне двійкове слово.

Перевіряємо: відсутність істинності хоста, старих викличних голів
і старого англомовного псевдоніма; наявність української межі
спостереження та повноту таблиць Д1–Д10.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UO = ROOT / "lib" / "unify-observe.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|T|NIL)(?!\w)")
REQUIRED = (
    "(визначити спостерігати-уніфікацію",
    "(визначити уніфікація-спостереження-стан",
    "(уніфікувати ",
    "(як-є unification-failure)",
    "(як-є unified)",
)


def check_uo() -> list[str]:
    errs: list[str] = []
    if not UO.is_file():
        return [f"missing {UO.relative_to(ROOT)}"]
    text = UO.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"unify-observe: host truthiness {m.group()!r} at offset {m.start()}")
    executable = text[text.find("(0011 "):]
    if re.search(r"\((?:001000|101010000)(?=\s|\()", executable):
        errs.append("unify-observe: historical D6/D9 executable head present")
    if "(визначити unify-observe " in text:
        errs.append("unify-observe: повернувся застарілий англійський псевдонім")
    for fn in REQUIRED:
        if fn not in text:
            errs.append(f"unify-observe: required surface missing: {fn}")
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
    all_errs.extend(check_uo())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("UNIFY-OBSERVE+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("UNIFY-OBSERVE: SOURCE PASS — no host truthiness or legacy D6/D9 executable head; semantics not asserted")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
