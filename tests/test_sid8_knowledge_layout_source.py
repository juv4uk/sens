"""Current-domain call-head witnesses for migrated knowledge and pair-layout Lisp.

Checks only source projections. Does not claim runtime parity.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class KnowledgeLayoutSourceTests(unittest.TestCase):
    def test_three_knowledge_modules_use_ratified_quote(self):
        for name in ("astronomy", "physics", "family"):
            with self.subTest(module=name):
                source = (ROOT / "knowledge" / (name + ".lisp")).read_text()
                self.assertRegex(source, r"\(defmodule\s+\S+\s+\(001\s+\(")
                self.assertNotRegex(source, r"\(00000001(?=\s|\))")

    def test_guard_reference_domain_definitions(self):
        source = (ROOT / "knowledge/guard-reference.lisp").read_text()
        self.assertIn("(0011 *guard-reference-directory*", source)
        self.assertNotIn("(00001001 *guard-reference-directory*", source)
        self.assertIn("reference", source)
        self.assertIn("language-policy", source)

    def test_machine_pair_layout_still_has_original_record(self):
        source = (ROOT / "lib/machine/layout/pair-x86-64.lisp").read_text()
        for expression in (
            "(0011 x86-pair-cell-bytes 16)",
            "(0011 x86-pair-car-offset 0)",
            "(0011 x86-pair-cdr-offset 8)",
            "(0011 x86-pair-layout",
            "(001",
            "(arena-argument-register rdi)",
            "(escape forbidden)",
        ):
            with self.subTest(expression=expression):
                self.assertIn(expression, source)
        self.assertNotRegex(source, r"\(00001001(?=\s|\))")

    def test_four_live_fixture_source_heads(self):
        expected = {
            "lisp-fs-conformance.lisp": ("(001000 ((empty", "(001 (hello world))"),
            "rivnopravnist-uk.lisp": ("(0011 подвоїти", "(01010 число число)", "(110"),
            "semantic-registry-self-hosted-witness.lisp": ("(0011 semantic-registry-self-hosted-witness", "(0010 (source)"),
            "semantic-coordinate-matrix-845.lisp": ("(0011 semantic-coordinate-matrix-845", "(001\n"),
        }
        for filename, needles in expected.items():
            with self.subTest(filename=filename):
                source = (ROOT / "tests" / "fixtures" / filename).read_text()
                for snippet in needles:
                    self.assertIn(snippet, source)
                self.assertNotRegex(source, r"\(00001001(?=\s|\))")
        # Binary-id data is still historical data, NOT an executable call head.
        registry = (ROOT / "tests/fixtures/semantic-registry-self-hosted-witness.lisp").read_text()
        self.assertIn("(semantic-registry-row-in registry 00000001)", registry)

if __name__ == "__main__":
    unittest.main()
