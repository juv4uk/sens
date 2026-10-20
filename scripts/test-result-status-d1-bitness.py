#!/usr/bin/env python3
"""Легка структурна перевірка чинної української Lisp-проєкції результатів.

Не обчислює закони SENS, не підміняє реального SENS-виконавця та
не вважає механічний огляд доказом релізного допуску.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

from domain_tables import read_domain_table
from report_ukr_projection_progress import (
    LispAtom, LispForm, LispOpaque, LispQuoted,
    parse_lisp_tokens, tokenize_lisp,
)

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "lib/result-status.lisp"
REQUIRED = (
    "створити-доведений",
    "створити-невідоме",
    "створити-частковий",
    "створити-заблокований",
    "створити-спірний",
    "створити-некоректний",
    "результат-позначений?",
    "результат-стан",
    "результат-вміст",
    "міркувати-спостерігати",
    "міркувати-у-спостерігати",
)
OLD_WIDTH = re.compile(r"#(?:d[0-9]+:|b|q2:)", re.IGNORECASE)
BINARY_HEAD = re.compile(r"[01]+")
LATIN = re.compile(r"[A-Za-z]")


def check_status_text(source: str) -> list[str]:
    """Перевіряє форми й активні токени, а не текст коментарів."""
    errors: list[str] = []
    try:
        forms = parse_lisp_tokens(tokenize_lisp(source))
    except ValueError as exc:
        return [f"неправильний Lisp: {exc}"]
    names: list[str] = []

    def visit(node: object) -> None:
        if isinstance(node, (LispOpaque, LispQuoted)):
            return
        if isinstance(node, LispAtom):
            word = node.token.value
            if word in {"t", "T", "NIL"}:
                errors.append(f"стара істинність хоста: {word}")
            if OLD_WIDTH.match(word):
                errors.append(f"застарілий літерал ширини: {word}")
            return
        if not isinstance(node, LispForm) or not node.items:
            return
        if isinstance(node.items[0], LispAtom):
            head = node.items[0].token.value
            if head == "як-є":
                return  # цитовані дані протоколу не є виконуваним кодом
            if BINARY_HEAD.fullmatch(head):
                errors.append(f"сирий виконуваний бітовий виклик: {head}")
            if LATIN.search(head):
                errors.append(f"історична латинська голова виклику: {head}")
        for item in node.items:
            visit(item)

    for form in forms:
        if (not isinstance(form, LispForm) or len(form.items) != 3
                or not isinstance(form.items[0], LispAtom)
                or form.items[0].token.value != "визначити"
                or not isinstance(form.items[1], LispAtom)):
            errors.append("очікується верхня форма (визначити українське-ім'я вираз)")
            continue
        name = form.items[1].token.value
        names.append(name)
        if LATIN.search(name):
            errors.append(f"історичне латинське визначення: {name}")
        visit(form.items[2])

    if len(names) != len(set(names)):
        errors.append("дубльоване визначення")
    for name in REQUIRED:
        if names.count(name) != 1:
            errors.append(f"потрібне українське визначення: {name}")
    return errors


def check_status() -> list[str]:
    if not STATUS.is_file():
        return ["немає lib/result-status.lisp"]
    return check_status_text(STATUS.read_text(encoding="utf-8"))


def check_domain(width: int, root: Path = ROOT) -> list[str]:
    path = root / f"lib/domains/d{width}.lisp"
    if not path.is_file():
        return [f"D{width}: таблиці немає"]
    try:
        rows = read_domain_table(path)
    except (ValueError, OSError) as exc:
        return [f"D{width}: неточна таблиця: {exc}"]
    keys = [row.bits for row in rows]
    if (len(keys) != 1 << width
            or len(set(keys)) != len(keys)
            or any(len(x) != width or set(x) - {"0", "1"} for x in keys)
            or set(keys) != {f"{n:0{width}b}" for n in range(1 << width)}):
        return [f"D{width}: невірна ширина, колізія або відсутні координати"]
    return []


def main() -> int:
    errors = check_status()
    for width in range(1, 11):
        errors.extend(check_domain(width))
    if errors:
        print("РЕЗУЛЬТАТИ+ДОМЕНИ: SOURCE_BLOCKED", file=sys.stderr)
        for issue in errors:
            print("  " + issue, file=sys.stderr)
        return 1
    print("РЕЗУЛЬТАТИ+ДОМЕНИ: SOURCE_PASS, SEMANTIC_UNVERIFIED")
    print("Українські форми та D1–D10 перевірено структурно; справжні SENS/T5M свідки окремо")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
