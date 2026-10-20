"""Перевірки обліку всіх Lisp-джерел без підміни runtime-доказу."""
from __future__ import annotations

import contextlib
import io
import shutil
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_all_lisp_triplets import main, scan


class AllLispTripletCensusTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def put(self, name: str, content: str | bytes):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def test_every_directory_counts_including_history(self):
        self.put("lib/один.lisp", "(визначити один так)\n")
        self.put("lib/один.sens", b"\x01")
        self.put("lib/один", "0\n")
        self.put("lib/другий.lisp", "(визначити другий так)\n")
        self.put("history/old.lisp", "(define old 1)\n")
        summary = scan(self.root)
        self.assertEqual(summary["total_lisp_files"], 3)
        self.assertEqual(summary["ukrainian_keyboard"], 2)
        self.assertEqual(summary["with_sens"], 1)
        self.assertEqual(summary["complete_triplets"], 1)
        self.assertEqual(summary["missing_sens"], 2)
        self.assertEqual(summary["unverified_triplets"], 1)
        self.assertFalse(summary["all_bounded_reverse_verified"])
        self.assertFalse(summary["release_ready"])
        self.assertGreaterEqual(summary["blocked_count"], 3)

    def test_existing_three_files_do_not_prove_inverse(self):
        self.put("либ/тест.lisp", "(визначити проба так)\n")
        self.put("либ/тест.sens", b"not real T5")
        self.put("либ/тест", "0\n")
        summary = scan(self.root)
        self.assertEqual(summary["complete_triplets"], 1)
        self.assertEqual(summary["bounded_verified"], 0)
        self.assertFalse(summary["all_bounded_reverse_verified"])

    def test_validator_rejection_is_not_silently_skipped(self):
        self.put("lib/проба.lisp", "(визначити проба так)\n")
        self.put("lib/проба.sens", b"invalid")
        self.put("lib/проба", "0\n")

        def reject(_source, _physical, _view):
            raise ValueError("T5 mismatch")

        summary = scan(self.root, verify_bounded=True, validator=reject)
        self.assertEqual(summary["bounded_verified"], 0)
        self.assertIn("T5 mismatch", str(summary["blocked_sample"]))

    def test_real_bounded_triplet_is_not_a_release_certificate(self):
        fixture = ROOT / "tests/fixtures/migration-d1-cond-cohort"
        for suffix in (".lisp", ".sens", ""):
            target = self.root / "lib" / ("branch" + suffix)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fixture / ("branch" + suffix), target)
        summary = scan(self.root, verify_bounded=True)
        self.assertEqual(summary["complete_triplets"], 1)
        self.assertEqual(summary["bounded_verified"], 1, summary["blocked_sample"])
        self.assertTrue(summary["all_bounded_reverse_verified"])
        self.assertFalse(summary["semantic_runtime_proven"])
        self.assertFalse(summary["release_ready"])

    def test_forged_boolean_roundtrip_is_not_a_three_way_proof(self):
        self.put("lib/проба.lisp", "(визначити проба так)\n")
        self.put("lib/проба.sens", b"not-a-real-carrier")
        self.put("lib/проба", "0\n")
        summary = scan(
            self.root, verify_bounded=True,
            validator=lambda *_: {"canonical_uk_roundtrip": True},
        )
        self.assertEqual(summary["bounded_verified"], 0)
        self.assertFalse(summary["all_bounded_reverse_verified"])
        self.assertIn("схема", str(summary["blocked_sample"]))

    def test_old_receipt_cannot_authorize_changed_lisp_source(self):
        fixture = ROOT / "tests/fixtures/migration-d1-cond-cohort"
        for suffix in (".lisp", ".sens", ""):
            target = self.root / "lib" / ("branch" + suffix)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fixture / ("branch" + suffix), target)
        from verify_uk_t5_triplet import verify
        source = self.root / "lib/branch.lisp"
        original_receipt = verify(
            source, source.with_suffix(".sens"), source.with_suffix("")
        )
        source.write_text("(як-є так)\n", encoding="utf-8")
        summary = scan(
            self.root, verify_bounded=True, validator=lambda *_: original_receipt
        )
        self.assertEqual(summary["bounded_verified"], 0)
        self.assertIn("source_sha256", str(summary["blocked_sample"]))

    def test_strict_mode_fails_without_actual_verification(self):
        self.put("lib/проба.lisp", "(визначити проба так)\n")
        self.put("lib/проба.sens", b"witness")
        self.put("lib/проба", "0\n")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--root", str(self.root), "--require-reversible"]), 2)

    def test_empty_repository_is_not_vacuously_proven(self):
        summary = scan(self.root, verify_bounded=True, validator=lambda *_: {})
        self.assertEqual(summary["total_lisp_files"], 0)
        self.assertFalse(summary["all_bounded_reverse_verified"])
        self.assertFalse(summary["release_ready"])


if __name__ == "__main__":
    unittest.main()
