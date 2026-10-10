#!/usr/bin/env python3
"""Issue #5029: provable binary migration changes executable heads ONLY."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sens_legacy_head_migration", ROOT / "scripts/sens8-to-ladder.py"
)
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


class LegacyHeadMigrationSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = M.load_bridge(ROOT)

    def test_current_owner_bridge_is_real_not_empty_stale_rust_regex(self):
        # Old loader searched for a removed 0b(...) => Some(d3(...)) pattern.
        self.assertIn("00001001", self.bridge)
        self.assertIn("00000001", self.bridge)
        self.assertIn("00000101", self.bridge)
        self.assertNotEqual(self.bridge["00001001"], "00001001")
        self.assertEqual(self.bridge["00000001"], "001")

    def test_stages_real_executable_heads_never_quoted_data_or_comments(self):
        source = (
            "; data 00001001 must stay\n"
            "(00001001 name (00000001 (00000101 00001001)))\n"
            "\"(00001001 quoted string)\"\n"
            "'(00001001 quoted-form)\n"
            "#; (00001001 discarded-form)\n"
        )
        out, edits = M.stage(source, self.bridge)
        self.assertEqual(len(edits), 2)
        self.assertIn("; data 00001001 must stay", out)
        self.assertIn("(0011 name (001 (00000101 00001001)))", out)
        self.assertIn('" (00001001 quoted string)"'.replace('" ', '"'), out)
        self.assertIn("'(00001001 quoted-form)", out)
        self.assertIn("#; (00001001 discarded-form)", out)
        self.assertEqual(source.replace(
            "(00001001 name (00000001 (00000101 00001001)))",
            "(0011 name (001 (00000101 00001001)))"
        ), out)

    def test_lambda_formal_variables_and_define_names_are_data(self):
        source = "(00001000 (00000011 x) (00000101 x))\n"
        out, edits = M.stage(source, self.bridge)
        self.assertEqual(len(edits), 2)
        self.assertIn("(00000011 x)", out)
        self.assertEqual(out, "(0010 (00000011 x) (100 x))\n")

    def test_unmapped_head_and_legacy_cond_fail_closed(self):
        for source, reason in [
            ("(11111111 x)\n", "no proved successor"),
            ("(00000111 ((00000010 x) (1) x))\n", "historical COND"),
        ]:
            with self.subTest(source=source):
                with self.assertRaises(M.Blocked) as caught:
                    M.stage(source, self.bridge)
                self.assertIn(reason, str(caught.exception))

    def test_no_executable_legacy_head_cannot_claim_migration(self):
        with self.assertRaises(M.Blocked):
            M.stage("; 00001001\n'(00001001 data)\n", self.bridge)

    def test_cli_stage_then_exact_compare_and_detect_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = root / "original.lisp"
            original.write_text("(00001001 value (00000001 ()))\n", encoding="utf-8")
            out = root / "staged"
            cmd = [sys.executable, str(ROOT / "scripts/sens8-to-ladder.py")]
            def run(*args):
                return subprocess.run([*cmd, *map(str,args)],cwd=ROOT,
                                      capture_output=True, text=True)
            good = run(original, "--apply", "--out", out)
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
            result = out / "original.lisp"
            self.assertTrue(result.is_file())
            self.assertEqual(original.read_text(encoding="utf-8"),
                             "(00001001 value (00000001 ()))\n")
            checked = run("--verify-only", result, "--original", original)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertIn("NOT_VERIFIED", checked.stdout)
            result.write_text(result.read_text(encoding="utf-8")+" ", encoding="utf-8")
            mismatch = run("--verify-only", result, "--original", original)
            self.assertEqual(mismatch.returncode, 2)
            self.assertIn("BLOCK", mismatch.stderr)
            self.assertEqual(run(original, "--apply", "--out", out).returncode, 2)
            self.assertEqual(run("--verify-only", result).returncode, 2)

    def test_real_si_library_is_source_staging_not_physical_admission(self):
        original = (ROOT / "lib/si.lisp").read_text(encoding="utf-8")
        proposed, edits = M.stage(original, self.bridge)
        self.assertGreater(len(edits), 0)
        self.assertTrue(proposed.startswith("; lib/si.lisp"))
        self.assertNotEqual(original, proposed)
        self.assertIn("scientific-constant/1", proposed)
        self.assertEqual(proposed.count("9192631770"), 1)
        self.assertNotIn("physical_T5_PUBLISHED", proposed)


if __name__ == "__main__":
    unittest.main()
