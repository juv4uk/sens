#!/usr/bin/env python3
"""Strict source+law tests, NO D10 selection or physical T5 writes."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "scripts/check_d10_general_congruence_merge_hobbies.py"
spec = importlib.util.spec_from_file_location("d10_hobby_crt", CODE)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class CongruenceHobbyResearch(unittest.TestCase):
    def test_exact_two_and_three_moduli_bruteforce(self):
        summary = m.run_checks()
        self.assertGreaterEqual(summary["independently_exhausted_systems"], 9000)
        self.assertGreater(summary["pair_incompatible"], 100)
        self.assertEqual(summary["D10_selected_delta"], 0)
        self.assertEqual(summary["ratified_delta"], 0)

    def test_actual_sympy_oracle(self):
        try:
            import sympy  # noqa: F401
        except ImportError:
            self.skipTest("Real SymPy donor installed by dedicated Actions job")
        obs = m.sympy_donor()
        self.assertGreaterEqual(obs["observations"], 10000)
        self.assertEqual(obs["status"], "PASS")

    def test_conflict_is_original_first_pair_not_after_aggregate(self):
        self.assertEqual((m.merge_congruences(
            [(0,4),(0,6),(1,2)])["i"],
            m.merge_congruences([(0,4),(0,6),(1,2)])["j"]), (0, 2))
        self.assertEqual(m.merge_congruences([(2,6),(5,9)])["modulus"], 18)

    def test_metamorphic_idempotence_and_negative_modulus(self):
        cases = [[(3,5)], [(2,6),(5,9)], [(2,3),(3,5),(2,7)]]
        for p in cases:
            self.assertEqual(m.merge_congruences(p), m.merge_congruences(p + p[:1]))
        for value in ([(0,0)], [(2,-1)], [(False,1)], [(1,"6")]):
            with self.assertRaises(m.InvalidCongruence):
                m.merge_congruences(value)

    def test_manifest_is_hold_and_no_current_exact_name_collision(self):
        x = m.validate_dossier()
        self.assertIsNone(x["proposal"]["coordinate"])
        self.assertFalse(x["proposal"]["selected"])
        self.assertFalse(x["proposal"]["ratified"])
        self.assertEqual(x["scope"]["selected_delta"], 0)
        self.assertEqual(len(x["negative_witnesses"]), 3)
        self.assertTrue(x["dedup_review"]["full_behavioral_dedup"].startswith("HOLD"))

    def test_fail_closed_manifest_mutations(self):
        raw = json.loads(m.DOSSIER.read_text())
        original_read_text = Path.read_text
        cases = [
            ("ratified", True), ("selected", True), ("coordinate", "0000000001"),
            ("semantic_name", "MODULO"), ("source_era", "legacy-sid8")
        ]
        for key, value in cases:
            clone = json.loads(json.dumps(raw))
            clone["proposal"][key] = value
            with patch.object(m.Path, "read_text", autospec=True) as reader:
                def synthetic(instance, *args, **kwargs):
                    if instance == m.DOSSIER:
                        return json.dumps(clone)
                    return original_read_text(instance, *args, **kwargs)
                reader.side_effect = synthetic
                with self.subTest(key=key), self.assertRaises(AssertionError):
                    m.validate_dossier()


if __name__ == "__main__":
    unittest.main()
