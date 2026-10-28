#!/usr/bin/env python3
"""Mechanism-only negative controls for a prospective research plan.

Tests only structural admission; never executes or decides SENS semantics.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_preregistration import InvalidPlan, strict_json, validate


def frozen_fixture() -> dict:
    """A synthetic fixture, explicitly not a real registered study."""
    tasks = []
    contrasts = []
    for number in range(9):
        tid = f"T{number+1:02d}-synthetic"
        input_digest = f"{number + 1:064x}"
        tasks.append({
            "id": tid,
            "input_sha256": input_digest,
            "reference_output_sha256": f"{number + 101:064x}",
            "verified_units": 8_192,
            "implementations": [
                {"language": "Rust", "source_sha": "a"*40},
                {"language": "Python", "source_sha": "b"*40},
            ],
            "ineligible_candidates": [
                {"language": "C", "reason": "Synthetic C implementation not yet available",
                 "evidence_url": "https://github.com/juv4uk/sens/issues/6287"},
                {"language": "SENS", "reason": "Synthetic SENS implementation not yet available",
                 "evidence_url": "https://github.com/juv4uk/sens/issues/6287"},
            ],
        })
        contrasts.append({
            "task": tid,
            "baseline": "Rust",
            "candidate": "Python",
            "input_sha256": input_digest,
            "metrics": ["wall_time_ns", "peak_rss_kib", "energy_uj"],
        })
    return {
        "schema": "sens-energy-prereg-v1",
        "state": "FROZEN",
        "protocol_sha": "c"*40,
        "analysis_sha": "d"*40,
        "variance_pilot_sha": "e"*40,
        "locked_at_utc": "2026-11-01T00:00:00Z",
        "first_confirmatory_at_utc": "2026-11-02T00:00:00Z",
        "lock_review_url": "https://github.com/juv4uk/sens/pull/999999",
        "host_id": "synthetic-host-not-a-real-machine",
        "host_cpu": "synthetic-cpu",
        "energy_sensor": "RAPL_PACKAGE",
        "energy_scope": "WHOLE_PACKAGE",
        "sensor_proof_url": "https://example.org/synthetic-meter",
        "max_work_bytes_per_invocation": 2 * 1024**3,
        "random_seed": 20261028,
        "sessions": 4,
        "pairs_per_session": 4,
        "precision_target": 0.10,
        "alpha": 0.05,
        "multiplicity": "HOLM_FWER",
        "analysis_state": "VALIDATED",
        "tasks": tasks,
        "contrasts": contrasts,
    }


class PreregistrationMechanismTests(unittest.TestCase):
    def assert_blocked(self, edit, reason):
        plan = frozen_fixture()
        edit(plan)
        with self.assertRaisesRegex(InvalidPlan, reason):
            validate(plan)

    def test_complete_structure_passes_only_structure(self):
        facts = validate(frozen_fixture())
        self.assertEqual(facts["tasks"], 9)
        self.assertEqual(facts["contrasts"], 9)
        self.assertEqual(facts["planned_candidate_cells"], 27)
        self.assertEqual(facts["explicit_na_cells"], 18)
        self.assertNotIn("energy_uj", facts)  # no measurements!

    def test_wrong_input_digest_blocks_parity_admission(self):
        self.assert_blocked(lambda p: p["contrasts"][0].update(
            input_sha256="f"*64), "input digest mismatch")

    def test_no_physical_sensor_blocks_energy_study(self):
        self.assert_blocked(lambda p: p.update(energy_sensor="ENERGY_NOT_MEASURED"),
                            "no valid physical instrument")

    def test_invalid_sensor_scope_is_blocked(self):
        self.assert_blocked(lambda p: p.update(energy_scope="ISOLATED_SENS_PROCESS"),
                            "conflicts with physical sensor")

    def test_frozen_after_measurement_is_blocked(self):
        self.assert_blocked(lambda p: p.update(
            locked_at_utc="2026-11-03T00:00:00Z"), "measurement is not after freeze")

    def test_underspecified_sample_size_is_blocked(self):
        self.assert_blocked(lambda p: p.update(sessions=1),
                            "fewer than four independent sessions")

    def test_invalid_ab_ba_balance_is_blocked(self):
        self.assert_blocked(lambda p: p.update(pairs_per_session=5),
                            "requires >=4 even AB/BA pairs")

    def test_unvalidated_statistical_method_is_blocked(self):
        self.assert_blocked(lambda p: p.update(analysis_state="DRAFT"),
                            "must validate")

    def test_missing_task_is_blocked(self):
        self.assert_blocked(lambda p: p["tasks"].pop(),
                            "exactly nine")

    def test_duplicate_contrast_is_blocked(self):
        self.assert_blocked(lambda p: p["contrasts"].append(
            copy.deepcopy(p["contrasts"][0])), "duplicate")

    def test_no_double_counted_energy_and_no_disguised_zero(self):
        self.assert_blocked(lambda p: p.update(energy_sensor="TDP_ESTIMATE"),
                            "no valid physical instrument")
        self.assert_blocked(lambda p: p.update(max_work_bytes_per_invocation=0),
                            "expected positive integer")

    def test_undeclared_candidate_is_blocked(self):
        self.assert_blocked(lambda p: p["tasks"][0]["ineligible_candidates"].pop(),
                            "missing candidate or explicit N/A")

    def test_implemented_candidate_cannot_be_marked_na(self):
        self.assert_blocked(lambda p: p["tasks"][0]["ineligible_candidates"].append(
            {"language": "Python", "reason": "Incorrectly masking an implemented candidate",
             "evidence_url": "https://github.com/juv4uk/sens/issues/6287"}),
            "implemented language")

    def test_duplicate_na_record_is_blocked(self):
        self.assert_blocked(lambda p: p["tasks"][0]["ineligible_candidates"].append(
            copy.deepcopy(p["tasks"][0]["ineligible_candidates"][0])), "duplicate language")

    def test_unsubstantiated_na_is_blocked(self):
        self.assert_blocked(lambda p: p["tasks"][0]["ineligible_candidates"][0].update(
            reason="slow"), "substantive reason")

    def test_missing_eligible_comparison_is_blocked(self):
        self.assert_blocked(lambda p: p["contrasts"].pop(),
                            "missing primary contrast")

    def test_all_27_cells_can_be_explicitly_eligible(self):
        plan = frozen_fixture()
        for task in plan["tasks"]:
            task["implementations"] += [
                {"language": "C", "source_sha": "1"*40},
                {"language": "SENS", "source_sha": "2"*40},
            ]
            task["ineligible_candidates"] = []
            for candidate in ("C", "SENS"):
                plan["contrasts"].append({
                    "task": task["id"], "baseline": "Rust", "candidate": candidate,
                    "input_sha256": task["input_sha256"],
                    "metrics": ["wall_time_ns", "peak_rss_kib", "energy_uj"],
                })
        facts = validate(plan)
        self.assertEqual(facts["planned_candidate_cells"], 27)
        self.assertEqual(facts["contrasts"], 27)
        self.assertEqual(facts["explicit_na_cells"], 0)

    def test_duplicate_json_key_is_blocked(self):
        # JSON otherwise silently accepts the last duplicate key, allowing
        # mismatches between a reviewer-visible field and the parsed plan.
        with self.assertRaisesRegex(InvalidPlan, "duplicate key"):
            strict_json('{"state":"FROZEN","state":"DRAFT"}')
        with self.assertRaisesRegex(InvalidPlan, "duplicate key"):
            strict_json('{"tasks":[{"id":"task-a","id":"task-b"}]}')

    def test_nonfinite_json_number_is_blocked(self):
        with self.assertRaisesRegex(InvalidPlan, "nonfinite constant"):
            strict_json('{"alpha": NaN}')

    def test_command_line_shows_structure_only(self):
        path = Path(__file__).with_name("check_preregistration.py")
        with tempfile.TemporaryDirectory() as d:
            fixture = Path(d) / "synthetic-plan.json"
            fixture.write_text(json.dumps(frozen_fixture()), encoding="utf-8")
            p = subprocess.run([sys.executable, str(path), str(fixture)],
                               capture_output=True, text=True, check=False)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("PREREG_STRUCTURE_OK", p.stdout)
            self.assertIn("proof=STRUCTURE_ONLY", p.stdout)
            self.assertIn("semantics=NOT_CHECKED", p.stdout)
            bad = frozen_fixture()
            bad["contrasts"][0]["input_sha256"] = "f"*64
            fixture.write_text(json.dumps(bad), encoding="utf-8")
            p = subprocess.run([sys.executable, str(path), str(fixture)],
                               capture_output=True, text=True, check=False)
            self.assertEqual(p.returncode, 2)
            self.assertIn("PREREG_BLOCKED", p.stderr)


if __name__ == "__main__":
    unittest.main()
