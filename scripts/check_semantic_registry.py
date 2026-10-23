#!/usr/bin/env python3
"""Лексичний аудит ратифікованих таблиць D1–D10, НЕ виконавець SENS.

Влада: (домен, біти) та колонка «укр» у lib/domains/dN.lisp.
Справжнє виконання й T5M-оберненість перевіряє окремий SENS/Zig гейт.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "lib/surface/semantic-registry.lisp"
API = ROOT / "lib/surface/semantic-registry-api.lisp"
SURFACES = ("ук", "укр", "san", "en", "LISP", "sym")


def tokens(source: str) -> list[str]:
    """Токени Lisp: крапка/коментарі — дані лише поза quoted string."""
    out: list[str] = []
    i = 0
    while i < len(source):
        c = source[i]
        if c.isspace():
            i += 1
        elif c == ";":
            end = source.find("\n", i)
            i = len(source) if end == -1 else end + 1
        elif c in "()":
            out.append(c)
            i += 1
        elif c == '"':
            start = i
            i += 1
            while i < len(source):
                if source[i] == "\\":
                    i += 2
                elif source[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise ValueError("незакритий текстовий рядок у таблиці")
            out.append(source[start:i])
        else:
            start = i
            while i < len(source) and not source[i].isspace() and source[i] not in "();":
                i += 1
            out.append(source[start:i])
    return out


def parse_all(items: list[str]) -> list:
    position = 0

    def one():
        nonlocal position
        if position >= len(items):
            raise ValueError("таблиця обірвалася посеред форми")
        token = items[position]
        position += 1
        if token == ")":
            raise ValueError("неочікувана закривальна дужка")
        if token != "(":
            return token
        result = []
        while position < len(items) and items[position] != ")":
            result.append(one())
        if position >= len(items):
            raise ValueError("незакритий список")
        position += 1
        return result

    roots = []
    while position < len(items):
        roots.append(one())
    return roots


def check(root, width: int) -> tuple[int, set[str], int]:
    """Перевірка таблиці рівно одного домену. Без запуску Lisp."""
    if not isinstance(width, int) or width not in range(1, 11):
        raise ValueError("допустимі ширини канону: D1–D10")
    if not isinstance(root, list) or not root or root[0] != "domain-table-1":
        raise ValueError(f"D{width}: очікується (domain-table-1 ...), не стара SID8-таблиця")
    rows = root[1:]
    expected = 1 << width
    if len(rows) != expected:
        raise ValueError(f"D{width}: очікується {expected} резидентів, отримано {len(rows)}")
    namespaces: set[str] = set()
    symbols = 0
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != 7:
            raise ValueError(f"D{width}#{index}: очікується слово і шість проєкцій")
        bits = row[0]
        if not isinstance(bits, str) or not re.fullmatch("[01]{" + str(width) + "}", bits):
            raise ValueError(f"D{width}#{index}: чужа ширина або не двійкове слово: {bits!r}")
        if bits != format(index, f"0{width}b"):
            raise ValueError(f"D{width}#{index}: дубль, пропуск або перестановка: {bits!r}")
        for column, field in zip(SURFACES, row[1:]):
            if not isinstance(field, list) or len(field) != 2 or field[0] != column:
                raise ValueError(f"D{width}:{bits}: відсутня або переставлена колонка {column}")
            if field[1] != [] and not isinstance(field[1], str):
                raise ValueError(f"D{width}:{bits}/{column}: значення має бути атомом, рядком або ()")
            namespaces.add(column)
        symbols += int(row[-1][1] != [])
        if width == 7 and row[5][1] != []:
            raise ValueError(f"D7:{bits}: клавіатурні символи не можуть визначати Lisp-функції")
    return len(rows), namespaces, symbols


def main() -> int:
    try:
        registry = parse_all(tokens(REGISTRY.read_text(encoding="utf-8")))
        if registry != [["прочитати-семантичний-реєстр"]]:
            raise ValueError("чинний semantic-registry повинен читати домени через SENS, а не містити SID8")
        api = API.read_text(encoding="utf-8")
        if "(визначити прочитати-семантичний-реєстр" not in api:
            raise ValueError("відсутній Lisp-читач семантичного реєстру")
        total = 0
        for width in range(1, 11):
            path = ROOT / f"lib/domains/d{width}.lisp"
            if f'"lib/domains/d{width}.lisp"' not in api:
                raise ValueError(f"D{width}: чинний SENS-читач не посилається на домен")
            forms = parse_all(tokens(path.read_text(encoding="utf-8")))
            if len(forms) != 1:
                raise ValueError(f"D{width}: очікується одна domain-table-1 форма")
            rows, columns, _symbols = check(forms[0], width)
            if columns != set(SURFACES):
                raise ValueError(f"D{width}: неповний перелік проєкцій")
            total += rows
            print(f"D{width}: SOURCE_OK exact bits {rows}/{1 << width}; укр read")
        if total != 2046:
            raise ValueError(f"неповний обсяг D1–D10: {total}")
        print("DOMAIN_REGISTRY_SOURCE_OK domains=10 residents=2046; виконання/T5M окремо")
        return 0
    except (OSError, ValueError) as exc:
        print(f"DOMAIN_REGISTRY_SOURCE_FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
