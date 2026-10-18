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

    def test_guard_reference_legacy_cond_is_explicitly_held(self):
        source = (ROOT / "knowledge/guard-reference.lisp").read_text()
        # The old three-field COND form needs a semantic migration before D3.
        self.assertIn("(00001001 *guard-reference-directory*", source)
        self.assertNotIn("(0011 *guard-reference-directory*", source)
        self.assertIn("(00000111", source)
        self.assertIn("reference", source)
        self.assertIn("language-policy", source)

    def test_machine_pair_layout_uses_ratified_ukr_and_preserves_original_record(self):
        source = (ROOT / "lib/machine/layout/pair-x86-64.lisp").read_text()
        d3 = (ROOT / "lib/domains/d3.lisp").read_text()
        d4 = (ROOT / "lib/domains/d4.lisp").read_text()

        self.assertRegex(d3, r"(?m)^\s*\(001\s+\(ук як-є\)\s+\(укр як-є\)")
        self.assertRegex(d4, r"(?m)^\s*\(0011\s+\(ук визначити\)\s+\(укр визначити\)")
        for expression in (
            "(визначити x86-pair-cell-bytes 16)",
            "(визначити x86-pair-car-offset 0)",
            "(визначити x86-pair-cdr-offset 8)",
            "(визначити x86-pair-layout",
            "(як-є\n",
            "(car (offset-bytes 0)",
            "(cdr (offset-bytes 8)",
            "(arena-argument-register rdi)",
            "(escape forbidden)",
        ):
            with self.subTest(expression=expression):
                self.assertIn(expression, source)
        self.assertEqual(source.count("(визначити "), 4)
        self.assertEqual(source.count("(як-є\n"), 1)
        self.assertNotRegex(source, r"\((?:0011|001|00001001)(?=\s|\))")

        # Undo only the five exact surface heads; data and machine layout
        # must reconstruct the original complete Git object byte-for-byte.
        restored = source.replace("(визначити ", "(0011 ").replace("(як-є\n", "(001\n")
        self.assertEqual(self._git_blob(restored), "ab039e48fc0bc44cd215f499897c76df35d2a9f2")

    @staticmethod
    def _git_blob(source):
        import hashlib
        raw = source.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes((0,)) + raw).hexdigest()

    def test_machine_pair_layout_wrong_peer_breaks_exact_inverse(self):
        source = (ROOT / "lib/machine/layout/pair-x86-64.lisp").read_text()
        wrong = source.replace(
            "(визначити x86-pair-car-offset 0)",
            "(функція x86-pair-car-offset 0)", 1,
        )
        self.assertNotEqual(wrong, source)
        restored_wrong = wrong.replace("(визначити ", "(0011 ").replace("(як-є\n", "(001\n")
        self.assertNotEqual(self._git_blob(restored_wrong), "ab039e48fc0bc44cd215f499897c76df35d2a9f2")

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
