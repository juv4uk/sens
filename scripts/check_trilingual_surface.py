#!/usr/bin/env python3
"""Спостережна звірка людських проєкцій із чинними D1–D10.

Точна тотожність — (домен, бітове слово), а не історичний byte SID8.
Д7 — алфавіт людської поверхні, Д2 — структура, Д24+ — математика.
Наявність назви НЕ підтверджує викличного допуску, виконання, T5M,
оберненості файлів чи готовності релізу. Семантику виконує лише СЕНС.
"""

from __future__ import annotations

import argparse
from collections import Counter

from domain_tables import CURRENT_HUMAN_TABLES, read_domain_tables

HUMAN_SURFACES = ("укр", "en", "san")
ALL_SURFACES = ("ук", "укр", "san", "en", "lisp", "sym")


def current_rows():
    """Читати лише ратифіковані точнодоменні таблиці, не SID8-реєстр."""
    rows = read_domain_tables(CURRENT_HUMAN_TABLES)
    identities = [(row.domain, row.bits) for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("повторено точну тотожність (домен, біти)")
    if {row.domain for row in rows} != {f"D{n}" for n in range(1, 11)}:
        raise ValueError("неповна сучасна драбина D1–D10")
    return rows


def counts(rows, language: str) -> tuple[int, int]:
    present = sum(getattr(row, language) is not None for row in rows)
    return present, len(rows) - present


def is_surface_complete(rows) -> bool:
    return all(all(getattr(row, language) is not None
                   for language in HUMAN_SURFACES) for row in rows)


def render_report(rows) -> str:
    per_domain = Counter(row.domain for row in rows)
    lines = [
        "Сучасні людські проєкції D1–D10 (не реєстр SID8/Sens8)",
        f"точнодоменних рядків: {len(rows)}; викличних функцій: НЕ ВИМІРЯНО",
        "ширини: " + " ".join(f"D{n}={per_domain[f'D{n}']}" for n in range(1, 11)),
        "",
        "проєкція  наявні  порожні  рядків",
    ]
    for language in ALL_SURFACES:
        present, empty = counts(rows, language)
        lines.append(f"{language:<9}{present:>7}{empty:>9}{len(rows):>8}")
    complete = sum(all(getattr(row, lang) is not None
                       for lang in HUMAN_SURFACES) for row in rows)
    lines.extend([
        "",
        f"укр/en/san заповнені разом: {complete}/{len(rows)}",
        f"повнота людських поверхонь: {'ТАК' if is_surface_complete(rows) else 'НІ'}",
        "релізний статус: НЕ ВИЗНАЧАЄТЬСЯ ЦИМ СКРИПТОМ",
        "для релізу потрібні нативні СЕНС/Zig виконання й оберненість T5M на одному SHA",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-complete", action="store_true",
        help="перевірити заповнення укр/en/san; не є доказом релізу",
    )
    args = parser.parse_args()
    try:
        rows = current_rows()
    except (OSError, ValueError) as error:
        print(f"помилка ратифікованих таблиць: {error}")
        return 2
    print(render_report(rows))
    return 1 if args.require_complete and not is_surface_complete(rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
