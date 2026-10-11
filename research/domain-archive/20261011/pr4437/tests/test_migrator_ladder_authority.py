#!/usr/bin/env python3
"""Regression: source migrators must consume ratified D1-D9 / Number ladder."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from domain_tables import validate_ratified_ladder


class MigratorLadderAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.foundation = json.loads(
            (ROOT / "knowledge/d1-d9-foundation.json").read_text(encoding="utf-8")
        )
        cls.numbers = json.loads(
            (ROOT / "knowledge/number-width-ratified.json").read_text(encoding="utf-8")
        )

    def test_all_nine_domain_tables_match_ratified_foundation(self):
        counts = validate_ratified_ladder(self.foundation, self.numbers)
        self.assertEqual(counts["D1"], 2)
        self.assertEqual(counts["D2"], 4)
        self.assertEqual(counts["D3"], 8)
        self.assertEqual(counts["D7"], 126)
        self.assertEqual(counts["D8"], 256)
        self.assertEqual(counts["D9"], 512)

    def test_missing_d8_or_d9_fails_closed(self):
        for label in ("D8", "D9"):
            with self.subTest(label=label):
                foundation = copy.deepcopy(self.foundation)
                del foundation["domains"][label]
                with self.assertRaisesRegex(ValueError, "missing ratified domains"):
                    validate_ratified_ladder(foundation, self.numbers)

    def test_same_width_but_wrong_coordinate_fails_closed(self):
        foundation = copy.deepcopy(self.foundation)
        foundation["domains"]["D8"]["residents"].pop("11110110")
        with self.assertRaisesRegex(ValueError, "coordinate mismatch"):
            validate_ratified_ladder(foundation, self.numbers)

    def test_d2_structure_drift_blocks_conversion(self):
        foundation = copy.deepcopy(self.foundation)
        foundation["domains"]["D2"]["residents"]["10"] = "SEPARATOR"
        with self.assertRaisesRegex(ValueError, "D2 structure"):
            validate_ratified_ladder(foundation, self.numbers)

    def test_number_24_48_96_ladder_checked_but_value_codec_not_invented(self):
        policy = copy.deepcopy(self.numbers)
        policy["ratified_prefix_bits"] = [24, 64, 96]
        with self.assertRaisesRegex(ValueError, "Number width ladder drift"):
            validate_ratified_ladder(self.foundation, policy)


if __name__ == "__main__":
    unittest.main()
