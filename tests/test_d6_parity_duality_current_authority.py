from __future__ import annotations

import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "benchmarks" / "d6-parity-duality" / "run.py"
RATIFIED = ROOT / "knowledge" / "d6-ratified.json"


class D6ParityDualityCurrentAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ns = runpy.run_path(str(RUNNER))
        cls.ratified = json.loads(RATIFIED.read_text(encoding="utf-8"))

    def test_parity_law_is_independent_of_coordinate_geometry(self) -> None:
        values = self.ns["corpus"]()
        witness = self.ns["semantic_witness"](values)
        self.assertEqual(len(values), 75)
        self.assertEqual(witness["period2_checks"], 1050)
        self.assertIsNotNone(witness["false_period1_first_counterexample"])
        self.assertIsNotNone(witness["false_even_equals_odd_first_counterexample"])
        self.assertEqual(len(witness["noninteger_rejections"]), 8)

    def test_current_resident_projection_comes_from_owner_map(self) -> None:
        current = self.ns["verify_current_residents"]()
        self.assertEqual(self.ratified["authority"], "#3393")
        self.assertEqual(current["EVENP"]["current_bits"], "010000")
        self.assertEqual(current["ODDP"]["current_bits"], "010001")
        self.assertEqual(current["EVENP"]["law_status"], "NEIGHBORHOOD-CANDIDATE")
        self.assertEqual(current["ODDP"]["law_status"], "NEIGHBORHOOD-CANDIDATE")
        geometry = self.ns["geometry_accounting"](current)
        self.assertEqual(geometry["current_ratified_projection"]["hamming_distance"], 1)
        self.assertFalse(geometry["one_bit_axis_is_semantically_proved"])
        self.assertEqual(geometry["semantic_geometry_status"], "NEIGHBORHOOD-CANDIDATE")

    def test_cli_runs_without_legacy_corpus_and_reports_current_authority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="sens-d6-parity-") as tmp:
            out = Path(tmp) / "out"
            result = subprocess.run(
                [sys.executable, str(RUNNER), "--out", str(out)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            relation = json.loads((out / "relation.json").read_text(encoding="utf-8"))
            self.assertEqual(relation["schema"], "d6-parity-duality/v2")
            self.assertEqual(
                relation["resident_projection"]["EVENP"]["current_bits"], "010000"
            )
            self.assertEqual(
                relation["resident_projection"]["ODDP"]["current_bits"], "010001"
            )
            self.assertEqual(
                relation["status"]["semantic_relation"],
                "BOUNDED-CONFIRMED-EXACT-INTEGER",
            )
            self.assertEqual(relation["status"]["geometry"], "NEIGHBORHOOD-CANDIDATE")
            self.assertNotIn("sr-qcstbceparwp", result.stdout)
            self.assertNotIn("sr-vnrkjfutjtyh", result.stdout)


if __name__ == "__main__":
    unittest.main()
