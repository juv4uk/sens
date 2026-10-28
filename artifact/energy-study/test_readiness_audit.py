"""Bounded synthetic evidence-only tests; never claim independent replication."""
import json
from pathlib import Path
import tempfile
import unittest

import readiness_audit as audit


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.path = Path(self.work.name) / "raw.json"
        pairs = []
        for session in ("day-1", "day-2"):
            for i, order in enumerate(("AB", "BA", "AB", "BA")):
                pairs.append({"process_id": f"{session}-process-{i}",
                              "session_id": session, "machine_id": "host-1",
                              "order": order, "baseline_ns": 100000,
                              "candidate_ns": 110000, "peak_rss_kib": 1024,
                              "energy_not_measured": True})
        self.record = {"schema": audit.SCHEMA,
                       "tasks": {"T01-symbolic-recursion": {
                           "schema": audit.TASK_SCHEMA, "metric": "wall_time_ns",
                           "parity": {"passed": True, "oracle_id": "independent:checked-output"},
                           "provenance": {"git_sha": "a" * 40,
                                          "cpu_model": "Intel Core i5-6400",
                                          "governor": "performance", "affinity": "cpu:0"},
                           "energy_note": "ENERGY_NOT_MEASURED: no sensor",
                           "pairs": pairs}}}
        self.write()

    def write(self):
        self.path.write_text(json.dumps(self.record), encoding="utf-8")

    def test_structural_success_is_not_reproduction_or_energy(self):
        x = audit.inspect(self.path)
        self.assertEqual(x["status"], "STRUCTURAL_PREFLIGHT_ONLY")
        self.assertEqual(x["independent_reproduction"], "NOT_REPRODUCED")
        self.assertEqual(x["energy_status"], "ENERGY_NOT_MEASURED")
        self.assertEqual(x["sens_semantics"], "NOT_EVALUATED")

    def test_missing_source_sha_blocks(self):
        self.record["tasks"]["T01-symbolic-recursion"]["provenance"]["git_sha"] = "not-a-git-checkout"
        self.write()
        self.assertIn("SOURCE_SHA_NOT_PINNED", self.issues())

    def test_same_session_not_independent(self):
        for item in self.pairs(): item["session_id"] = "same-day"
        self.write()
        self.assertIn("INDEPENDENT_SESSIONS_NOT_DEMONSTRATED", self.issues())

    def test_parity_selftest_is_not_external_parity(self):
        self.task()["parity"]["oracle_id"] = "parity_check.py --selftest"
        self.write()
        self.assertIn("PARITY_SELFTEST_ONLY", self.issues())

    def test_missing_rss_is_not_zero(self):
        del self.pairs()[0]["peak_rss_kib"]
        self.write()
        self.assertIn("PEAK_RSS_NOT_RECORDED", self.issues())

    def test_fake_energy_rejected(self):
        self.pairs()[0]["energy_uj"] = 1234
        self.write()
        self.assertIn("ENERGY_CONFLICT_WITH_NOT_MEASURED", self.issues())

    def test_negative_or_nonfinite_elapsed_rejected(self):
        self.pairs()[0]["candidate_ns"] = -1
        self.write()
        self.assertIn("INVALID_ELAPSED_TIME", self.issues())
        self.pairs()[0]["candidate_ns"] = float("nan")
        self.write()
        with self.assertRaisesRegex(audit.InvalidRaw, "nonfinite"):
            audit.load_raw(self.path)

    def test_single_order_blocks(self):
        for item in self.pairs(): item["order"] = "AB"
        self.write()
        self.assertIn("ORDER_UNBALANCED", self.issues())

    def test_missing_cpu_identification_blocks(self):
        self.task()["provenance"]["cpu_model"] = "x86_64"
        self.write()
        self.assertIn("CPU_MODEL_UNSPECIFIED", self.issues())

    def test_uncontrolled_jit_warmup_reported(self):
        self.task()["warmup_note"] = "Node is JIT; no warmup was applied"
        self.write()
        self.assertIn("JIT_WARMUP_NOT_CONTROLLED", self.issues())

    def test_duplicate_json_key_rejected(self):
        self.path.write_text('{"schema":"sens-energy-study-raw/v1","schema":"other","tasks":{}}')
        with self.assertRaisesRegex(audit.InvalidRaw, "duplicate JSON key"):
            audit.load_raw(self.path)

    def test_symlink_rejected(self):
        link = self.path.parent / "alias.json"
        link.symlink_to(self.path)
        with self.assertRaisesRegex(audit.InvalidRaw, "linked"):
            audit.load_raw(link)

    def test_wrong_schema_rejected(self):
        self.record["schema"] = "sens-paired-physical/v1"
        self.write()
        with self.assertRaisesRegex(audit.InvalidRaw, "unsupported"):
            audit.inspect(self.path)

    def test_read_only_does_not_mutate_samples(self):
        before = self.path.read_bytes()
        audit.inspect(self.path)
        self.assertEqual(self.path.read_bytes(), before)

    def task(self): return self.record["tasks"]["T01-symbolic-recursion"]
    def pairs(self): return self.task()["pairs"]
    def issues(self): return self.report()["tasks"]["T01-symbolic-recursion"]["issues"]
    def report(self): return audit.inspect(self.path)


if __name__ == "__main__":
    unittest.main()
