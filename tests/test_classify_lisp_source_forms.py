#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "classify-lisp-source-forms.py"
SPEC = importlib.util.spec_from_file_location("classify_forms", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

CONTRACT = ROOT / "contracts" / "core1-historical-sid-map.lisp"


class ThreePassClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.by_sid, cls.by_my, cls.by_hist = mod.load_mapping(CONTRACT)

    def classify(self, source: str):
        heads = mod.scan_heads("sample.lisp", source)
        return mod.classify_three_passes(
            heads, self.by_sid, self.by_my, self.by_hist
        )

    def test_pass1_detects_legacy_sid8_head(self):
        hits = self.classify("(00000101 x)\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].pass_number, 1)
        self.assertEqual(hits[0].representation, "sid8-sens8")
        self.assertEqual(hits[0].my_lisp, "car")
        self.assertEqual(hits[0].historical, "CAR")

    def test_pass2_detects_my_lisp_head(self):
        hits = self.classify("(car x)\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].pass_number, 2)
        self.assertEqual(hits[0].sid8, "00000101")

    def test_pass2_detects_symbolic_my_lisp_head(self):
        hits = self.classify("(+ a b)\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].pass_number, 2)
        self.assertEqual(hits[0].historical, "PLUS")

    def test_pass2_detects_empty_list_literal(self):
        hits = self.classify("(cons x ())\n")
        self.assertEqual(
            [(hit.pass_number, hit.token, hit.my_lisp) for hit in hits],
            [(2, "cons", "cons"), (2, "()", "empty-list")],
        )

    def test_pass3_detects_uppercase_lisp_1_5_head(self):
        hits = self.classify("(PLUS a b)\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].pass_number, 3)
        self.assertEqual(hits[0].my_lisp, "+")
        self.assertEqual(hits[0].sid8, "00001100")

    def test_three_forms_in_one_file_are_separated_by_pass(self):
        source = """
(00000100 a b)
(car x)
(COND (p a) (T b))
"""
        hits = self.classify(source)
        self.assertEqual(
            [(hit.pass_number, hit.token) for hit in hits],
            [(1, "00000100"), (2, "car"), (3, "COND")],
        )

    def test_comments_strings_and_quoted_data_do_not_count(self):
        source = """
; (00000101 x)
'(CAR x)
#| (PLUS a b) |#
(car "CAR")
"""
        hits = self.classify(source)
        self.assertEqual([(hit.pass_number, hit.token) for hit in hits], [(2, "car")])

    def test_lowercase_historical_apply_is_my_lisp_pass2(self):
        hits = self.classify("(apply f xs)\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].pass_number, 2)

    def test_uppercase_apply_is_historical_pass3(self):
        hits = self.classify("(APPLY f xs)\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].pass_number, 3)
        self.assertEqual(hits[0].sid8, "10101111")


    def test_uppercase_define_preserves_both_legacy_sid_candidates(self):
        hits = self.classify("(DEFINE foo x)\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].pass_number, 3)
        self.assertEqual(
            set(hits[0].sid8.split("|")),
            {"00001001", "00001011"},
        )

    def test_comment_between_open_paren_and_head_is_ignored(self):
        hits = self.classify("( ; comment before head\n car x)\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].pass_number, 2)
        self.assertEqual(hits[0].token, "car")

    def test_unknown_eight_bit_head_is_still_pass1_unmapped(self):
        hits = self.classify("(11111111 x)\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].pass_number, 1)
        self.assertEqual(hits[0].status, "unmapped")
        self.assertEqual(hits[0].sid8, "11111111")

    def test_user_defined_lowercase_head_is_my_lisp_pass2_unmapped(self):
        hits = self.classify("(sqrt-iter x n)\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].pass_number, 2)
        self.assertEqual(hits[0].status, "unmapped")


if __name__ == "__main__":
    unittest.main()
