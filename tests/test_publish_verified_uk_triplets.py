#!/usr/bin/env python3
"""Triplet writer guarantees: admitted canonical uk, T5 bytes, 0/1 view, no overwrite."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from publish_verified_uk_triplets import (
    ProjectionBlocked, attest_source, export, no_symlink_destination,
)
from sens_t5_codec import decode_bytes


class SafeTripletPublisher(unittest.TestCase):
    REL1 = "tests/fixtures/migration-d1-cond-cohort/branch.lisp"
    REL2 = "tests/fixtures/migration-d4-selector-cohort/caar.lisp"

    def test_existing_canonical_uk_source_is_admissible_as_three_views(self):
        for rel in (self.REL1, self.REL2):
            with self.subTest(rel=rel):
                src = (ROOT / rel).read_bytes()
                words, packed, view = attest_source(src)
                self.assertEqual(decode_bytes(packed), words)
                self.assertEqual(view, (" ".join(words) + "\n").encode("ascii"))
                self.assertNotIn(b"2", view)
                self.assertGreater(len(packed), 0)

    def test_two_real_fixture_sources_batch_is_atomic_and_verified(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "mirror"
            report = Path(td) / "admit.json"
            original1 = (ROOT / self.REL1).read_bytes()
            original2 = (ROOT / self.REL2).read_bytes()
            res = export(ROOT, target, report, [self.REL1, self.REL2], write=True)
            self.assertEqual(res["summary"]["triplets_written"], 2)
            self.assertEqual(res["summary"]["original_executables_oracle_certified"], 0)
            self.assertEqual((target / self.REL1).read_bytes(), original1)
            self.assertEqual((target / self.REL2).read_bytes(), original2)
            for rel in (self.REL1, self.REL2):
                out = target / Path(rel)
                packed = out.with_suffix(".sens").read_bytes()
                words = decode_bytes(packed)
                self.assertEqual(out.with_suffix("").read_bytes(),
                                 (" ".join(words) + "\n").encode("ascii"))
            self.assertEqual(json.loads(report.read_text())["summary"]["triplets_written"], 2)
            # All generated files must be in the EXTERNAL mirror, not the source.
            self.assertEqual((ROOT / self.REL1).read_bytes(), original1)
            self.assertEqual((ROOT / self.REL2).read_bytes(), original2)

    def test_preview_only_does_not_write_or_fake_semantics(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "mirror"
            report = Path(td) / "preview.json"
            out = export(ROOT, target, report, [self.REL1], write=False)
            self.assertEqual(out["summary"]["candidates"], 1)
            self.assertEqual(out["summary"]["triplets_written"], 0)
            self.assertEqual(out["summary"]["original_executables_oracle_certified"], 0)
            self.assertFalse(target.exists())

    def test_noncanonical_and_unknown_uk_does_not_create_any_triplet(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "repo"
            src.mkdir()
            (src / "unknown.lisp").write_text("(невідома-функція ())\n", encoding="utf-8")
            target = Path(td) / "mirror"
            res = export(src, target, Path(td) / "blocked.json",
                         ["unknown.lisp"], write=True)
            self.assertEqual(res["summary"]["blocked"], 1)
            self.assertEqual(res["summary"]["triplets_written"], 0)
            self.assertFalse(target.exists())

    def test_bad_member_blocks_entire_cohort_even_with_good_source(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "mirror"
            res = export(ROOT, target, Path(td) / "blocked.json",
                         [self.REL1, "does-not-exist.lisp"], write=True)
            self.assertEqual(res["summary"]["blocked"], 1)
            self.assertEqual(res["summary"]["triplets_written"], 0)
            self.assertFalse(target.exists())

    def test_existing_view_or_sens_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "mirror"
            view = target / Path(self.REL1).with_suffix("")
            view.parent.mkdir(parents=True)
            view.write_text("tampered \u2603\n", encoding="utf-8")
            res = export(ROOT, target, Path(td) / "blocked.json", [self.REL1], write=True)
            self.assertEqual(res["summary"]["blocked"], 1)
            self.assertEqual(view.read_text(encoding="utf-8"), "tampered \u2603\n")
            self.assertFalse(view.with_suffix(".sens").exists())

    def test_report_write_failure_rolls_back_all_new_triplets(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "mirror"
            report = Path(td) / "report.json"
            with mock.patch("publish_verified_uk_triplets.json.dump",
                            side_effect=OSError("simulated report write failure")):
                with self.assertRaisesRegex(OSError, "report write failure"):
                    export(ROOT, target, report, [self.REL1], write=True)
            lisp = target / self.REL1
            self.assertFalse(lisp.exists())
            self.assertFalse(lisp.with_suffix(".sens").exists())
            self.assertFalse(lisp.with_suffix("").exists())
            self.assertFalse(report.exists())

    def test_reject_symlink_source_and_output_parent(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src"
            src.mkdir()
            (src / "original.lisp").write_text("(як-є ())\n")
            (src / "link.lisp").symlink_to(src / "original.lisp")
            out = export(src, Path(td) / "mirror", Path(td) / "blocked.json",
                         ["link.lisp"], write=True)
            self.assertEqual(out["summary"]["blocked"], 1)
            self.assertEqual(out["summary"]["triplets_written"], 0)

    def test_symlinked_mirror_parent_cannot_write_into_source_tree(self):
        # The lexical target is outside ROOT, but its real path points inside
        # source. No staged .sens/view may be materialized via this alias.
        with tempfile.TemporaryDirectory() as td:
            alias = Path(td) / "linked-checkout"
            alias.symlink_to(ROOT, target_is_directory=True)
            destination = alias / "blocked-mirror-4756"
            with self.assertRaisesRegex(ProjectionBlocked, "outside source repository"):
                export(ROOT, destination, Path(td) / "blocked.json",
                       [self.REL1], write=True)
            self.assertFalse((ROOT / "blocked-mirror-4756").exists())
            self.assertFalse(destination.exists())

    def test_no_filename_confusion_or_source_mirror_escape(self):
        with tempfile.TemporaryDirectory() as td:
            for bad in ("/etc/passwd.lisp", "../escape.lisp", "./file.lisp",
                        "tests/foo.sens", "tests\\backslash.lisp"):
                res = export(ROOT, Path(td) / "out",
                             Path(td) / ("report-" + str(len(bad)) + "-" +
                             str(abs(hash(bad))) + ".json"),
                             [bad], write=False)
                self.assertEqual(res["summary"]["blocked"], 1, bad)
            with self.assertRaises(ProjectionBlocked):
                export(ROOT, ROOT / "mirror", Path(td) / "x.json",
                       [self.REL1], write=True)


if __name__ == "__main__":
    unittest.main()
