#!/usr/bin/env python3
"""Структурний контроль чинних українських D1/D3/D4 законів знань.

Історичні Git blob, англійські DEFINE й #d1-літерали не є релізним
контрактом. Ця перевірка не імітує виконання SENS: його виконують
crates/sens/tests/knowledge_journal_d3_ukr.rs та knowledge_d1_recovery.rs.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "lib/knowledge.lisp"
NAMES = (
    "голова-твердження-знань-заперечена?",
    "клаузи-бази-знань-коректні?",
    "отримати-поле-пакета-знань",
)
LEGACY_HEADS = (
    "knowledge-not-head?",
    "knowledge-clauses-valid?",
    "knowledge-package-field",
)
TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()";]+')


def parse(source: str):
    tokens = [
        match.group() for match in TOKEN.finditer(source)
        if not match.group().startswith(";")
    ]
    position = 0

    def expression():
        nonlocal position
        if position >= len(tokens):
            raise ValueError("незакрита форма")
        word = tokens[position]
        position += 1
        if word == ")":
            raise ValueError("зайва закривальна дужка")
        if word != "(":
            return word
        items = []
        while position < len(tokens) and tokens[position] != ")":
            items.append(expression())
        if position >= len(tokens):
            raise ValueError("незакрита дужка")
        position += 1
        return items

    forms = []
    while position < len(tokens):
        forms.append(expression())
    return forms


def active_ukrainian_definitions(source: str):
    forms = parse(source)
    definitions = {}
    for form in forms:
        if not isinstance(form, list) or len(form) < 2 or form[0] != "визначити":
            continue
        name = form[1]
        if not isinstance(name, str):
            raise ValueError("некоректне ім'я визначення")
        if name in definitions:
            raise ValueError("повторне визначення " + name)
        definitions[name] = form

    if any(name not in definitions for name in NAMES):
        raise ValueError("втрачене українське визначення")
    # Історичні англійські виконувані псевдоніми прибрано з укр-модуля
    # (owner, коміт 3d9c0aecc «прибрати 20 старих англійських виконуваних
    # псевдонімів»). Вони більше не є прозорим сумісним зв'язуванням, тож
    # будь-яке їхнє повторне визначення тут є дрейфом укр-поверхні.
    for old_name in LEGACY_HEADS:
        if old_name in definitions:
            raise ValueError("відновлено історичний англійський виконуваний псевдонім")
    if re.search(r"(?<![\w])#(?:d\d+:|b[01]|q2:)", source):
        # Коментарі та рядки не є виконуваним кодом — скануємо лише
        # токени програми. Історичні пояснення залишаються дозволені.
        executable = "\n".join(
            line.split(";", 1)[0] for line in source.splitlines()
        )
        if re.search(r"#(?:d\d+:|b[01]|q2:)", executable):
            raise ValueError("застарілий числовий source-літерал")
    return {name: definitions[name] for name in NAMES}


def check(source: str):
    definitions = active_ukrainian_definitions(source)
    head, clauses, field = (definitions[name] for name in NAMES)

    if head[2][:2] != ["функція", ["голова"]]:
        raise ValueError("змінено сигнатуру запереченої голови")
    if head[2][2][0] != "за-умовою":
        raise ValueError("змінено D1 умовний закон голови")
    branches = head[2][2][1:]
    expected_heads = (
        ["тотожне?", "голова", ["як-є", "not?"]],
        ["тотожне?", "голова", ["як-є", "not"]],
    )
    # Жоден D3 EQ не має отримувати складену голову. Це перевірка
    # захисту форми, не Python-симуляція поведінки SENS.
    if len(branches) != 4 or branches[0] != [
        ["хибне?", ["атом?", "голова"]], ["атом?", ["як-є", ["стан"]]]
    ] or [part[0] for part in branches[1:3]] != list(expected_heads):
        raise ValueError("втрачено D3 atom-guard або протокольні not/not? маркери")
    if [part[1] for part in branches[1:]] != [
        ["атом?", ["як-є", []]],
        ["атом?", ["як-є", []]],
        ["атом?", ["як-є", ["стан"]]],
    ]:
        raise ValueError("зміна справжніх D1 відповідей голови")

    if clauses[2][:2] != ["функція", ["клаузи"]]:
        raise ValueError("змінено сигнатуру списку клауз")
    if clauses[2][2][0] != "за-умовою":
        raise ValueError("змінено D3 обхід клауз")
    rows = clauses[2][2][1:]
    if len(rows) != 4 or rows[0] != [
        ["порожній?", "клаузи"], ["атом?", ["як-є", []]]
    ] or rows[1] != [
        ["атом?", "клаузи"], ["атом?", ["як-є", ["стан"]]]
    ] or rows[2] != [
        ["клауза-бази-знань-коректна?", ["перше", "клаузи"]],
        ["клаузи-бази-знань-коректні?", ["решта", "клаузи"]],
    ] or rows[3] != [
        ["атом?", ["як-є", []]], ["атом?", ["як-є", ["стан"]]]
    ]:
        raise ValueError("зміна рекурсії, D1 або відмови для списку клауз")

    if field[2][:2] != ["функція", ["назва", "пакет"]]:
        raise ValueError("змінено сигнатуру пакета")
    next_field = ["отримати-поле-пакета-знань", "назва", ["решта", "пакет"]]
    if field[2][2] != [
        "за-умовою",
        [["атом?", "пакет"], ["як-є", []]],
        [["хибне?", ["атом?", "назва"]], ["як-є", []]],
        [["атом?", ["перше", "пакет"]], next_field],
        [["хибне?", ["атом?", ["перше-першого", "пакет"]]], next_field],
        [["тотожне?", "назва", ["перше-першого", "пакет"]],
         ["решта-першого", "пакет"]],
        [["атом?", ["як-є", []]], next_field],
    ]:
        raise ValueError("зміна D4 захисту CAAR або рекурсії поля пакета")

    for definition in (head, clauses, field):
        if len(definition) != 3:
            raise ValueError("неправильна D4 DEFINE")
        for expr in walk(definition):
            if isinstance(expr, list) and expr and expr[0] == "за-умовою":
                if any(not isinstance(branch, list) or len(branch) != 2
                       for branch in expr[1:]):
                    raise ValueError("не двопольова D3 COND")
    return definitions


def walk(node):
    if isinstance(node, list):
        yield node
        for child in node:
            yield from walk(child)


class RecoverKnowledge(unittest.TestCase):
    def test_current_ukrainian_d1_d3_d4_laws(self):
        self.assertEqual(set(check(PATH.read_text(encoding="utf-8"))), set(NAMES))

    def test_exact_width_for_every_ratified_coordinate_d1_d10(self):
        total = 0
        for width in range(1, 11):
            s = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
            coords = re.findall(r"(?m)^\s*\(([01]+)\s+\(ук\s", s)
            self.assertEqual(len(coords), 1 << width, f"D{width} slot count")
            self.assertEqual(len(set(coords)), len(coords), f"D{width} collision")
            self.assertEqual(set(coords),
                {f"{i:0{width}b}" for i in range(1 << width)},
                f"D{width} missing / wrong width")
            total += len(coords)
        self.assertEqual(total, 2046)

    def test_bad_mutations_rejected_without_historical_git_pin(self):
        source = PATH.read_text(encoding="utf-8")
        self.assertEqual(len(check(source)), 3)
        mutations = [
            source.replace(
                "((хибне? (атом? голова)) (атом? (як-є (стан))))",
                "((хибне? (атом? голова)) (атом? (як-є ())))", 1,
            ),
            source.replace(
                "((тотожне? голова (як-є not?)) (атом? (як-є ())))",
                "((тотожне? голова (як-є вигадане-заперечення)) (атом? (як-є ())))",
                1,
            ),
            source.replace("(клаузи-бази-знань-коректні? (решта клаузи))",
                           "(клаузи-бази-знань-коректні? (перше клаузи))", 1),
            source.replace("(перше-першого пакет)", "(перше пакет)", 1),
            source.replace(
                "((тотожне? голова (як-є not)) (атом? (як-є ())))",
                "((тотожне? голова (як-є not)) (атом? (як-є (стан))))", 1
            ),
            source + "\n(визначити knowledge-not-head? голова-твердження-знань-заперечена?)\n",
        ]
        for changed in mutations:
            self.assertNotEqual(changed, source)
            with self.assertRaises(ValueError):
                check(changed)


if __name__ == "__main__":
    unittest.main()
