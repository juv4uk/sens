#!/usr/bin/env python3
"""Fail-closed static guard for owner-directed common mathematics (#2490/#3021).

This guards semantic *scope*, not execution parity. Cross-kernel runtime
conformance still needs independent per-substrate oracle/CI witnesses.
"""

from pathlib import Path
import re
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from domain_tables import number_domains  # noqa: E402
CONTRACT = ROOT / "language-contract.lisp"
PROFILES = ROOT / "contracts/core-profile-contract.lisp"
LADDER = ROOT / "contracts/numeric-domains-ratification.lisp"

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
        self.assertEqual(
            number_domains(LADDER),
            (("D12", 12), ("D24", 24), ("D48", 48), ("D96", 96), ("D192", 192)),
        )
        contract = LADDER.read_text(encoding="utf-8")
        self.assertIn("(schema . numeric-d12-start-extension-1)", contract)
        self.assertIn("(identity-law .", contract)
        self.assertIn("D7 text", contract)
        language = CONTRACT.read_text(encoding="utf-8")
        number_law = law_body(language, "number-ladder-all-kernels")
        self.assertIn("D12", number_law)
        self.assertIn("D24", number_law)
        self.assertIn("D(12 * 2^n)", number_law)

    def test_guard_rejects_removed_or_duplicate_law(self):
        sample = '(mathematics-all-kernels . "Core1 and Core2")'
        self.assertEqual(law_body(sample, "mathematics-all-kernels"), "Core1 and Core2")
        with self.assertRaisesRegex(ValueError, "exactly one law"):
            law_body(sample + sample, "mathematics-all-kernels")
        with self.assertRaisesRegex(ValueError, "exactly one law"):
            law_body(sample, "number-ladder-all-kernels")

if __name__ == "__main__":
    unittest.main()
