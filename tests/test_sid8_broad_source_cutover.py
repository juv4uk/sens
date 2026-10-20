#!/usr/bin/env python3
"""Перевірка українських викличних голів після міграції SID8.

Це лише перевірка поверхні джерел, не доказ виконання SENS чи T5M.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
COHORT = (
    "scripts/build-dependency-classification.lisp",
    "scripts/check-core4-predicate-answer-scale.lisp",
    "scripts/check-core4-predicate-answer-boundary.lisp",
    "experiments/probabilistic-decision-jev-like.lisp",
    "scripts/generate-function-table.lisp",
    "scripts/generate-uk-surface-audit.lisp",
    "scripts/verify-repo.lisp",
)


def count_top_level_arguments(source: str, index: int) -> int:
    """Підрахувати аргументи українського виклику з урахуванням вкладеності."""
    match = re.match(r"\(\s*відобразити(?=\s|\))", source[index:])
    if not match:
        raise ValueError("очікується українська голова відобразити (D6 MAP)")
    i = index + match.end()
    count = 0
    while i < len(source):
        while i < len(source) and source[i].isspace():
            i += 1
        if source[i] == ")":
            return count
        if source[i] == "(":
            depth = 0
            quoted = False
            while i < len(source):
                char = source[i]
                if char == '"':
                    backslashes = 0
                    j = i - 1
                    while j >= 0 and source[j] == "\\":
                        backslashes += 1
                        j -= 1
                    if backslashes % 2 == 0:
                        quoted = not quoted
                if not quoted:
                    if char == "(":
                        depth += 1
                    elif char == ")":
                        depth -= 1
                        if depth == 0:
                            i += 1
                            break
                i += 1
            if depth != 0:
                raise ValueError("незакритий аргумент відобразити")
        elif source[i] == '"':
            i += 1
            while i < len(source):
                if source[i] == "\\":
                    i += 2
                elif source[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
        else:
            while i < len(source) and not source[i].isspace() and source[i] != ")":
                i += 1
        count += 1
    raise ValueError("незакритий виклик відобразити")


class TestBroaderSid8LispCutover(unittest.TestCase):
    def test_current_map_residents_have_separate_ratifed_domain_authority(self):
        # D6 and D8 are separately ratified current domains. Historical
        # сід8 MAP source cells cannot act as D8's earlier authority.
        foundation = json.loads((ROOT / "knowledge/d1-d9-foundation.json").read_text())
        current_d8 = json.loads((ROOT / "knowledge/d8-ratified.json").read_text())
        self.assertEqual(foundation["domains"]["D6"]["residents"]["101000"], "MAP")
        self.assertEqual(current_d8["status"], "owner-ratified")
        self.assertEqual(current_d8["authority"], "#3960")
        self.assertEqual(current_d8["date"], "2026-10-06")
        self.assertEqual(current_d8["width"], 8)
        self.assertEqual(current_d8["occupancy"], 256)
        self.assertEqual(current_d8["residents"]["11000101"], "MAP")
        self.assertEqual(
            foundation["domains"]["D8"]["residents"]["11000101"],
            current_d8["residents"]["11000101"],
        )

    def test_current_ukr_map_heads_keep_two_arguments(self):
        # Не заморожуємо історичні кількості викликів: перевіряємо чинну форму.
        total = 0
        for path in COHORT:
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                self.assertNotRegex(source, r"\(\s*(?:101000|00110111)(?=\s|\))")
                matches = list(re.finditer(r"\(\s*відобразити(?=\s|\))", source))
                for call in matches:
                    self.assertEqual(count_top_level_arguments(source, call.start()), 2)
                total += len(matches)
        self.assertGreater(total, 0)

    def test_no_old_definition_call_heads_in_executable_cohort(self):
        for path in COHORT:
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                self.assertNotRegex(source, r"\(\s*00001001(?=\s|\))")

if __name__ == "__main__":
    unittest.main()
