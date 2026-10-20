#!/usr/bin/env python3
"""Негативні регресії release gate: звіт не може видати облік за доказ семантики."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-release-triple-corpus.py"
spec = importlib.util.spec_from_file_location("sens_release_triple_corpus_test", SCRIPT)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def ledger() -> dict:
    return {
        "schema": "sens-t5-triplet-inventory/v1",
        "failed_required": [],
        "strict": True,
        "status": "PHYSICAL_VIEW_ONLY_UK_PENDING",
        "unpaired_lisp_sources": [],
        "summary": {
            "physical_pairs_seen": 1,
            "physical_blocked": 0,
            "view_present_valid": 1,
            "view_missing": 0,
            "view_invalid_or_unsafe": 0,
            "uk_oracle_verified": 0,
            "release_admitted": 0,
            "original_executable_migrations_certified": 0,
            "lisp_sources_seen": 1,
            "lisp_with_physical": 1,
            "lisp_without_physical": 0,
        },
        "files": [{
            "sens": "приклад.sens",
            "source": "приклад.lisp",
            "view_status": "PHYSICAL_VIEW_PASS",
            "uk_oracle": "NOT_VERIFIED",
            "release_admitted": False,
            "original_executable_migration_credit": 0,
        }],
    }


class ReleaseTripleCorpusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "evidence.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_checker(self, status: str = "0") -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = checker.main([str(self.path), status])
        return result, output.getvalue()

    def write(self, data: object) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_complete_views_are_not_executable_semantics(self) -> None:
        self.write(ledger())
        code, output = self.run_checker()
        self.assertEqual(code, 1)
        self.assertIn("RELEASE_BLOCKED", output)

    def test_missing_and_invalid_json_fail_closed(self) -> None:
        self.assertEqual(self.run_checker()[0], 1)
        self.path.write_text("{", encoding="utf-8")
        code, output = self.run_checker()
        self.assertEqual(code, 1)
        self.assertIn("invalid triple ledger", output)

    def test_noninteger_runner_status_reports_block_instead_of_traceback(self) -> None:
        self.write(ledger())
        code, output = self.run_checker("invalid")
        self.assertEqual(code, 1)
        self.assertIn("exit status must be an integer", output)

    def test_missing_summary_and_incorrect_types_block(self) -> None:
        for broken in (
            {"schema": "sens-t5-triplet-inventory/v1"},
            {**ledger(), "summary": []},
            {**ledger(), "files": []},
            {**ledger(), "failed_required": "not-a-list"},
        ):
            with self.subTest(broken=broken):
                self.write(broken)
                code, output = self.run_checker()
                self.assertEqual(code, 1)
                self.assertIn("RELEASE_BLOCKED", output)

    def test_forged_totals_do_not_pretend_oracle_pass(self) -> None:
        for field in ("uk_oracle_verified", "release_admitted"):
            with self.subTest(field=field):
                report = ledger()
                report["summary"][field] = 1
                self.write(report)
                code, output = self.run_checker()
                self.assertEqual(code, 1)
                self.assertIn("contradict per-file evidence", output)

    def test_invalid_view_or_required_witness_blocks(self) -> None:
        report = ledger()
        report["summary"]["view_present_valid"] = 0
        report["summary"]["view_missing"] = 1
        report["files"][0]["view_status"] = "MISSING_VIEW"
        self.write(report)
        self.assertEqual(self.run_checker()[0], 1)
        report["failed_required"] = ["приклад.sens"]
        self.write(report)
        self.assertEqual(self.run_checker()[0], 1)

    def test_missing_lisp_without_sens_is_real_release_debt(self) -> None:
        report = ledger()
        report["status"] = "BLOCKED"
        report["summary"]["lisp_sources_seen"] = 2
        report["summary"]["lisp_without_physical"] = 1
        report["unpaired_lisp_sources"] = ["неперетворена-програма.lisp"]
        self.write(report)
        code, output = self.run_checker()
        self.assertEqual(code, 1)
        self.assertIn("RELEASE_BLOCKED", output)

    def test_source_inventory_cannot_hide_missing_lisp(self) -> None:
        for broken in (
            {"lisp_sources_seen": 2},
            {"lisp_without_physical": 1},
            {"lisp_with_physical": 2},
        ):
            with self.subTest(broken=broken):
                report = ledger()
                report["summary"].update(broken)
                self.write(report)
                code, output = self.run_checker()
                self.assertEqual(code, 1)
                self.assertIn("contradict per-file evidence", output)

    def test_duplicate_or_escaping_source_path_rejected(self) -> None:
        for files in (
            ["a.lisp", "a.lisp"],
            ["../outside.lisp"],
            ["/outside.lisp"],
            ["not-a-lisp-file"],
        ):
            with self.subTest(files=files):
                report = ledger()
                report["unpaired_lisp_sources"] = files
                self.write(report)
                code, output = self.run_checker()
                self.assertEqual(code, 1)
                self.assertIn("RELEASE_BLOCKED", output)

    def test_boolean_and_negative_counts_are_not_numbers_of_proofs(self) -> None:
        for count in (True, -1, "1"):
            with self.subTest(count=count):
                report = ledger()
                report["summary"]["physical_pairs_seen"] = count
                self.write(report)
                self.assertEqual(self.run_checker()[0], 1)


if __name__ == "__main__":
    unittest.main()
