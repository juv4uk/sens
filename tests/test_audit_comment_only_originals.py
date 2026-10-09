#!/usr/bin/env python3
"""Exact Git-source comment-only proof must never count executable migration."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_comment_only_originals.py"
spec = importlib.util.spec_from_file_location("comment_only_originals", SCRIPT)
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class CommentOnlyOriginalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="comment-only-original-")
        self.root = Path(self.temp.name)
        (self.root / "lib").mkdir()
        (self.root / "lib" / "comment.lisp").write_bytes(
            b"; selected profile marker\n\n  ; this (is not a form)\n"
        )
        (self.root / "lib" / "active.lisp").write_bytes(
            b"; a comment\n(001 ()) ; actual executable expression\n"
        )
        self.rows = [
            {
                "path": f"lib/{name}.lisp",
                "source_git_blob_sha": audit.git_blob_sha(
                    (self.root / "lib" / f"{name}.lisp").read_bytes()
                ),
                "source_scope": audit.UNCLASSIFIED,
                "status": "BLOCKED",
                "same_stem_sens_already_exists": False,
                "source_is_executable_proven": False,
                "independent_semantic_oracle_passed": False,
                "reason": "unproved active Lisp source",
            }
            for name in ("comment", "active")
        ]
        self.report = {
            "schema": audit.CANDIDATE_SCHEMA,
            "mode": "read-only canonical migrator dry-run",
            "source_era": "auto",
            "summary": {
                "physical_outputs_created": 0,
                "original_unpaired_executables_migrated_by_this_tool": 0,
                "scanned": 2,
                "original_unpaired_sources_scanned": 2,
                "blocked": 2,
                "mechanical_candidates": 0,
            },
            "blocked_sources": self.rows,
            "mechanical_candidates": [],
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_comment_only_source_does_not_become_executable_sens(self):
        out = audit.scan(self.root, self.report)
        self.assertEqual(out["summary"]["original_unpaired"], 2)
        self.assertEqual(out["summary"]["strict_comment_only_review_candidates"], 1)
        self.assertEqual(out["sources"][0]["path"], "lib/comment.lisp")
        self.assertFalse(out["sources"][0]["physical_sens_published"])
        self.assertFalse(out["sources"][0]["independent_semantic_oracle_passed"])
        self.assertEqual(out["sources"][0]["classification"],
                         "COMMENT_ONLY_REVIEW_PENDING")

    def test_lexically_active_and_tricky_comments_cannot_be_misclassified(self):
        for raw,expected in (
            (b"; leading comment\n  ; trailing comment", True),
            (b"", True),
            (b"\n \t\n", True),
            (b"(001 ())\n", False),
            (b" ;comment\n(111 ())", False),
            (b"#| block comments are NOT semicolon lines |#", False),
            (b'";not really a comment"', False),
            (b"\xef\xbb\xbf; BOM is not a conservative comment", False),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(audit.semantic_lines(raw)[0], expected)
        with self.assertRaises(audit.AuditError):
            audit.semantic_lines(b"\xff")

    def test_modified_git_blob_and_forged_path_fail_closed(self):
        row = self.report["blocked_sources"][0]
        row["source_git_blob_sha"] = "a" * 40
        with self.assertRaisesRegex(audit.AuditError, "Git blob drift"):
            audit.scan(self.root, self.report)
        row["source_git_blob_sha"] = audit.git_blob_sha(
            (self.root / "lib/comment.lisp").read_bytes())
        for bad in ("../outside.lisp", "/absolute.lisp", "lib//comment.lisp",
                    "lib/./comment.lisp", "lib\\comment.lisp", "lib/comment.txt"):
            with self.subTest(bad=bad):
                row["path"] = bad
                with self.assertRaises(audit.AuditError):
                    audit.scan(self.root, self.report)

    def test_existing_sens_and_symlink_rejected(self):
        (self.root / "lib/comment.sens").write_bytes(b"\x00")
        with self.assertRaisesRegex(audit.AuditError, "already paired"):
            audit.scan(self.root, self.report)
        (self.root / "lib/comment.sens").unlink()
        (self.root / "lib/comment.lisp").unlink()
        (self.root / "lib/comment.lisp").symlink_to("active.lisp")
        with self.assertRaisesRegex(audit.AuditError, "symlink"):
            audit.scan(self.root, self.report)

    def test_corrupt_or_incomplete_canonical_report_fails_closed(self):
        for mutate in (
            lambda r: r["summary"].__setitem__("scanned", 3),
            lambda r: r["summary"].__setitem__("physical_outputs_created", 1),
            lambda r: r.__setitem__("source_era", "legacy"),
            lambda r: r["blocked_sources"].append(dict(r["blocked_sources"][0])),
        ):
            state = json.loads(json.dumps(self.report))
            mutate(state)
            with self.assertRaises(audit.AuditError):
                audit.scan(self.root, state)

    def test_real_core2_profile_marker_is_comment_only_but_not_admitted(self):
        original = ROOT / "lib/core2.lisp"
        self.assertTrue(original.is_file())
        raw = original.read_bytes()
        self.assertEqual(audit.git_blob_sha(raw),
                         "9a39a1d341dde7faf3a1899b52f78a7b1e931783")
        self.assertTrue(audit.semantic_lines(raw)[0])
        self.assertFalse((ROOT / "lib/core2.sens").exists())


if __name__ == "__main__":
    unittest.main()
