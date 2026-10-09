#!/usr/bin/env python3
"""Pure two-variable CSP support law. Research only: no D10 opcode authority."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-symbolic-ai-arc-support-20261009.json"


def canonical(values, pair=False):
    if type(values) is not list:
        raise ValueError("requires finite canonical list")
    if pair:
        if any(type(x) is not list or len(x) != 2 or
               any(type(n) is not int for n in x) for x in values):
            raise ValueError("relation must be ordered pairs of exact integers")
        tuples = [tuple(x) for x in values]
    else:
        if any(type(x) is not int for x in values):
            raise ValueError("domain must contain exact integers")
        tuples = values
    if tuples != sorted(set(tuples)):
        raise ValueError("noncanonical sorted unique list")
    return tuples


def project_support(left, right, relation):
    """Local relation arc projection, NOT graph-wide constraint solving."""
    canonical(left)
    canonical(right)
    canonical(relation, pair=True)
    leftset, rightset = set(left), set(right)
    supported = [(a, b) for a, b in relation if a in leftset and b in rightset]
    if not supported:
        return {"status": "NO-SUPPORT", "left": [], "right": []}
    return {"status": "SUPPORTED",
            "left": sorted({a for a, _ in supported}),
            "right": sorted({b for _, b in supported})}


def independent_support(left, right, relation):
    """Existential support per candidate; independent of edge filtering."""
    canonical(left)
    canonical(right)
    canonical(relation, pair=True)
    sx = [x for x in left if any([x, y] in relation for y in right)]
    sy = [y for y in right if any([x, y] in relation for x in left)]
    if not sx:
        assert not sy
        return {"status": "NO-SUPPORT", "left": [], "right": []}
    return {"status": "SUPPORTED", "left": sx, "right": sy}


def all_cases():
    """768 deterministic cases shared with actual SWI-Prolog CLP(FD)."""
    pairs = [[a, b] for a in range(3) for b in range(3)]
    entries = []
    full = [0, 1, 2]
    for mask in range(1 << len(pairs)):
        relation = [p for i, p in enumerate(pairs) if mask & (1 << i)]
        entries.append({"left": full, "right": full, "relation": relation})
    for mask in (0, 1, 37, 511):
        relation = [p for i, p in enumerate(pairs) if mask & (1 << i)]
        for lm in range(8):
            for rm in range(8):
                entries.append({"left": [i for i in full if lm & (1 << i)],
                                "right": [i for i in full if rm & (1 << i)],
                                "relation": relation})
    assert len(entries) == 768
    return entries


def emit(path):
    cases = all_cases()
    Path(path).write_text(json.dumps(cases, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"D10-SYMBOLIC-CLP: emitted {len(cases)} canonical cases")


def check(prolog_path, cases_path):
    expected = [project_support(**case) for case in
                json.loads(Path(cases_path).read_text(encoding="utf-8"))]
    observed = json.loads(Path(prolog_path).read_text(encoding="utf-8"))
    if observed != expected:
        for i, (a, b) in enumerate(zip(expected, observed)):
            if a != b:
                raise AssertionError(f"real Prolog mismatch at {i}: expected {a}, got {b}")
        raise AssertionError(f"real Prolog output length mismatch {len(expected)} / {len(observed)}")
    assert len(observed) == 768
    print("D10-SYMBOLIC-CLP: REAL-SWIPL-PARITY PASS 768/768")


class TestArcSupport(unittest.TestCase):
    def test_source_dossier_is_unselected(self):
        d = json.loads(DOSSIER.read_text(encoding="utf-8"))
        assert d["status"] == "RESEARCH-ONLY-UNSELECTED"
        assert d["candidate"]["semantic_name"] == "BINARY-CONSTRAINT-SUPPORT-PROJECTION"
        assert d["candidate"]["candidate_only"] == {
            "selected": False, "ratified": False, "coordinate": None,
            "physical_sens": False, "owner_review_required": True}
        assert d["candidate"]["dedup"] == "PENDING-FULL-D1-D9-AND-D10-BEHAVIOR"
        assert d["candidate"]["ownership"] == "HOLD-CORE-VS-DERIVED-CLP-LIBRARY"
        assert d["accounting"] == {"new_selected": 0,
                                   "new_coordinates": 0,
                                   "new_ratified": 0}
        assert len(d["candidate"]["witnesses"]) >= 2
        assert len(d["candidate"]["falsifiers"]) >= 4
        assert d["primary_sources"][1]["source_pointer"].endswith(
            "library/clp/clpfd.pl:4074-4145")

    def test_real_donor_evidence_does_not_ratify(self):
        proof = json.loads((ROOT / "knowledge/d10-symbolic-ai-clp-oracle-evidence-v1.json")
                           .read_text(encoding="utf-8"))
        self.assertEqual(proof["schema"], "d10-symbolic-ai-clp-oracle-evidence/v1")
        self.assertEqual(proof["status"], "DONOR-OBSERVED-RESEARCH-NOT-SENS-EXECUTION")
        self.assertEqual(proof["observed_runtime"], "SWI-Prolog 9.0.4 for x86_64-linux")
        self.assertEqual(proof["real_swi_prolog"]["shared_cases"], 768)
        self.assertEqual(proof["real_swi_prolog"]["matched"], 768)
        self.assertEqual(proof["mathematical_python"],
                         {"cases": 32768, "supported": 19759,
                          "conflicts": 13009, "groups_passed": 5})
        self.assertEqual(proof["authority"],
                         {"new_selected": 0, "new_ratified": 0, "new_coordinates": 0})
        self.assertGreaterEqual(len(proof["constraints_unproven"]), 4)
        dossier = json.loads(DOSSIER.read_text(encoding="utf-8"))
        self.assertEqual(dossier["experiments"]["oracle_evidence"],
                         "knowledge/d10-symbolic-ai-clp-oracle-evidence-v1.json")
        self.assertIn("CORE", dossier["candidate"]["ownership"])

    def test_examples(self):
        d = json.loads(DOSSIER.read_text(encoding="utf-8"))
        for c in d["candidate"]["witnesses"]:
            with self.subTest(c=c):
                got = project_support(c["dx"], c["dy"], c["allowed"])
                self.assertEqual(got, c["out"])
                self.assertEqual(got, independent_support(c["dx"], c["dy"], c["allowed"]))

    def test_every_three_by_three_finite_relation_and_domain(self):
        pairs = [[a, b] for a in range(3) for b in range(3)]
        checked, supported, conflicts = 0, 0, 0
        for mask in range(1 << len(pairs)):
            rel = [p for i, p in enumerate(pairs) if mask & (1 << i)]
            for lm in range(8):
                L = [i for i in range(3) if lm & (1 << i)]
                for rm in range(8):
                    R = [i for i in range(3) if rm & (1 << i)]
                    result = project_support(L, R, rel)
                    self.assertEqual(result, independent_support(L, R, rel))
                    if result["status"] == "NO-SUPPORT":
                        conflicts += 1
                    else:
                        supported += 1
                        newL, newR = result["left"], result["right"]
                        self.assertTrue(all(any([x, y] in rel for y in newR) for x in newL))
                        self.assertTrue(all(any([x, y] in rel for x in newL) for y in newR))
                        self.assertEqual(result, project_support(newL, newR, rel))
                    checked += 1
        self.assertEqual(checked, 32768)
        self.assertGreater(supported, 0)
        self.assertGreater(conflicts, 0)
        print(f"D10-SYMBOLIC-CLP: exhaustive PASS {checked} supported={supported} conflicts={conflicts}")

    def test_symmetry_and_subset_monotonicity(self):
        relations = ([[1, 3], [1, 5], [2, 5]], [[1, 5], [2, 3]], [])
        for rel in relations:
            for lx in ([], [1], [1, 2]):
                for ly in ([], [3], [3, 5]):
                    actual = project_support(lx, ly, list(rel))
                    transposed = sorted([[y, x] for x, y in rel])
                    reversed_result = project_support(ly, lx, transposed)
                    self.assertEqual(actual["status"], reversed_result["status"])
                    self.assertEqual(actual["left"], reversed_result["right"])
                    self.assertEqual(actual["right"], reversed_result["left"])
                    larger = project_support([1, 2], [3, 5], list(rel))
                    self.assertTrue(set(actual["left"]) <= set(larger["left"]))
                    self.assertTrue(set(actual["right"]) <= set(larger["right"]))

    def test_rejects_noncanonical_inputs(self):
        invalid = [
            ([2, 1], [3], []), ([1, 1], [3], []),
            ([True], [3], []), ([1.0], [3], []),
            ([1], [3], [[1, 3], [1, 3]]),
            ([1], [3], [[1, 4], [1, 3]]),
            ([1], [3], [[1, True]]),
            ([1], [3], [[1, 3, 4]]),
            (None, [3], []), ([1], "3", [])
        ]
        for left, right, relation in invalid:
            with self.subTest(left=left, right=right, relation=relation):
                with self.assertRaises(ValueError):
                    project_support(left, right, relation)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--emit":
        emit(sys.argv[2])
    elif len(sys.argv) == 4 and sys.argv[1] == "--check":
        check(sys.argv[2], sys.argv[3])
    else:
        unittest.main(verbosity=2)
