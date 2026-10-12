"""Domain-head classification in the active Lisp linter is exact-width.

This checks the ratified canonical tables, not a historical eight-bit alias.
The D5 MACRO operation is deliberately not equated to a compound defmacro form.
"""
import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/linter.lisp"
AUTHORITY = ROOT / "knowledge/d1-d9-foundation.json"
HEAD_EQUAL = re.compile(r"\(\(11110111 head ([01]+)\)\s+\(001 ([^\s()]+)\)\)")


def rules_for(section, following, source):
    block = source.split(f"(0011 {section}\n", 1)[1].split(
        f"(0011 {following}\n", 1
    )[0]
    matches = HEAD_EQUAL.findall(block)
    if len(matches) != len(set(matches)):
        raise AssertionError("duplicate source rules")
    return dict(matches)


class DomainLinterHeadCutover(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.domains = json.loads(AUTHORITY.read_text(encoding="utf-8"))["domains"]
        cls.short = rules_for("lint-short-head", "lint-head", cls.source)
        cls.long = rules_for("lint-head", "lint-max2", cls.source)

    def test_short_forms_use_only_current_d3(self):
        self.assertEqual(self.short, {"001": "quote", "110": "cond"})
        for bits, resident in (("001", "QUOTE"), ("110", "COND")):
            self.assertEqual(self.domains["D3"]["residents"][bits], resident)

    def test_full_head_uses_exact_domain_ladder(self):
        self.assertEqual(self.long, {
            "0011": "def",
            "0010": "lambda",
            "110": "cond",
            "001": "quote",
            "001000": "let",
            "001001": "let*",
        })
        expected = {
            ("D4", "0011"): "DEFINE",
            ("D4", "0010"): "LAMBDA",
            ("D3", "110"): "COND",
            ("D3", "001"): "QUOTE",
            ("D6", "001000"): "LET",
            ("D6", "001001"): "LET*",
        }
        for (domain, bits), resident in expected.items():
            with self.subTest(domain=domain, bits=bits):
                self.assertEqual(self.domains[domain]["width"], len(bits))
                self.assertEqual(self.domains[domain]["residents"][bits], resident)

    def test_no_flat_eight_bit_head_alias_or_ambiguous_macro(self):
        self.assertTrue(all(len(bits) != 8 for bits in (*self.short, *self.long)))
        self.assertNotIn("defmacro", self.long.values())
        self.assertEqual(self.domains["D8"]["residents"]["11110111"], "EQUAL")
        self.assertIn("(11110111 head 0011)", self.source)
        self.assertNotIn("(11110111 head 00001001)", self.source)


if __name__ == "__main__":
    unittest.main()
