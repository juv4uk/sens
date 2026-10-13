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
HEAD_EQUAL = re.compile(r"\(\(101 head ([01]+)\)\s+\(001 ([^\s()]+)\)\)")


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
        self.assertNotIn("(11110111 head ", self.source)
        self.assertIn("(101 head 0011)", self.source)
        self.assertNotIn("(11110111 head 00001001)", self.source)


    def test_non_atomic_heads_fail_closed_before_d3_eq(self):
        """D3 EQ rejects Pair arguments: both linter branches guard first."""
        for name, following, expected_comparisons in (
            ("lint-short-head", "lint-head", 2),
            ("lint-head", "lint-max2", 6),
        ):
            with self.subTest(name=name):
                block = self.source.split(f"(0011 {name}\n", 1)[1].split(
                    f"(0011 {following}\n", 1
                )[0]
                guard = "((0100 (010 head)) head)"
                self.assertIn(guard, block)
                self.assertLess(block.index(guard), block.index("(101 head "))
                self.assertEqual(block.count("(101 head "), expected_comparisons)
                self.assertEqual(block.count("(11110111 head "), 0)
        self.assertIn("(11110111 (lint-form-head ast)", self.source)

    def test_every_2046_exact_domain_word_is_classified_only_at_its_width(self):
        """Every possible D1..D10 coordinate is challenged, not executed.

        Residency of D10 (1024) or any other slot does NOT grant callable
        mechanism. This witness classifies candidate data heads only.
        """
        lookup = {
            ("D3", "001"): "quote", ("D3", "110"): "cond",
            ("D4", "0011"): "def", ("D4", "0010"): "lambda",
            ("D6", "001000"): "let", ("D6", "001001"): "let*",
        }
        short = {("D3", bits): name for bits, name in self.short.items()}
        full = {("D" + str(len(bits)), bits): name for bits, name in self.long.items()}
        self.assertEqual(full, lookup)
        self.assertEqual(short, {
            ("D3", "001"): "quote",
            ("D3", "110"): "cond",
        })
        count = 0
        matched_short = matched_full = 0
        for width in range(1, 11):
            for value in range(1 << width):
                candidate = (f"D{width}", format(value, f"0{width}b"))
                self.assertEqual(len(candidate[1]), width)
                self.assertEqual(int(candidate[1], 2), value)
                self.assertEqual(full.get(candidate), lookup.get(candidate))
                if candidate in full:
                    matched_full += 1
                if candidate in short:
                    matched_short += 1
                # Same numeric payload in another domain CANNOT be adopted.
                if width != 3 and value in (0b001, 0b110):
                    self.assertNotIn(candidate, short)
                count += 1
        self.assertEqual((count, matched_full, matched_short), (2046, 6, 2))

    def test_one_bit_head_mutation_never_keeps_the_same_linter_role(self):
        """Mutate every bit of each admitted head; aliases are forbidden."""
        lookup = {("D" + str(len(w)), w): role for w, role in self.long.items()}
        for (domain, word), role in lookup.items():
            for index in range(len(word)):
                flipped = word[:index] + ("1" if word[index] == "0" else "0") + word[index+1:]
                self.assertNotEqual(
                    lookup.get((domain, flipped)), role,
                    (domain, word, flipped, role)
                )

    def test_binary_head_budget_is_explicit_not_host_bytes(self):
        """Count source call-head codebits, not packed-file compression."""
        self.assertEqual(self.source.count("(101 head "), 8)
        self.assertEqual(self.source.count("((0100 (010 head)) head)"), 2)
        old_eight_bits = 8 * 8
        new_three_bits = 8 * 3
        gate_bits = 2 * (4 + 3)
        self.assertEqual(old_eight_bits - new_three_bits - gate_bits, 26)
        # Narrow change: D8 EQUAL remains where it compares nonatom data.
        self.assertEqual(self.source.count("(11110111 "), 11)


if __name__ == "__main__":
    unittest.main()
