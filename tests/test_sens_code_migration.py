#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-to-sens-codes.py"
SPEC = importlib.util.spec_from_file_location("sens_migrator", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

FOUNDATION = ROOT / "knowledge" / "d1-d7-foundation.json"
TEXT7 = ROOT / "crates" / "sens" / "src" / "text7_projection_generated.rs"
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
DOMAIN_SURFACES = [
    ROOT / "lib" / "surface" / "domain-surfaces-d1-d4.lisp",
    ROOT / "lib" / "surface" / "domain-surfaces-d5.lisp",
]


class SensCodeMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data, _ = mod.load_foundation(FOUNDATION)
        cls.data = data
        cls.code_map = mod.build_map(data, ["D3", "D4", "D5", "D6"])
        cls.code_map = mod.augment_code_map_with_domain_surfaces(
            cls.code_map, DOMAIN_SURFACES
        )
        cls.code_map = mod.augment_code_map_with_registry_aliases(
            cls.code_map, REGISTRY
        )
        cls.text7 = mod.build_text7_encoder(data, TEXT7)
        cls.legacy = mod.build_legacy_sid_map(REGISTRY, cls.code_map)

    def test_current_d3_authority_is_used(self):
        self.assertEqual(self.code_map["CAR"].bits, "100")
        self.assertEqual(self.code_map["CDR"].bits, "011")
        self.assertEqual(self.code_map["EQ"].bits, "101")
        self.assertEqual(self.code_map["COND"].bits, "110")

    def test_legacy_mirror_still_rewrites_only_call_heads(self):
        source = "(CONS (CAR x) (CDR y))\n"
        converted, hits, blocked = mod.rewrite(source, self.code_map)
        self.assertEqual(converted, "(111 (100 x) (011 y))\n")
        self.assertEqual(len(hits), 3)
        self.assertFalse(blocked)

    def test_empty_list_is_d3_empty_not_open_close(self):
        for source in ["()\n", "(   )\n"]:
            converted, hits, shadowed = mod.binary_rewrite(
                source, self.code_map, self.text7, self.legacy
            )
            self.assertEqual(converted, "000\n")
            self.assertFalse(hits)
            self.assertFalse(shadowed)

    def test_nested_empty_list_uses_000(self):
        converted, _, _ = mod.binary_rewrite(
            "(CONS () ())\n", self.code_map, self.text7, self.legacy
        )
        self.assertEqual(converted, "10 111 00 000 00 000 01\n")
        self.assertNotIn("10 01", converted)

    def test_function_surface_aliases_resolve_before_text7(self):
        cases = {
            "atom?": "010",
            "eq?": "101",
            "сполучити": "111",
            "aṇu?": "010",
            "додати": "01010",
            "+": "01010",
        }
        for surface, bits in cases.items():
            converted, hits, _ = mod.binary_rewrite(
                f"({surface} x)\n",
                self.code_map,
                self.text7,
                self.legacy,
            )
            self.assertTrue(converted.startswith(f"10 {bits} 00 "), (surface, converted))
            self.assertTrue(hits, surface)

    def test_binary_source_uses_d2_structure_and_exact_function_words(self):
        source = "(CONS (CAR x) (CDR y))\n"
        converted, hits, shadowed = mod.binary_rewrite(
            source, self.code_map, self.text7
        )
        # x = SLP1 0x50, y = SLP1 0x26.
        self.assertEqual(
            converted,
            "10 111 00 10 100 00 1010000 01 00 "
            "10 011 00 0100110 01 01\n",
        )
        self.assertEqual([hit.label for hit in hits], ["CONS", "CAR", "CDR"])
        self.assertFalse(shadowed)

    def test_legacy_sid8_call_heads_migrate_to_current_domains(self):
        cases = {
            "00000101": ("100", "CAR"),
            "00001001": ("0011", "DEFINE"),
            "00001100": ("01010", "PLUS"),
            "00110111": ("101000", "MAP"),
        }
        for sid8, (current, label) in cases.items():
            converted, hits, _ = mod.binary_rewrite(
                f"({sid8} x)\n",
                self.code_map,
                self.text7,
                self.legacy,
            )
            self.assertTrue(
                converted.startswith(f"10 {current} 00 "),
                (sid8, converted),
            )
            self.assertEqual(hits[0].label, label)

    def test_unmapped_legacy_sid8_call_head_fails_closed(self):
        # Legacy PRINT has no ratified D3-D6 coordinate in the current foundation.
        with self.assertRaises(mod.BinaryMigrationError):
            mod.binary_rewrite(
                "(01001000 x)\n",
                self.code_map,
                self.text7,
                self.legacy,
            )

    def test_current_exact_width_head_is_preserved(self):
        converted, _, _ = mod.binary_rewrite(
            "(100 x)\n",
            self.code_map,
            self.text7,
            self.legacy,
        )
        self.assertTrue(converted.startswith("10 100 00 "))

    def test_comments_are_absent_and_do_not_change_binary_output(self):
        commented = """; outside
(CAR ; inline
  #| outer #| nested |# block |#
  x)
"""
        plain = "(CAR x)\n"
        a, _, _ = mod.binary_rewrite(commented, self.code_map, self.text7)
        b, _, _ = mod.binary_rewrite(plain, self.code_map, self.text7)
        self.assertEqual(a, b)
        self.assertNotIn(";", a)
        self.assertNotIn("#", a)

    def test_comment_markers_inside_string_are_data_not_comments(self):
        source = '(LIST ";not-comment" "#|not-comment|#")\n'
        converted, hits, _ = mod.binary_rewrite(source, self.code_map, self.text7)
        self.assertTrue(converted.startswith("10 1110 "))
        self.assertEqual([hit.label for hit in hits], ["LIST"])
        self.assertRegex(converted, r"^[01\s]+$")

    def test_d7_digits_encode_source_spelling_not_number_domain(self):
        converted, _, _ = mod.binary_rewrite("(foo 25)\n", self.code_map, self.text7)
        # 2 -> text.digit.2 = 0011101; 5 -> text.digit.5 = 0111011.
        self.assertIn("0011101 0111011", converted)

    def test_quoted_call_head_is_text_not_callable_domain(self):
        converted, hits, _ = mod.binary_rewrite("'(CAR x)\n", self.code_map, self.text7)
        self.assertFalse(hits)
        # CAR must not appear as the D3 100 word when quoted.
        words = converted.split()
        self.assertNotEqual(words[words.index("10") + 1], "100")
        self.assertRegex(converted, r"^[01\s]+$")

    def test_standalone_dot_is_d2_dot_but_dot_inside_symbol_is_text7(self):
        dotted, _, _ = mod.binary_rewrite("(a . b)\n", self.code_map, self.text7)
        self.assertIn(" 11 ", dotted)
        symbol, _, _ = mod.binary_rewrite("(foo a.b)\n", self.code_map, self.text7)
        # Text7 sign.dot = 1111010.
        self.assertIn("1111010", symbol)

    def test_shadowed_builtin_stays_text7_in_binary_source(self):
        source = "(DEFUN CAR (x) x)\n(CAR y)\n"
        converted, hits, shadowed = mod.binary_rewrite(source, self.code_map, self.text7)
        self.assertIn("CAR", shadowed)
        self.assertFalse(any(hit.label == "CAR" for hit in hits))
        self.assertRegex(converted, r"^[01\s]+$")

    def test_unencodable_character_fails_closed(self):
        with self.assertRaises(mod.BinaryMigrationError):
            mod.binary_rewrite("(foo 🙂)\n", self.code_map, self.text7)

    def test_binary_output_is_ascii_bits_only(self):
        source = '(CONS "привіт" test-25)\n'
        converted, _, _ = mod.binary_rewrite(source, self.code_map, self.text7)
        self.assertRegex(converted, r"^[01\s]+$")
        converted.encode("ascii")


if __name__ == "__main__":
    unittest.main()
