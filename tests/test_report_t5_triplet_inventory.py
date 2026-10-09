#!/usr/bin/env python3
"""Незалежні негативні тести read-only інвентаризації SENS-трійок."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from report_t5_triplet_inventory import GOLDEN, inspect, main
from sens_t5_codec import encode_words


class TripletInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sens-t5-triplet-")
        self.root = Path(self.temp.name)
        self.words = ["10", "110", "00", "10", "0", "00", "000", "01", "01"]
        self.expected = (" ".join(self.words) + "\n").encode("ascii")
        self.physical = encode_words(self.words)
        self.source = self.root / "case.lisp"
        self.sens = self.root / "case.sens"
        self.view = self.root / "case"
        self.source.write_text("(за-умовою (так так))\n", encoding="utf-8")
        self.sens.write_bytes(self.physical)

    def tearDown(self):
        self.temp.cleanup()

    def scan(self, strict=False, required=("case.sens",)):
        return inspect(self.root, include_untracked=True,
                       strict=strict, required=required)

    def test_known_good_view_checks_typed_width_and_preserves_all_source_bytes(self):
        self.view.write_bytes(self.expected)
        before = (self.source.read_bytes(), self.sens.read_bytes(), self.view.read_bytes())
        result = self.scan(strict=True)
        self.assertEqual(result["status"], "PHYSICAL_VIEW_ONLY_UK_PENDING")
        self.assertEqual(result["failed_required"], [])
        self.assertEqual(result["summary"]["view_present_valid"], 1)
        self.assertEqual(result["summary"]["uk_oracle_verified"], 0)
        self.assertEqual(result["summary"]["release_admitted"], 0)
        self.assertEqual(result["summary"]["original_executable_migrations_certified"], 0)
        self.assertEqual(result["files"][0]["view_status"], "PHYSICAL_VIEW_PASS")
        self.assertEqual(before, (
            self.source.read_bytes(), self.sens.read_bytes(), self.view.read_bytes(),
        ))

    def test_missing_view_reports_real_debt_but_required_gate_blocks(self):
        report = self.scan(required=())
        self.assertEqual(report["status"], "INCOMPLETE_VIEWS")
        self.assertEqual(report["summary"]["view_missing"], 1)
        self.assertEqual(report["files"][0]["view_status"], "MISSING_VIEW")
        required = self.scan()
        self.assertEqual(required["status"], "BLOCKED")
        self.assertEqual(required["failed_required"], ["case.sens"])
        self.assertEqual(self.scan(strict=True)["status"], "BLOCKED")

    def test_noncanonical_ascii_views_are_rejected_byte_for_byte(self):
        variants = (
            b"",
            self.expected[:-1],
            self.expected + b"\n",
            b" " + self.expected,
            self.expected.replace(b" ", b"  ", 1),
            self.expected.replace(b" ", b"\t", 1),
            self.expected.replace(b"\n", b"\r\n"),
            self.expected.replace(b"0", b"2", 1),
            self.expected.replace(b"0", b"0b", 1),
            self.expected.replace(b"0", b"(", 1),
            self.expected.replace(b"0", "ні".encode("utf-8"), 1),
            self.expected.replace(b"10 ", b"1 0 ", 1),
            self.expected.replace(b"000 ", b"00 0 ", 1),
        )
        for variant in variants:
            with self.subTest(variant=variant):
                self.view.write_bytes(variant)
                result = self.scan()
                self.assertEqual(result["status"], "BLOCKED")
                self.assertEqual(result["files"][0]["view_status"], "VIEW_MISMATCH")
                self.assertEqual(result["summary"]["view_present_valid"], 0)

    def test_exact_word_width_collision_has_distinct_transport_bytes(self):
        left = ["0", "00", "000"]
        right = ["000", "00", "0"]
        self.assertNotEqual(encode_words(left), encode_words(right))
        self.sens.write_bytes(encode_words(left))
        self.view.write_bytes((" ".join(right) + "\n").encode("ascii"))
        row = self.scan()["files"][0]
        self.assertEqual(row["view_status"], "VIEW_MISMATCH")

    def test_physical_corruption_does_not_turn_view_into_admission(self):
        self.view.write_bytes(self.expected)
        self.sens.write_bytes(b"\xf3")
        report = self.scan()
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["files"][0]["physical_status"], "BLOCKED")
        self.assertEqual(report["files"][0]["view_status"], "PHYSICAL_BLOCKED")
        self.assertEqual(report["summary"]["uk_oracle_verified"], 0)

    def test_source_missing_blocks_even_with_perfect_t5_view(self):
        self.view.write_bytes(self.expected)
        self.source.unlink()
        row = self.scan()["files"][0]
        self.assertEqual(row["physical_status"], "BLOCKED")
        self.assertEqual(row["view_status"], "PHYSICAL_BLOCKED")

    def test_view_symlink_is_rejected_even_if_target_contains_correct_bytes(self):
        original = self.root / "external"
        original.write_bytes(self.expected)
        self.view.symlink_to(original)
        row = self.scan()["files"][0]
        self.assertEqual(row["view_status"], "UNSAFE_LINK")
        self.assertEqual(self.scan()["status"], "BLOCKED")

    def test_required_path_cannot_traverse_root_or_reference_unknown_file(self):
        for path in ("../case.sens", "/tmp/case.sens", "case.lisp",
                     "sub/../case.sens", "case\\other.sens"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.scan(required=(path,))
        self.view.write_bytes(self.expected)
        report = self.scan(required=("unknown.sens",))
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["failed_required"], ["unknown.sens"])

    def test_empty_scope_does_not_claim_release_success(self):
        self.sens.unlink()
        result = self.scan(required=())
        self.assertEqual(result["status"], "NO_FILES")
        self.assertEqual(result["summary"]["release_admitted"], 0)

    def test_cli_receipt_is_read_only_and_not_an_extensionless_program(self):
        self.view.write_bytes(self.expected)
        original=(self.source.read_bytes(),self.sens.read_bytes(),self.view.read_bytes())
        with tempfile.TemporaryDirectory(prefix="sens-report-outside-") as target:
            receipt=Path(target)/"receipt.json"
            rc=main([str(self.root),"--include-untracked","--require-view",
                     "case.sens","--report",str(receipt)])
            self.assertEqual(rc,0)
            self.assertTrue(receipt.is_file())
            data=json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(data["summary"]["view_present_valid"],1)
            self.assertEqual(data["files"][0]["uk_oracle"],"NOT_VERIFIED")
            prior=receipt.read_bytes()
            # Second attempt must not replace a prior proof receipt.
            self.assertEqual(main([str(self.root),"--include-untracked",
                                   "--report",str(receipt)]),2)
            self.assertEqual(receipt.read_bytes(),prior)
        self.assertEqual(original,(
            self.source.read_bytes(),self.sens.read_bytes(),self.view.read_bytes(),
        ))

    def test_receipt_target_cannot_clobber_any_of_three_program_files(self):
        self.view.write_bytes(self.expected)
        for path in (self.source,self.sens,self.view):
            original=path.read_bytes()
            with self.subTest(path=path.name):
                code=main([str(self.root),"--include-untracked",
                           "--report",str(path)])
                self.assertEqual(code,2)
                self.assertEqual(path.read_bytes(),original)
        # Even a NEW receipt path inside the corpus is forbidden.
        forbidden=self.root/"new-receipt.json"
        self.assertEqual(main([str(self.root),"--include-untracked",
                               "--report",str(forbidden)]),2)
        self.assertFalse(forbidden.exists())

    def test_external_receipt_symlink_and_existing_file_fail_closed(self):
        self.view.write_bytes(self.expected)
        with tempfile.TemporaryDirectory(prefix="sens-report-outside-") as target:
            other=Path(target)
            receipt=other/"existing.json"
            receipt.write_bytes(b"sentinel-json")
            self.assertEqual(main([str(self.root),"--include-untracked",
                                   "--report",str(receipt)]),2)
            self.assertEqual(receipt.read_bytes(),b"sentinel-json")
            link=other/"redirect.json"
            link.symlink_to(self.view)
            self.assertEqual(main([str(self.root),"--include-untracked",
                                   "--report",str(link)]),2)
            self.assertEqual(self.view.read_bytes(),self.expected)
            bad_dir=other/"linked-parent"
            bad_dir.symlink_to(self.root,target_is_directory=True)
            self.assertEqual(main([str(self.root),"--include-untracked",
                                   "--report",str(bad_dir/"report.json")]),2)
            self.assertFalse((self.root/"report.json").exists())

    def test_receipt_atomic_create_once_under_new_external_directory(self):
        self.view.write_bytes(self.expected)
        with tempfile.TemporaryDirectory(prefix="sens-report-outside-") as target:
            output=Path(target)/"nested"/"cohort"/"proof.json"
            rc=main([str(self.root),"--include-untracked",
                     "--report",str(output)])
            self.assertEqual(rc,0)
            evidence=json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(evidence["summary"]["view_present_valid"],1)
            self.assertEqual(evidence["summary"]["release_admitted"],0)
            self.assertFalse(list(output.parent.glob(".sens-triplet-receipt-*")))

    def test_real_checked_in_ukrainian_branch_triplet_is_not_original_credit(self):
        sens = ROOT / GOLDEN
        lisp = sens.with_suffix(".lisp")
        view = sens.with_suffix("")
        self.assertEqual(lisp.read_text(encoding="utf-8"),
                         "(за-умовою (ні (перше ())) (так так))\n")
        self.assertEqual(len(sens.read_bytes()), 12)
        self.assertEqual(view.read_bytes(),
                         b"10 110 00 10 0 00 10 100 00 000 01 01 00 10 1 00 1 01 01\n")
        # Git tracked scan of the REAL repository may have other missing views;
        # only THIS explicit golden is a hard required path.
        result = inspect(ROOT, required=(GOLDEN,))
        self.assertEqual(result["failed_required"], [])
        record = next(row for row in result["files"] if row["sens"] == GOLDEN)
        self.assertEqual(record["view_status"], "PHYSICAL_VIEW_PASS")
        self.assertFalse(record["release_admitted"])
        self.assertEqual(result["summary"]["original_executable_migrations_certified"], 0)


if __name__ == "__main__":
    unittest.main()
