#!/usr/bin/env python3
"""Контракти окремих слів: пробіл зберігає межу домену, не є нульовим байтом."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-sens-domain-spaces.py"
SPEC = importlib.util.spec_from_file_location("sens_domain_spaces", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class DomainSpaceFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.widths = mod.domain_widths(
            ROOT / "knowledge" / "d1-d11-foundation.json",
            ROOT / "contracts" / "numeric-domains-ratification.lisp",
        )

    def audit(self, text, *, suffix=".bits"):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / f"candidate{suffix}"
            path.write_bytes(text.encode("utf-8"))
            return mod.analyze(path, self.widths)

    def test_quote_empty_list_keeps_five_separate_words(self):
        report = self.audit("10 001 00 000 01")
        self.assertEqual(report["domain_widths"], [2, 3, 2, 3, 2])
        self.assertEqual(report["semantic_bits"], 12)
        self.assertEqual(report["separator_spaces"], 4)
        self.assertEqual(report["view_bytes"], 16)
        self.assertEqual(report["view_storage_bits"], 128)
        self.assertEqual(report["status"], "VISIBLE_WORD_VIEW_ONLY_NOT_ORACLE_VERIFIED")
        self.assertFalse(report["physical_codec_invoked"])

    def test_quote_nested_list_keeps_seven_separate_words(self):
        report = self.audit("10 001 00 10 000 01 01")
        self.assertEqual(report["domain_widths"], [2, 3, 2, 2, 3, 2, 2])
        self.assertEqual(report["semantic_bits"], 16)
        self.assertEqual(report["view_bytes"], 22)
        self.assertEqual(report["physical_carrier"], "NOT_READ_ZIG_T5M")

    def test_identical_concatenation_retains_distinct_domain_boundaries(self):
        a = self.audit("1 01")
        b = self.audit("10 1")
        self.assertEqual(a["semantic_bits"], b["semantic_bits"])
        self.assertEqual(a["domain_widths"], [1, 2])
        self.assertEqual(b["domain_widths"], [2, 1])
        self.assertNotEqual(a["domain_widths"], b["domain_widths"])

    def test_d12_number_word_is_visible(self):
        report = self.audit("0" * 11 + "1")
        self.assertEqual(report["domain_widths"], [12])
        self.assertFalse(report["reader_oracle_validated"])

    def test_number_word_width_is_distinct_from_d7_digit_text(self):
        report = self.audit("0" * 23 + "1")
        self.assertEqual(report["domain_widths"], [24])
        self.assertFalse(report["reader_oracle_validated"])

    def test_invalid_no_separators_as_one_unratified_width(self):
        with self.assertRaisesRegex(ValueError, "unsupported word widths"):
            self.audit("1000100000010")

    def test_double_space_is_not_normalized(self):
        with self.assertRaisesRegex(ValueError, "single ASCII spaces"):
            self.audit("10  001")

    def test_ends_and_start_space_are_rejected(self):
        for payload in (" 10 001", "10 001 ", " "):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, "single ASCII spaces"):
                    self.audit(payload)

    def test_newlines_tabs_and_crlf_are_not_silent_domain_separators(self):
        for payload in ("10\n001", "10\t001", "10\r\n001"):
            with self.subTest(payload=repr(payload)):
                with self.assertRaisesRegex(ValueError, "single ASCII spaces"):
                    self.audit(payload)

    def test_only_literal_binary_digits(self):
        for payload in ("10 D3:001", "(QUOTE ())", "10 x 001"):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, "single ASCII spaces"):
                    self.audit(payload)

    def test_empty_and_non_sens_files_rejected(self):
        with self.assertRaisesRegex(ValueError, "nonempty"):
            self.audit("")
        for suffix in (".lisp", ".sens"):
            with self.subTest(suffix=suffix):
                with self.assertRaisesRegex(ValueError, r"textual \.bits word view"):
                    self.audit("10 001", suffix=suffix)

    def test_view_storage_is_never_claimed_as_physical_t5m(self):
        for payload in ("1", "10", "11110110", "10 001 00 000 01"):
            with self.subTest(payload=payload):
                report = self.audit(payload)
                self.assertGreater(report["view_storage_bits"], report["semantic_bits"])
                self.assertEqual(
                    report["view_storage_bits"], 8 * (
                        report["semantic_bits"] + report["separator_spaces"]
                    )
                )
                self.assertNotIn("physical_bit_exact", report)
                self.assertEqual(report["physical_carrier"], "NOT_READ_ZIG_T5M")

    def test_current_d10_and_d11_word_widths_are_visible_not_callable_proofs(self):
        self.assertIn(10, self.widths)
        self.assertIn(11, self.widths)
        report = self.audit("0" * 10 + " " + "0" * 11)
        self.assertEqual(report["domain_widths"], [10, 11])
        self.assertFalse(report["reader_oracle_validated"])
        self.assertEqual(report["physical_carrier"], "NOT_READ_ZIG_T5M")


if __name__ == "__main__":
    unittest.main()
