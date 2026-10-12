#!/usr/bin/env python3
"""Regression witnesses for the bounded macro source domain migration."""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib" / "macro.lisp"
QUOTED_MARKER = "          ((00000111"
# Git blob SHA-1 of the entire unchanged quoted subtree, including whitespace
# and the exact end-of-file bytes, from the pre-migration source at
# b5b18ef9ba2430c1fc102c4ca08d2a33f62383f1.
QUOTED_SUBTREE_GIT_BLOB = "79d6b71e51581c810282b549ece53f2f4b051548"
LEGACY_EXECUTABLE_HEAD = re.compile(r"\(\s*(?:01001101|00000100|00000001)\b")


def split_outer_and_quoted_template(source: str) -> tuple[str, str]:
    if source.count(QUOTED_MARKER) != 1:
        raise AssertionError("expected exactly one quoted macro-template boundary")
    start = source.index(QUOTED_MARKER)
    return source[:start], source[start:]


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def executable_legacy_heads(outer: str) -> list[str]:
    without_comments = re.sub(r";[^\n]*", "", outer)
    return [match.group(0) for match in LEGACY_EXECUTABLE_HEAD.finditer(without_comments)]


class MacroDomainMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.outer, cls.quoted = split_outer_and_quoted_template(cls.source)

    def test_ratified_executable_heads_use_exact_d3_d4_coordinates(self) -> None:
        self.assertIn("(make-macro\n  (0001\n", self.outer)  # D4 EVAL
        self.assertIn("(111 (001 00001000)", self.outer)       # D3 CONS of quoted argument
        self.assertIn("(111 (001 args)", self.outer)            # D3 CONS of quoted argument
        self.assertIn("        (001\n", self.outer)             # D3 QUOTE for the template
        self.assertEqual(self.outer.count("(111 (001 00001000)"), 1)
        self.assertEqual(self.outer.count("(111 (001 args)"), 1)
        self.assertEqual(self.outer.count("        (001\n"), 1)
        self.assertEqual(executable_legacy_heads(self.outer), [])

    def test_quoted_template_is_identical_to_the_historical_git_blob(self) -> None:
        payload = self.quoted.encode("utf-8")
        self.assertEqual(git_blob_sha1(payload), QUOTED_SUBTREE_GIT_BLOB)
        # This is deliberately historical quoted data, not admitted current code.
        self.assertTrue(LEGACY_EXECUTABLE_HEAD.search(self.quoted))

    def test_negative_control_detects_a_legacy_executable_head(self) -> None:
        regressed = self.source.replace("(0001\n", "(01001101\n", 1)
        outer, quoted = split_outer_and_quoted_template(regressed)
        self.assertTrue(executable_legacy_heads(outer))
        # The negative control must not mistake quoted historical data for code.
        self.assertEqual(
            git_blob_sha1(quoted.encode("utf-8")), QUOTED_SUBTREE_GIT_BLOB
        )

    def test_mutating_quoted_data_breaks_its_preservation_witness(self) -> None:
        tampered = self.quoted.replace("((00000010 args)", "((00000011 args)", 1)
        self.assertNotEqual(
            git_blob_sha1(tampered.encode("utf-8")), QUOTED_SUBTREE_GIT_BLOB
        )


if __name__ == "__main__":
    unittest.main()
