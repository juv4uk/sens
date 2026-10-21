#!/usr/bin/env python3
"""Легка перевірка української Lisp-проєкції перекладу та ширин D1–D10.

Не виконує семантику SENS і не підтверджує T5M або готовність релізу.
Цитовані протокольні поля зберігаються як дані.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

from domain_tables import read_domain_table
from report_ukr_projection_progress import (
    LispAtom, LispForm, LispOpaque, LispQuoted,
    _projection_reasons, parse_lisp_tokens, tokenize_lisp,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/translation.lisp"
PRIMARY = (
    "переклад-стан",
    "переклад-вид",
    "статус-запису-перекладу-коректний?",
    "запис-огляду-перекладу-коректний?",
    "переклад-перевірка",
    "переклад-доказ-запис",
)
RAW_WIDTH = re.compile(r"#(?:d[0-9]+:|b|q2:)", re.IGNORECASE)
LATIN = re.compile(r"[A-Za-z]")


def check_translation_text(source: str) -> list[str]:
    """Структурний аудит лише виконуваних форм; ніколи не oracle."""
    errors: list[str] = []
    try:
        roots = parse_lisp_tokens(tokenize_lisp(source))
        # Дійсний зовнішній стан knowledge.lisp: тільки читання значення,
        # не англійський DEFINE, параметр чи виклична голова.
        errors.extend(_projection_reasons(
            source, external_value_symbols=frozenset({"*knowledge-journal*"})
        ))
    except ValueError as exc:
        return [f"некоректна структура Lisp: {exc}"]

    definitions: list[str] = []
    active_atoms: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, (LispQuoted, LispOpaque)):
            return
        if isinstance(node, LispAtom):
            active_atoms.append(node.token.value)
            return
        if not isinstance(node, LispForm):
            return
        if node.items and isinstance(node.items[0], LispAtom):
            head = node.items[0].token.value
            if head == "як-є":
                return   # дані: не перекладати, не тлумачити як виклики
        for child in node.items:
            walk(child)

    for node in roots:
        if not isinstance(node, LispForm) or len(node.items) != 3:
            errors.append("верхній рівень має містити лише (визначити назва вираз)")
            continue
        head, name, _expression = node.items
        if not isinstance(head, LispAtom) or head.token.value != "визначити":
            errors.append("замість українського DEFINE знайдено іншу форму")
            continue
        if not isinstance(name, LispAtom):
            errors.append("неправильна назва визначення")
            continue
        definitions.append(name.token.value)
        walk(_expression)

    if len(definitions) != len(set(definitions)):
        errors.append("дубльовані визначення")
    for name in definitions:
        if LATIN.search(name):
            errors.append(f"англомовне DEFINE-зв'язування: {name}")
    for required in PRIMARY:
        if definitions.count(required) != 1:
            errors.append(f"відсутнє єдине українське визначення: {required}")
    # Український модуль не зобов’язаний мати обидва D1-літерали:
    # відсутність явного «ні» не дає права змінювати умовні закони.
    if "так" not in set(active_atoms):
        errors.append("чинний D1-літерал так відсутній")
    for atom in active_atoms:
        if atom in {"t", "T", "NIL"}:
            errors.append(f"стара істинність хоста: {atom}")
        if RAW_WIDTH.match(atom):
            errors.append(f"застарілий машинний літерал у програмі: {atom}")
    return errors


def check_domain(width: int, root: Path = ROOT) -> list[str]:
    path = root / f"lib/domains/d{width}.lisp"
    if not path.is_file():
        return [f"D{width}: таблицю не знайдено"]
    try:
        rows = read_domain_table(path)
    except (ValueError, OSError) as exc:
        return [f"D{width}: некоректна таблиця: {exc}"]
    keys = [row.bits for row in rows]
    if len(keys) != 1 << width:
        return [f"D{width}: очікувано {1 << width} координат, отримано {len(keys)}"]
    if len(set(keys)) != len(keys) or any(
        len(bits) != width or set(bits) - {"0", "1"} for bits in keys
    ):
        return [f"D{width}: повторена, не двійкова чи неточна координата"]
    if set(keys) != {f"{i:0{width}b}" for i in range(1 << width)}:
        return [f"D{width}: неповна ратифікована драбина"]
    return []


def main() -> int:
    errors = check_translation_text(SOURCE.read_text(encoding="utf-8"))
    for width in range(1, 11):
        errors.extend(check_domain(width))
    if errors:
        print("ПЕРЕКЛАД+ДОМЕНИ: SOURCE_BLOCKED", file=sys.stderr)
        for item in errors:
            print(f"  {item}", file=sys.stderr)
        return 1
    print("ПЕРЕКЛАД+ДОМЕНИ: SOURCE_PASS, SEMANTIC_UNVERIFIED")
    print("Українські Lisp-форми D1–D10 перевірено статично; фізична оборотність та виконання потребують SENS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
