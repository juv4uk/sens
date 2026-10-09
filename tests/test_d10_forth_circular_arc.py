#!/usr/bin/env python3
"""A Forth-derived circular-interval research law, not a D10 resident."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-forth-circular-arc-v1.json"


def circular_contains(value, low, high, modulus):
    if any(type(arg) is not int for arg in (value, low, high, modulus)):
        raise ValueError("exact integers only")
    if modulus < 2 or not all(0 <= arg < modulus for arg in (value, low, high)):
        raise ValueError("noncanonical residue or invalid modulus")
    if low < high:
        return 1 if low <= value < high else 0
    if low > high:
        return 1 if value >= low or value < high else 0
    return 0


def enumerate_arc_contains(value, low, high, modulus):
    """Independent ring walk, never uses the branch comparisons above."""
    present = set()
    cursor = low
    # Empty when low==high: do not treat a full cycle as a full ring.
    while cursor != high or (cursor == low and not present and low != high):
        present.add(cursor)
        cursor = (cursor + 1) % modulus
    return 1 if value in present else 0


class CircularArcResearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dossier = json.loads(DOSSIER.read_text(encoding="utf-8"))

    def test_explicit_boundary_witnesses(self):
        samples = [
            (250, 240, 16, 256, 1),
            (10, 240, 16, 256, 1),
            (16, 240, 16, 256, 0),
            (100, 240, 16, 256, 0),
            (5, 0, 10, 256, 1),
            (10, 0, 10, 256, 0),
            (7, 7, 7, 256, 0),
            (4095, 4088, 8, 4096, 1),
            (0, 4088, 8, 4096, 1),
            (8, 4088, 8, 4096, 0),
        ]
        for value, low, high, modulus, expected in samples:
            with self.subTest(args=(value, low, high, modulus)):
                self.assertEqual(circular_contains(value, low, high, modulus), expected)
                self.assertEqual(enumerate_arc_contains(value, low, high, modulus), expected)

    def test_exhaustive_finite_rings(self):
        total = 0
        for modulus in range(2, 26):
            for low in range(modulus):
                for high in range(modulus):
                    for value in range(modulus):
                        result = circular_contains(value, low, high, modulus)
                        self.assertEqual(result, enumerate_arc_contains(value, low, high, modulus))
                        # A second algebraic oracle uses clockwise distance.
                        expected = (int((value - low) % modulus < (high - low) % modulus)
                                    if low != high else 0)
                        self.assertEqual(result, expected)
                        total += 1
        self.assertEqual(total, 105624)
        print("D10-FORTH-RING: PASS 105624 exhaustive finite-ring witnesses")

    def test_rotation_equivariance_and_endpoint_exclusivity(self):
        m = 4096
        for low, high, value in ((4088, 8, 4095), (4088, 8, 10),
                                  (100, 200, 150), (10, 10, 10),
                                  (4090, 4, 4)):
            base = circular_contains(value, low, high, m)
            for shift in (0, 1, 2048, 4095):
                self.assertEqual(base, circular_contains(
                    (value + shift) % m, (low + shift) % m,
                    (high + shift) % m, m))
            self.assertEqual(circular_contains(high, low, high, m), 0)

    def test_invalid_domain_rejects(self):
        cases = ((256, 240, 16, 256), (-1, 240, 16, 256),
                 (1, 0, 1, 1), (1, 0, 1, 0),
                 (1, 0, 1, -1), (1.0, 0, 1, 8),
                 (True, 0, 1, 8), (1, 0, 1, 8.0),
                 (1, -1, 1, 8), (1, 1, 8, 8))
        for args in cases:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    circular_contains(*args)

    def test_d10_research_only_schema(self):
        d = self.dossier
        self.assertEqual(d["schema"], "d10-forth-circular-arc-research/v1")
        self.assertEqual(d["status"], "RESEARCH-ONLY-NOT-SELECTED")
        self.assertEqual(d["accounting"],
                         {"selected_delta": 0, "ratified_delta": 0, "coordinate_delta": 0})
        r = d["candidate"]
        self.assertEqual(r["semantic_name"], "CIRCULAR-HALF-OPEN-CONTAINS")
        self.assertEqual(r["authority"],
                         {"selected": False, "ratified": False, "coordinate": None,
                          "physical_t5": False, "fpga_opcode": False})
        self.assertEqual(r["dedup"]["behavioral_proof"], "PENDING")
        self.assertEqual(r["dedup"]["core_status"], "HOLD-CORE-VS-DERIVED-LIBRARY")
        self.assertGreaterEqual(len(r["positive_witnesses"]), 2)
        self.assertGreaterEqual(len(r["falsifiers"]), 3)
        self.assertTrue(any(src["source_class"] == "PRIMARY-NORMATIVE-DONOR"
                            for src in d["source"]))
        self.assertTrue(any(src["source_class"] == "OWNER-DEVICE-MOTIVATION-NOT-EXECUTED-DONOR"
                            for src in d["source"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
