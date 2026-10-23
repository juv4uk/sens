"""Перевірка актуальної драбини D1–D10 та історичного SID8 crosswalk.

Це тест джерельної цілісності координат і української проєкції;
він НЕ підміняє виконання СЕНС або фізичне T5M roundtrip.
"""
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/migrate-domain-ladder-source-batch.py"
spec = importlib.util.spec_from_file_location("sens_exact_2046", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("мігратор доменної драбини відсутній")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class ExactWidth2046(unittest.TestCase):
    def test_all_ratified_coordinates_without_invented_callability(self):
        actual = mod.verify_full_domain_bitspace(ROOT)
        self.assertEqual(actual["typed_coordinates"], 2046)
        self.assertEqual(actual["meaningful_bits"], 18434)
        self.assertEqual(actual["counts_by_domain"], {
            f"D{width}": 1 << width for width in range(1, 11)
        })
        self.assertEqual(actual["runtime_admission_claims_added"], 0)

    def test_legacy_to_ukr_requires_current_domain_identity(self):
        mapping, blocked = mod.authority(ROOT)
        self.assertEqual((len(mapping), len(blocked)), (171, 85))
        self.assertEqual(mapping["00001001"], "визначити")
        self.assertEqual(mapping["00000011"], "тотожне?")
        self.assertEqual(mapping["00000100"], "сполучити")
        for old in ("10101000", "01011010", "00110111"):
            self.assertNotIn(old, mapping)
            self.assertIn(old, blocked)
        self.assertEqual(len(set(mapping) | set(blocked)), 256)
        self.assertFalse(set(mapping) & set(blocked))
        for old, spelling in mapping.items():
            self.assertRegex(old, r"^[01]{8}$")
            self.assertTrue(spelling)
            self.assertNotRegex(spelling, r"^[01]+$")
        # Колізія бітового payload не перетворює старий DEFINE на D8.
        d8 = (ROOT / "lib/domains/d8.lisp").read_text(encoding="utf-8")
        self.assertIn("(00001001 (ук підмножина?) (укр підмножина?)", d8)
        self.assertNotEqual(mapping["00001001"], "підмножина?")

    def test_different_widths_never_form_the_same_identity(self):
        pairs = (((3, "010"), (4, "0010")),
                 ((7, "1000001"), (8, "01000001")),
                 ((9, "000000001"), (10, "0000000001")))
        for left, right in pairs:
            self.assertNotEqual(left, right)

    def test_d7_text_is_never_callable_by_table_mutation(self):
        self.corrupt("d7", 65, {"lisp": "CAR"}, "D7 v2 text coordinate drift")

    def test_d7_word_cannot_silently_widen_to_8_bits(self):
        self.corrupt("d7", 65, {"bits": "01000001"}, "wrong-width coordinate")

    def test_d10_duplicate_address_is_rejected(self):
        self.corrupt("d10", 0, {"bits": "0000000001"}, "duplicate or wrong-width")

    def corrupt(self, domain, index, changes, reason):
        original = mod.read_domain_table

        def altered(path):
            rows = original(path)
            if path.stem == domain:
                rows[index] = replace(rows[index], **changes)
            return rows

        with patch.object(mod, "read_domain_table", side_effect=altered):
            with self.assertRaisesRegex(ValueError, reason):
                mod.verify_full_domain_bitspace(ROOT)


if __name__ == "__main__":
    unittest.main()
