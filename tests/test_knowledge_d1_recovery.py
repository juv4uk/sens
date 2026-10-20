#!/usr/bin/env python3
"""Чинні D1-свідки знань; історичні blob/SID/#d1 не є активним кодом.

Це структурні інваріанти, а не Python-виконання SENS. Виконувані
позитивні й негативні випадки містить crates/sens/tests/knowledge_d1_recovery.rs.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/knowledge.lisp"
PRIMARY = (
    "голова-твердження-знань-заперечена?",
    "клаузи-бази-знань-коректні?",
    "отримати-поле-пакета-знань",
)
RETIRED = (
    "knowledge-not-head?",
    "knowledge-clauses-valid?",
    "knowledge-package-field",
)
D1_NEGATION_LAWS = (
    "((тотожне? голова (як-є not?)) так)",
    "((тотожне? голова (як-є not)) так)",
    "(так ні)",
)


def executable_source(source: str) -> str:
    # Коментарі вилучаємо, протокольні лапки не підмінюємо семантикою.
    return re.sub(r";[^\n]*", "", source)


def validate_current_source(source: str) -> None:
    code = executable_source(source)
    for name in PRIMARY:
        expression = re.compile(r"(?m)^\(визначити\s+" + re.escape(name) + r"\s")
        if len(expression.findall(code)) != 1:
            raise ValueError(f"первинна українська функція відсутня або дубльована: {name}")
    for name in RETIRED:
        if re.search(r"(?m)^\(визначити\s+" + re.escape(name) + r"\s", code):
            raise ValueError(f"стару англійську прив'язку повернуто: {name}")
    head = code.index("(визначити голова-твердження-знань-заперечена?")
    end = code.index("(визначити терми-бази-знань-коректні?", head)
    definition = code[head:end]
    for law in D1_NEGATION_LAWS:
        if law not in definition:
            raise ValueError(f"D1 точний позитивний/негативний свідок втрачено: {law}")
    if "(тотожне? назва (перше-першого пакет))" not in code:
        raise ValueError("D4:1000 селектор поля пакета втрачено")
    if "#d1:" in code:
        raise ValueError("застарілий текстовий літерал D1 в активному коді")


class KnowledgeCurrentD1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_primary_ukrainian_functions_and_current_d1(self):
        validate_current_source(self.source)

    def test_exact_width_for_all_ratified_d1_d10_coordinates(self):
        total = 0
        for width in range(1, 11):
            table = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
            coords = re.findall(r"(?m)^\s*\(([01]+)\s+\(ук\s", table)
            expected = {f"{n:0{width}b}" for n in range(1 << width)}
            self.assertEqual(len(coords), 1 << width, f"D{width}: residents")
            self.assertEqual(set(coords), expected, f"D{width}: exact width and completeness")
            total += len(coords)
        self.assertEqual(total, 2046)
        # Ратифікована координата != самостійно доведена викличність.

    def test_negative_remove_d1_no(self):
        begin = self.source.index("(визначити голова-твердження-знань-заперечена?")
        end = self.source.index("(визначити терми-бази-знань-коректні?", begin)
        fragment = self.source[begin:end]
        self.assertEqual(fragment.count("(так ні)"), 1)
        broken = self.source[:begin] + fragment.replace("(так ні)", "(так так)", 1) + self.source[end:]
        with self.assertRaisesRegex(ValueError, "D1"):
            validate_current_source(broken)

    def test_negative_change_atomic_eq(self):
        broken = self.source.replace(
            "((тотожне? голова (як-є not?)) так)",
            "((атом? голова) так)", 1,
        )
        self.assertNotEqual(broken, self.source)
        with self.assertRaisesRegex(ValueError, "D1"):
            validate_current_source(broken)

    def test_negative_resurrect_english_alias(self):
        broken = self.source + "\n(визначити knowledge-not-head? голова-твердження-знань-заперечена?)\n"
        with self.assertRaisesRegex(ValueError, "стару англійську"):
            validate_current_source(broken)


if __name__ == "__main__":
    unittest.main()
