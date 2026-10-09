#!/usr/bin/env python3
"""#4460: guard top-level Lisp fixture records against bogus executable T5 migration.

A quoted (expr . "...") is data inside a test record.  This classification
does not authorize translating the string's contents or lowering any semantics.
"""

import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "knowledge/migration-nonprogram-expr-records-2026-10-08.json"

EXPECTED_PATHS = frozenset(
    {
        "tests/fixtures/canon-laws-v2-witness.lisp",
        "tests/fixtures/canon-zero-v2.lisp",
        "tests/fixtures/conformance.lisp",
        "tests/fixtures/exact-q-binary-v1.lisp",
        "tests/fixtures/knowledge-clause-kind-v1.lisp",
        "tests/fixtures/linter.lisp",
        "tests/fixtures/macro-conformance.lisp",
        "tests/fixtures/mathematical-result-v1.lisp",
        "tests/fixtures/reason-honesty-v1.lisp",
        "tests/fixtures/reason-module-honesty-v1.lisp",
        "tests/fixtures/reason-observe-honesty-v1.lisp",
        "tests/fixtures/structure-core-v1.lisp",
        "tests/fixtures/unification-outcome-v1.lisp",
    }
)


def lex_lisp(source: str) -> list[str]:
    """A conservative lexical scanner, not an evaluator or domain mapper."""
    result = []
    i = 0
    while i < len(source):
        c = source[i]
        if c.isspace():
            i += 1
        elif c == ";":
            end = source.find("\n", i)
            i = len(source) if end < 0 else end + 1
        elif c in "()":
            result.append(c)
            i += 1
        elif c == '"':
            i += 1
            while i < len(source):
                if source[i] == "\\":
                    i += 2
                elif source[i] == '"':
                    i += 1
                    result.append("<STRING>")
                    break
                else:
                    i += 1
            else:
                raise ValueError("unterminated Lisp string")
        else:
            start = i
            while (
                i < len(source)
                and not source[i].isspace()
                and source[i] not in '();"'
            ):
                i += 1
            if i == start:
                raise ValueError("unhandled Lisp token")
            result.append(source[start:i])
    return result


def record_envelopes_only(source: str) -> tuple[bool, int]:
    """Each *top-level* form must start with an (expr . quoted-source) field."""
    try:
        tokens = lex_lisp(source)
    except ValueError:
        return False, 0
    if not tokens:
        return False, 0
    count = 0
    depth = 0
    current: list[str] = []
    for token in tokens:
        if depth == 0 and token != "(":
            return False, count
        current.append(token)
        if token == "(":
            depth += 1
        elif token == ")":
            depth -= 1
            if depth < 0:
                return False, count
            if depth == 0:
                # The string is a *record field*, never an executable head.
                if current[:6] != ["(", "(", "expr", ".", "<STRING>", ")"]:
                    return False, count
                count += 1
                current = []
    return (depth == 0 and count > 0), count


def git_blob_sha1(payload: bytes) -> str:
    header = b"blob " + str(len(payload)).encode("ascii") + b"\0"
    return hashlib.sha1(header + payload).hexdigest()


class MigrationNonProgramExprRecords(unittest.TestCase):
    def test_exact_path_set_and_no_automatic_sens(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "sens-migration-nonprogram-manifest/1")
        self.assertEqual(data["issue"], 4460)
        self.assertEqual(
            data["classification"],
            "lisp-fixture-record-envelope-not-executable-program",
        )
        self.assertIs(data["automatic_sens_companion"], False)
        self.assertEqual(data["embedded_expr_migration_status"], "separate-unproven")
        entries = data["entries"]
        self.assertEqual(len(entries), 13)
        self.assertEqual({row["path"] for row in entries}, EXPECTED_PATHS)
        for row in entries:
            rel = Path(row["path"])
            self.assertEqual(rel.parts[:2], ("tests", "fixtures"))
            self.assertEqual(rel.suffix, ".lisp")
            payload = (ROOT / rel).read_bytes()
            self.assertEqual(git_blob_sha1(payload), row["git_blob_sha1"], row["path"])
            valid, count = record_envelopes_only(payload.decode("utf-8"))
            self.assertTrue(valid, f"{row['path']}: top-level nonrecord form")
            self.assertGreater(count, 0, row["path"])
            self.assertFalse(
                (ROOT / rel.with_suffix(".sens")).exists(),
                f"{row['path']}: a record-wrapper must not gain automatic .sens",
            )

    def test_executable_and_mixed_sources_are_not_exempt(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        paths = {row["path"] for row in data["entries"]}
        for executable in (
            "lib/core.lisp",
            "lib/core1.lisp",
            "lib/machine/dispatch/native-first.lisp",
        ):
            self.assertNotIn(executable, paths)
            self.assertTrue((ROOT / executable).is_file())
        self.assertEqual(
            record_envelopes_only('((expr . "(quote ())") (expected . "()"))'),
            (True, 1),
        )
        for not_a_record in (
            "(111 (000))",
            '((expr . "(quote ())"))\n(111 000)',
            "((expr . (quote ())) (expected . nil))",
            '((expr . "(quote ())") (expected . "()")',
        ):
            self.assertFalse(record_envelopes_only(not_a_record)[0])


if __name__ == "__main__":
    unittest.main()
