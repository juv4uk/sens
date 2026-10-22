"""Чинний лексичний guard машинної української проєкції.

Історичне відновлення Git blob не є тестом живого коду: оптимізації
змінюють кількість форм і позиції токенів. Виконання, байтову тотожність
та негативні свідки перевіряє справжній SENS у
crates/sens/tests/machine_effect_{add,d5_arithmetic}_projection.rs.
Цей файл НЕ є Python-виконавцем SENS.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/machine/projection/x86-64.lisp"
PARITY = ROOT / "lib/machine/dispatch/native-first-parity.lisp"


class MachineUkrainianLocalBindingTests(unittest.TestCase):
    def test_live_machine_projection_has_one_ukrainian_entrypoint(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertEqual(source.count("(визначити проєктувати-машинний-ефект-на-х86"), 1)
        self.assertEqual(source.count("(визначити закодувати-машинний-ефект-на-х86"), 1)
        self.assertEqual(source.count("(визначити проєктувати-двійковий-ефект-на-х86"), 1)
        for old in ("(визначити x86-project-machine-effect",
                    "(визначити x86-encode-machine-effect"):
            self.assertNotIn(old, source)

    def test_shared_builder_keeps_all_three_exactly_selected_ops(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("(функція (ефект команда)", source)
        self.assertIn("(список команда (як-є rax) (як-є rcx))", source)
        self.assertEqual(source.count("(список (як-є mov-r64-imm64)"), 2)
        for operation in ("add", "sub", "imul"):
            self.assertEqual(source.count("(як-є " + operation + "-r64-r64)"), 1)
        for predicate in ("додавання", "віднімання", "множення"):
            self.assertEqual(source.count(
                "(машинний-ефект-форма-" + predicate + "-64? ефект)"), 1)
        self.assertIn("(як-є x86-projection-rejected)", source)

    def test_quoted_data_and_verdict_labels_are_not_callable_aliases(self):
        projection = SOURCE.read_text(encoding="utf-8")
        parity = PARITY.read_text(encoding="utf-8")
        for literal in ("mov-r64-imm64", "rax", "rcx", "add-r64-r64",
                        "sub-r64-r64", "imul-r64-r64", "ret"):
            self.assertIn("(як-є " + literal + ")", projection)
        for literal in ("kind", "expected", "actual", "native-parity-case",
                        "execution-route", "native-or-route-mismatch"):
            self.assertIn("(як-є " + literal + ")", parity)


if __name__ == "__main__":
    unittest.main(verbosity=2)
