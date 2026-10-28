#!/usr/bin/env python3
"""Exercise the existing #6291 preflight on actual checked-in research raw data.

This is structural provenance testing, not a SENS semantic oracle, independent
reproduction, physical energy measurement, or confirmation of language rankings.
FAIR (Wilkinson et al. 2016) motivates preserving exact research-object
provenance; Kalibera & Jones (2013) motivates session-level evidence.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
AUDITOR = ROOT / "artifact/energy-study/readiness_audit.py"
RAW = ROOT / "benchmarks/language-energy-study/raw"
T01 = RAW / "T01-python-vs-javascript-8x4.json"
T04 = RAW / "measure-T04-T05-T06-python-vs-javascript-8x4.json"


class RealRawReadinessIntegration(unittest.TestCase):
    def run_audit(self, path: Path):
        run = subprocess.run(
            [sys.executable, str(AUDITOR), str(path)],
            capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertFalse(run.stderr, run.stderr)
        self.assertIn(run.returncode, (0, 2), run.stdout)
        return run.returncode, json.loads(run.stdout)

    def test_real_T01_is_explicitly_blocked_not_certified(self):
        code, report = self.run_audit(T01)
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "READINESS_BLOCKED")
        self.assertEqual(report["independent_reproduction"], "NOT_REPRODUCED")
        self.assertEqual(report["energy_status"], "ENERGY_NOT_MEASURED")
        self.assertEqual(report["sens_semantics"], "NOT_EVALUATED")
        task = report["tasks"]["T01-symbolic-recursion"]
        self.assertEqual(task["pairs"], 32)
        self.assertEqual(task["sessions"], 1)
        self.assertTrue({"SOURCE_SHA_NOT_PINNED", "INDEPENDENT_SESSIONS_NOT_DEMONSTRATED",
                         "PEAK_RSS_NOT_RECORDED", "PARITY_SELFTEST_ONLY",
                         "TIME_BOUNDARY_UNSPECIFIED"}.issubset(task["issues"]))

    def test_real_T04_records_two_rss_values_without_false_alarm(self):
        code, report = self.run_audit(T04)
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "READINESS_BLOCKED")
        self.assertEqual(report["independent_reproduction"], "NOT_REPRODUCED")
        self.assertEqual(report["energy_status"], "ENERGY_NOT_MEASURED")
        for tid in ("T04-sorting", "T05-allocation-gc", "T06-io"):
            task = report["tasks"][tid]
            self.assertEqual(task["pairs"], 32)
            self.assertNotIn("PEAK_RSS_NOT_RECORDED", task["issues"], tid)
            self.assertIn("SOURCE_SHA_NOT_PINNED", task["issues"], tid)
            self.assertIn("TIME_BOUNDARY_UNSPECIFIED", task["issues"], tid)
        real = json.loads(T04.read_text(encoding="utf-8"))
        first = real["tasks"]["T04-sorting"]["pairs"][0]
        self.assertGreater(first["baseline_peak_rss_kib"], 0)
        self.assertGreater(first["candidate_peak_rss_kib"], 0)

    def test_tampered_actual_rss_is_detected_without_editing_raw(self):
        real = json.loads(T04.read_text(encoding="utf-8"))
        real["tasks"]["T04-sorting"]["pairs"][0]["candidate_peak_rss_kib"] = 0
        with tempfile.TemporaryDirectory() as folder:
            mutated = Path(folder) / "mutant.json"
            mutated.write_text(json.dumps(real), encoding="utf-8")
            code, report = self.run_audit(mutated)
            self.assertEqual(code, 2)
            self.assertIn("PEAK_RSS_NOT_RECORDED", report["tasks"]["T04-sorting"]["issues"])
            self.assertEqual(report["independent_reproduction"], "NOT_REPRODUCED")

    def test_actual_sources_are_read_only(self):
        originals = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (T01, T04)}
        for p in originals:
            self.run_audit(p)
        for path, digest in originals.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
