"""Finite, offline negative controls for immutable GitHub runner evidence."""
import copy
import json
import unittest
from pathlib import Path
from verify import EVIDENCE, validate

GOOD = json.loads(Path(EVIDENCE).read_text(encoding="utf-8"))


class EvidenceTests(unittest.TestCase):
    def test_original_exact_runner_rows(self):
        self.assertEqual([], validate(copy.deepcopy(GOOD)))

    def test_missing_energy_is_not_zero(self):
        mutated = copy.deepcopy(GOOD)
        mutated["measurement"]["energy_joules"] = 0.0
        self.assertIn("ENERGY_OR_INFERENCE_FABRICATED", validate(mutated))

    def test_no_made_up_confidence_interval(self):
        mutated = copy.deepcopy(GOOD)
        mutated["measurement"]["confidence_interval"] = [0.50, 0.54]
        self.assertIn("ENERGY_OR_INFERENCE_FABRICATED", validate(mutated))

    def test_no_fake_independent_sessions(self):
        mutated = copy.deepcopy(GOOD)
        mutated["environment"]["independent_sessions"] = 5
        self.assertIn("SESSION_COUNT_INVALID", validate(mutated))

    def test_exact_input_is_frozen(self):
        mutated = copy.deepcopy(GOOD)
        mutated["workload"]["input_n"] = 12
        self.assertIn("WORKLOAD_OR_PARITY_MISMATCH", validate(mutated))

    def test_source_sha_is_pinned(self):
        mutated = copy.deepcopy(GOOD)
        mutated["provenance"]["source_measure_git_blob"] = "0" * 40
        self.assertIn("PROVENANCE_MISMATCH", validate(mutated))

    def test_no_silent_sample_mutation(self):
        mutated = copy.deepcopy(GOOD)
        mutated["samples"][0]["elapsed_seconds"] = "0.43"
        self.assertIn("RAW_LOG_MISMATCH:1", validate(mutated))

    def test_no_deleted_trial(self):
        mutated = copy.deepcopy(GOOD)
        mutated["samples"].pop()
        self.assertIn("SAMPLE_COUNT_INVALID", validate(mutated))


if __name__ == "__main__":
    unittest.main()
