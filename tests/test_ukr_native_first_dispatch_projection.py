#!/usr/bin/env python3
"""Перевірка D3/D4 проєкції native-first; виконання доводить окремий SENS-тест."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    ROOT / "lib/machine/dispatch/native-first.lisp",
    ROOT / "lib/machine/dispatch/native-first-execute.lisp",
)
D3 = ROOT / "lib/domains/d3.lisp"
D4 = ROOT / "lib/domains/d4.lisp"


def active_lisp(source: str) -> str:
    """Blank comments and strings before checking executable syntax."""
    output = []
    for line in source.splitlines():
        visible = []
        in_string = False
        escaped = False
        for char in line:
            if not in_string and char == ";":
                break
            if in_string:
                visible.append(" ")
                if escaped:
                    escaped = False
                elif char == "\\\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            elif char == '"':
                in_string = True
                visible.append(" ")
            else:
                visible.append(char)
        output.append("".join(visible))
    return "\\n".join(output)


class NativeFirstUkrProjection(unittest.TestCase):
    def test_d3_d4_names_match_the_ratified_ukr_column(self):
        for path, rows in (
            (D3, (
                ("001", "як-є"), ("010", "атом?"), ("011", "решта"),
                ("100", "перше"), ("101", "тотожне?"),
                ("110", "за-умовою"), ("111", "сполучити"),
            )),
            (D4, (("0010", "функція"), ("0011", "визначити"))),
        ):
            table = path.read_text(encoding="utf-8")
            for bits, name in rows:
                with self.subTest(domain=path.name, bits=bits, name=name):
                    self.assertRegex(
                        table,
                        rf"(?m)^\\s*\\({bits}\\s+\\(ук\\s+[^()]+\\)\\s+\\(укр\\s+{re.escape(name)}\\)",
                    )

    def test_active_native_first_sources_have_no_executable_bit_heads_or_tags(self):
        raw_head = re.compile(r"\\(\\s*(?:001|010|011|100|101|110|111|0001|0010|0011|0101)(?=\\s|\\))")
        forbidden_tag = re.compile(r"#(?:d\\d+:[01]+|b[01]+|q2)")
        for path in FILES:
            source = path.read_text(encoding="utf-8")
            code = active_lisp(source)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertIsNone(raw_head.search(code), "call heads must use current Ukrainian surfaces")
                self.assertIsNone(forbidden_tag.search(code), "no SID8/Sens8 or machine-width source tags")

    def test_execute_dispatch_keeps_native_and_evaluator_routes_distinct(self):
        source = FILES[1].read_text(encoding="utf-8")
        for required in (
            "(визначити нативне-виконати-план",
            "(як-є native-plan)",
            "(як-є evaluator-fallback)",
            "(читати-всі текст-джерела)",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)
        self.assertNotIn("#d1:", active_lisp(source))
        self.assertNotIn("#q2", active_lisp(source))

    def test_callable_head_mutation_is_detected(self):
        source = FILES[0].read_text(encoding="utf-8")
        mutated = source.replace("(визначити ", "(визначити-неправильно ", 1)
        self.assertNotEqual(source, mutated)
        self.assertNotEqual(active_lisp(source), active_lisp(mutated))


if __name__ == "__main__":
    unittest.main(verbosity=2)
