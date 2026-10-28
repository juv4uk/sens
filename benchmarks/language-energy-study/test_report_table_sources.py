#!/usr/bin/env python3
"""Negative controls for FAIR raw-source retention and measured-output admission."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import report_table


TASK = "T01-symbolic-recursion"


def physical(lang: str, *, mode: str = "measure", sessions: int = 4) -> dict:
    pairs = []
    for process in range(8):
        for k in range(4):
            pairs.append({
                "process_id": f"{lang}-{TASK}-p{process}",
                "order": "AB" if k % 2 == 0 else "BA",
                "machine_id": "one-real-machine",
                "session_id": f"s{process % sessions}",
                "baseline_ns": 100_000_000,
                "candidate_ns": 70_000_000,
                "baseline_peak_rss_kib": 20_000,
                "candidate_peak_rss_kib": 22_000,
            })
    return {
        "schema": "sens-paired-physical/v1", "metric": "wall_time_ns",
        "parity": {"passed": True, "oracle_id": "measured-output-check",
                   "size_mode": mode},
        "provenance": {
            "git_sha": "a" * 40, "binary_sha256": "b" * 64,
            "cpu_model": "synthetic", "rustc": "synthetic",
            "os": "synthetic", "affinity": "synthetic",
            "governor": "synthetic", "turbo": "synthetic",
            "timing_source": "synthetic",
        },
        "pairs": pairs,
    }


def write_file(folder: Path, name: str, data: dict) -> None:
    (folder / name).write_text(json.dumps({"schema": "sens-energy-study-raw/v1",
                                           "tasks": {TASK: data}}),
                               encoding="utf-8")


class ReportRetentionTests(unittest.TestCase):
    def test_sens_and_javascript_same_task_both_preserved(self):
        with tempfile.TemporaryDirectory() as dirname:
            folder = Path(dirname)
            write_file(folder, "javascript.json", physical("javascript"))
            write_file(folder, "sens.json", physical("sens"))
            records = report_table.load_raw(folder)
            self.assertEqual(len(records), 2)
            self.assertEqual({k.split("::")[0] for k in records},
                             {"javascript.json", "sens.json"})
            with mock.patch.object(report_table, "analyze", return_value={
                    "status": "INCONCLUSIVE", "ratio": None,
                    "ci95_ratio": None}):
                rows = report_table.rows(records)
            self.assertEqual(len(rows), 4)  # 2 sources x 2 metrics
            self.assertEqual({r["candidate"] for r in rows},
                             {"javascript", "sens"})
            self.assertEqual({r["source"] for r in rows},
                             {"javascript.json", "sens.json"})
            self.assertEqual({r["mode"] for r in rows}, {"measure"})

    def test_equal_task_and_candidate_multiple_sessions_not_overwritten(self):
        with tempfile.TemporaryDirectory() as dirname:
            folder = Path(dirname)
            write_file(folder, "day1.json", physical("sens"))
            write_file(folder, "day2.json", physical("sens"))
            records = report_table.load_raw(folder)
            self.assertEqual(len(records), 2)
            with mock.patch.object(report_table, "analyze", return_value={
                    "status": "INCONCLUSIVE", "ratio": None, "ci95_ratio": None}):
                self.assertEqual(len(report_table.rows(records)), 4)

    def test_mixed_languages_not_attributed_to_sens(self):
        data = physical("sens")
        data["pairs"][0]["process_id"] = f"javascript-{TASK}-p0"
        record = {f"mixed.json::{TASK}": dict(data, _task_id=TASK,
                                               _source_file="mixed.json")}
        rows = report_table.rows(record)
        self.assertEqual({r["status"] for r in rows}, {"BLOCKED"})
        self.assertEqual({r["reason"] for r in rows},
                         {"MIXED_CANDIDATE_LANGUAGES"})
        self.assertEqual({r["candidate"] for r in rows}, {"UNKNOWN"})

    def test_explicit_metadata_conflict_is_blocked(self):
        data = physical("sens")
        data["pairs"][1]["candidate_language"] = "javascript"
        rows = report_table.rows({TASK: data})
        self.assertTrue(all(r["reason"] == "CONFLICTING_CANDIDATE_METADATA"
                            for r in rows))

    def test_oracle_selftest_is_not_measured_parity(self):
        data = physical("sens")
        data["parity"]["oracle_id"] = "parity_check.py --selftest"
        rows = report_table.rows({TASK: data})
        self.assertEqual({r["reason"] for r in rows},
                         {"SELFTEST_IS_NOT_MEASURED_OUTPUT_PARITY"})
        self.assertTrue(all(r["ratio"] is None and r["status"] == "BLOCKED"
                            for r in rows))

    def test_rejected_attempt_prevents_admission(self):
        data = physical("sens")
        data["rejected"] = [{"reason": "wrong-output"}]
        rows = report_table.rows({TASK: data})
        self.assertEqual({r["reason"] for r in rows},
                         {"REJECTED_MEASUREMENT_ATTEMPTS"})

    def test_absent_rss_is_explicit_not_measured(self):
        data = physical("sens")
        for p in data["pairs"]:
            del p["baseline_peak_rss_kib"]
        rows = report_table.rows({TASK: data})
        self.assertEqual(rows[1]["status"], "NOT_MEASURED")
        self.assertEqual(rows[1]["reason"], "METRIC_NOT_MEASURED")
        self.assertIsNone(rows[1]["ratio"])

    def test_empty_and_corrupted_raw_fail_closed(self):
        rows = report_table.rows({TASK: dict(physical("sens"), pairs=[])})
        self.assertTrue(all(r["status"] == "BLOCKED" for r in rows))
        with tempfile.TemporaryDirectory() as dirname:
            folder = Path(dirname)
            (folder / "bad.json").write_text('{"tasks":[]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "tasks object missing"):
                report_table.load_raw(folder)

    def test_render_names_sources_candidates_and_blockers(self):
        data = physical("sens", mode="verify")
        data["parity"]["passed"] = False
        row = report_table.rows({TASK: data})
        view = report_table.render(row, markdown=True)
        self.assertIn("sens", view)
        self.assertIn("verify", view)
        self.assertIn("PARITY_NOT_PROVED", view)
        self.assertNotIn("0.000", view)


if __name__ == "__main__":
    unittest.main()
