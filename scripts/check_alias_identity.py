#!/usr/bin/env python3
"""Перевірка однозначності чинної УКР-проєкції D1–D10, без старого SID8.

Влада над (домен, точне слово, укр) — лише lib/domains/dN.lisp.
D2 задає граматику; D7 є текстом, а D3:000 — структурним порожнім
значенням: вони не потрапляють до простору викличних голів.

Неповні en/sym проєкції можуть збігатися (наприклад MAP D6/D8):
це не дозвіл вгадувати тотожність через ім'я. Цей guard перевіряє
однозначність саме повної виконуваної «укр», а не право виконання
кожної ратифікованої координати. Runtime і T5M перевіряються окремо.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import sys

# Уніт-тест підключає файл напряму через spec_from_file_location,
# тому scripts/ не гарантовано міститься у sys.path.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from domain_tables import read_domain_table

REGISTRY = "lib/surface/semantic-registry.lisp"
EXPECTED_READER = "(прочитати-семантичний-реєстр)"


def check_rows(rows: list) -> list[str]:
    """Повне УКР-ім'я не має означати дві різні викличні координати."""
    owners: dict[tuple[str, str], set[str]] = defaultdict(set)
    problems: list[str] = []
    for row in rows:
        identity = f"{row.domain}:{row.bits}"
        if row.width in (2, 7) or (row.width == 3 and row.bits == "000"):
            continue
        for column in ("ук", "укр"):
            value = getattr(row, "uk" if column == "ук" else "ukr")
            if value is None or value == "()":
                if column == "укр" and row.width != 1:
                    problems.append(f"{identity}: відсутня повна (укр ...) проєкція")
                continue
            owners[(column, value)].add(identity)
    for (column, name), identities in sorted(owners.items()):
        if len(identities) > 1:
            problems.append(
                f"неоднозначна ({column} {name}): " + ", ".join(sorted(identities))
            )
    return problems


def check(root: Path) -> list[str]:
    """Аудит точних D1–D10, придатний і для тимчасових тестових таблиць."""
    rows = []
    for width in range(1, 11):
        table = root / f"lib/domains/d{width}.lisp"
        if not table.is_file():
            return [f"D{width}: відсутня ратифікована таблиця {table}"]
        try:
            domain_rows = read_domain_table(table)
        except (OSError, ValueError) as exc:
            return [f"D{width}: неправильна ширина або структура: {exc}"]
        exact = [format(index, f"0{width}b") for index in range(1 << width)]
        if [row.bits for row in domain_rows] != exact:
            return [f"D{width}: координати пропущені, дубльовані або переставлені"]
        rows.extend(domain_rows)
    if len(rows) != 2046:
        return [f"драбина D1–D10 неповна: {len(rows)}/2046"]
    return check_rows(rows)


def check_registry(root: Path) -> list[str]:
    """Виконуваний реєстр читає домени, не дублює стару W8-таблицю."""
    path = root / REGISTRY
    if not path.is_file():
        return [f"відсутній {REGISTRY}"]
    live = "\n".join(line.split(";", 1)[0] for line in
                     path.read_text(encoding="utf-8").splitlines()).strip()
    if live != EXPECTED_READER:
        return [f"{REGISTRY}: потрібне читання D1–D10 через SENS, не SID8"]
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    root = Path(ap.parse_args().root).resolve()
    try:
        problems = check_registry(root) + check(root)
    except (OSError, ValueError) as exc:
        problems = [str(exc)]
    if problems:
        print(f"УКР_НЕОДНОЗНАЧНІСТЬ: {len(problems)}", flush=True)
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print("УКР_ДОМЕНИ_OK: D1–D10; 2046 точних координат; повні викличні назви однозначні; виконання окремо")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
