#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SCRIPT = SCRIPTS / "classify-lisp-source-forms.py"
SPEC = importlib.util.spec_from_file_location("classify_forms", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

from sens_source_resolver import build_resolver

HIST = ROOT / "contracts" / "core1-historical-sid-map.lisp"
FOUNDATION = ROOT / "knowledge" / "d1-d7-foundation.json"
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
SURFACES = [
    ROOT / "lib" / "surface" / "domain-surfaces-d1-d4.lisp",
    ROOT / "lib" / "surface" / "domain-surfaces-d5.lisp",
]


class ThreePassClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolver = build_resolver(
            historical_map=HIST,
            foundation=FOUNDATION,
            registry=REGISTRY,
            domain_surfaces=SURFACES,
        )

    def classify(self, source: str):
        heads = mod.scan_heads("sample.lisp", source)
        return mod.classify_heads(heads, self.resolver)

    def test_pass1_detects_legacy_sid8_and_resolves_current_car(self):
        historical, current, dynamic, empty = self.classify("(00000101 x)\n")
        self.assertFalse(current)
        self.assertFalse(dynamic)
        self.assertFalse(empty)
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual((hit.pass_number, hit.representation), (1, "sid8-sens8"))
        self.assertEqual(hit.legacy_sid8, "00000101")
        self.assertEqual((hit.current_domain, hit.current_bits, hit.current_label), ("D3", "100", "CAR"))

    def test_pass1_uses_named_registry_role_not_bit_shape_for_map(self):
        historical, _, _, _ = self.classify("(00110111 f xs)\n")
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual(hit.pass_number, 1)
        self.assertEqual((hit.current_domain, hit.current_bits, hit.current_label), ("D6", "101000", "MAP"))

    def test_pass2_detects_known_my_lisp_surface(self):
        historical, _, dynamic, _ = self.classify("(car x)\n")
        self.assertFalse(dynamic)
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual((hit.pass_number, hit.representation), (2, "my-lisp-surface"))
        self.assertEqual((hit.current_domain, hit.current_bits), ("D3", "100"))

    def test_pass2_detects_symbolic_and_ukrainian_surfaces(self):
        for source, bits in [
            ("(+ a b)\n", "01010"),
            ("(додати a b)\n", "01010"),
            ("(атом? x)\n", "010"),
        ]:
            historical, _, dynamic, _ = self.classify(source)
            self.assertFalse(dynamic, source)
            self.assertEqual(len(historical), 1, source)
            self.assertEqual(historical[0].pass_number, 2, source)
            self.assertEqual(historical[0].current_bits, bits, source)

    def test_pass3_detects_uppercase_lisp_1_5(self):
        historical, _, dynamic, _ = self.classify("(PLUS a b)\n")
        self.assertFalse(dynamic)
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual((hit.pass_number, hit.representation), (3, "lisp1-1.5-uppercase"))
        self.assertEqual((hit.current_domain, hit.current_bits, hit.current_label), ("D5", "01010", "PLUS"))

    def test_current_exact_head_is_not_reclassified_as_historical(self):
        historical, current, dynamic, _ = self.classify("(100 x)\n")
        self.assertFalse(historical)
        self.assertFalse(dynamic)
        self.assertEqual(len(current), 1)
        self.assertEqual((current[0].current_domain, current[0].current_label), ("D3", "CAR"))

    def test_empty_list_is_structural_inventory_not_function_pass(self):
        historical, current, dynamic, empty = self.classify("(cons x ())\n")
        self.assertEqual([(h.pass_number, h.token) for h in historical], [(2, "cons")])
        self.assertFalse(current)
        self.assertFalse(dynamic)
        self.assertEqual([h.token for h in empty], ["()"])

    def test_unknown_user_call_head_is_dynamic_not_fake_my_lisp(self):
        historical, current, dynamic, empty = self.classify("(sqrt-iter x n)\n")
        self.assertFalse(historical)
        self.assertFalse(current)
        self.assertFalse(empty)
        self.assertEqual([h.token for h in dynamic], ["sqrt-iter"])

    def test_three_real_generations_are_separated_and_clause_symbols_are_not_pass2(self):
        source = """
(00000100 a b)
(car x)
(COND (p a) (T b))
"""
        historical, _, dynamic, _ = self.classify(source)
        self.assertEqual(
            [(hit.pass_number, hit.token) for hit in historical],
            [(1, "00000100"), (2, "car"), (3, "COND")],
        )
        # The lexical scanner still sees p/T as list heads inside old COND
        # clause containers, but crucially they are NOT mislabeled as pass 2.
        self.assertEqual([head.token for head in dynamic], ["p", "T"])

    def test_comments_strings_and_reader_quoted_data_do_not_count(self):
        source = """
; (00000101 x)
'(CAR x)
#| (PLUS a b) |#
(car "CAR")
"""
        historical, current, dynamic, empty = self.classify(source)
        self.assertEqual([(hit.pass_number, hit.token) for hit in historical], [(2, "car")])
        self.assertFalse(current)
        self.assertFalse(dynamic)
        self.assertFalse(empty)

    def test_uppercase_define_collapses_two_legacy_candidates_to_one_current_identity(self):
        historical, _, dynamic, _ = self.classify("(DEFINE foo x)\n")
        self.assertFalse(dynamic)
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual(hit.pass_number, 3)
        self.assertEqual((hit.current_domain, hit.current_bits, hit.current_label), ("D4", "0011", "DEFINE"))
        self.assertEqual(hit.resolution, "resolved")

    def test_unknown_eight_bit_head_is_pass1_but_unresolved(self):
        historical, _, dynamic, _ = self.classify("(11111111 x)\n")
        self.assertFalse(dynamic)
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual(hit.pass_number, 1)
        self.assertEqual(hit.resolution, "legacy-unmapped")
        self.assertEqual(hit.legacy_sid8, "11111111")

    def test_old_registry_function_without_current_domain_is_legacy_unmapped(self):
        historical, _, dynamic, _ = self.classify("(01001000 x)\n")
        self.assertFalse(dynamic)
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual(hit.pass_number, 1)
        self.assertEqual(hit.legacy_sid8, "01001000")
        self.assertEqual(hit.resolution, "legacy-unmapped")
        self.assertEqual(hit.current_domain, "")


if __name__ == "__main__":
    unittest.main()
