"""Physical-research instrumentation tests; no SENS language semantics."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks" / "measurement-triad"))
import verdict

SPEC = importlib.util.spec_from_file_location("study", Path(__file__).with_name("study.py"))
study = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(study)


class PhysicalStudyTests(unittest.TestCase):
    def test_corpus_observation_matches_independent_physical_bytes(self):
        data = (ROOT / "lib/core4.lisp").read_bytes()
        self.assertGreater(len(data), 512)
        for n in (1, 512, 513):
            observed = sum(data[i % len(data)] for i in range(n))
            self.assertEqual(
                study.physical_expected(n),
                f"PHYSICAL_COPY\tbytes={len(data)}\tcopies={n}\tobserved={observed}")

    def test_hierarchical_metrics_require_real_positive_evidence(self):
        evidence = {
            "schema": verdict.PHYSICAL_SCHEMA,
            "metric": "energy_uj",
            "parity": {"passed": True, "oracle_id": "physical-byte-parity"},
            "provenance": {name: "captured" for name in verdict.REQUIRED_PROVENANCE},
            "pairs": [
                {"process_id": f"block-{block}", "order": ("AB" if index % 2 == 0 else "BA"),
                 "baseline_energy_uj": 1000 + block, "candidate_energy_uj": 900 + block}
                for block in range(8) for index in range(4)
            ],
        }
        result = verdict.analyze(evidence, draws=1000, seed=1)
        self.assertEqual(result["metric"], "energy_uj")
        self.assertEqual(result["independent_processes"], 8)
        self.assertLess(result["ratio"], 1.0)
        evidence["pairs"][0]["candidate_energy_uj"] = 0
        with self.assertRaises(verdict.InvalidEvidence):
            verdict.analyze(evidence, draws=1000, seed=1)

    def test_without_exact_parity_no_numeric_verdict(self):
        evidence = {
            "schema": verdict.PHYSICAL_SCHEMA, "metric": "peak_rss_kib",
            "parity": {"passed": False, "oracle_id": "physical-byte-parity"}
        }
        result = verdict.analyze(evidence)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIsNone(result["ratio"])


if __name__ == "__main__":
    unittest.main()
