#!/usr/bin/env python3
"""Source-level regression for audited historical MAP -> current D6 cutover.

The historical 8-bit MAP has two same-named D6/D8 successors. These audited source sites each apply MAP to exactly one sequence, so their
concrete old MAP heads were resolved to the ratified D6 resident. No global SID8
correspondence or D8 identity is changed by this source-local proof.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
YANTRA = ROOT / "lib" / "yantra.lisp"
LINTER = ROOT / "lib" / "linter.lisp"
CORE = ROOT / "lib" / "core.lisp"
KNOWLEDGE = ROOT / "lib" / "knowledge.lisp"

class AuditedMapSourceCutover(unittest.TestCase):
    def test_authority_retains_distinct_d6_and_d8_map(self):
        x = json.loads((ROOT / "knowledge" / "d1-d9-foundation.json").read_text())
        self.assertEqual(x["domains"]["D6"]["residents"]["101000"], "MAP")
        self.assertEqual(x["domains"]["D8"]["residents"]["11000101"], "MAP")
        old = json.loads((ROOT / "knowledge" / "sens8-current-coverage-v1.json").read_text())
        entry = next(row for row in old["rows"] if row["legacy_code"] == "00110111")
        self.assertIn("D6:101000 MAP", entry["current_target"])
        self.assertIn("D8:11000101 MAP", entry["current_target"])

    def test_yantra_four_single_sequence_map_calls(self):
        source = YANTRA.read_text(encoding="utf-8")
        expected = (
            "(101000 json->tool-call tcs)",
            "(101000 encode-tool-call tcs)",
            "(101000 encode-message messages)",
            "(101000 tc-id (msg-tool-calls m))",
        )
        self.assertEqual(len(re.findall(r"\(101000(?=\s|\))", source)), 4)
        for expr in expected:
            with self.subTest(expr=expr):
                self.assertEqual(source.count(expr), 1)
        self.assertNotRegex(source, r"\(00110111(?=\s|\))")
        self.assertNotRegex(source, r"\(00001001(?=\s|\))")

    def test_knowledge_clause_mapping_is_single_sequence(self):
        source = KNOWLEDGE.read_text(encoding="utf-8")
        expected = "(101000 (00001000 (clause) (00100111 (00000001 tell) module-name clause)) clauses)"
        self.assertEqual(source.count(expected), 1)
        self.assertNotRegex(source, r"\(00110111(?=\s|\))")

    def test_core_let_expansion_maps_are_single_sequence(self):
        source = CORE.read_text(encoding="utf-8")
        expected = (
            "(101000 (00001000 (binding) (00000101 binding)) bindings)",
            "(101000 (00001000 (binding) (00101111 binding)) bindings)",
        )
        for expr in expected:
            with self.subTest(expr=expr):
                self.assertEqual(source.count(expr), 1)
        self.assertNotRegex(source, r"\(00110111(?=\s|\))")

    def test_linter_eight_single_sequence_maps_keep_old_macro_datum(self):
        source = LINTER.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"\(101000(?=\s|\))", source)), 8)
        self.assertNotRegex(source, r"\(00110111(?=\s|\))")
        self.assertNotRegex(source, r"\(00001001(?=\s|\))")
        # This literal is historical input data, *not* a call head:
        # changing it without a reader/AST migration would corrupt linting.
        self.assertIn("head 00001010", source)
        self.assertEqual(source.count("head 00001010"), 1)

if __name__ == "__main__":
    unittest.main()
