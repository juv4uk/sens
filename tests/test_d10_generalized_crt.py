#!/usr/bin/env python3
"""Generalized CRT research: independent arithmetic proof + *real* SymPy donor."""
from __future__ import annotations

import json
from math import gcd, lcm
from pathlib import Path
import unittest

from sympy import __version__ as sympy_version
from sympy.ntheory.modular import solve_congruence

ROOT = Path(__file__).resolve().parents[1]


def generalized_merge(a: int, m: int, b: int, n: int):
    """Language-observable exact law, not an admitted SENS opcode."""
    if any(type(x) is not int for x in (a, m, b, n)) or m <= 0 or n <= 0:
        raise ValueError("exact integral residues, positive integral moduli required")
    g = gcd(m, n)
    delta = b - a
    if delta % g:
        return ("CONFLICT", g, delta)
    reduced = n // g
    # A modulus of one has exactly one residue, so no modular inverse is needed.
    k = 0 if reduced == 1 else ((delta // g) * pow(m // g, -1, reduced)) % reduced
    period = lcm(m, n)
    residue = (a + m * k) % period
    return ("CONSISTENT", residue, period)


def exhaustive_canonical_reference(a: int, m: int, b: int, n: int):
    """Independent bounded enumeration; no modular inverse or SymPy."""
    period = lcm(m, n)
    candidates = [i for i in range(period)
                  if i % m == a % m and i % n == b % n]
    if not candidates:
        return ("CONFLICT", gcd(m, n), b - a)
    if len(candidates) != 1:
        raise AssertionError(f"not a unique canonical residue: {candidates}")
    return ("CONSISTENT", candidates[0], period)


class D10GeneralizedCRT(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dossier = json.loads((ROOT / "knowledge/d10-generalized-congruence-research-v1.json")
                                 .read_text(encoding="utf-8"))

    def test_representative_witnesses_and_conflict(self):
        examples = [
            ((2, 3, 3, 5), ("CONSISTENT", 8, 15)),
            ((2, 4, 6, 8), ("CONSISTENT", 6, 8)),
            ((-1, 6, 5, 8), ("CONSISTENT", 5, 24)),
            ((12, 6, 0, 6), ("CONSISTENT", 0, 6)),
            ((0, 1, 3, 7), ("CONSISTENT", 3, 7)),
            ((1, 4, 2, 6), ("CONFLICT", 2, 1)),
        ]
        for args, expected in examples:
            with self.subTest(args=args):
                self.assertEqual(generalized_merge(*args), expected)
                self.assertEqual(exhaustive_canonical_reference(*args), expected)

    def test_real_sympy_oracle_and_independent_exhaustion(self):
        self.assertEqual(sympy_version, "1.14.0")
        checked = compatible = incompatible = 0
        for m in range(1, 10):
            for n in range(1, 10):
                for a in range(-6, 7):
                    for b in range(-6, 7):
                        ours = generalized_merge(a, m, b, n)
                        independent = exhaustive_canonical_reference(a, m, b, n)
                        self.assertEqual(ours, independent)
                        donor = solve_congruence((a, m), (b, n))
                        if ours[0] == "CONFLICT":
                            self.assertIsNone(donor)
                            self.assertNotEqual((b - a) % gcd(m, n), 0)
                            incompatible += 1
                        else:
                            self.assertEqual(tuple(map(int, donor)), ours[1:])
                            self.assertEqual(ours[1] % m, a % m)
                            self.assertEqual(ours[1] % n, b % n)
                            self.assertLess(ours[1], ours[2])
                            compatible += 1
                        checked += 1
        self.assertEqual(checked, 13689)
        self.assertGreater(compatible, 0)
        self.assertGreater(incompatible, 0)
        print(f"D10-GENERALIZED-CRT: PASS real SymPy {sympy_version} "
              f"cases={checked} compatible={compatible} incompatible={incompatible}")

    def test_periodic_shift_swap_and_arbitrary_width(self):
        for a, m, b, n in ((7, 12, 3, 18), (8, 17, 6, 19), (5, 10, 8, 15)):
            canonical = generalized_merge(a, m, b, n)
            moved = generalized_merge(a + 101 * m, m, b - 303 * n, n)
            self.assertEqual(canonical[:1], moved[:1])
            if canonical[0] == "CONSISTENT":
                self.assertEqual(canonical, moved)
                self.assertEqual(canonical, generalized_merge(b, n, a, m))
            else:
                self.assertEqual(canonical[1], moved[1])
                self.assertEqual(canonical[1], generalized_merge(b, n, a, m)[1])
        big = 2 ** 521 - 1
        value = generalized_merge(-2 ** 300, big, -2 ** 300, big)
        self.assertEqual(value, ("CONSISTENT", (-2 ** 300) % big, big))

    def test_fail_closed_invalid_inputs(self):
        for args in ((1, 0, 2, 3), (1, -4, 2, 3), (1, 4, 2, 0),
                     (True, 4, 2, 3), (1.0, 4, 2, 3), (1, 4, 2, 3.0)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    generalized_merge(*args)

    def test_machine_dossier_no_selected_or_ratification(self):
        d = self.dossier
        self.assertEqual(d["schema"], "d10-generalized-congruence-research/v1")
        self.assertEqual(d["status"], "RESEARCH-ONLY-OWNER-REVIEW")
        self.assertEqual(d["accounting"], {"new_selected": 0,
                                            "new_coordinates": 0,
                                            "new_ratified": 0})
        roots = d["proposed_laws"]
        self.assertEqual(len(roots), 1)
        root = roots[0]
        self.assertEqual(root["semantic_name"], "GENERALIZED-CONGRUENCE-MERGE")
        self.assertEqual(root["dedup"], "EXACT-NAME-ONLY-FOUNDATION-D10; BEHAVIORAL-PROOF-PENDING")
        self.assertEqual(root["ownership"], "HOLD-CORE-VS-DERIVED-MATH")
        self.assertEqual((root["coordinate"], root["ratified"], root["selected"]),
                         (None, False, False))
        self.assertGreaterEqual(len(root["positive_witnesses"]), 2)
        self.assertGreaterEqual(len(root["falsifiers"]), 3)
        self.assertTrue(all(source.get("kind") for source in d["donor_sources"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
