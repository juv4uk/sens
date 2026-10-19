"""Поточний закон поверхні Core1: жодних wire-літералів або бітових голів.

Перевірка використовує чинний механічний валідатор; вона не пінить старий blob
або offsets, які закономірно змінюються під час наступної міграції.
Жодної Python-реалізації семантики SENS тут немає.
"""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/core1.lisp"
sys.path.insert(0, str(ROOT / "scripts"))
from check_no_encoded_source_literals import find_forbidden_literals


class Core1CurrentSourceTests(unittest.TestCase):
    def test_live_source_is_clean_and_raw_head_mutant_is_rejected(self):
        source = SOURCE.read_text(encoding="utf-8")
        path = SOURCE.relative_to(ROOT)

        # Позитивний свідок: вся виконувана програма, а не лише змінені рядки.
        findings = find_forbidden_literals(source, path=path)
        self.assertEqual(
            findings,
            [],
            "Core1 має використовувати поточну укр-проєкцію та десяткові числа; "
            f"знайдено: {findings!r}",
        )

        # Негативний свідок: повернення старої D3:011 call-head має бути виявлене.
        needle = "(решта лексеми)"
        self.assertIn(needle, source, "очікуваний поточний D3-виклик відсутній")
        mutant = source.replace(needle, "(011 лексеми)", 1)
        mutant_findings = find_forbidden_literals(mutant, path=path)
        self.assertTrue(
            any(item.token == "011" and item.reason == "numeric function/opcode head"
                for item in mutant_findings),
            f"валідатор не відхилив стару D3:011 голову: {mutant_findings!r}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
