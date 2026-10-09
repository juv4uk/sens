#!/usr/bin/env python3
"""Guard current D1/D3 separation law against accidental Contract 10 resurrection."""
import runpy
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
current_ground_separated = runpy.run_path(
    str(ROOT / "experiments/research-2019-h-nil-corpus.py")
)["current_ground_separated"]


class CurrentDomainEmptyGroundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = (ROOT / "language-contract.lisp").read_text(encoding="utf-8")

    def test_ratified_d3_empty_is_structural_not_function8_zero(self):
        self.assertTrue(current_ground_separated(self.contract))

    def test_missing_d3_ground_law_fails_closed(self):
        changed = self.contract.replace("000 structural empty ()", "000 callable NIL")
        self.assertNotEqual(changed, self.contract)
        self.assertFalse(current_ground_separated(changed))

    def test_reauthorizing_legacy_function8_fails_closed(self):
        changed = self.contract.replace(
            "They are not universal semantic identity",
            "They are universal semantic identity",
        )
        self.assertNotEqual(changed, self.contract)
        self.assertFalse(current_ground_separated(changed))

    def test_collapsing_predicate_and_structural_empty_fails_closed(self):
        changed = self.contract.replace(
            "PredicateBit is not Number, host Bool, T/NIL, Symbol, structural ()",
            "PredicateBit is structural ()",
        )
        self.assertNotEqual(changed, self.contract)
        self.assertFalse(current_ground_separated(changed))


if __name__ == "__main__":
    unittest.main()
