"""Adversarial witness checks: 8 quoted-symbol cases remain unadmitted."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/report_machine_block_quote_data_frontier.py"
spec = importlib.util.spec_from_file_location("quote_data_frontier", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PhysicalQuoteDataFrontier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = mod.ORIGINAL.read_bytes()
        cls.oracle = mod.ORACLE.read_text(encoding="utf-8")
        cls.projection = mod.TEXT7.read_text(encoding="utf-8")

    def audit(self, **changes):
        inputs = {
            "original": self.source,
            "oracle": self.oracle,
            "projection": self.projection,
        }
        inputs.update(changes)
        return mod.census(**inputs)

    def test_exact_original_and_nine_history_cases(self):
        a = self.audit()
        self.assertEqual(a["original_git_blob"], mod.SOURCE_BLOB)
        self.assertEqual(a["independent_observer_cases"], 9)
        self.assertEqual(len(a["quote_symbol_data_blocked_cases"]), 8)
        self.assertEqual(a["quoted_atoms_by_observation"]["empty"], [])
        self.assertEqual(set(a["unique_historical_quote_atoms"]), set(mod.EXPECTED_ATOMS))
        self.assertEqual(a["case_sensitive_nonrepresentable_labels"], ["L1", "L2"])
        self.assertEqual(a["physical_originals_certified"], 0)
        self.assertFalse(a["release_admitted"])
        self.assertEqual(a["ratified_d10_residents_added"], 0)

    def test_any_original_git_blob_mutation_blocks(self):
        with self.assertRaisesRegex(ValueError, "historical Git blob drifted"):
            self.audit(original=self.source + b" ")

    def test_missing_historical_case_or_changed_atom_blocks(self):
        with self.assertRaisesRegex(ValueError, "nine named cases"):
            self.audit(oracle=self.oracle.replace('"concat_right_empty":', '"renamed":', 1))
        with self.assertRaisesRegex(ValueError, "symbol set changed"):
            self.audit(oracle=self.oracle.replace('"L1"', '"L0"', 1))

    def test_proposed_uppercase_layout_change_forces_review(self):
        with self.assertRaisesRegex(ValueError, "uppercase label layout changed"):
            self.audit(projection=self.projection + '\n    ("L", Some(&[0x42])),\n')

    def test_nested_symbol_data_is_distinct_from_quote_empty(self):
        assert not mod.symbol_leaves([])
        self.assertEqual(mod.symbol_leaves(["mov", ["r1", "r2"]]),
                         ["mov", "r1", "r2"])
        with self.assertRaisesRegex(ValueError, "unadmitted historical observable"):
            mod.symbol_leaves([{"unverified": "symbol"}])

    def test_checker_does_not_write_original_or_encode_any_t5(self):
        before = self.source
        a = self.audit()
        self.assertEqual(mod.ORIGINAL.read_bytes(), before)
        self.assertEqual(a["status"], "RESEARCH_BLOCKED_NOT_AN_ADMISSION")
        self.assertNotIn("newly_certified_files", json.dumps(a))
        self.assertFalse(a["release_admitted"])


if __name__ == "__main__":
    unittest.main()
