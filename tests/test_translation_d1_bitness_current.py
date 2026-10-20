#!/usr/bin/env python3
"""Регресії поточної української перевірки перекладу; не SENS-eval."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
PATH = SCRIPTS / "test-translation-d1-bitness.py"
SPEC = importlib.util.spec_from_file_location("translation_d1_current_guard", PATH)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = guard
SPEC.loader.exec_module(guard)


class CurrentTranslationD1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = (ROOT / "lib/translation.lisp").read_text(encoding="utf-8")

    def test_real_current_ukrainian_source(self):
        self.assertEqual(guard.check_translation_text(self.source), [])
        self.assertEqual(guard.main(), 0)
        self.assertNotIn("(визначити translation-status ", self.source)

    def test_latin_definition_and_old_raw_d1_are_rejected(self):
        renamed = self.source.replace(
            "(визначити переклад-стан\n", "(визначити translation-status\n", 1
        )
        self.assertNotEqual(renamed, self.source)
        self.assertTrue(any(
            "англомовн" in reason for reason in guard.check_translation_text(renamed)
        ))
        raw = self.source.replace(
            "(функція (пропозиція)", "(функція (пропозиція) #d1:1", 1
        )
        self.assertNotEqual(raw, self.source)
        self.assertTrue(any(
            "машинний літерал" in reason for reason in guard.check_translation_text(raw)
        ))

    def test_quoted_protocol_data_is_not_reinterpreted_as_code(self):
        example = self.source + (
            "\n(визначити протокольний-свідок "
            "(як-є (translation-status t NIL #d1:1)))\n"
        )
        self.assertEqual(guard.check_translation_text(example), [])

    def test_duplicate_and_malformed_forms_are_rejected(self):
        duplicate = self.source + "\n(визначити переклад-стан (як-є ()))\n"
        self.assertTrue(any(
            "дубльовані" in reason for reason in guard.check_translation_text(duplicate)
        ))
        malformed = self.source + "\n(визначити незакрите ("
        self.assertTrue(any(
            "некоректна структура" in reason
            for reason in guard.check_translation_text(malformed)
        ))

    def test_exact_domain_widths_without_new_semantic_authority(self):
        for width in range(1, 11):
            with self.subTest(width=width):
                self.assertEqual(guard.check_domain(width), [])
        with self.subTest(missing="D1"):
            from tempfile import TemporaryDirectory
            with TemporaryDirectory() as temp:
                self.assertTrue(guard.check_domain(1, Path(temp)))


if __name__ == "__main__":
    unittest.main()
