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

    @staticmethod
    def make_current_t5m(target: Path) -> None:
        """Перекодувати лише тимчасову копію, не історичне джерело."""
        from sens_t5_t5m_codec import encode_t5m_projection
        target.with_suffix(".sens").write_bytes(encode_t5m_projection(
            target.read_text(encoding="ascii")
        ))

    def test_nested_agent_worktree_is_not_part_of_repository_file_census(self):
        self.put("lib/головний.lisp", "()\n")
        self.put(".worktrees/інша-гілка/lib/чужий-знімок.lisp", "()\n")
        report = scan(self.root)
        self.assertEqual(report["total_lisp_files"], 1)
        self.assertEqual(report["potential_program_files"], 1)
        self.assertEqual(report["potential_program_missing_sens"], 1)

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

    def test_proven_program_not_blocked_by_separate_comment_only_profile(self):
        # Істина про програму не залежить від відсутності .sens у файлі
        # без виконуваних форм; звичайний текст не потребує машинного коду.
        fixture = ROOT / "tests/semantic/native-t5"
        source = self.root / "lib/branch.lisp"
        source.parent.mkdir(parents=True, exist_ok=True)
        for suffix in (".lisp", ".sens", ""):
            shutil.copyfile(fixture / ("cond-short-circuit" + suffix),
                            source.with_suffix(suffix))
        self.make_current_t5m(source.with_suffix(""))
        from sens_t5_t5m_codec import encode_t5m_projection
        source.with_suffix(".sens").write_bytes(
            encode_t5m_projection(source.with_suffix("").read_text(encoding="ascii"))
        )
        self.put("lib/пояснення.lisp", "; Це лише документація\n")
        result = scan(self.root, verify_bounded=True)
        self.assertEqual(result["total_lisp_files"], 2)
        self.assertEqual(result["comment_only_nonprogram_lisp"], 1)
        self.assertEqual(result["potential_program_files"], 1)
        self.assertEqual(result["potential_program_missing_sens"], 0)
        self.assertEqual(result["bounded_verified"], 1)
        self.assertTrue(result["all_bounded_reverse_verified"])
        self.assertFalse(result["semantic_runtime_proven"])
        self.assertFalse(result["release_ready"])
        # Фізичний .sens для коментарів не може замаскуватися
        # зеленим підсумком перевірки іншої справжньої програми.
        self.put("lib/пояснення.sens", b"not-an-executable-program")
        invalid = scan(self.root, verify_bounded=True)
        self.assertEqual(invalid["bounded_verified"], 1)
        self.assertEqual(invalid["comment_only_with_physical"], 1)
        self.assertFalse(invalid["all_bounded_reverse_verified"])
        self.assertIn("необґрунтований", str(invalid["blocked_sample"]))

    def test_nested_block_comments_are_not_machine_programs(self):
        # Лексичні #| ... |# не створюють виконуваних слів D2/T5M.
        # Дужки та символи старих мов усередині коментаря інертні.
        self.put("lib/опис.lisp",
                 "#| зовнішній (define fake 1)\n"
                 "  #| внутрішній ; () |#\n"
                 "  завершення |#\n; ще опис\n")
        self.put("lib/програма.lisp", "(визначити проба так)\n")
        report = scan(self.root)
        self.assertEqual(report["total_lisp_files"], 2)
        self.assertEqual(report["comment_only_nonprogram_lisp"], 1)
        self.assertEqual(report["potential_program_files"], 1)
        self.assertEqual(report["potential_program_missing_sens"], 1)
        self.assertEqual(report["comment_only_style_warnings"], 1)
        self.assertEqual(report["blocked_count"], 1)
        self.assertEqual(report["blocked_sample"][0]["path"], "lib/програма.lisp")
        self.assertFalse(report["release_ready"])

    def test_unclosed_block_comment_is_not_exempted(self):
        self.put("lib/помилка.lisp", "#| незакритий коментар (визначити проба так)\n")
        report = scan(self.root)
        self.assertEqual(report["comment_only_nonprogram_lisp"], 0)
        self.assertEqual(report["potential_program_files"], 1)
        self.assertEqual(report["potential_program_missing_sens"], 1)
        self.assertIn("lib/помилка.lisp", str(report["blocked_sample"]))
        self.assertFalse(report["all_bounded_reverse_verified"])

    def test_executable_code_after_block_comment_still_needs_sens(self):
        self.put("lib/програма.lisp",
                 "#| інертний опис |#\n(визначити проба так)\n")
        report = scan(self.root)
        self.assertEqual(report["comment_only_nonprogram_lisp"], 0)
        self.assertEqual(report["potential_program_missing_sens"], 1)
        self.assertIn("немає звичайного однойменного .sens",
                      str(report["blocked_sample"]))

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
        self.assertEqual(report["with_sens"], 1)
        self.assertEqual(report["missing_sens"], 0)
        self.assertIn("необґрунтований", str(report["blocked_sample"]))
        self.assertFalse(report["release_ready"])

    def test_one_file_with_two_real_causes_is_one_blocked_file(self):
        # Одна несправна програма: дві причини, але один файл.
        self.put("lib/english.lisp", "(define foo 1)\n")
        report = scan(self.root)
        self.assertEqual(report["blocked_count"], 2)
        self.assertEqual(report["blocked_file_count"], 1)
        self.assertEqual(report["potential_program_missing_complete_triplet"], 1)
        self.assertEqual(report["potential_program_without_bounded_proof"], 1)
        self.assertFalse(report["all_bounded_reverse_verified"])

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
        fixture = ROOT / "tests/semantic/native-t5"
        for suffix in (".lisp", ".sens", ""):
            target = self.root / "lib" / ("branch" + suffix)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fixture / ("cond-short-circuit" + suffix), target)
        self.make_current_t5m(self.root / "lib/branch")
        from sens_t5_t5m_codec import encode_t5m_projection
        target = self.root / "lib" / "branch"
        target.with_suffix(".sens").write_bytes(
            encode_t5m_projection(target.read_text(encoding="ascii"))
        )
        summary = scan(self.root, verify_bounded=True)
        self.assertEqual(summary["complete_triplets"], 1)
        self.assertEqual(summary["bounded_verified"], 1, summary["blocked_sample"])
        self.assertEqual(summary["bounded_verified_t5m"], 1)
        self.assertEqual(summary["bounded_verified_legacy_t5"], 0)
        self.assertTrue(summary["all_bounded_reverse_verified"])
        self.assertFalse(summary["semantic_runtime_proven"])
        self.assertFalse(summary["release_ready"])

    def test_comments_outside_keyboard_are_style_only_not_program_changes(self):
        fixture = ROOT / "tests/semantic/native-t5"
        target = self.root / "lib" / "branch"
        target.parent.mkdir(parents=True, exist_ok=True)
        for suffix in (".lisp", ".sens", ""):
            shutil.copyfile(fixture / ("cond-short-circuit" + suffix), target.with_suffix(suffix))
        self.make_current_t5m(target)
        source = target.with_suffix(".lisp")
        source.write_text("; inert historical comment ٢\n" +
                          source.read_text(encoding="utf-8"), encoding="utf-8")
        from sens_t5_t5m_codec import encode_t5m_projection
        target.with_suffix(".sens").write_bytes(
            encode_t5m_projection(target.read_text(encoding="ascii"))
        )
        report = scan(self.root, verify_bounded=True)
        self.assertEqual(report["ukrainian_keyboard"], 0)
        self.assertEqual(report["program_style_warnings"], 1)
        self.assertEqual(report["blocked_count"], 0, report["blocked_sample"])
        self.assertEqual(report["bounded_verified"], 1, report["blocked_sample"])
        self.assertTrue(report["all_bounded_reverse_verified"])
        self.assertFalse(report["semantic_runtime_proven"])
        self.assertFalse(report["release_ready"])

    def test_live_latin_call_is_a_real_source_defect_not_comment_style(self):
        self.put("lib/проба.lisp", "; harmless English note\n(визначити проба (old-call так))\n")
        report = scan(self.root)
        self.assertEqual(report["program_style_warnings"], 0)
        self.assertIn("виконувана Lisp-проєкція", str(report["blocked_sample"]))
        self.assertIn("old-call", str(report["blocked_sample"]))
        self.assertEqual(report["potential_program_missing_sens"], 1)

    def test_invalid_callable_source_cannot_report_full_t5m_proof(self):
        # Перевіряємо політику обліку, не семантику SENS: навіть
        # коректна за формою квитанція кодека не легалізує old-call.
        import hashlib

        source = self.put("lib/проба.lisp",
                          "(визначити проба (old-call так))\n")
        physical = self.put("lib/проба.sens", b"mechanical-receipt-fixture")
        view = self.put("lib/проба", "0\n")

        def accepted_mechanical_receipt(actual_source, actual_physical, actual_view):
            files = (actual_source, actual_physical, actual_view)
            source_hash, physical_hash, view_hash = (
                hashlib.sha256(file.read_bytes()).hexdigest() for file in files
            )
            return {
                "schema": "sens-uk-t5-view-bounded-proof/v1",
                "status": "BOUNDED_TRIPLE_PARITY_ONLY_NOT_RELEASE_ADMISSION",
                "canonical_uk_roundtrip": True,
                "program_identity_roundtrip": True,
                "canonical_view_roundtrip": True,
                "physical_codec": "t5m",
                "physical_T5_roundtrip": False,
                "physical_T5M_roundtrip": True,
                "source": str(actual_source),
                "sens": str(actual_physical),
                "view": str(actual_view),
                "source_sha256": source_hash,
                "physical_sha256": physical_hash,
                "view_sha256": view_hash,
                "typed_word_sha256": "0" * 64,
                "typed_word_count": 1,
                "runtime_oracle_admitted_by_this_audit": False,
                "old_originals_migrated_by_this_audit": 0,
            }

        report = scan(self.root, verify_bounded=True,
                      validator=accepted_mechanical_receipt)
        self.assertEqual(report["bounded_verified"], 1)
        self.assertFalse(report["all_bounded_reverse_verified"])
        self.assertFalse(report["all_current_t5m_bounded_reverse_verified"])
        self.assertEqual(report["invalid_program_source_projection"], 1)
        self.assertIn("old-call", str(report["blocked_sample"]))
        self.assertFalse(report["release_ready"])

    def test_current_t5m_triplet_is_counted_only_after_real_reverse_proof(self):
        from sens_t5_t5m_codec import encode_t5m_projection
        fixture = ROOT / "tests/semantic/native-t5"
        target = self.root / "lib" / "branch"
        target.parent.mkdir(parents=True, exist_ok=True)
        for suffix in (".lisp", ".sens", ""):
            shutil.copyfile(fixture / ("cond-short-circuit" + suffix), target.with_suffix(suffix))
        words = target.read_text(encoding="ascii")
        target.with_suffix(".sens").write_bytes(encode_t5m_projection(words))
        evidence = scan(self.root, verify_bounded=True)
        self.assertEqual(evidence["complete_triplets"], 1)
        self.assertEqual(evidence["bounded_verified"], 1, evidence["blocked_sample"])
        self.assertEqual(evidence["bounded_verified_t5m"], 1)
        self.assertEqual(evidence["bounded_verified_legacy_t5"], 0)
        self.assertTrue(evidence["all_bounded_reverse_verified"])
        self.assertTrue(evidence["all_current_t5m_bounded_reverse_verified"])
        self.assertEqual(evidence["current_t5m_without_bounded_proof"], 0)
        self.assertFalse(evidence["semantic_runtime_proven"])
        self.assertFalse(evidence["release_ready"])

    def test_legacy_t5_cannot_certify_the_current_corpus(self):
        # Старі фізичні T5-байти не означають сучасний T5M-доказ.
        from verify_uk_t5_t5m_triplet import verify
        fixture = ROOT / "tests/semantic/native-t5"
        target = self.root / "lib/branch"
        target.parent.mkdir(parents=True, exist_ok=True)
        for suffix in (".lisp", ".sens", ""):
            shutil.copyfile(fixture / ("cond-short-circuit" + suffix), target.with_suffix(suffix))
        # Чинний T5-кодек, не невизначена історична послідовність байтів.
        from sens_t5_t5m_codec import encode_words
        target.with_suffix(".sens").write_bytes(
            encode_words(target.read_text(encoding="ascii").split())
        )
        historical = scan(self.root, verify_bounded=True,
                          validator=lambda source, physical, view: verify(
                              source, physical, view, codec="t5"))
        self.assertEqual(historical["bounded_verified"], 1, historical["blocked_sample"])
        self.assertEqual(historical["bounded_verified_legacy_t5"], 1)
        self.assertEqual(historical["bounded_verified_t5m"], 0)
        self.assertFalse(historical["all_bounded_reverse_verified"])
        # Для коротких точних слів T5 і T5M можуть мати тотожні
        # фізичні байти. Автовибір законно визначає їх як T5M-сумісні;
        # за самими байтами неможливо довести історичний спосіб створення.
        current = scan(self.root, verify_bounded=True)
        self.assertEqual(current["bounded_verified"], 1, current["blocked_sample"])
        self.assertEqual(current["bounded_verified_t5m"], 1)
        self.assertTrue(current["all_bounded_reverse_verified"])
        self.assertFalse(current["semantic_runtime_proven"])

    def test_t5m_receipt_cannot_claim_legacy_t5_roundtrip_as_well(self):
        from sens_t5_t5m_codec import encode_t5m_projection
        from verify_uk_t5_t5m_triplet import verify
        fixture = ROOT / "tests/semantic/native-t5"
        target = self.root / "lib" / "branch"
        target.parent.mkdir(parents=True, exist_ok=True)
        for suffix in (".lisp", ".sens", ""):
            shutil.copyfile(fixture / ("cond-short-circuit" + suffix), target.with_suffix(suffix))
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
        fixture = ROOT / "tests/semantic/native-t5"
        for suffix in (".lisp", ".sens", ""):
            target = self.root / "lib" / ("branch" + suffix)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fixture / ("cond-short-circuit" + suffix), target)
        from verify_uk_t5_t5m_triplet import verify
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

    def test_symlinked_lisp_does_not_get_invisible_release_credit(self):
        # Навіть одна справжня перевірена трійка не доводить облік
        # другого .lisp, якщо той є символічним посиланням.
        fixture = ROOT / "tests/semantic/native-t5"
        target = self.root / "lib" / "branch"
        target.parent.mkdir(parents=True, exist_ok=True)
        for suffix in (".lisp", ".sens", ""):
            shutil.copyfile(fixture / ("cond-short-circuit" + suffix), target.with_suffix(suffix))
        self.make_current_t5m(target)
        (self.root / "lib" / "посилання.lisp").symlink_to("branch.lisp")
        summary = scan(self.root, verify_bounded=True)
        self.assertEqual(summary["total_lisp_files"], 2)
        self.assertEqual(summary["potential_program_files"], 1)
        self.assertEqual(summary["bounded_verified"], 1, summary["blocked_sample"])
        self.assertEqual(summary["undecidable_lisp_files"], 1)
        self.assertFalse(summary["all_bounded_reverse_verified"])
        self.assertFalse(summary["release_ready"])
        self.assertIn("не звичайний файл", str(summary["blocked_sample"]))

    def _put_reviewed_evidence(self):
        # Тільки справжній маніфест #4460 із чинним pinned Git blob.
        manifest = "knowledge/migration-nonprogram-evidence-manifest-2026-10-08.json"
        original = ("evidence/MYLISP-LINTER-THRESHOLDS/my-lisp/2168f4f.lisp")
        self.put(manifest, (ROOT / manifest).read_bytes())
        self.put(original, (ROOT / original).read_bytes())
        return original, manifest

    def test_reviewed_evidence_data_does_not_need_fake_sens(self):
        original, _ = self._put_reviewed_evidence()
        report = scan(self.root, verify_bounded=True,
                      validator=lambda *_: self.fail("дані не запускаються"))
        self.assertEqual(report["total_lisp_files"], 1)
        self.assertEqual(report["reviewed_nonprogram_lisp"], 1)
        self.assertEqual(report["reviewed_nonprogram_pin_drift"], 0)
        self.assertEqual(report["nonprogram_style_warnings"], 1)
        self.assertEqual(report["potential_program_files"], 0)
        self.assertEqual(report["blocked_count"], 0, report["blocked_sample"])
        self.assertEqual(report["bounded_verified"], 0)
        self.assertFalse(report["all_current_t5m_bounded_reverse_verified"])
        self.assertFalse(report["release_ready"])

    def test_changed_reviewed_data_loses_exemption_without_a_review(self):
        original, _ = self._put_reviewed_evidence()
        path = self.root / original
        path.write_text(path.read_text(encoding="utf-8").replace(
            'status (як-є passed)', 'status (як-є failed)'), encoding="utf-8")
        report = scan(self.root)
        self.assertEqual(report["reviewed_nonprogram_lisp"], 0)
        self.assertEqual(report["reviewed_nonprogram_pin_drift"], 1)
        self.assertEqual(report["potential_program_files"], 1)
        self.assertIn("SHA затверджених Lisp-даних", str(report["blocked_sample"]))
        self.assertFalse(report["release_ready"])

    def test_reviewed_nonprogram_with_unapproved_sens_is_reported(self):
        original, _ = self._put_reviewed_evidence()
        self.put(original[:-5] + ".sens", b"not-admitted")
        report = scan(self.root)
        self.assertEqual(report["reviewed_nonprogram_lisp"], 1)
        self.assertEqual(report["unapproved_nonprogram_physical"], 1)
        self.assertEqual(report["potential_program_files"], 0)
        self.assertIn("недопущений .sens", str(report["blocked_sample"]))
        self.assertFalse(report["release_ready"])

    def test_incomplete_nonprogram_manifest_is_not_wildcard_exemption(self):
        original, manifest = self._put_reviewed_evidence()
        import json
        data = json.loads((self.root / manifest).read_text(encoding="utf-8"))
        data["entries"] = data["entries"][:1]
        self.put(manifest, json.dumps(data, ensure_ascii=False))
        report = scan(self.root)
        self.assertEqual(report["reviewed_nonprogram_lisp"], 0)
        self.assertEqual(report["potential_program_files"], 1)
        self.assertEqual(report["potential_program_missing_sens"], 1)
        self.assertFalse(report["all_bounded_reverse_verified"])

    def test_empty_repository_is_not_vacuously_proven(self):
        summary = scan(self.root, verify_bounded=True, validator=lambda *_: {})
        self.assertEqual(summary["total_lisp_files"], 0)
        self.assertFalse(summary["all_bounded_reverse_verified"])
        self.assertFalse(summary["release_ready"])


if __name__ == "__main__":
    unittest.main()
