#!/usr/bin/env python3
"""Чинний Core: українські виклики й D1-макроси без історичного SID8.

Це перевірка джерельного контракту, НЕ Python-симуляція SENS.
Виконання перевіряє crates/sens/tests/core_postcore_ukr.rs.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/core.lisp"

REQUIRED = (
    "(визначити тотожність",
    "(визначити решта-першого",
    "(визначити перше-першого",
    "(визначити решта-решти",
    "(визначити та (макрос",
    "(визначити або (макрос",
)
TRUE_D1 = "((порожній? аргументи) (атом? (як-є ())))"
FALSE_D1 = "((порожній? аргументи) (атом? (сполучити (як-є ()) (як-є ()))))"


def check_current_core_source(source: str) -> None:
    # Історичні W8-опкоди не можна видавати за чинну функцію.
    # Жодного SHA-піну старого стану: перевіряємо поточне джерело.
    raw = re.search(r"(?m)^\s*\([01]{8}(?=\s|\))", source)
    if raw:
        raise ValueError("LEGACY_W8_CALL_HEAD")
    for expression in REQUIRED:
        if expression not in source:
            raise ValueError(f"MISSING_CURRENT_UKR_CORE {expression}")
    if TRUE_D1 not in source or FALSE_D1 not in source:
        raise ValueError("D1_ZERO_ARITY_MACROS_MUST_RETURN_PREDICATE")
    if "((порожній? аргументи) (як-є так))" in source:
        raise ValueError("QUOTED_TRUE_IS_NOT_D1")
    if "((порожній? аргументи) (як-є ні))" in source:
        raise ValueError("QUOTED_FALSE_IS_NOT_D1")


class CoreHelperCutoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = SOURCE.read_text(encoding="utf-8")

    def test_current_ukrainian_core_without_w8_execution(self):
        check_current_core_source(self.src)

    def test_no_english_executable_define_heads(self):
        self.assertNotRegex(self.src, r"(?m)^\s*\((?:define|def|0011)\s+")
        self.assertNotRegex(self.src, r"(?m)^\s*\((?:00011111|00100000)\s+")

    def test_quoted_d1_mutants_rejected(self):
        for old, bad in (
            (TRUE_D1, "((порожній? аргументи) (як-є так))"),
            (FALSE_D1, "((порожній? аргументи) (як-є ні))"),
        ):
            with self.subTest(bad=bad):
                mutant = self.src.replace(old, bad, 1)
                self.assertNotEqual(mutant, self.src)
                with self.assertRaises(ValueError):
                    check_current_core_source(mutant)

    def test_historical_w8_call_head_rejected(self):
        mutant = self.src.replace("(перше (решта значення-функції))",
                                  "(00011111 (решта значення-функції))", 1)
        self.assertNotEqual(mutant, self.src)
        with self.assertRaisesRegex(ValueError, "LEGACY_W8_CALL_HEAD"):
            check_current_core_source(mutant)


if __name__ == "__main__":
    unittest.main()
