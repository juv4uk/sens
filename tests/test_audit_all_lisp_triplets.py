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

    def test_comment_only_lisp_has_no_machine_program_to_reverse(self):
        self.put("lib/опис.lisp", "; Український опис\n; Без програми\n")
        self.put("lib/порожній.lisp", "  \n\t\n")
        self.put("lib/програма.lisp", "(визначити проба так)\n")
        report = scan(self.root, verify_bounded=True,
                      validator=lambda *_: self.fail("немає фізичної пари"))
        self.assertEqual(report["total_lisp_files"], 3)
        self.assertEqual(report["comment_only_nonprogram_lisp"], 2)
        self.assertEqual(report["potential_program_files"], 1)
        self.assertEqual(report["potential_program_missing_sens"], 1)
        self.assertEqual(report["missing_sens"], 3)  # повний фізичний перепис
        self.assertEqual(report["blocked_count"], 1)  # не 3 штучних блокери
        self.assertEqual(report["comment_only_style_warnings"], 1)
        self.assertEqual(report["blocked_sample"][0]["path"], "lib/програма.lisp")
        self.assertFalse(report["all_bounded_reverse_verified"])
        self.assertFalse(report["release_ready"])

    def test_noncommented_lisp_is_never_auto_exempted_from_program_census(self):
        self.put("lib/опис.lisp", '; опис\n(визначити функцію так)\n')
        report = scan(self.root)
        self.assertEqual(report["comment_only_nonprogram_lisp"], 0)
        self.assertEqual(report["potential_program_files"], 1)
        self.assertEqual(report["potential_program_missing_sens"], 1)
        self.assertIn("немає", str(report["blocked_sample"]))

    def test_comment_only_with_unproved_sens_is_not_silently_exempt(self):
        self.put("lib/опис.lisp", "; тільки опис\n")
        self.put("lib/опис.sens", b"fake")
        report = scan(self.root)
        self.assertEqual(report["comment_only_nonprogram_lisp"], 1)
        self.assertEqual(report["potential_program_files"], 0)
        self.assertIn("необґрунтований", str(report["blocked_sample"]))
        self.assertFalse(report["release_ready"])

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
        self.assertEqual(summary["bounded_verified_t5m"], 0)
        self.assertEqual(summary["bounded_verified_legacy_t5"], 0)
        self.assertFalse(summary["all_bounded_reverse_verified"])

    def test_binary_d2_under_lisp_is_not_a_verified_ukrainian_program(self):
        # Keyboard characters are not evidence of a human Lisp program.
        words = "10 110 00 1 01" + chr(10)
        self.put("lib/не-лісп.lisp", words)
        self.put("lib/не-лісп.sens", b"unverified-physical")
        self.put("lib/не-лісп", words)
        self.put("lib/належний.bits", words)
        def must_not_call(*_args):
            self.fail("двійковий D2 під .lisp не можна зараховувати до укр-свідків")
        report = scan(self.root, verify_bounded=True, validator=must_not_call)
        self.assertEqual(report["total_lisp_files"], 1)
        self.assertEqual(report["ukrainian_keyboard"], 1)
        self.assertEqual(report["misnamed_binary_lisp"], 1)
        self.assertEqual(report["complete_triplets"], 1)
        self.assertEqual(report["bounded_verified"], 0)
        self.assertFalse(report["all_bounded_reverse_verified"])
        self.assertIn("потрібен .bits", str(report["blocked_sample"]))

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
        self.assertEqual(
            summary["bounded_verified_t5m"] + summary["bounded_verified_legacy_t5"], 1
        )
        self.assertTrue(summary["all_bounded_reverse_verified"])
        self.assertFalse(summary["semantic_runtime_proven"])
        self.assertFalse(summary["release_ready"])

    def test_comments_outside_keyboard_are_style_only_not_program_changes(self):
        fixture = ROOT / "tests/fixtures/migration-d1-cond-cohort"
        target = self.root / "lib" / "branch"
        target.parent.mkdir(parents=True, exist_ok=True)
        for suffix in (".lisp", ".sens", ""):
            shutil.copyfile(fixture / ("branch" + suffix), target.with_suffix(suffix))
        source = target.with_suffix(".lisp")
        source.write_text("; inert historical comment ٢\n" +
                          source.read_text(encoding="utf-8"), encoding="utf-8")
        report = scan(self.root, verify_bounded=True)
        self.assertEqual(report["ukrainian_keyboard"], 0)
        self.assertEqual(report["bounded_verified"], 1, report["blocked_sample"])
        self.assertTrue(report["all_bounded_reverse_verified"])
        self.assertFalse(report["semantic_runtime_proven"])
        self.assertFalse(report["release_ready"])

    def test_current_t5m_triplet_is_counted_only_after_real_reverse_proof(self):
        from sens_t5_codec import encode_t5m_projection
        fixture = ROOT / "tests/fixtures/migration-d1-cond-cohort"
        target = self.root / "lib" / "branch"
        target.parent.mkdir(parents=True, exist_ok=True)
        for suffix in (".lisp", ".sens", ""):
            shutil.copyfile(fixture / ("branch" + suffix), target.with_suffix(suffix))
        words = target.read_text(encoding="ascii")
        target.with_suffix(".sens").write_bytes(encode_t5m_projection(words))
        evidence = scan(self.root, verify_bounded=True)
        self.assertEqual(evidence["complete_triplets"], 1)
        self.assertEqual(evidence["bounded_verified"], 1, evidence["blocked_sample"])
        self.assertEqual(evidence["bounded_verified_t5m"], 1)
        self.assertEqual(evidence["bounded_verified_legacy_t5"], 0)
        self.assertTrue(evidence["all_bounded_reverse_verified"])
        self.assertFalse(evidence["semantic_runtime_proven"])
        self.assertFalse(evidence["release_ready"])

    def test_t5m_receipt_cannot_claim_legacy_t5_roundtrip_as_well(self):
        from sens_t5_codec import encode_t5m_projection
        from verify_uk_t5_triplet import verify
        fixture = ROOT / "tests/fixtures/migration-d1-cond-cohort"
        target = self.root / "lib" / "branch"
        target.parent.mkdir(parents=True, exist_ok=True)
        for suffix in (".lisp", ".sens", ""):
            shutil.copyfile(fixture / ("branch" + suffix), target.with_suffix(suffix))
        target.with_suffix(".sens").write_bytes(encode_t5m_projection(
            target.read_text(encoding="ascii")
        ))
        genuine = verify(target.with_suffix(".lisp"), target.with_suffix(".sens"), target)
        self.assertEqual(genuine["physical_codec"], "t5m")
        genuine["physical_T5_roundtrip"] = True
        evidence = scan(self.root, verify_bounded=True, validator=lambda *_: genuine)
        self.assertEqual(evidence["bounded_verified"], 0)
        self.assertEqual(evidence["bounded_verified_t5m"], 0)
        self.assertEqual(evidence["bounded_verified_legacy_t5"], 0)
        self.assertIn("T5/T5M", str(evidence["blocked_sample"]))
        self.assertFalse(evidence["release_ready"])

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
