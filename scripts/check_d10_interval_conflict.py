#!/usr/bin/env python3
"""D10 research-only exact interval conflict law / proof-carrying constraints.

Sources: Boost.Interval intersect/empty and IEEE 1788 interval model;
source-order choice of a conflicting pair is an explicitly new research
hypothesis, not falsely attributed to the standard.

Python is an executable arithmetic model, NOT a SENS interpreter oracle.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from fractions import Fraction
import itertools
import json
from pathlib import Path
import random
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "knowledge/d10-cross-hobby-interval-constraint-20261009.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
LOWER = ROOT / "knowledge/d1-d9-foundation.json"
NAME = "EXACT-INTERVAL-CONFLICT-WITNESS"


def exact(x):
    if type(x) is int:
        return Fraction(x)
    if isinstance(x, Fraction):
        return x
    if type(x) is str and x.strip():
        return Fraction(x)
    raise TypeError("source bound must be an explicit exact rational (not float/bool)")


@dataclass(frozen=True)
class Interval:
    source: str
    lo: Fraction
    hi: Fraction


def parse(records):
    if not isinstance(records, (list, tuple)) or not records:
        raise ValueError("expected a nonempty ordered sequence")
    seen = set()
    out = []
    for rec in records:
        if not isinstance(rec, (list, tuple)) or len(rec) != 3:
            raise ValueError("each constraint has source, lower, upper")
        source, lo, hi = rec
        if not isinstance(source, str) or not source or source in seen:
            raise ValueError("source identifiers must be unique, nonempty and opaque")
        seen.add(source)
        low, high = exact(lo), exact(hi)
        if low > high:
            raise ValueError("closed lower endpoint above upper endpoint")
        out.append(Interval(source, low, high))
    return out


def constrain(records):
    a = parse(records)
    lo = a[0].lo
    hi = a[0].hi
    lo_winner = 0
    hi_winner = 0
    for i, item in enumerate(a[1:], 1):
        # Stable earliest witness on equal attaining bounds.
        if item.lo > lo:
            lo, lo_winner = item.lo, i
        if item.hi < hi:
            hi, hi_winner = item.hi, i
    if lo <= hi:
        return ("SAT", lo, hi, a[lo_winner].source, a[hi_winner].source)
    # Deterministic witness: lexicographically first conflicting input pair.
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            if a[i].hi < a[j].lo:
                return ("UNSAT", i, j, a[j].source, a[i].source,
                        a[j].lo, a[i].hi)
            if a[j].hi < a[i].lo:
                return ("UNSAT", i, j, a[i].source, a[j].source,
                        a[i].lo, a[j].hi)
    raise AssertionError("L > U implies at least one disjoint pair")


def independent_oracle(records):
    """Materialize all pairwise conflicts, vs the streaming-bound algorithm."""
    a = parse(records)
    pairs = []
    for (i, v), (j, w) in itertools.combinations(enumerate(a), 2):
        if v.hi < w.lo:
            pairs.append((i, j, w.source, v.source, w.lo, v.hi))
        if w.hi < v.lo:
            pairs.append((i, j, v.source, w.source, v.lo, w.hi))
    if pairs:
        return ("UNSAT",) + min(pairs, key=lambda pair: pair[:2])
    lows = sorted(enumerate(a), key=lambda t: (-t[1].lo, t[0]))
    highs = sorted(enumerate(a), key=lambda t: (t[1].hi, t[0]))
    return ("SAT", lows[0][1].lo, highs[0][1].hi,
            lows[0][1].source, highs[0][1].source)


def verify_proposal(proposal, inv, foundation):
    c = proposal["candidate"]
    assert proposal["schema"] == "d10-cross-hobby-exact-interval-conflict/v1"
    assert proposal["status"] == "RESEARCH-PENDING-OWNER-REVIEW"
    assert proposal["source"]["standard"] == "IEEE 1788-2015 interval arithmetic"
    assert proposal["source"]["url"].startswith("https://standards.ieee.org/")
    assert proposal["source"]["library_url"].startswith("https://live.boost.org/")
    assert c["semantic_name"] == NAME
    assert c["source_class"] == "EXACT-RATIONAL-INTERVAL-CONSTRAINT"
    assert c["domain_width"] == 10
    assert c["coordinate"] is None and c["ratified"] is False and c["selected"] is False
    assert c["proposal_status"] == "pending-owner-review"
    assert all(c[field] for field in
               ("law", "arguments", "result", "surface_uk", "surface_ukr",
                "difference_from_D6", "unblock_fanout", "expressibility_gap"))
    assert len(c["positive_witnesses"]) == 5 and len(c["falsifiers"]) >= 5
    assert len(proposal["holds"]) >= 3 and all(
        row["status"].startswith("HOLD-") for row in proposal["holds"])
    assert inv["domain"] == "D10" and inv["capacity"] == 1024
    assert inv["accounting"]["ratified_d10_residents"] == 0
    assert inv["accounting"]["selected_semantic_candidates"] >= 630
    assert len(inv["rows"]) == inv["accounting"]["selected_semantic_candidates"]
    assert NAME not in {r["semantic_name"] for r in inv["rows"]}, (
        "candidate already selected; use canonical history/growth transition")
    assert foundation["status"] == "owner-ratified"
    lower_names = {
        str(x).upper()
        for dom in foundation["domains"].values()
        for x in dom["residents"].values()
    }
    assert "INTERSECTION" in lower_names
    assert NAME not in lower_names
    assert proposal["snapshot"]["selected"] == 630
    assert re.fullmatch(r"[0-9a-f]{40}", proposal["snapshot"]["inventory_blob_sha"])
    assert c["stable_proposal_id"] == "D10-INT-CERT-20261009"
    print("D10 INTERVAL dossier: PASS source-pinned NOT-SELECTED, no coordinates, no ratification")


class ExactIntervalLaw(unittest.TestCase):
    def test_documented_witnesses(self):
        sat = constrain([("a", 0, 4), ("b", 2, 6)])
        self.assertEqual(sat, ("SAT", Fraction(2), Fraction(4), "b", "a"))
        self.assertEqual(constrain([("a", 0, 2), ("b", 2, 4)]),
                         ("SAT", Fraction(2), Fraction(2), "b", "a"))
        self.assertEqual(constrain([("a", 0, 1), ("b", 2, 3)]),
                         ("UNSAT", 0, 1, "b", "a", Fraction(2), Fraction(1)))
        self.assertEqual(constrain([("a", 1, 3), ("b", 1, 3)]),
                         ("SAT", Fraction(1), Fraction(3), "a", "a"))
        self.assertEqual(constrain([("a", 0, 4), ("b", 5, 9),
                                    ("c", -100, 100), ("d", 20, 30)]),
                         ("UNSAT", 0, 1, "b", "a", Fraction(5), Fraction(4)))

    def test_exhaustive_four_constraints(self):
        intervals = [(lo, hi) for lo in range(-2, 3)
                      for hi in range(lo, 3)]
        total = 0
        for combo in itertools.product(intervals, repeat=4):
            rec = [(f"s{i}", lo, hi) for i, (lo, hi) in enumerate(combo)]
            self.assertEqual(constrain(rec), independent_oracle(rec))
            total += 1
        print(f"exact 4-interval combinations: {total}")

    def test_random_exact_rationals_and_order(self):
        rng = random.Random(20261009)
        for length in range(1, 10):
            for _ in range(400):
                records = []
                for i in range(length):
                    p = Fraction(rng.randint(-5000, 5000), rng.randint(1, 400))
                    q = Fraction(rng.randint(-5000, 5000), rng.randint(1, 400))
                    records.append((f"source-{i}", min(p, q), max(p, q)))
                self.assertEqual(constrain(records), independent_oracle(records))

    def test_singleton_and_repeated_bounds(self):
        self.assertEqual(constrain([("a", "2/3", "2/3")]),
                         ("SAT", Fraction(2, 3), Fraction(2, 3), "a", "a"))
        self.assertEqual(constrain([("a", 1, 2), ("b", 1, 2), ("c", 1, 2)]),
                         ("SAT", Fraction(1), Fraction(2), "a", "a"))

    def test_exact_negative_controls(self):
        for bad in [
            [], [("a", 4, 2)], [("a", 0.5, 1)], [("a", False, True)],
            [("a", 1, 2), ("a", 2, 3)], [("", 0, 1)], [("a", 0, 1, 2)]
        ]:
            with self.assertRaises((ValueError, TypeError)):
                constrain(bad)

    def test_unsat_certificate(self):
        for records in [
            [("a", 0, 1), ("b", 2, 3)],
            [("a", 2, 3), ("b", 0, 1)],
            [("a", "-1/3", "1/2"), ("b", "2/3", "7/3")]
        ]:
            result = constrain(records)
            self.assertEqual(result[0], "UNSAT")
            self.assertLess(result[-1], result[-2])
            self.assertNotEqual(result[3], result[4])

    def test_dossier_mutation_defense(self):
        proposal = json.loads(PROPOSAL.read_text(encoding="utf-8"))
        inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
        foundation = json.loads(LOWER.read_text(encoding="utf-8"))
        verify_proposal(proposal, inv, foundation)
        mutations = [
            lambda p: p["candidate"].update(selected=True),
            lambda p: p["candidate"].update(ratified=True),
            lambda p: p["candidate"].update(coordinate="1000000000"),
            lambda p: p["candidate"].update(semantic_name="INTERSECTION"),
            lambda p: p["candidate"].update(domain_width=9),
            lambda p: p["candidate"].update(falsifiers=[]),
            lambda p: p["source"].update(library_url="unverified"),
            lambda p: p["status"].__class__ and p.update(status="SELECTED")
        ]
        for f in mutations:
            bad = copy.deepcopy(proposal)
            f(bad)
            with self.assertRaises(AssertionError):
                verify_proposal(bad, inv, foundation)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    verify_proposal(json.loads(PROPOSAL.read_text(encoding="utf-8")),
                    json.loads(INVENTORY.read_text(encoding="utf-8")),
                    json.loads(LOWER.read_text(encoding="utf-8")))
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ExactIntervalLaw)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
