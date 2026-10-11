#!/usr/bin/env python3
"""D10 research-only bounded rational approximation: exact law and falsifiers.

Donor context: juv4uk/spanda README.md (E-P Dance exact p/q -> analog -> p/q).
Independent comparison: Python's Fraction.limit_denominator and exhaustive
brute-force rational search. No SENS runtime/bit-coordinate implementation.
"""
from __future__ import annotations

import argparse
import copy
from fractions import Fraction
import json
import random
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-cross-hobby-bounded-rational-v1.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
NAME = "BEST-BOUNDED-RATIONAL"


def nearest_bounded_cf(x: Fraction, maximum_denominator: int) -> Fraction:
    """Exact continued-fraction convergents and semiconvergents; no float."""
    if not isinstance(x, Fraction):
        raise TypeError("x must be an EXACT rational Fraction")
    if type(maximum_denominator) is not int or maximum_denominator < 1:
        raise ValueError("max denominator must be a positive integer")
    if x.denominator <= maximum_denominator:
        return x

    n, d = x.numerator, x.denominator
    p0, q0, p1, q1 = 0, 1, 1, 0
    while True:
        a = n // d
        q2 = q0 + a * q1
        if q2 > maximum_denominator:
            break
        p0, q0, p1, q1 = p1, q1, p0 + a * p1, q2
        n, d = d, n - a * d
        if d == 0:
            return Fraction(p1, q1)
    k = (maximum_denominator - q0) // q1
    lower_or_upper = Fraction(p0 + k * p1, q0 + k * q1)
    other = Fraction(p1, q1)
    return min((lower_or_upper, other),
               key=lambda value: (abs(value - x), value.denominator, value))


def brute_nearest(x: Fraction, maximum_denominator: int) -> Fraction:
    """Independent finite oracle enumerating only adjacent integer numerators."""
    if maximum_denominator < 1:
        raise ValueError("invalid denominator bound")
    candidates: set[Fraction] = set()
    for q in range(1, maximum_denominator + 1):
        p = (x.numerator * q) // x.denominator
        candidates.add(Fraction(p, q))
        candidates.add(Fraction(p + 1, q))
    return min(candidates,
               key=lambda y: (abs(y - x), y.denominator, y))


def validate_dossier(d: dict, inv: dict, foundation: dict) -> None:
    assert d["schema"] == "d10-spanda-bounded-rational-proposal/v1"
    assert d["status"] == "RESEARCH-PENDING-OWNER-REVIEW"
    assert d["selected_inventory_effect"] == d["coordinate_effect"] == d["ratification_effect"] == 0
    assert d["donor"]["owner_project"] == "juv4uk/spanda"
    assert d["donor"]["path"] == "README.md"
    assert re.fullmatch("[a-f0-9]{40}", d["donor"]["blob_sha"])
    assert d["donor"]["lines"] == "19-38"
    assert d["algorithm_reference"]["docs_url"].startswith("https://docs.python.org/")
    assert d["algorithm_reference"]["source_url"].startswith("https://github.com/python/cpython/")
    item = d["candidate"]
    assert item["semantic_name"] == NAME
    assert item["width"] == 10
    assert item["coordinate"] is None and item["ratified"] is False
    assert item["selected"] is False and item["status"] == "pending-review"
    assert item["surface_uk"] and item["surface_ukr"]
    assert len(item["positivity"]) >= 3 and len(item["falsifiers"]) >= 3
    assert len(d["holds"]) >= 4
    assert all(h["status"].startswith("HOLD-") for h in d["holds"])
    assert item["expressibility_gap"] and item["unblock_fanout"]
    assert inv["domain"] == "D10" and inv["capacity"] == 1024
    assert inv["accounting"]["ratified_d10_residents"] == 0
    # Historical baseline is frozen, but selected research count may grow.
    assert inv["accounting"]["selected_semantic_candidates"] >= d["baseline"]["selected"]
    assert NAME not in {str(r["semantic_name"]).upper() for r in inv["rows"]}, (
        "candidate has already been selected: use growth transition instead")
    lower = {
        str(name).upper()
        for domain in foundation["domains"].values()
        for name in domain["residents"].values()
    }
    assert NAME not in lower
    assert foundation["status"] == "owner-ratified"
    assert item["source_class"] == "EXACT-RATIONAL-APPROXIMATION"
    assert d["limitations"] and d["candidate"]["uncertainty"]


