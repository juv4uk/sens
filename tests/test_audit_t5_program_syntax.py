#!/usr/bin/env python3
"""Regression: packed T5 exact-width validity is NOT sufficient D2 syntax."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_t5_program_syntax import audit, main
from sens_t5_codec import encode_words


class AuditT5D2SyntaxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidate = os.environ.get("SENS_TRIT_BIN")
        if not candidate or not Path(candidate).is_file():
            raise RuntimeError(
                "set SENS_TRIT_BIN to built Rust sens-trit: "
                "cargo build -p sens-cli --bin sens-trit"
            )
        cls.reader = Path(candidate).resolve()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def pair(self, stem: str, source: str, words: list[str]) -> Path:
        lisp = self.root / f"{stem}.lisp"
        lisp.parent.mkdir(parents=True, exist_ok=True)
        lisp.write_text(source, encoding="utf-8")
        path = self.root / f"{stem}.sens"
        path.write_bytes(encode_words(words))
        return path

    def examine(self, *, strict=False):
        return audit(self.root, reader=self.reader, include_untracked=True,
                     strict_source=strict)

    def test_no_files_never_counts_as_migration_success(self):
        report = self.examine()
        self.assertEqual(report["status"], "NO_FILES")
        self.assertTrue(report["empty_is_not_certification"])
        self.assertEqual(report["summary"]["executable_semantics_certified"], 0)
        self.assertEqual(
            main([str(self.root), "--reader", str(self.reader), "--include-untracked",
                  "--require-files"]), 2
        )

    def test_valid_d2_single_and_multiple_roots(self):
        cases = {
            "atom": "000",
            "empty": "10 01",
            "nested": "10 001 00 10 000 01 01",
            "tworoots": "10 01 10 000 01",
        }
        for name, text in cases.items():
            self.pair(name, text + "\n", text.split())
        report = self.examine(strict=True)
        self.assertEqual(report["status"], "SYNTAX_ONLY")
        self.assertEqual(report["summary"]["d2_syntax_pass"], 4)
        self.assertEqual(report["summary"]["executable_semantics_certified"], 0)
        self.assertTrue(all(
            row["syntax_status"] == "PASS_D2_SYNTAX" for row in report["files"]
        ))

    def test_binary_word_transport_valid_but_unexpected_close_is_not_a_program(self):
        # One exact D2 CLOSE is perfectly valid as a physical typed word.
        # It is not a complete D2 program: the Rust parser must reject it.
        self.pair("close", "01\n", ["01"])
        report = self.examine()
        self.assertEqual(report["summary"]["physical_pass"], 1)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["summary"]["d2_syntax_blocked"], 1)
        self.assertIn("Rust D2 reader rejected", report["files"][0]["syntax_reason"])
        self.assertIn("D2 grammar rejected", report["files"][0]["syntax_reason"])
        self.assertIn("one exact typed word per line",
                      report["files"][0]["d2_word_coordinate_diagnostic"])
        self.assertEqual(report["files"][0]["oracle_status"], "NOT_VERIFIED")

    def test_missing_close_is_not_made_complete_by_byte_eof(self):
        self.pair("truncated-form", "10 001\n", ["10", "001"])
        report = self.examine()
        self.assertEqual(report["summary"]["physical_pass"], 1)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["summary"]["d2_syntax_pass"], 0)

    def test_nested_truncated_d2_identifies_unclosed_exact_word_coordinates(self):
        # The 2-bit words form an unclosed outer list despite physical
        # T5 roundtrip. One-based indices and original widths are preserved.
        self.pair("nested-unclosed", "10 001 00 10 000 01\\n",
                  ["10", "001", "00", "10", "000", "01"])
        row = self.examine()["files"][0]
        self.assertEqual(row["syntax_status"], "BLOCKED")
        hint = row["d2_structure_balance_hint"]
        self.assertEqual(hint["typed_word_count"], 6)
        self.assertEqual(hint["d2_opens"], 2)
        self.assertEqual(hint["d2_closes"], 1)
        self.assertEqual(hint["unclosed_open_count"], 1)
        self.assertEqual(hint["first_unclosed_open_word"], 1)
        self.assertEqual(hint["last_unclosed_open_word"], 1)
        self.assertEqual(hint["unclosed_open_contexts"][0]["typed_words"],
                         ["10", "001", "00", "10"])
        self.assertIn("D2 grammar rejected", row["syntax_reason"])
        self.assertEqual(row["oracle_status"], "NOT_VERIFIED")

    def test_d2_unexpected_close_hint_does_not_grant_syntax_or_semantics(self):
        self.pair("underflow", "01 10 01\\n", ["01", "10", "01"])
        row = self.examine()["files"][0]
        self.assertEqual(row["syntax_status"], "BLOCKED")
        hint = row["d2_structure_balance_hint"]
        self.assertEqual(hint["first_unmatched_close_word"], 1)
        self.assertEqual(hint["unclosed_open_count"], 0)
        self.assertEqual(row["oracle_status"], "NOT_VERIFIED")

    def test_d2_nested_valid_pair_gets_no_failure_hint(self):
        self.pair("nested-ok", "10 10 000 01 01\\n",
                  ["10", "10", "000", "01", "01"])
        row = self.examine()["files"][0]
        self.assertEqual(row["syntax_status"], "PASS_D2_SYNTAX")
        self.assertNotIn("d2_structure_balance_hint", row)

    def test_malformed_byte_rejected_before_rust_grammar(self):
        path = self.pair("corrupt", "10 01\n", ["10", "01"])
        path.write_bytes(b"\xf3")  # not valid T5 five-trit byte
        row = self.examine()["files"][0]
        self.assertEqual(row["physical_status"], "BLOCKED")
        self.assertEqual(row["syntax_status"], "BLOCKED")

    def test_symbolic_source_syntax_pass_but_oracle_still_pending(self):
        self.pair("symbolic", "()\n", ["000"])
        report = self.examine()
        self.assertEqual(report["status"], "SYNTAX_ONLY")
        self.assertEqual(report["summary"]["symbolic_source_pending_oracle"], 1)
        self.assertEqual(report["summary"]["executable_semantics_certified"], 0)
        self.assertEqual(self.examine(strict=True)["status"], "BLOCKED")

    def test_typed_boundary_collision_is_preserved_not_guessed(self):
        a = self.pair("a", "01 000\n", ["01", "000"])
        b = self.pair("b", "01000\n", ["01000"])
        self.assertNotEqual(a.read_bytes(), b.read_bytes())
        # Naked D2 CLOSE is not a legal top-level expression, but D5 atom is.
        report = self.examine()
        self.assertEqual(report["summary"]["physical_pass"], 2)
        self.assertEqual(report["summary"]["d2_syntax_pass"], 1)
        self.assertEqual(report["summary"]["d2_syntax_blocked"], 1)

    def test_cli_report_is_read_only(self):
        self.pair("case", "10 01\n", ["10", "01"])
        report_path = self.root / "audit.json"
        rc = main([str(self.root), "--reader", str(self.reader),
                   "--include-untracked", "--output", str(report_path)])
        self.assertEqual(rc, 0)
        self.assertTrue(report_path.is_file())
        self.assertEqual(list(self.root.rglob("*.sens")), [self.root / "case.sens"])


if __name__ == "__main__":
    unittest.main()
