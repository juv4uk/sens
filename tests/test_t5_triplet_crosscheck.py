#!/usr/bin/env python3
"""Міжкомпонентна регресія: generation, bounded Ukrainian proof та inventory.

Ці три незалежні перевірки не підміняють спільний machine/semantic authority.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import sens_spaced_view as physical
import verify_uk_t5_triplet as ukrainian
import report_t5_triplet_inventory as inventory
from sens_t5_codec import SensT5Error

GOLDEN = ROOT / "tests/fixtures/migration-d1-cond-cohort"


class TripletCrossComponentContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sens-cross-triplet-")
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "src"
        self.folder = self.repo / "canary"
        self.folder.mkdir(parents=True)
        for name in ("branch.lisp", "branch.sens", "branch"):
            shutil.copyfile(GOLDEN / name, self.folder / name)
        self.lisp = self.folder / "branch.lisp"
        self.sens = self.folder / "branch.sens"
        self.view = self.folder / "branch"

    def reports(self):
        physical_report = physical.check_or_stage(
            self.repo, "canary/branch.sens")
        ukrainian_report = ukrainian.verify(
            self.lisp, self.sens, self.view)
        inventory_report = inventory.inspect(
            self.repo, include_untracked=True,
            required=("canary/branch.sens",), strict=True)
        matches = [r for r in inventory_report["files"]
                   if r["sens"] == "canary/branch.sens"]
        self.assertEqual(len(matches), 1)
        return physical_report, ukrainian_report, inventory_report, matches[0]

    def test_all_independent_layers_agree_on_exact_content(self):
        a, b, c, row = self.reports()
        self.assertEqual(a["status"], "VERIFY")
        self.assertTrue(b["canonical_uk_roundtrip"])
        self.assertTrue(b["canonical_view_roundtrip"])
        self.assertEqual(row["view_status"], "PHYSICAL_VIEW_PASS")
        self.assertEqual(c["failed_required"], [])
        self.assertEqual(a["source_sha256"], b["source_sha256"])
        self.assertEqual(a["source_sha256"], row["source_sha256"])
        self.assertEqual(a["sens_sha256"], b["physical_sha256"])
        self.assertEqual(a["sens_sha256"], row["physical_sha256"])
        self.assertEqual(a["view_sha256"], b["view_sha256"])
        self.assertEqual(a["view_sha256"], row["view_sha256"])
        self.assertEqual(a["typed_word_sha256"], b["typed_word_sha256"])
        self.assertEqual(a["typed_word_sha256"], row["typed_word_sha256"])
        self.assertEqual(a["words"], b["typed_word_count"])
        self.assertEqual(a["words"], row["typed_word_count"])
        self.assertEqual(a["physical_bytes"], 12)
        self.assertFalse(a["release_admitted"])
        self.assertFalse(b["runtime_oracle_admitted_by_this_audit"])
        self.assertFalse(row["release_admitted"])
        self.assertEqual(c["summary"]["original_executable_migrations_certified"], 0)

    def test_english_source_cannot_gain_authority_from_valid_binary_view(self):
        self.lisp.write_text("(COND (ні (перше ())) (так так))\n",
                             encoding="utf-8")
        a = physical.check_or_stage(self.repo, "canary/branch.sens")
        c = inventory.inspect(self.repo, include_untracked=True,
                              required=("canary/branch.sens",))
        self.assertEqual(a["status"], "VERIFY")
        self.assertFalse(a["release_admitted"])
        self.assertEqual(c["files"][0]["view_status"], "PHYSICAL_VIEW_PASS")
        with self.assertRaises(ukrainian.ProjectionBlocked):
            ukrainian.verify(self.lisp, self.sens, self.view)

    def test_stale_view_is_rejected_by_all_three(self):
        self.view.write_bytes(self.view.read_bytes().replace(b" ", b"  ", 1))
        with self.assertRaises(physical.ViewError):
            physical.check_or_stage(self.repo, "canary/branch.sens")
        with self.assertRaises(ukrainian.ProjectionBlocked):
            ukrainian.verify(self.lisp, self.sens, self.view)
        c = inventory.inspect(self.repo, include_untracked=True,
                              required=("canary/branch.sens",), strict=True)
        self.assertEqual(c["status"], "BLOCKED")
        self.assertEqual(c["files"][0]["view_status"], "VIEW_MISMATCH")

    def test_corrupted_t5_cannot_be_rehabilitated_by_matching_text(self):
        self.sens.write_bytes(self.sens.read_bytes() + bytes([243]))
        with self.assertRaises((SensT5Error, physical.ViewError)):
            physical.check_or_stage(self.repo, "canary/branch.sens")
        with self.assertRaises(ukrainian.ProjectionBlocked):
            ukrainian.verify(self.lisp, self.sens, self.view)
        c = inventory.inspect(self.repo, include_untracked=True,
                              required=("canary/branch.sens",), strict=True)
        self.assertEqual(c["status"], "BLOCKED")
        self.assertEqual(c["files"][0]["view_status"], "PHYSICAL_BLOCKED")


if __name__ == "__main__":
    unittest.main()
