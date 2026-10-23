"""Регресія мігратора голів: український апостроф ≠ Lisp QUOTE.

Це тест міграційного сканера, НЕ свідчення SENS-виконання.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "migrate-exact-domain.py"
SPEC = importlib.util.spec_from_file_location("sens_migrate_exact_apostrophe", PATH)
assert SPEC is not None and SPEC.loader is not None
scanner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = scanner
SPEC.loader.exec_module(scanner)


class УкраїнськийАпострофПриМіграції(unittest.TestCase):
    def test_імя_не_поглинає_виклик_сід8(self):
        old = "00001100"
        source = (
            "; (00001100 7 8) — коментар\n"
            "(визначити ім'я\n"
            "  (функція (ім'я) (00001100 ім'я 1)))\n"
            "(як-є (00001100 ім'я))\n"
            "'(00001100 2 3)\n"
            "\"(00001100 ім'я)\"\n"
        )
        identity = scanner.Identity("D5", "01010", "PLUS", "додати")
        unresolved = []
        edits = scanner.plan(
            source, {}, legacy_heads={old: identity}, unresolved=unresolved
        )
        self.assertEqual(unresolved, [])
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0].source, old)
        self.assertEqual(edits[0].identity.domain, "D5")
        self.assertEqual(edits[0].identity.bits, "01010")

        migrated = scanner.apply_edits(source, edits)
        self.assertIn("(додати ім'я 1)", migrated)
        self.assertIn("\"(00001100 ім'я)\"", migrated)
        self.assertIn("'(00001100 2 3)", migrated)
        self.assertIn("; (00001100 7 8)", migrated)
        self.assertIn('"(00001100 ім\\'я)"', migrated)
        self.assertEqual(migrated.count("(додати"), 1)

    def test_окремий_апостроф_залишається_цитуванням(self):
        identity = scanner.Identity("D5", "01010", "PLUS", "додати")
        source = "'(00001100 2 3)\n(00001100 1 2)\n"
        edits = scanner.plan(source, {}, legacy_heads={"00001100": identity})
        self.assertEqual(len(edits), 1)
        self.assertEqual(scanner.apply_edits(source, edits),
                         "'(00001100 2 3)\n(додати 1 2)\n")


if __name__ == "__main__":
    unittest.main()
