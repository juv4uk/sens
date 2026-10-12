#!/usr/bin/env python3
"""Prove one in-place Lisp cutover; preserve independent pinned SID8 S0 oracle."""
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

MIGRATED = ("tests/fixtures/machine-replaceability-witness.lisp",
            "90d9066779db127e3b34eb285fc138da5a87e4a7", 16)
PINNED_S0 = ("tests/fixtures/post-d4-evalquote-witness.lisp",
             "ed0a87df18e1f5bde0997b642f406113c16bb6d0")

def git_blob(sha):
    return subprocess.run(["git", "cat-file", "blob", sha], cwd=ROOT,
                          capture_output=True, check=True).stdout.decode("utf-8")

class SID8WitnessSourceCutover(unittest.TestCase):
    def test_machine_rewrite_exact_old_to_ratified_heads(self):
        mapping, blocked = module.authority(ROOT)
        path, original_sha, expected = MIGRATED
        historic = git_blob(original_sha)
        updated = (ROOT / path).read_text(encoding="utf-8")
        rewritten, count, issues = module.rewrite(historic, mapping, blocked)
        self.assertEqual(issues, [])
        self.assertEqual(count, expected)
        self.assertEqual(rewritten, updated)

    def test_pinned_s0_witness_is_untouched_historical_code(self):
        path, original_sha = PINNED_S0
        historic = git_blob(original_sha)
        actual = (ROOT / path).read_text(encoding="utf-8")
        self.assertEqual(actual, historic,
                         "S0 oracle is pinned to SID8; domain rewrite requires new oracle")
        self.assertIn("(00000001 (00001000 (X Y) (00000100 X Y)))", actual)
        self.assertIn("(00000001 00000100)", actual)
        self.assertIn("(00000001 00000101)", actual)

    def test_machine_executable_heads_are_current(self):
        path = MIGRATED[0]
        source = (ROOT / path).read_text(encoding="utf-8")
        heads = module.executable_call_heads(source, module.guard_module(ROOT))
        for old in ("00001001", "00001000", "00000100", "00000101",
                    "00000111", "00000011"):
            self.assertNotIn(old, heads)

if __name__ == "__main__":
    unittest.main()
