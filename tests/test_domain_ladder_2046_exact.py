"""Exhaustive 2046-cell D1–D10 witness for historical SID8 migration.

A ratified coordinate is NOT automatically a callable runtime mechanism.
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
    raise RuntimeError("SID8 source migrator missing")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class ExactWidth2046(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = mod.exact_domain_catalog(ROOT)

    def test_full_2046_codes_and_exact_bit_mass(self):
        self.assertEqual(self.c["count"], 2046)
        self.assertEqual(self.c["widths"], {f"D{w}": 1 << w for w in range(1, 11)})
        self.assertEqual(self.c["address_bits"], 18434)
        self.assertEqual(self.c["min_packed_bytes"], 2305)
        self.assertFalse(self.c["callable_inferred"])
        for width in range(1, 11):
            for value in range(1 << width):
                self.assertIn((width, format(value, f"0{width}b")), self.c["identities"])
        for width, bits in ((7, "0100001"), (7, "0101010")):
            self.assertIn((width, bits), self.c["identities"])

    def test_different_width_means_different_function_identity(self):
        pairs = (((3, "010"), (4, "0010")),
                 ((7, "1000001"), (8, "01000001")),
                 ((9, "000000001"), (10, "0000000001")))
        for left, right in pairs:
            self.assertIn(left, self.c["identities"])
            self.assertIn(right, self.c["identities"])
            self.assertNotEqual(left, right)

    def test_legacy_256_cells_only_171_admitted(self):
        mapping, blocked = mod.authority(ROOT)
        self.assertEqual((len(mapping), len(blocked)), (171, 85))
        self.assertEqual(mapping["00001001"], "0011")
        self.assertEqual(mapping["00000011"], "101")
        for old in ("10101000", "01011010", "00110111"):
            self.assertNotIn(old, mapping)
            self.assertIn(old, blocked)
        for bits in mapping.values():
            self.assertIn((len(bits), bits), self.c["identities"])

    def test_d7_cannot_mint_lisp_callable(self):
        self.corrupt("d7", 65, {"lisp": "CAR"}, "data/callability drift")

    def test_d7_cannot_be_widened_to_w8(self):
        self.corrupt("d7", 65, {"bits": "01000001"}, "changed coordinate")

    def test_d10_cannot_be_reordered_even_when_full(self):
        original = mod.read_domain_table
        def swapped(path):
            rows = original(path)
            if path.stem == "d10":
                rows[0], rows[1] = rows[1], rows[0]
            return rows
        with patch.object(mod, "read_domain_table", side_effect=swapped):
            with self.assertRaisesRegex(ValueError, "changed coordinate"):
                mod.exact_domain_catalog(ROOT)

    def corrupt(self, domain, index, changes, reason):
        original = mod.read_domain_table
        def invalid(path):
            rows = original(path)
            if path.stem == domain:
                rows[index] = replace(rows[index], **changes)
            return rows
        with patch.object(mod, "read_domain_table", side_effect=invalid):
            with self.assertRaisesRegex(ValueError, reason):
                mod.exact_domain_catalog(ROOT)


if __name__ == "__main__":
    unittest.main()
