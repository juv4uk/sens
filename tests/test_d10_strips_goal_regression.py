#!/usr/bin/env python3
"""Exact STRIPS goal regression and independent forward-state proof boundary."""
from __future__ import annotations

import importlib.util
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_d10_strips_goal_regression.py"
DOSSIER = ROOT / "knowledge/d10-symbolic-ai-strips-goal-regression-research-v1.json"
spec = importlib.util.spec_from_file_location("research_strips_regression", SCRIPT)
assert spec and spec.loader
reg = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = reg
spec.loader.exec_module(reg)


class STRIPSResearch(unittest.TestCase):
    def test_backward_regression_exact_named_witnesses(self):
        witnesses = [
            # Positive case: must be ready before an observation is performed.
            (["ready"], ["observed"], [], ["observed"],
             {"status": "POSSIBLE", "required_before": ["ready"], "destroyed_goals": []}),
            # If add makes the entire goal true and no pre, predecessor may be empty.
            ([], ["observed"], [], ["observed"],
             {"status": "POSSIBLE", "required_before": [], "destroyed_goals": []}),
            # Deleting the sole wanted goal makes THIS action impossible.
            ([], [], ["observed"], ["observed"],
             {"status": "IMPOSSIBLE_BY_DELETE", "required_before": None,
              "destroyed_goals": ["observed"]}),
            # Irrelevant deletion must not block successful goal regression.
            (["ready"], ["observed"], ["obsolete"], ["observed", "retained"],
             {"status": "POSSIBLE", "required_before": ["ready", "retained"],
              "destroyed_goals": []}),
            (["ready"], ["ready"], [], [],  # empty goal != impossible
             {"status": "POSSIBLE", "required_before": ["ready"], "destroyed_goals": []}),
            ([], [], [], [],  # vacuous action & goal
             {"status": "POSSIBLE", "required_before": [], "destroyed_goals": []}),
            (["ready"], ["observed"], ["ready"], ["observed"],
             {"status": "POSSIBLE", "required_before": ["ready"], "destroyed_goals": []}),
            ([], ["observed"], ["ready"], ["observed", "ready"],
             {"status": "IMPOSSIBLE_BY_DELETE", "required_before": None,
              "destroyed_goals": ["ready"]}),
        ]
        for pre, add, delete, goal, want in witnesses:
            with self.subTest(pre=pre, add=add, delete=delete, goal=goal):
                self.assertEqual(reg.regress(pre, add, delete, goal), want)
                self.assertEqual(reg.brute_predecessor(pre, add, delete, goal), want)

    def test_exhaustive_all_1728_three_atom_action_goal_configurations(self):
        result = reg.exhaustive_3()
        self.assertEqual(result["configurations"], 12 ** 3)
        self.assertGreater(result["impossible_action_goal_cases"], 0)
        self.assertEqual(result["status"], "RESEARCH_ONLY_NOT_SELECTED")
        self.assertFalse(result["d10_ratified"])
        self.assertIsNone(result["d10_coordinate"])
        self.assertEqual(result["original_executable_migrations"], 0)

    def test_extra_atom_does_not_change_weakest_precondition(self):
        pre, add, delete, goal = ["power"], ["ready"], ["fault"], ["ready", "aligned"]
        expected = reg.regress(pre, add, delete, goal)
        self.assertEqual(expected["required_before"], ["aligned", "power"])
        for state in reg.all_states(("power", "ready", "fault", "aligned", "irrelevant")):
            reaches = reg.satisfies_after(state, pre, add, delete, goal)
            self.assertEqual(set(expected["required_before"]) <= state, reaches)

    def test_symbol_permutation_and_input_order_do_not_add_hidden_semantics(self):
        order = list("abcde")
        rng = random.Random(1971)
        for _ in range(640):
            pre = rng.sample(order, rng.randrange(6))
            add = rng.sample(order, rng.randrange(6))
            delete = rng.sample([x for x in order if x not in add],
                                rng.randrange(6 - len(add)))
            goal = rng.sample(order, rng.randrange(6))
            actual = reg.regress(pre, add, delete, goal)
            self.assertEqual(actual, reg.brute_predecessor(pre, add, delete, goal))
            self.assertEqual(actual, reg.regress(pre[::-1], add[::-1], delete[::-1], goal[::-1]))
            self.assertEqual(actual, reg.regress(tuple(pre), tuple(add), tuple(delete), tuple(goal)))

    def test_false_negative_weakening_and_destroy_ignore_are_detected(self):
        # A flawed shortcut dropping P from the regression could admit a world
        # that cannot actually execute action, even if the add list hits G.
        p, a, d, g = {"power"}, {"observed"}, set(), {"observed"}
        bad = g - a
        self.assertEqual(bad, set())
        counterexample = set()
        self.assertTrue(bad <= counterexample)
        self.assertFalse(reg.satisfies_after(counterexample, p, a, d, g))
        # A flawed pure projection would erase the delete conflict entirely.
        result = reg.regress([], [], ["observed"], ["observed"])
        self.assertEqual(result["status"], "IMPOSSIBLE_BY_DELETE")
        self.assertIsNone(result["required_before"])
        self.assertNotEqual(result["required_before"], [])

    def test_invalid_host_or_ambiguous_action_blocks(self):
        invalid = [
            (["a"], ["a"], ["a"], [], "added and deleted"),
            (["a", "a"], [], [], [], "duplicate"),
            (["A"], [], [], [], "lowercase"),
            (["a b"], [], [], [], "lowercase"),
            ("a", [], [], [], "list"),
            (["a"] * 17, [], [], [], "at most"),
            ([], [], [], ["a"] * 2, "duplicate"),
        ]
        for p, a, d, g, clue in invalid:
            with self.subTest(pre=p, add=a, delete=d, goal=g):
                with self.assertRaisesRegex(reg.ResearchBlocked, clue):
                    reg.regress(p, a, d, g)

    def test_bound_and_no_automatic_core_promotion(self):
        dossier = json.loads(DOSSIER.read_text(encoding="utf-8"))
        candidate = dossier["candidate"]
        self.assertEqual(candidate["stable_id"],
                         "d10.symbolic-ai.strips-weakest-positive-predecessor.research.20261009")
        self.assertEqual(candidate["status"], "HOLD-CORE-VS-DERIVED-LIBRARY-REVIEW")
        self.assertIsNone(candidate["coordinate"])
        self.assertFalse(candidate["selected"])
        self.assertFalse(candidate["ratified"])
        self.assertEqual(dossier["migration"]["original_executable_files_migrated"], 0)
        self.assertEqual(dossier["authority"]["scope"], "RESEARCH-ONLY")

    def test_cli_never_claims_binary_executable_or_selection(self):
        p = subprocess.run([sys.executable, str(SCRIPT), "--self-check"],
                           text=True, capture_output=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr)
        record = json.loads(p.stdout)
        self.assertEqual(record["configurations"], 1728)
        self.assertEqual(record["status"], "RESEARCH_ONLY_NOT_SELECTED")
        failure = subprocess.run([sys.executable, str(SCRIPT), "--pre", "bad Symbol"],
                                 text=True, capture_output=True)
        self.assertEqual(failure.returncode, 2)
        self.assertEqual(json.loads(failure.stdout)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
