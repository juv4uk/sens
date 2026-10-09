#!/usr/bin/env python3
"""Pure finite Boolean unit-closure, research only: no SENS semantic admission."""
from __future__ import annotations

import itertools
import json
import random
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-dll1962-unit-closure-research-v1.json"


def validate(cnf, assumptions):
    if type(cnf) is not list or type(assumptions) is not list:
        raise ValueError("canonical finite lists only")
    if any(type(l) is not int or l == 0 for l in assumptions):
        raise ValueError("exact, nonzero literals required")
    if assumptions != sorted(set(assumptions)):
        raise ValueError("assumptions must be sorted unique")
    if any(-lit in assumptions for lit in assumptions):
        raise ValueError("conflicting assumptions must be normalized externally")
    clauses = []
    for clause in cnf:
        if type(clause) is not list or any(type(l) is not int or l == 0 for l in clause):
            raise ValueError("canonical clause of exact nonzero integers required")
        if clause != sorted(set(clause)):
            raise ValueError("clause must be sorted unique")
        if any(-lit in clause for lit in clause):
            raise ValueError("tautological clause must be normalized externally")
        clauses.append(tuple(clause))
    if clauses != sorted(set(clauses)):
        raise ValueError("CNF clauses must be sorted unique")
    return clauses


def unit_closure(cnf, assumptions):
    clauses = validate(cnf, assumptions)
    forced = set(assumptions)
    while True:
        pending = set()
        for clause in clauses:
            if any(l in forced for l in clause):
                continue
            residue = [l for l in clause if -l not in forced]
            if not residue:
                return {"status": "CONTRADICTION", "forced": sorted(forced)}
            if len(residue) == 1:
                pending.add(residue[0])
        if not pending:
            break
        new = min(pending, key=lambda l: (abs(l), l))
        if -new in forced:
            return {"status": "CONTRADICTION", "forced": sorted(forced)}
        if new in forced:
            raise AssertionError("unit selection did not progress")
        forced.add(new)
    return {"status": "QUIESCENT", "forced": sorted(forced),
            "all_satisfied": all(any(l in forced for l in c) for c in clauses)}


def independent_rounds(cnf, assumptions):
    """Independent simultaneous rounds; no first-unit scheduling algorithm."""
    clauses = validate(cnf, assumptions)
    truth = {abs(l): l > 0 for l in assumptions}
    while True:
        new_truth = dict(truth)
        for clause in clauses:
            if any(truth.get(abs(l)) == (l > 0) for l in clause if abs(l) in truth):
                continue
            remaining = [l for l in clause if abs(l) not in truth]
            if not remaining:
                return "CONTRADICTION", None
            if len(remaining) == 1:
                lit = remaining[0]
                if abs(lit) in new_truth and new_truth[abs(lit)] != (lit > 0):
                    return "CONTRADICTION", None
                new_truth[abs(lit)] = lit > 0
        if new_truth == truth:
            return "QUIESCENT", tuple(sorted(v if t else -v for v, t in truth.items()))
        truth = new_truth


def canonical_cnf(clauses):
    return [list(c) for c in sorted({tuple(sorted(c)) for c in clauses})]


def literal_universe(n):
    result = []
    for signs in itertools.product((-1, 0, 1), repeat=n):
        clause = sorted((i + 1) * s for i, s in enumerate(signs) if s)
        if clause:
            result.append(clause)
    return canonical_cnf(result)


def assumptions_for(n):
    for signs in itertools.product((-1, 0, 1), repeat=n):
        yield sorted((i + 1) * s for i, s in enumerate(signs) if s)


def generated():
    """2304 portable cases: 256 2-variable CNFs × 9 assumption sets."""
    universe = literal_universe(2)
    assert len(universe) == 8
    ass = list(assumptions_for(2))
    assert len(ass) == 9
    for mask in range(1 << 8):
        cnf = canonical_cnf([universe[i] for i in range(8) if (mask >> i) & 1])
        for facts in ass:
            yield cnf, facts


def real_donor_corpus():
    """600 deterministic canonical cases, no false claim to exhaust all SAT CNFs."""
    universe = literal_universe(3)
    rng = random.Random(1962)
    facts = list(assumptions_for(3))
    for i in range(600):
        length = i % 9
        chosen = rng.sample(universe, length)
        yield canonical_cnf(chosen), facts[i % len(facts)]


