"""Точкова перевірка ратифікованої української проєкції вектора.
Це не замінює реального виконання СЕНС у тестах Rust.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib" / "persistent-vector.lisp"
D9 = ROOT / "lib" / "domains" / "d9.lisp"

RESIDENTS = {
    "101010111": "вектор-кількість",
    "101011000": "вектор-список",
    "101011101": "вектор-додати",
    "101101101": "вектор-порожній",
    "101111011": "вектор-з-список",
    "110000010": "вектор-н-тий",
}
ROW = re.compile(r"^\s*\(([01]{9})\s+\(ук\s+[^()\s]+\)\s+\(укр\s+([^()\s]+)\)", re.MULTILINE)


class PersistentVectorUkrPrimaryProjectionTests(unittest.TestCase):
    def test_all_source_characters_are_on_ukrainian_keyboard(self):
        source = SOURCE.read_text(encoding="utf-8")
        allowed = set("абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
                      "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
                      "0123456789 ();\'-+*/:,.!?%№=\\\"_" + chr(9) + chr(10) + chr(13))
        unexpected = set(source) - allowed
        self.assertEqual(unexpected, set(), f"Символи поза українською розкладкою: {unexpected}")

    def test_d9_exact_ukrainian_residents(self):
        table = D9.read_text(encoding="utf-8")
        rows = dict(ROW.findall(table))
        source = SOURCE.read_text(encoding="utf-8")
        definitions = re.findall(r"(?m)^\(визначити\s+([^\s()]+)\s", source)
        self.assertEqual(len(definitions), len(set(definitions)))
        for bits, name in RESIDENTS.items():
            with self.subTest(bits=bits, name=name):
                self.assertEqual(rows.get(bits), name)
                self.assertIn(name, definitions)
        self.assertNotRegex(source, r"(?m)^\(визначити\s+vec[->]")
        self.assertNotRegex(source, r"\(\s*[01]{9}(?:\s|\))")

    def test_core4_does_not_restore_mixed_keyboard_alias_definitions(self):
        # D7 identifiers are not an English/Cyrillic mixture. These historical
        # aliases duplicate already-defined Ukrainian closures and never
        # represent a distinct ratified call mechanism.
        core = (ROOT / "lib/core4.lisp").read_text(encoding="utf-8")
        names = re.findall(r"(?m)^\(визначити\s+([^\s()]+)", core)
        mixed = [
            name for name in names
            if re.search(r"[A-Za-z]", name)
            and re.search(r"[\u0400-\u052F]", name)
        ]
        self.assertEqual(mixed, [], f"D7 змішані виконавчі аліаси: {mixed}")
        self.assertIn("(визначити вектор-н-тий елемент-списку-за-індексом)", core)
        self.assertIn("(визначити кліпс-змінна-терм", core)

    def test_d9_import_script_uses_canonical_ukrainian_resident(self):
        source = (ROOT / "scripts/apply-d9-map-vec-list-batch.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('("мапа-отримати", "вектор-н-тий")', source)
        self.assertNotIn('"вектор-n-тий"', source)

    def test_calls_of_vector_are_ukrainian(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("(визначити вектор-з-список", source)
        self.assertIn("(вектор-додати ", source)
        self.assertIn("(вектор-кількість ", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
