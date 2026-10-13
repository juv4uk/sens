#!/usr/bin/env python3
"""Свідок резидентності мігрованих головних вузлів — точковий інформативний тест.

Ідея (ми цінуємо кожен біт):

  Ширина бінарного ключа = адреса домену. Тож КОЖЕН бінарний головний вузол
  шириною n у мігрованих джерелах SENS мусить бути РАТИФІКОВАНИМ резидентом
  домену Dn. Не «схоже на», не «десь є» — точний резидент точної ширини.

Це використовує всі 2046 функцій-резидентів D1..D10 як ЄДИНУ авторитетну
таблицю (жодного нового парсера чи таблиці) і ловить саме те, що ламає
міграцію: одрук у коді, вигаданий код, хибну ширину, залишок старої назви.

Правила (fail-closed — будь-яка невдача = ненульовий вихід):

  1. ШИРИНА Є ДОМЕНОМ. Кожен головний бітрядок має ширину 1..10.
  2. РЕЗИДЕНТНІСТЬ. Бітрядок ширини n має бути рядком канонічної таблиці Dn.
  3. ІНФОРМАТИВНІСТЬ. Вивід — таблиця (домен | ширина | резидентів | сайтів |
     різних | поза-таблицею), а не «ok/fail». Це свідчення, а не галочка.

Read-only: жодного файла не змінює.
Запуск: python3 scripts/check-migrated-head-residency.py [корінь ...]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from domain_tables import read_domain_table, CURRENT_HUMAN_TABLES  # noqa: E402

# Мігровані виконувані джерела: усе під lib/, крім самих таблиць доменів,
# згенерованих артефактів і поверхонь (це не виконувана міграція).
DEFAULT_SCOPES = ("lib",)
SKIP_PARTS = {"lib/domains", "lib/generated", "lib/surface"}

# Головний вузол = бітрядок одразу після '(', обмежений пробілом/дужкою.
# Довжина НЕ обмежена зверху навмисно: хибно довгий код теж має бути спійманий.
HEAD = re.compile(r"\(([01]+)(?=[\s()])")


def strip_strings_and_comments(text: str) -> str:
    """Прибрати рядкові літерали та ';'-коментарі, щоб не читати дані за код."""
    out: list[str] = []
    i, n = 0, len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == ";":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def load_residents() -> dict[int, set[str]]:
    residents: dict[int, set[str]] = {}
    for table in CURRENT_HUMAN_TABLES:
        width = int(table.stem[1:])
        bucket = residents.setdefault(width, set())
        for row in read_domain_table(table):
            bucket.add(row.bits)
    return residents


def in_scope(path: Path, scopes: tuple[str, ...]) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if path.suffix != ".lisp":
        return False
    if any(rel == s or rel.startswith(s + "/") for s in scopes):
        return any(rel == skip or rel.startswith(skip + "/") for skip in SKIP_PARTS) is False
    return False


def main(argv: list[str]) -> int:
    scopes = tuple(argv[1:]) or DEFAULT_SCOPES
    residents = load_residents()
    total_residents = sum(len(v) for v in residents.values())

    sites: dict[int, int] = {}
    distinct: dict[int, set[str]] = {}
    outside: dict[int, set[str]] = {}
    bad_width: set[str] = set()
    files_scanned = 0
    for path in sorted(ROOT.rglob("*.lisp")):
        if not in_scope(path, scopes):
            continue
        files_scanned += 1
        text = strip_strings_and_comments(path.read_text(encoding="utf-8", errors="strict"))
        for match in HEAD.finditer(text):
            bits = match.group(1)
            width = len(bits)
            sites[width] = sites.get(width, 0) + 1
            distinct.setdefault(width, set()).add(bits)
            if width not in residents:
                bad_width.add(bits)
            elif bits not in residents[width]:
                outside.setdefault(width, set()).add(bits)

    print("свідок резидентності головних вузлів")
    print(f"область: {', '.join(scopes)}  (файлів: {files_scanned})")
    print(f"резидентів у D1..D10: {total_residents}")
    print()
    header = f"{'домен':<6}{'ширина':<8}{'резидентів':<12}{'сайтів':<9}{'різних':<8}{'поза-таблицею':<14}"
    print(header)
    print("-" * len(header))
    grand_sites = 0
    for width in sorted(residents):
        rows = len(residents[width])
        s = sites.get(width, 0)
        d = len(distinct.get(width, set()))
        o = len(outside.get(width, set()))
        grand_sites += s
        print(f"D{width:<5}{width:<8}{rows:<12}{s:<9}{d:<8}{o:<14}")
    print("-" * len(header))
    print(f"{'разом':<6}{'':<8}{total_residents:<12}{grand_sites:<9}"
          f"{sum(len(v) for v in distinct.values()):<8}"
          f"{sum(len(v) for v in outside.values()):<14}")
    print()

    failures: list[str] = []
    if bad_width:
        failures.append(
            "ширина не є доменом 1..10: " + ", ".join(sorted(bad_width)[:10])
        )
    for width in sorted(outside):
        if outside[width]:
            failures.append(
                f"D{width}: не-резиденти: " + ", ".join(sorted(outside[width])[:10])
            )
    if failures:
        for line in failures:
            print(f"HEAD-RESIDENCY: FAIL: {line}")
        return 1
    print("HEAD-RESIDENCY: PASS — кожен головний вузол є резидентом точної ширини")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