def all_model_assignments(cnf, assumptions):
    vars_ = sorted({abs(l) for c in cnf for l in c} | {abs(l) for l in assumptions})
    if len(vars_) > 4:
        return []
    result = []
    for bits in itertools.product((False, True), repeat=len(vars_)):
        model = dict(zip(vars_, bits))
        if (all(model[abs(l)] == (l > 0) for l in assumptions)
                and all(any(model[abs(l)] == (l > 0) for l in c) for c in cnf)):
            result.append(model)
    return result


class TestD10UnitPropagation(unittest.TestCase):
    def test_witnesses_and_non_sat_boundary(self):
        cases = [
            (canonical_cnf([[1],[-1,2],[-2,3]]), [], "QUIESCENT", [1,2,3], True),
            (canonical_cnf([[1],[-1]]), [], "CONTRADICTION", None, None),
            (canonical_cnf([[-1,2],[1,3]]), [1], "QUIESCENT", [1,2], True),
            (canonical_cnf([[-1,2]]), [], "QUIESCENT", [], False),
            (canonical_cnf([[1,2],[1,-2],[-1,2],[-1,-2]]), [], "QUIESCENT", [], False),
            (canonical_cnf([[]]), [], "CONTRADICTION", None, None),
        ]
        for cnf, facts, status, forced, satisfied in cases:
            with self.subTest(cnf=cnf, assumptions=facts):
                got = unit_closure(cnf, facts)
                self.assertEqual(got["status"], status)
                if forced is not None:
                    self.assertEqual(got["forced"], forced)
                    self.assertIs(got["all_satisfied"], satisfied)

    def test_exhaustive_binary_cnfs_and_models(self):
        count = contradictions = quiescent = 0
        for cnf, facts in generated():
            result = unit_closure(cnf, facts)
            status, expected = independent_rounds(cnf, facts)
            self.assertEqual(result["status"], status)
            models = all_model_assignments(cnf, facts)
            if status == "CONTRADICTION":
                self.assertEqual(models, [])
                contradictions += 1
            else:
                self.assertEqual(tuple(result["forced"]), expected)
                for lit in result["forced"]:
                    self.assertTrue(all(model[abs(lit)] == (lit > 0) for model in models))
                if result["all_satisfied"]:
                    self.assertTrue(all(any(lit in result["forced"] for lit in clause)
                                        for clause in cnf))
                quiescent += 1
            count += 1
        self.assertEqual(count, 2304)
        print(f"D10-DLL1962: PASS {count} exact finite cases "
              f"contradiction={contradictions} quiescent={quiescent}")

    def test_idempotence_and_order_independence(self):
        for cnf, facts in itertools.islice(generated(), 0, 120):
            res = unit_closure(cnf, facts)
            if res["status"] == "QUIESCENT":
                self.assertEqual(unit_closure(cnf, res["forced"]), res)
                alternate = independent_rounds(cnf, facts)
                self.assertEqual(tuple(res["forced"]), alternate[1])

    def test_reject_noncanonical_or_tautological(self):
        cases = [
            ([[1,1]], []), ([[1,-1]], []), ([[2,1]], []),
            ([[0]], []), ([[True]], []), ([[1],[1]], []),
            ([], [1,1]), ([], [-1,1]), ([], [0]),
            ([], [False]), ([], [2,1]), (["1"], []),
        ]
        for cnf, assumptions in cases:
            with self.subTest(cnf=cnf, assumptions=assumptions):
                with self.assertRaises(ValueError):
                    unit_closure(cnf, assumptions)

    def test_non_admission_dossier(self):
        x = json.loads(DOSSIER.read_text(encoding="utf-8"))
        self.assertEqual(x["schema"], "d10-dll1962-unit-closure-research/v1")
        self.assertEqual(x["status"], "RESEARCH-ONLY-UNSELECTED-NOT-RATIFIED")
        self.assertEqual(x["candidate"]["name"], "FINITE-CNF-UNIT-FIXPOINT")
        self.assertEqual(x["candidate"]["authority"],
                         {"selected": False, "ratified": False, "coordinate": None})
        self.assertEqual(x["candidate"]["dedup"], "PENDING-FULL-D1-D9-AND-D10-BEHAVIOR")
        self.assertEqual(x["accounting"],
                         {"selected_delta":0,"ratified_delta":0,"coordinate_delta":0})


if __name__ == "__main__":
    unittest.main(verbosity=2)
