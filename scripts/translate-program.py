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


def translate_program(source: str, translations: dict[str, str | None]) -> str:
    """Перекладаємо викличні голови, не дані, цитати чи формальні параметри.

    Це лише текстова допоміжна проєкція: жодного runtime, D7-кодування
    або перетворення історичних байтів SID8 у сучасні координати.
    """
    protected_quote_heads: set[str] = set()
    protected_formal_heads: set[str] = set()
    for row in read_domain_tables(
        tuple(path for path in PROGRAM_TABLES if path.stem in {"d3", "d4"})
    ):
        if (row.domain, row.bits) not in {
            ("D3", "001"), ("D4", "0010"), ("D4", "0011")
        }:
            continue
        names = {
            name for name in (row.uk, row.ukr, row.san, row.en) if name
        }
        if (row.domain, row.bits) == ("D3", "001"):
            protected_quote_heads.update(names)
        else:
            # FUNCTION/LAMBDA parameters and DEFINE declaration head
            # are syntax/bindings, not callable expressions.
            protected_formal_heads.update(names)

    output: list[str] = []
    index = 0
    length = len(source)
    frames = [
        {"head": False, "literal": False, "next_literal": False, "apostrophe": False}
    ]

    def finish_expression(frame: dict[str, bool]) -> None:
        frame["head"] = False
        frame["next_literal"] = False
        frame["apostrophe"] = False

    while index < length:
        character = source[index]
        frame = frames[-1]
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
                    index = min(index + 2, length)
                elif source[index] == '"':
                    index += 1
                    break
                else:
                    index += 1
            output.append(source[start:index])
            finish_expression(frame)
        elif character.isspace():
            output.append(character)
            index += 1
        elif character == "'":
            output.append(character)
            index += 1
            frame["apostrophe"] = True
        elif character == "(":
            literal = frame["literal"] or frame["next_literal"] or frame["apostrophe"]
            finish_expression(frame)
            frames.append(
                {"head": True, "literal": literal, "next_literal": False, "apostrophe": False}
            )
            output.append(character)
            index += 1
        elif character == ")":
            if len(frames) == 1:
                raise ValueError("зайва закривальна дужка у проєкції")
            frames.pop()
            output.append(character)
            index += 1
        else:
            start = index
            while index < length:
                current = source[index]
                if current.isspace() or current in '();\"':
                    break
                index += 1
            token = source[start:index]
            callable_head = frame["head"] and not (
                frame["literal"] or frame["next_literal"] or frame["apostrophe"]
            )
            if callable_head and token in translations and translations[token] is None:
                raise ValueError(
                    f"неоднозначна сучасна доменна проєкція: {token!r}"
                )
            output.append(translations.get(token, token) if callable_head else token)
            protect_next = callable_head and (
                token in protected_quote_heads or token in protected_formal_heads
            )
            finish_expression(frame)
            if protect_next:
                frame["next_literal"] = True

    if len(frames) != 1:
        raise ValueError("незакрита дужка у проєкції")
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
