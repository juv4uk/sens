#!/usr/bin/env python3
"""Exact proof of two historical SID8 call-head source changes, never .sens."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-sid8-source-batch.py"
spec = importlib.util.spec_from_file_location("sid8_fixture_source", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

SOURCES = (
    ("tests/fixtures/machine-replaceability-witness.lisp",
     "90d9066779db127e3b34eb285fc138da5a87e4a7", 16),
    ("tests/fixtures/post-d4-evalquote-witness.lisp",
     "ed0a87df18e1f5bde0997b642f406113c16bb6d0", 14),
)

class SID8TwoWitnessSourceCutover(unittest.TestCase):
    def test_original_sources_rewrite_only_executable_call_heads(self):
        mapping, blocked = module.authority(ROOT)
        for path, old_sha, expected in SOURCES:
            with self.subTest(path=path):
                before = subprocess.run(
                    ["git", "cat-file", "blob", old_sha],
                    cwd=ROOT, capture_output=True, check=True
                ).stdout.decode("utf-8")
                after = (ROOT / path).read_text(encoding="utf-8")
                rewritten, count, issues = module.rewrite(before, mapping, blocked)
                self.assertEqual(issues, [])
                self.assertEqual(count, expected)
                self.assertEqual(rewritten, after,
                                 "only admitted Lisp heads may change")

    def test_quoted_lambda_and_bare_identity_are_preserved(self):
        text = (ROOT / SOURCES[1][0]).read_text(encoding="utf-8")
        self.assertIn("(001 (00001000 (X Y) (00000100 X Y)))", text)
        self.assertIn("(001 00000100)", text)
        self.assertIn("(001 00000101)", text)

    def test_both_fixtures_have_no_retired_exec_heads(self):
        for path, _, _ in SOURCES:
            with self.subTest(path=path):
                s = (ROOT / path).read_text(encoding="utf-8")
                # Never mistake old data beneath QUOTE for executable heads.
                active = module.executable_call_heads(s, module.guard_module(ROOT))
                for old in ("00001001", "00001000", "00000100",
                            "00000101", "00000111", "00000011"):
                    self.assertNotIn(old, active)

if __name__ == "__main__":
    unittest.main()
