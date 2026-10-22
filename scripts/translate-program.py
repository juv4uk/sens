#!/usr/bin/env python3
"""Лише допоміжна проєкція назв із чинної точної драбини D1–D10.

Ніяких історичних byte SID8/Sens8: джерело відповідностей — виключно
ратифіковані рядки lib/domains/dN.lisp (точний домен + точні біти).
D2 визначає структуру, D7 визначає текстові дані; їх не перекладати
як імена функцій. Неоднозначний символ відхиляється, а не вгадується.

Цей інструмент переписує людський текст, НЕ виконує SENS, НЕ пакує T5M
і НЕ надає викличного допуску. Семантичний шлях належить самому SENS.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from domain_tables import CURRENT_HUMAN_TABLES, read_domain_tables

# Повні дані D7 не є викличними головами; D2 не є лексичними операторами.
PROGRAM_TABLES = tuple(
    path for path in CURRENT_HUMAN_TABLES
    if path.stem not in {"d2", "d7"}
)
LANGUAGE_FIELDS = {
    "en": "en", "ук": "uk", "укр": "ukr",
    "uk": "uk", "ukr": "ukr", "sa": "san", "san": "san",
}


def registry_rows() -> list[dict[str, str]]:
    """Кожна відповідність прив'язана до сучасної доменної координати."""
    rows = []
    for row in read_domain_tables(PROGRAM_TABLES):
        if row.domain == "D3" and row.bits == "000":
            # Порожній список — структурне значення, не назва функції.
            continue
        names = {
            language: getattr(row, field)
            for language, field in LANGUAGE_FIELDS.items()
        }
        names["_identity"] = f"{row.domain}:{row.bits}"
        rows.append({key: value for key, value in names.items() if value})
    if not rows:
        raise ValueError("чинні доменні таблиці не містять жодної проєкції")
    return rows


def human_languages(rows: list[dict[str, str]]) -> set[str]:
    return {
        language
        for row in rows
        for language in row
        if language in LANGUAGE_FIELDS
    }


def translation_map(
    source_language: str, target_language: str
) -> dict[str, str | None]:
    if source_language not in LANGUAGE_FIELDS or target_language not in LANGUAGE_FIELDS:
        raise ValueError("невідома людська проєкція")
    if LANGUAGE_FIELDS[source_language] == LANGUAGE_FIELDS[target_language]:
        raise ValueError("джерело й ціль мають бути різними проєкціями")

    translations: dict[str, str | None] = {}
    owners: dict[str, str] = {}
    for row in registry_rows():
        source_name = row.get(source_language)
        target_name = row.get(target_language)
        if not source_name or not target_name:
            continue
        identity = row["_identity"]
        if source_name in owners and owners[source_name] != identity:
            # Наприклад, en:map існує у D6 і D8. Жоден не має
            # переваги лише через назву або вісім бітів.
            translations[source_name] = None
            continue
        owners[source_name] = identity
        translations[source_name] = target_name
    return translations


def translate_program(source: str, translations: dict[str, str]) -> str:
    """Rewrite symbols while preserving layout, comments, strings and shared symbols."""
    output: list[str] = []
    index = 0
    length = len(source)

    while index < length:
        character = source[index]
        if character == ";":
            end = source.find("\n", index)
            if end == -1:
                output.append(source[index:])
                break
            output.append(source[index : end + 1])
            index = end + 1
        elif character == '"':
            start = index
            index += 1
            while index < length:
                if source[index] == "\\":
                    index += 2
                elif source[index] == '"':
                    index += 1
                    break
                else:
                    index += 1
            output.append(source[start:index])
        elif character.isspace() or character in "()":
            output.append(character)
            index += 1
        elif character == "'":
            output.append(character)
            index += 1
        else:
            start = index
            while index < length:
                current = source[index]
                if current.isspace() or current in "();\"":
                    break
                index += 1
            token = source[start:index]
            if token in translations and translations[token] is None:
                raise ValueError(f"неоднозначна сучасна доменна проєкція: {token!r}")
            output.append(translations.get(token, token))

    return "".join(output)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="source program, or - for stdin")
    parser.add_argument("--from", dest="source_language", required=True)
    parser.add_argument("--to", dest="target_language", required=True)
    parser.add_argument("-o", "--output", type=Path, help="write here instead of stdout")
    return parser.parse_args()


def main() -> int:
    args = arguments()
    try:
        rows = registry_rows()
        languages = human_languages(rows)
        unknown = {args.source_language, args.target_language} - languages
        if unknown:
            raise ValueError(
                "unknown human surface(s): " + ", ".join(sorted(unknown))
            )
        if args.source_language == args.target_language:
            raise ValueError("source and target surfaces must differ")
        translations = translation_map(args.source_language, args.target_language)
    except (OSError, ValueError) as error:
        print(f"translation registry error: {error}", file=sys.stderr)
        return 2

    source = (
        sys.stdin.read()
        if str(args.input) == "-"
        else args.input.read_text(encoding="utf-8")
    )
    try:
        translated = translate_program(source, translations)
    except ValueError as error:
        print(f"projection error: {error}", file=sys.stderr)
        return 2
    if args.output:
        args.output.write_text(translated, encoding="utf-8")
    else:
        sys.stdout.write(translated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
