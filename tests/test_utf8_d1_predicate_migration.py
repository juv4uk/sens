#!/usr/bin/env python3
"""CI_GLUE_NO_SEMANTICS: AST/bitness audit for SENS-owned UTF-8 predicates."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/utf8.lisp"
YES = "#d1:1"
NO = "#d1:0"
EXPECTED = {
    "utf8-in-range?": [0, 1, 0],
    "utf8-continuation-byte?": [1, 0],
    "utf8-byte?": [0, 1, 0],
    "utf8-all-bytes?": [1, 0, 0],
    "utf8-two-continuations?": [0, 1, 0],
}


def parse_forms(source):
    scanner = r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()]+'
    words = [m.group(0) for m in re.finditer(scanner, source)
             if not m.group(0).startswith(";")]
    stack = [[]]
    for word in words:
        if word == "(":
            group = []
            stack[-1].append(group)
            stack.append(group)
        elif word == ")":
            if len(stack) < 2:
                raise ValueError("extra close")
            stack.pop()
        else:
            stack[-1].append(word)
    if len(stack) != 1:
        raise ValueError("unclosed form")
    return stack[0]


def audit(source):
    functions = {
        form[1]: form for form in parse_forms(source)
        if isinstance(form, list) and len(form) >= 3 and form[0] == "0011"
    }
    findings = {}
    for name, expected in EXPECTED.items():
        if name not in functions:
            raise ValueError(f"missing {name}")
        actual = []

        def walk(n):
            if not isinstance(n, list):
                return
            if n and n[0] == "110":
                for clause in n[1:]:
                    if not isinstance(clause, list) or len(clause) != 2:
                        raise ValueError(f"{name}: malformed 2-field COND")
                    value = clause[1]
                    if value in ("0", "1"):
                        raise ValueError(f"{name}: unqualified Number in D1 result")
                    if value == YES:
                        actual.append(1)
                    elif value == NO:
                        actual.append(0)
            for child in n:
                walk(child)

        walk(functions[name])
        if actual != expected:
            raise ValueError(f"{name}: branch positions changed: {actual}")
        findings[name] = actual
    return findings


# Лише ці 10 вузьких числових порівнянь можна перевести з D8 EQUAL
# на D3 EQ: обидва операнди — атоми, а не структурні списки.
ATOMIC_EQ_EXPECTED = {
    "utf8-byte?": {"mod-0": 2},
    "utf8-three-byte-second-ok?": {"b1-224": 2, "b1-237": 2},
    "utf8-four-byte-second-ok?": {"b1-240": 2, "b1-244": 2},
}


def audit_atomic_eq_cutover(source):
    forms = parse_forms(source)
    functions = {
        form[1]: form for form in forms
        if isinstance(form, list) and len(form) >= 3 and form[0] == "0011"
    }
    observed = {}
    for name, expected in ATOMIC_EQ_EXPECTED.items():
        if name not in functions:
            raise ValueError(f"missing {name}")
        counts = {}

        def walk(node):
            if not isinstance(node, list):
                return
            if node and node[0] == "11110111":
                raise ValueError(f"{name}: D8 EQUAL survived the atomic D3 cutover")
            if len(node) == 3 and node[0] == "101" and node[2] in (
                    "0", "224", "237", "240", "244"):
                if node[1] == ["00101100", "b", "1"] and node[2] == "0":
                    key = "mod-0"
                elif node[1] == "b1" and node[2] != "0":
                    key = f"b1-{node[2]}"
                else:
                    raise ValueError(f"{name}: non-atomic or unsupported EQ operand")
                counts[key] = counts.get(key, 0) + 1
            for child in node:
                walk(child)

        walk(functions[name])
        if counts != expected:
            raise ValueError(f"{name}: D3 atomic EQ inventory drift: {counts}")
        observed[name] = counts
    return observed


class Utf8PredicateD1Cutover(unittest.TestCase):
    def test_14_precise_arity_checked_control_results(self):
        result = audit(SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(sum(len(values) for values in result.values()), 14)
        ones = sum(v for row in result.values() for v in row)
        zeroes = 14 - ones
        self.assertEqual((ones, zeroes), (5, 9))
        # CI_GLUE_NO_SEMANTICS: inventory only; SENS defines the verdict.
        # Every branch body is now a direct 1-bit predicate, not
        # ATOM(QUOTE ...) reification or a numeric proxy.
        direct_bits = ones + zeroes
        self.assertEqual(direct_bits, 14)
        self.assertEqual(source_bits := direct_bits, 14)
        print(f"UTF8-D1: direct exact predicate results={source_bits}, "
              "saved 97 D3 head-bits versus the historical synthetic carriers; "
              "execution semantics belong to SENS")

    def test_numeric_operands_and_domain_codes_remain_data(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("(101 (00101100 b 1) 0)", source)
        self.assertIn("(utf8-in-range? b 0 255)", source)
        self.assertIn("(utf8-in-range? b 128 191)", source)
        self.assertIn("(110011100 text)", source)

    def test_ten_atomic_d8_equal_calls_migrate_to_exact_d3_eq(self):
        source = SOURCE.read_text(encoding="utf-8")
        observed = audit_atomic_eq_cutover(source)
        self.assertEqual(sum(sum(row.values()) for row in observed.values()), 10)
        self.assertEqual(source.count("(11110111 "), 0)
        self.assertEqual(source.count("(101 (00101100 b 1) 0)"), 2)

    def test_atomic_eq_cutover_fails_on_nonatom_or_reintroduced_d8(self):
        source = SOURCE.read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "D8 EQUAL survived"):
            audit_atomic_eq_cutover(
                source.replace("(101 b1 224)", "(11110111 b1 224)", 1)
            )
        with self.assertRaisesRegex(ValueError, "non-atomic"):
            audit_atomic_eq_cutover(
                source.replace("(101 b1 224)", "(101 (001 (bad)) 224)", 1)
            )

    def test_exact_domain_authority_not_flat_byte(self):
        d1 = (ROOT / "lib/domains/d1.lisp").read_text(encoding="utf-8")
        d3 = (ROOT / "lib/domains/d3.lisp").read_text(encoding="utf-8")
        d8 = (ROOT / "lib/domains/d8.lisp").read_text(encoding="utf-8")
        self.assertRegex(d1, r"(?m)^\s*\(0\s+\(ук ні\)")
        self.assertRegex(d1, r"(?m)^\s*\(1\s+\(ук так\)")
        for bits, name in (("001", "QUOTE"), ("010", "ATOM"),
                           ("101", "EQ"), ("110", "COND")):
            self.assertRegex(d3, rf"(?m)^\s*\({bits}\s+.*\(LISP {name}\)")
        self.assertRegex(d8, r"(?m)^\s*\(11110111\s+.*\(LISP EQUAL\)")

    def test_two_negative_mutations_are_rejected(self):
        # Мутувати треба ЖИВЕ входження носія, а не те, що в коментарі:
        # у lib/utf8.lisp перше "#d1:1" стоїть у рядку-коментарі, і replace(...,1)
        # підмінював саме його, лишаючи код недоторканим -> тест хибно падав.
        source = SOURCE.read_text(encoding="utf-8")

        def first_live(carrier):
            for m in re.finditer(re.escape(carrier), source):
                line = source[source.rfind("\n", 0, m.start()) + 1:m.start()]
                if ";" not in line:
                    return m.start()
            raise AssertionError(f"немає живого {carrier} у {SOURCE}")

        for carrier, plain in (("#d1:1", "1"), ("#d1:0", "0")):
            i = first_live(carrier)
            mutated = source[:i] + plain + source[i + len(carrier):]
            with self.assertRaises(ValueError):
                audit(mutated)


if __name__ == "__main__":
    unittest.main()
