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
        for surface in ("визначити", "функція", "як-є", "за-умовою",
                        "атом?", "тотожне?", "перше", "решта"):
            self.assertRegex(source, r"[(]" + re.escape(surface) + r"(?=\s)")

    def test_d1_verdicts_are_executed_predicates_not_unbound_names(self):
        source = SOURCE.read_text(encoding="utf-8")
        executable = "\n".join(
            line.split(";", 1)[0] for line in source.splitlines()
        )
        self.assertIsNone(re.search(r"(?<![\w-])(?:так|ні)(?![\w-])", executable))
        self.assertIn("(атом? (як-є ()))", executable)
        self.assertIn("(атом? (сполучити (як-є ()) (як-є ())))", executable)
