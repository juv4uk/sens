#!/usr/bin/env python3
"""Regression #4453: no mechanical result may be counted as SENS admission."""
from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sens_inventory as inventory
from sens_t5_codec import encode_words

GOLDEN = ROOT / "tests/fixtures/migration-d1-cond-cohort"


class FailClosedInventory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sens-admission-inventory-")
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.repo = self.work / "repo"
        self.fixture = self.repo / "fixtures"
        self.fixture.mkdir(parents=True)

    def copy_good(self, directory=None):
        directory = directory or self.fixture
        directory.mkdir(parents=True, exist_ok=True)
        for filename in ("branch.lisp", "branch.sens", "branch"):
            shutil.copyfile(GOLDEN / filename, directory / filename)
        return directory

    def inspect(self):
        return inventory.inspect(self.repo, ("fixtures",))

    def test_real_gold_triplet_is_bounded_but_never_release_admitted(self):
        self.copy_good()
        result = self.inspect()
        self.assertEqual(result["schema"], "sens-triple-inventory-failclosed/v2")
        self.assertEqual(result["summary"]["files_seen"], 1)
        self.assertEqual(result["summary"]["mechanically_admitted"], 0)
        self.assertEqual(result["summary"]["release_admitted"], 0)
        self.assertEqual(result["summary"]["original_executable_migrations_certified"], 0)
        row = result["files"][0]
        self.assertEqual(row["status"], inventory.GOOD_UK)
        self.assertEqual(row["words"], 19)
        self.assertEqual(row["physical_bytes"], 12)
        self.assertFalse(row["release_admitted"])
        self.assertEqual(row["source_era"], "UNKNOWN_NOT_INFERRED")
        self.assertEqual(row["independent_execution_oracle"], "NOT_VERIFIED")
        self.assertEqual(len(row["typed_word_sha256"]), 64)
        self.assertEqual(len(row["source_sha256"]), 64)
        self.assertEqual(len(row["sens_sha256"]), 64)
        self.assertEqual(len(row["view_sha256"]), 64)

    def test_mechanical_binary_without_view_is_never_admitted(self):
        self.copy_good()
        (self.fixture / "branch").unlink()
        row = self.inspect()["files"][0]
        self.assertEqual(row["status"], inventory.MISSING)
        self.assertFalse(row["release_admitted"])
        self.assertNotIn("sens_sha256", row)

    def test_english_lisp_with_correct_t5_and_view_still_unproven(self):
        self.copy_good()
        (self.fixture / "branch.lisp").write_text(
            "(COND (ні (перше ())) (так так))\n", encoding="utf-8"
        )
        row = self.inspect()["files"][0]
        self.assertEqual(row["status"], inventory.PHYSICAL_ONLY)
        self.assertEqual(len(row["typed_word_sha256"]), 64)
        self.assertIn("uk_blocker", row)
        self.assertFalse(row["release_admitted"])
        self.assertEqual(row["independent_execution_oracle"], "NOT_VERIFIED")

    def test_declarative_head_does_not_grant_executable_status(self):
        (self.fixture / "data.lisp").write_text("(schema foo bar)\n", encoding="utf-8")
        row = self.inspect()["files"][0]
        self.assertEqual(row["status"], inventory.NONPROGRAM)
        self.assertEqual(row["source_kind"], "declarative_candidate")
        self.assertEqual(row["original_executable_migration_credit"], 0)
        self.assertFalse(row["release_admitted"])

    def test_corrupt_t5_blocks_even_with_matching_source_and_view(self):
        self.copy_good()
        (self.fixture / "branch.sens").write_bytes(b"\xf3")
        row = self.inspect()["files"][0]
        self.assertEqual(row["status"], inventory.BLOCKED)
        self.assertEqual(self.inspect()["summary"]["release_admitted"], 0)

    def test_explicit_w8_never_forces_historical_legacy_mode(self):
        self.copy_good()
        (self.fixture / "eight.lisp").write_text(
            "(11111111 1)\n", encoding="utf-8"
        )
        (self.fixture / "eight.sens").write_bytes(encode_words(["10", "11111111", "00", "1", "01"]))
        (self.fixture / "eight").write_text(
            "10 11111111 00 1 01\n", encoding="ascii"
        )
        report = self.inspect()
        self.assertEqual(report["summary"]["files_seen"], 2)
        row = next(x for x in report["files"] if x["path"] == "fixtures/eight.lisp")
        self.assertEqual(row["status"], inventory.PHYSICAL_ONLY)
        self.assertEqual(row["source_era"], "UNKNOWN_NOT_INFERRED")
        self.assertFalse(row["release_admitted"])
        self.assertNotIn("legacy", str(row).lower())

    def test_missing_scope_and_symlink_scope_fail_closed(self):
        with self.assertRaises(inventory.InventoryBlocked):
            inventory.inspect(self.repo, ("../outside",))
        with self.assertRaises(inventory.InventoryBlocked):
            inventory.inspect(self.repo, ("fixtures/../fixtures",))
        with self.assertRaises(inventory.InventoryBlocked):
            inventory.inspect(self.repo, ("missing",))
        alias = self.repo / "alias"
        alias.symlink_to(self.fixture, target_is_directory=True)
        with self.assertRaises(inventory.InventoryBlocked):
            inventory.inspect(self.repo, ("alias",))

    def test_distinct_same_basename_sources_are_not_collapsed(self):
        self.copy_good()
        self.copy_good(self.fixture / "more")
        report = self.inspect()
        self.assertEqual(report["summary"]["files_seen"], 2)
        self.assertEqual(len({r["path"] for r in report["files"]}), 2)
        self.assertEqual(report["summary"]["by_status"][inventory.GOOD_UK], 2)
        self.assertEqual(report["summary"]["release_admitted"], 0)

    def test_require_bounded_uk_is_a_proof_not_release_gate(self):
        self.copy_good()
        rc = inventory.main([
            "--root", str(self.repo), "fixtures",
            "--require-bounded-uk", "fixtures/branch.lisp"
        ])
        self.assertEqual(rc, 0)
        self.assertEqual(inventory.main([
            "--root", str(self.repo), "fixtures",
            "--require-bounded-uk", "fixtures/unknown.lisp"
        ]), 2)

    def test_receipt_cannot_clobber_any_existing_file_or_repo(self):
        self.copy_good()
        report = self.inspect()
        with self.assertRaises(inventory.InventoryBlocked):
            inventory.write_receipt(self.fixture / "data.json", report, self.repo)
        outside = self.work / "receipt.json"
        inventory.write_receipt(outside, report, self.repo)
        self.assertIn('"release_admitted": 0', outside.read_text(encoding="utf-8"))
        with self.assertRaises(FileExistsError):
            inventory.write_receipt(outside, report, self.repo)
        with self.assertRaises(inventory.InventoryBlocked):
            inventory.write_receipt(self.work / "branch.sens", report, self.repo)


if __name__ == "__main__":
    unittest.main()
