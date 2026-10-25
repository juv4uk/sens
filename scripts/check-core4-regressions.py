#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Запобіжник проти двох відкочуваних регресій Core4 (див. коміт 962ea550).

Регресія 1 (COND): у джерелі Core4 жоден `за-умовою` не повинен мати клаузу
з != 2 елементів. Ратифікований закон D3:110 COND вимагає рівно
`(test expression)`; тричастинна клауза `(test expr expr)` заборонена.

Регресія 2 (CLIPS): у `твердження-кліпс?` та `виведення-кліпс?` голова CLIPS
порівнюється структурно через `однакові?` (D8 EQUAL), а не атомно через
`тотожне?` (D3 EQ), і без атомного бар'єра над головою форми.

Використання:
    python3 scripts/check-core4-regressions.py --check

Вихід: 0 — регресій немає; 1 — знайдено регресію (друкуються файл:рядок).
"""

import argparse
import os
import sys

# Файли-джерела Core4, які скануємо (core4.lisp + його дзеркала у parts/).
TARGETS = [
    "lib/core4.lisp",
    "lib/core4-parts/core4-d8-d9.lisp",
    "lib/core4-parts/core4-language.lisp",
]

COND_HEAD = "за-умовою"
CLIPS_FUNCS = ("твердження-кліпс?", "виведення-кліпс?")
ATOM_HEAD = "атом?"
EQ_HEAD = "тотожне?"
FIRST_HEAD = "перше"
FORM_SYM = "форма"


class Sym(str):
    """Символ; зберігає позицію (рядок) для звітів."""

    line: int

    def __new__(cls, text, line):
        obj = super().__new__(cls, text)
        obj.line = line
        return obj


class SList(list):
    """Список; зберігає позицію (рядок) відкривальної дужки."""

    line: int

    def __init__(self, items, line):
        super().__init__(items)
        self.line = line


def strip_comment(text):
    """Прибирає `;`-коментар поза рядковим літералом."""
    out = []
    in_str = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == "\\" and i + 1 < len(text):
                out.append(ch)
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_str = False
            out.append(ch)
        else:
            if ch == '"':
                in_str = True
                out.append(ch)
            elif ch == ";":
                # пропустити до кінця рядка
                while i < len(text) and text[i] != "\n":
                    i += 1
                continue
            else:
                out.append(ch)
        i += 1
    return "".join(out)


DELIMS = set("() \t\r\n")
# `'` є складовою імені символу (напр. `ім'я`, `число-п'ять`), а не читацькою цитатою.


def tokenize(text):
    """Повертає список (kind, value, line); kind in {'(', ')', 'atom'}."""
    tokens = []
    line = 1
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\n":
            line += 1
            i += 1
            continue
        if ch in " \t\r":
            i += 1
            continue
        if ch == "(":
            tokens.append(("(", None, line))
            i += 1
            continue
        if ch == ")":
            tokens.append((")", None, line))
            i += 1
            continue
        if ch == '"':
            j = i + 1
            buf = ['"']
            while j < n:
                c = text[j]
                if c == "\\" and j + 1 < n:
                    buf.append(text[j:j + 2])
                    j += 2
                    continue
                if c == '"':
                    buf.append('"')
                    j += 1
                    break
                if c == "\n":
                    line += 1
                buf.append(c)
                j += 1
            tokens.append(("atom", "".join(buf), line))
            i = j
            continue
        # символ/число
        j = i
        buf = []
        while j < n and text[j] not in DELIMS and text[j] != '"':
            if text[j] == "\n":
                break
            buf.append(text[j])
            j += 1
        tokens.append(("atom", "".join(buf), line))
        i = j
    return tokens


def parse(text):
    """Читає всі top-level форми. Повертає (forms, ok)."""
    tokens = tokenize(strip_comment(text))
    pos = 0
    forms = []
    ok = True

    def read_form():
        nonlocal pos, ok
        if pos >= len(tokens):
            ok = False
            return None
        kind, value, line = tokens[pos]
        if kind == "(":
            pos += 1
            items = []
            while pos < len(tokens) and tokens[pos][0] != ")":
                items.append(read_form())
            if pos >= len(tokens):
                ok = False
                return SList(items, line)
            pos += 1  # спожити ')'
            return SList(items, line)
        if kind == ")":
            ok = False
            pos += 1
            return None
        pos += 1
        return Sym(value, line)

    while pos < len(tokens):
        before = pos
        forms.append(read_form())
        if pos == before:
            pos += 1
    return forms, ok


def is_list(x):
    return isinstance(x, list)


def head_of(form):
    if is_list(form) and form and isinstance(form[0], Sym):
        return str(form[0])
    return None


def walk(form):
    """Рекурсивно обходить усі підформи (включно з form)."""
    yield form
    if is_list(form):
        for item in form:
            yield from walk(item)


def line_of(form):
    return getattr(form, "line", None)


def is_pershe_forma(expr):
    return (
        is_list(expr)
        and len(expr) == 2
        and isinstance(expr[0], Sym)
        and str(expr[0]) == FIRST_HEAD
        and isinstance(expr[1], Sym)
        and str(expr[1]) == FORM_SYM
    )


def check_cond_regression(path, forms):
    """Повертає список (line, msg) для тричастинних клауз за-умовою."""
    problems = []
    for form in walk(forms):
        if head_of(form) != COND_HEAD:
            continue
        clauses = form[1:]
        if not clauses:
            continue
        for clause in clauses:
            if not is_list(clause):
                problems.append(
                    (line_of(form),
                     "{}: клауза `за-умовою` не є списком: {}".format(path, clause))
                )
                continue
            if len(clause) != 2:
                problems.append(
                    (line_of(clause) or line_of(form),
                     "{}:{}: клауза `за-умовою` має {} елементів, а не 2 "
                     "(D3:110 COND тричастинна заборонена)".format(
                         path, line_of(clause) or line_of(form), len(clause)))
                )
    return problems


def check_clips_regression(path, forms):
    """Повертає список (line, msg) для тотожне?/атомний бар'єр у CLIPS-функціях."""
    problems = []
    for form in walk(forms):
        if head_of(form) != "визначити":
            continue
        if len(form) < 2 or not isinstance(form[1], Sym):
            continue
        name = str(form[1])
        if name not in CLIPS_FUNCS:
            continue
        for sub in walk(form):
            if head_of(sub) == EQ_HEAD and len(sub) >= 2 and is_pershe_forma(sub[1]):
                problems.append(
                    (line_of(sub),
                     "{}:{}: `{}` вживає атомне `тотожне?` (D3 EQ) над "
                     "`(" + "перше" + " форма)` замість структурного `однакові?` (D8 EQUAL)".format(
                         path, line_of(sub), name))
                )
            if head_of(sub) == ATOM_HEAD and len(sub) >= 2 and is_pershe_forma(sub[1]):
                problems.append(
                    (line_of(sub),
                     "{}:{}: `{}` містить атомний бар'єр `(атом? (" + "перше" + " форма))`, "
                     "який заборонено (регресія a9b4ccdc)".format(
                         path, line_of(sub), name))
                )
    return problems


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Запобіжник проти двох регресій Core4 (962ea550).")
    parser.add_argument(
        "--check", action="store_true",
        help="виконати перевірку (інакше — лише довідка)")
    parser.add_argument(
        "files", nargs="*",
        help="файли для сканування (типово: core4.lisp + дзеркала у parts/)")
    args = parser.parse_args(argv)

    if not args.check:
        parser.print_help()
        return 0

    root = repo_root()
    targets = args.files or TARGETS
    problems = []
    parse_warnings = []
    for rel in targets:
        path = rel if os.path.isabs(rel) else os.path.join(root, rel)
        if not os.path.exists(path):
            problems.append((None, "{}: файл не знайдено".format(rel)))
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        forms, ok = parse(text)
        if not ok:
            parse_warnings.append(
                "{}: незакриті дужки / неочікувана структура (перевірку виконано "
                "на розібраному префіксі)".format(rel))
        problems.extend(check_cond_regression(rel, forms))
        problems.extend(check_clips_regression(rel, forms))

    for warning in parse_warnings:
        print("УВАГА: " + warning)

    if problems:
        print("ЗНАЙДЕНО РЕГРЕСІЇ Core4 ({}):".format(len(problems)))
        for _, msg in sorted(problems, key=lambda p: (p[1] or "")):
            print("  " + msg)
        return 1

    print("OK: регресій Core4 не знайдено у {} файлах: {}".format(
        len(targets), ", ".join(targets)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
