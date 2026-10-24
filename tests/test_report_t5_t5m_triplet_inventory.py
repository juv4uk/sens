#!/usr/bin/env python3
"""Незалежні негативні тести read-only інвентаризації SENS-трійок."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from report_t5_t5m_triplet_inventory import GOLDEN, inspect, main
from audit_all_lisp_triplets import git_blob_sha
from sens_t5_t5m_codec import encode_words

# Під'єднання вже наявного релізного gate, без дублювання його законів.
_GATE_PATH = ROOT / "scripts" / "check-release-triple-corpus.py"
_GATE_SPEC = importlib.util.spec_from_file_location("sens_release_triple_gate", _GATE_PATH)
assert _GATE_SPEC and _GATE_SPEC.loader
release_gate = importlib.util.module_from_spec(_GATE_SPEC)
_GATE_SPEC.loader.exec_module(release_gate)



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

    def test_bits_source_provenance_matches_real_sha_and_physical_view(self):
        # The lower pair auditor accepts same-stem .bits without a .lisp.
        # The release inventory must never report an imaginary .lisp source.
        self.source.unlink()
        bits = self.root / "case.bits"
        bits.write_bytes(self.expected)
        self.view.write_bytes(self.expected)
        result = self.scan(strict=True)
        row = result["files"][0]
        self.assertEqual(row["source"], "case.bits")
        self.assertEqual(row["source_sha256"], hashlib.sha256(self.expected).hexdigest())
        self.assertEqual(row["view_status"], "PHYSICAL_VIEW_PASS")
        self.assertEqual(result["summary"]["uk_oracle_verified"], 0)
        self.assertEqual(result["summary"]["release_admitted"], 0)

    def test_missing_view_reports_real_debt_but_required_gate_blocks(self):
        report = self.scan(required=())
        self.assertEqual(report["status"], "INCOMPLETE_VIEWS")
        self.assertEqual(report["summary"]["view_missing"], 1)
        self.assertEqual(report["files"][0]["view_status"], "MISSING_VIEW")
        required = self.scan()
        self.assertEqual(required["status"], "BLOCKED")
        self.assertEqual(required["failed_required"], ["case.sens"])
        self.assertEqual(self.scan(strict=True)["status"], "BLOCKED")

    def test_unpaired_lisp_is_visible_even_when_existing_view_passes(self):
        self.view.write_bytes(self.expected)
        additional = self.root / "ще-програма.lisp"
        additional.write_text("(визначити відповідь так)\n", encoding="utf-8")
        original = additional.read_bytes()
        report = self.scan(required=())
        self.assertEqual(report["status"], "INCOMPLETE_SOURCE_PAIRS")
        self.assertEqual(report["summary"]["lisp_sources_seen"], 2)
        self.assertEqual(report["summary"]["lisp_with_physical"], 1)
        self.assertEqual(report["summary"]["lisp_without_physical"], 1)
        self.assertEqual(report["unpaired_lisp_sources"], ["ще-програма.lisp"])
        self.assertEqual(report["summary"]["view_present_valid"], 1)
        self.assertEqual(self.scan(strict=True)["status"], "BLOCKED")
        self.assertEqual(additional.read_bytes(), original)

    def test_nonprogram_lisp_does_not_require_physical_t5m(self):
        self.view.write_bytes(self.expected)
        comment = self.root / "пояснення.lisp"
        comment.write_text(
            "; український опис\n#| зовнішній #| вкладений |# коментар |#\n",
            encoding="utf-8",
        )
        report = self.scan(strict=True, required=())
        self.assertEqual(report["status"], "PHYSICAL_VIEW_ONLY_UK_PENDING")
        self.assertEqual(report["summary"]["lisp_without_physical"], 1)
        self.assertEqual(report["summary"]["unpaired_nonprogram_lisp_sources"], 1)
        self.assertEqual(report["summary"]["unpaired_program_lisp_sources"], 0)
        self.assertEqual(report["unpaired_lisp_sources"], ["пояснення.lisp"])
        self.assertEqual(report["unpaired_program_lisp_sources"], [])
        self.assertEqual(report["summary"]["uk_oracle_verified"], 0)
        self.assertEqual(report["summary"]["release_admitted"], 0)

    def test_reviewed_nonprogram_sha_pin_is_not_a_fake_runtime_block(self):
        self.view.write_bytes(self.expected)
        approved = self.root / "затверджені-дані.lisp"
        approved.write_text("(таблиця (дані так))\n", encoding="utf-8")
        original = approved.read_bytes()
        pin = {"затверджені-дані.lisp": (git_blob_sha(original), "перевірені-дані")}

        with patch("report_t5_t5m_triplet_inventory.reviewed_nonprogram_pins",
                   return_value=pin):
            report = self.scan(strict=True, required=())
        self.assertEqual(report["status"], "PHYSICAL_VIEW_ONLY_UK_PENDING")
        self.assertEqual(report["unpaired_nonprogram_lisp_sources"],
                         ["затверджені-дані.lisp"])
        self.assertEqual(report["unpaired_program_lisp_sources"], [])
        self.assertEqual(report["summary"]["release_admitted"], 0)

        # Зміна бодай одного біта втрачає право на статус затверджених даних.
        approved.write_text("(таблиця (дані ні))\n", encoding="utf-8")
        with patch("report_t5_t5m_triplet_inventory.reviewed_nonprogram_pins",
                   return_value=pin):
            drift = self.scan(strict=True, required=())
        self.assertEqual(drift["status"], "BLOCKED")
        self.assertEqual(drift["unpaired_program_lisp_sources"],
                         ["затверджені-дані.lisp"])

    def test_unclosed_block_comment_is_not_silently_exempted(self):
        self.view.write_bytes(self.expected)
        (self.root / "невалідний.lisp").write_text(
            "#| незакритий коментар\n", encoding="utf-8"
        )
        report = self.scan(strict=True, required=())
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["summary"]["unpaired_nonprogram_lisp_sources"], 0)
        self.assertEqual(report["summary"]["unpaired_program_lisp_sources"], 1)
        self.assertEqual(report["unpaired_program_lisp_sources"], ["невалідний.lisp"])
        self.assertEqual(report["summary"]["release_admitted"], 0)

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
        self.assertEqual(result["summary"]["lisp_sources_seen"], 1)
        self.assertEqual(result["summary"]["lisp_without_physical"], 1)
        self.assertEqual(result["unpaired_lisp_sources"], ["case.lisp"])
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


    def check_release_gate(self, report: dict, status: str = "0") -> tuple[int, str]:
        with tempfile.TemporaryDirectory(prefix="sens-release-gate-test-") as temp:
            path = Path(temp) / "mechanical-report.json"
            path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                rc = release_gate.main([str(path), status])
            return rc, output.getvalue()

    def test_release_gate_blocks_complete_physical_triplet_without_native_oracle(self):
        self.view.write_bytes(self.expected)
        receipt = self.scan(strict=True)
        self.assertEqual(receipt["status"], "PHYSICAL_VIEW_ONLY_UK_PENDING")
        code, output = self.check_release_gate(receipt)
        self.assertEqual(code, 1)
        self.assertIn("RELEASE_BLOCKED", output)
        self.assertNotIn("RELEASE_TRIPLE_FULL_CORPUS_PASS", output)

    def test_release_gate_refuses_forged_semantics_even_if_counts_match_rows(self):
        self.view.write_bytes(self.expected)
        receipt = self.scan(strict=True)
        altered = json.loads(json.dumps(receipt))
        altered["summary"]["uk_oracle_verified"] = 1
        altered["summary"]["release_admitted"] = 1
        altered["files"][0]["uk_oracle"] = "VERIFIED"
        altered["files"][0]["release_admitted"] = True
        code, output = self.check_release_gate(altered)
        self.assertEqual(code, 1)
        self.assertIn("RELEASE_BLOCKED", output)
        self.assertNotIn("RELEASE_TRIPLE_FULL_CORPUS_PASS", output)

    def test_release_gate_rejects_bad_exit_or_malformed_inventory(self):
        self.view.write_bytes(self.expected)
        report = self.scan(strict=True)
        for variation in (
            {"schema": report["schema"], "summary": {}},
            {**report, "files": []},
            {**report, "schema": "unexpected-schema"},
        ):
            with self.subTest(variation=variation):
                code, output = self.check_release_gate(variation)
                self.assertEqual(code, 1)
                self.assertIn("RELEASE_BLOCKED", output)
        self.assertEqual(self.check_release_gate(report, "7")[0], 1)
        self.assertEqual(self.check_release_gate(report, "invalid")[0], 1)


    def release_verdict(self, report: dict, inventory_status: str = "0"):
        receipt = self.root / "release-triple.json"
        receipt.write_text(json.dumps(report), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/check-release-triple-corpus.py"),
             str(receipt), inventory_status],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )

    def test_release_gate_does_not_promote_valid_physical_triple_to_semantic_go(self):
        self.view.write_bytes(self.expected)
        report = self.scan(strict=True)
        self.assertEqual(report["status"], "PHYSICAL_VIEW_ONLY_UK_PENDING")
        self.assertEqual(report["summary"]["view_present_valid"], 1)
        checked = self.release_verdict(report)
        self.assertEqual(checked.returncode, 1, checked.stdout + checked.stderr)
        self.assertIn("RELEASE_BLOCKED", checked.stderr)
        self.assertNotIn("RELEASE_TRIPLE_FULL_CORPUS_PASS", checked.stdout)

    def test_release_gate_rejects_forged_oracle_even_with_consistent_counters(self):
        self.view.write_bytes(self.expected)
        report = self.scan(strict=True)
        report["summary"]["uk_oracle_verified"] = 1
        report["summary"]["release_admitted"] = 1
        report["files"][0]["uk_oracle"] = "VERIFIED"
        report["files"][0]["release_admitted"] = True
        checked = self.release_verdict(report)
        self.assertEqual(checked.returncode, 1, checked.stdout + checked.stderr)
        self.assertIn("RELEASE_BLOCKED: mechanical inventory cannot assert native SENS semantic", checked.stderr)
        self.assertNotIn("RELEASE_TRIPLE_FULL_CORPUS_PASS", checked.stdout)

    def test_release_gate_rejects_informational_inventory_without_strict_proof(self):
        self.view.write_bytes(self.expected)
        report = self.scan(strict=False)
        checked = self.release_verdict(report)
        self.assertEqual(checked.returncode, 1, checked.stdout + checked.stderr)
        self.assertIn("RELEASE_BLOCKED", checked.stderr)

    def test_release_gate_rejects_invalid_status_without_python_traceback(self):
        self.view.write_bytes(self.expected)
        report = self.scan(strict=True)
        checked = self.release_verdict(report, "not-a-status")
        self.assertEqual(checked.returncode, 1, checked.stdout + checked.stderr)
        self.assertIn("RELEASE_BLOCKED", checked.stderr)
        self.assertNotIn("Traceback", checked.stderr)


    def test_informational_inventory_reports_debt_but_not_auditor_failure(self):
        # Missing/malformed current pairs are visible debt, not an unrelated
        # main-branch stop; an exception or strict release request must fail.
        self.view.write_bytes(b"0\\n")
        original = (self.source.read_bytes(), self.sens.read_bytes(), self.view.read_bytes())
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            rc = main([str(self.root), "--include-untracked", "--informational"])
        self.assertEqual(rc, 0, output.getvalue())
        first = json.loads(output.getvalue().splitlines()[0])
        self.assertEqual(first["status"], "BLOCKED")
        self.assertEqual(first["release_admitted"], 0)
        self.assertIn("T5_TRIPLET_INVENTORY_DEBT", output.getvalue())
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main([str(self.root), "--include-untracked", "--informational",
                                   "--strict"]), 2)
            self.assertEqual(main([str(self.root / "absent"), "--include-untracked",
                                   "--informational"]), 2)
        self.assertEqual(original, (self.source.read_bytes(), self.sens.read_bytes(),
                                    self.view.read_bytes()))


if __name__ == "__main__":
    unittest.main()
