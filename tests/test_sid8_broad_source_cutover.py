#!/usr/bin/env python3
"""Fail-closed regression for the seven-file in-place SID8 -> domain cutover.

This is a SOURCE law witness, not independent runtime or T5 admission.
Historic source literals in strings, comments and quoted data stay unchanged.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
COHORT = {
    "scripts/build-dependency-classification.lisp": 9,
    "scripts/check-core4-predicate-answer-scale.lisp": 9,
    "scripts/check-core4-predicate-answer-boundary.lisp": 0,
    "experiments/probabilistic-decision-jev-like.lisp": 1,
    "scripts/generate-function-table.lisp": 2,
    "scripts/generate-uk-surface-audit.lisp": 1,
    "scripts/verify-repo.lisp": 1,
}


def count_top_level_arguments(source: str, index: int) -> int:
    """Count complete Lisp forms after a map head, respecting nested lists/strings."""
    match = re.match(r"\(\s*101000(?=\s|\))", source[index:])
    if not match:
        raise ValueError("expected current D6 MAP head")
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
                raise ValueError("unclosed MAP argument")
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
    raise ValueError("unclosed D6 MAP call")


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

    def test_each_migrated_file_retains_the_exact_single_sequence_map_calls(self):
        total = 0
        for path, expected in COHORT.items():
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                matches = list(re.finditer(r"\(\s*101000(?=\s|\))", source))
                self.assertEqual(len(matches), expected)
                self.assertNotRegex(source, r"\(\s*00110111(?=\s|\))")
                for call in matches:
                    self.assertEqual(count_top_level_arguments(source, call.start()), 2)
                total += len(matches)
        self.assertEqual(total, 23)

    def test_no_old_definition_call_heads_in_executable_cohort(self):
        for path in COHORT:
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                # verify-repo intentionally embeds historical source *strings*
                # for compatibility audits. Never replace those literals.
                if path == "scripts/verify-repo.lisp":
                    self.assertIn('"(00001001 "', source)
                else:
                    self.assertNotRegex(source, r"\(\s*00001001(?=\s|\))")

if __name__ == "__main__":
    unittest.main()