def validate_witnesses(d: dict) -> None:
    for case in d["candidate"]["positivity"]:
        x = Fraction(case["x"])
        want = Fraction(case["result"])
        actual = nearest_bounded_cf(x, case["M"])
        assert actual == want, (case, str(actual))
        assert brute_nearest(x, case["M"]) == want


class ExactLawTests(unittest.TestCase):
    def test_fixed_witnesses(self):
        dossier = json.loads(DOSSIER.read_text(encoding="utf-8"))
        validate_witnesses(dossier)

    def test_exhaustive_independent_brute_oracle(self):
        total = 0
        for p in range(-17, 18):
            for q in range(1, 14):
                x = Fraction(p, q)
                for m in range(1, 19):
                    got = nearest_bounded_cf(x, m)
                    self.assertEqual(got, brute_nearest(x, m), (p, q, m))
                    self.assertLessEqual(got.denominator, m)
                    self.assertGreater(got.denominator, 0)
                    total += 1
        print(f"exhaustive distinct source inputs: {total} triple cases")

    def test_random_vs_independent_python_stdlib(self):
        rand = random.Random(20261009)
        for _ in range(1000):
            x = Fraction(rand.randrange(-999999, 999999),
                         rand.randrange(1, 99999))
            m = rand.randrange(1, 2000)
            self.assertEqual(nearest_bounded_cf(x, m),
                             x.limit_denominator(m))

    def test_sign_symmetry_except_exact_midpoint_tie(self):
        self.assertEqual(nearest_bounded_cf(Fraction(3, 2), 1), Fraction(1))
        self.assertEqual(nearest_bounded_cf(Fraction(-3, 2), 1), Fraction(-2))
        self.assertEqual(nearest_bounded_cf(Fraction(1, 2), 1), Fraction(0))
        self.assertEqual(nearest_bounded_cf(Fraction(-1, 2), 1), Fraction(-1))

    def test_float_not_silently_accepted(self):
        with self.assertRaises(TypeError):
            nearest_bounded_cf(3.14159, 100)

    def test_invalid_denominator_bounds(self):
        for invalid in [0, -1, True, False, 1.5, "8"]:
            with self.assertRaises(ValueError):
                nearest_bounded_cf(Fraction(2, 7), invalid)

    def test_fail_closed_mutations(self):
        d = json.loads(DOSSIER.read_text(encoding="utf-8"))
        i = json.loads(INVENTORY.read_text(encoding="utf-8"))
        f = json.loads(FOUNDATION.read_text(encoding="utf-8"))
        validate_dossier(d, i, f)
        mutants = [
            ("fake selected", lambda z: z["candidate"].__setitem__("selected", True)),
            ("fake bit coord", lambda z: z["candidate"].__setitem__("coordinate", "1000000000")),
            ("forged ratification", lambda z: z["candidate"].__setitem__("ratified", True)),
            ("missing source pin", lambda z: z["donor"].__setitem__("blob_sha", "no-proof")),
            ("omitted falsifiers", lambda z: z["candidate"].__setitem__("falsifiers", [])),
            ("wrong width", lambda z: z["candidate"].__setitem__("width", 9)),
            ("lower-level collision", lambda z: z["candidate"].__setitem__("semantic_name", "ROUND")),
            ("old count forged", lambda z: z.__setitem__("ratification_effect", 1)),
        ]
        for label, mutator in mutants:
            bad = copy.deepcopy(d)
            mutator(bad)
            with self.subTest(label=label):
                with self.assertRaises(AssertionError):
                    validate_dossier(bad, i, f)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    dossier = json.loads(DOSSIER.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    validate_dossier(dossier, inventory, foundation)
    validate_witnesses(dossier)
    print("D10 BOUNDED-RATIONAL: research proposal PASS; 0 selected, 0 ratified, 0 coordinates")
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ExactLawTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)


if __name__ == "__main__":
    main()
