#!/usr/bin/env python3
"""Fail-closed static guard for owner-directed common mathematics (#2490/#3021).

This guards semantic *scope*, not execution parity. Cross-kernel runtime
conformance still needs independent per-substrate oracle/CI witnesses.
"""

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "language-contract.lisp"
PROFILES = ROOT / "contracts/core-profile-contract.lisp"
LADDER = ROOT / "knowledge/number-width-ratified.json"

def law_body(source, name):
    pattern = r"\(" + re.escape(name) + r'\s*\.\s*"((?:[^"\\]|\\.)*)"\)'
    matches = re.findall(pattern, source)
    if len(matches) != 1:
        raise ValueError(f"{name}: expected exactly one law, got {len(matches)}")
    return matches[0]

class SharedMathematicsScope(unittest.TestCase):
    def test_single_language_math_scope_across_all_kernels(self):
        text = CONTRACT.read_text(encoding="utf-8")
        body = law_body(text, "mathematics-all-kernels")
        for token in ("Core1", "Core2", "Core3", "Core4", "Core-Math",
                      "CPU", "GPU", "FPGA", "unsupported"):
            self.assertIn(token, body)
        self.assertIn("not monopolize", body)
        self.assertIn("may never redefine", body)
        self.assertIn("math-parity-proof", text)
        self.assertIn("number-ladder-all-kernels", text)

    def test_all_profiles_consume_same_law(self):
        text = PROFILES.read_text(encoding="utf-8")
        self.assertIn("(mathematics-shared-across-all-profiles . required)", text)
        self.assertIn("(kernel-may-redefine-number-or-arithmetic . forbidden)", text)
        self.assertIn("(unsupported-mathematical-operation . explicit-failure-not-new-semantics)", text)

    def test_number_ladder_is_not_function_domain_or_text7(self):
        ladder = json.loads(LADDER.read_text(encoding="utf-8"))
        self.assertEqual(ladder["status"], "owner-ratified")
        self.assertEqual(ladder["semantic_space"], "Number")
        self.assertEqual(ladder["ratified_prefix_bits"], [24, 48, 96, 192])
        self.assertEqual(ladder["growth_law"], "width(n) = 24 * 2^n")
        self.assertIn("D1-D8", ladder["separate_from"])
        self.assertIn("Text7", ladder["separate_from"])
        self.assertIn("signedness", ladder["not_yet_ratified"])
        self.assertIn("integer versus rational field layout", ladder["not_yet_ratified"])
        self.assertIn("overflow versus automatic widening semantics", ladder["not_yet_ratified"])
        self.assertIn("decimal literal lowering law", ladder["not_yet_ratified"])
        number_law = law_body(CONTRACT.read_text(encoding="utf-8"), "number-ladder-all-kernels")
        self.assertIn("24/48/96/192", number_law)

    def test_guard_rejects_removed_or_duplicate_law(self):
        sample = '(mathematics-all-kernels . "Core1 and Core2")'
        self.assertEqual(law_body(sample, "mathematics-all-kernels"), "Core1 and Core2")
        with self.assertRaisesRegex(ValueError, "exactly one law"):
            law_body(sample + sample, "mathematics-all-kernels")
        with self.assertRaisesRegex(ValueError, "exactly one law"):
            law_body(sample, "number-ladder-all-kernels")

if __name__ == "__main__":
    unittest.main()
