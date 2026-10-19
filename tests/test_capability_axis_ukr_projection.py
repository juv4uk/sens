"""Regression for the current exact-domain machine capability projection.

Active source must use ratified Ukrainian D3/D4 call heads and D1 YES as the
surface value `так`. Historical SID8 spellings remain in Git history only;
actual lookup/evaluation behavior is covered by crates/sens/tests/machine_capability_axis.rs.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/machine/capability-axis.lisp"
D3 = ROOT / "lib/domains/d3.lisp"
D4 = ROOT / "lib/domains/d4.lisp"

HEADS = {
    "0011": "визначити",
    "0010": "функція",
    "001": "як-є",
    "110": "за-умовою",
    "010": "атом?",
    "101": "тотожне?",
    "100": "перше",
    "011": "решта",
}
RAW_PATTERN = re.compile(
    r"[(](" + "|".join(HEADS.keys()) + r")(?=\s)"
)


def assert_exact_projection(testcase, table_path, bits, surface, english, lisp):
    table = table_path.read_text(encoding="utf-8")
    rows = [
        line for line in table.splitlines()
        if re.match(rf"^\s*[(]{re.escape(bits)}\s", line)
    ]
    testcase.assertEqual(len(rows), 1, f"{bits}: expected one exact-width row")
    testcase.assertIn(f"(укр {surface})", rows[0])
    testcase.assertIn(f"(en {english})", rows[0])
    testcase.assertIn(f"(LISP {lisp})", rows[0])


class CapabilityAxisUkrProjectionTests(unittest.TestCase):
    def test_full_ukr_operator_heads_match_ratified_domain_rows(self):
        for bits, surface, english, lisp in (
            ("001", "як-є", "quote", "QUOTE"),
            ("010", "атом?", "atom?", "ATOM"),
            ("011", "решта", "cdr", "CDR"),
            ("100", "перше", "car", "CAR"),
            ("101", "тотожне?", "eq?", "EQ"),
            ("110", "за-умовою", "cond", "COND"),
        ):
            assert_exact_projection(self, D3, bits, surface, english, lisp)
        for bits, surface, english, lisp in (
            ("0010", "функція", "lambda", "LAMBDA"),
            ("0011", "визначити", "define", "DEFINE"),
        ):
            assert_exact_projection(self, D4, bits, surface, english, lisp)

    def test_active_source_contains_only_exact_names_and_numeric_data(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIsNone(RAW_PATTERN.search(source),
                          "raw D3/D4 coordinates may not be executable heads")
        for forbidden in ("#d1:", "#d24:", "#b", "#q2", "machine-capability-legacy-sid-axis",
                          "machine-capabilities-for-sid", "x86-legacy-sid"):
            self.assertNotIn(forbidden, source, f"legacy token remains: {forbidden}")
        # Цінність цього guard — точна проєкція, а не фіксована кількість
        # викликів після ручного переписування самого алгоритму.
        for head in ("визначити", "функція", "як-є", "за-умовою",
                     "атом?", "тотожне?", "перше", "решта", "так"):
            pattern = re.compile(r"[(]" + re.escape(head) + r"(?=\s)")
            self.assertRegex(source, pattern, f"не знайдено ратифіковану голову: {head}")

        for declaration in (
            "(визначити можливість-знайти-рядок-домену",
            "(визначити спроможності-для-домену",
            "(визначити можливість-знайти-рядок",
            "(визначити статус-свідка-цілі-машини",
        ):
            self.assertIn(declaration, source)

        # D3 EQ — лише для атомів; непорожній список не можна порівнювати
        # з порожнім через EQ. Цю помилку вже перевіряє живий Rust/SENS тест.
        for list_name in ("рядки-доменів", "рядки-можливостей", "знайдений-рядок"):
            self.assertIn(f"(атом? {list_name})", source)
            self.assertNotIn(f"(тотожне? {list_name} (як-є ()))", source)

        for evidence in ("(5 10", "(3 4", "(x86-64 witnessed)", "(arm64 absent)"):
            self.assertIn(evidence, source)
        self.assertNotIn("(ні", source)

    def test_negative_surface_mutant_is_not_accepted_as_ratified_projection(self):
        source = SOURCE.read_text(encoding="utf-8")
        mutated = source.replace("(так", "(ні", 1)
        self.assertNotEqual(mutated, source)
        self.assertIn("(ні", mutated)
        self.assertNotIn("(ні", source)
