#!/usr/bin/env python3
"""Fail-closed owner L1–L7 migration policy regressions."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/owner_l1_l7_gate.py"
spec = importlib.util.spec_from_file_location("owner_l1_l7_gate_tests", PATH)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)
FOUNDATION = gate.engine.load_foundation(ROOT / "knowledge/d1-d9-foundation.json")


def apply(source: str, *, era: str = "auto"):
    return gate.inspect(source, FOUNDATION, source_era=era)


def verdicts(findings):
    return [(f.law, f.verdict) for f in findings]


class OwnerLaws(unittest.TestCase):
    def test_l2_explicit_t_clause_only(self):
        src = "(110 (t (001 ())))"
        staged, found = apply(src)
        self.assertEqual(staged, "(110 (1 (001 ())))")
        self.assertIn(("L2", "STAGED"), verdicts(found))
        self.assertEqual(src, "(110 (t (001 ())))")  # no in-place mutation

    def test_l1_exact_predicate_accepts_form_without_truthiness(self):
        source = "(110 ((010 (001 ())) (001 ())))"
        staged, found = apply(source)
        self.assertEqual(staged, source)
        self.assertFalse(any(f.verdict == "BLOCK" for f in found))

    def test_l1_arbitrary_truthiness_blocked(self):
        _, found = apply("(110 ((001 000) (001 000)))")
        self.assertIn(("L1", "BLOCK"), verdicts(found))

    def test_l2_not_special_outside_cond(self):
        _, found = apply("(t (001 ()))")
        self.assertIn(("L3", "BLOCK"), verdicts(found))

    def test_l3_no_unratified_executable_name(self):
        _, found = apply("(unknown-function (001 ()))")
        self.assertIn(("L3", "BLOCK"), verdicts(found))
        self.assertIn("D10 proposal", found[0].reason)

    def test_l3_unproven_w8_blocks(self):
        _, found = apply("(11110111 (001 ()))")
        self.assertIn(("L3", "BLOCK"), verdicts(found))

    def test_l4_d8_equal_alias_is_pinned(self):
        staged, found = apply("(equal? (001 ()) (001 ()))")
        self.assertTrue(staged.startswith("(11110111 "))
        self.assertIn(("L4", "STAGED"), verdicts(found))
        self.assertNotIn(("L3", "BLOCK"), verdicts(found))

    def test_l4_null_exact_d4_resident(self):
        staged, found = apply("(null (001 ()))")
        self.assertTrue(staged.startswith("(0101 "))
        self.assertIn(("L4", "STAGED"), verdicts(found))

    def test_l4_requires_unique_resident(self):
        data = {"domains": {name: dict(FOUNDATION["domains"][name])
                            for name in ("D3", "D4", "D5", "D6", "D7", "D8", "D9")}}
        data["domains"]["D8"]["residents"] = {}
        _, found = gate.inspect("(equal? (001 ()))", data)
        self.assertIn(("L4", "BLOCK"), verdicts(found))

    def test_l5_retired_live_form_blocks(self):
        _, found = apply("(structural-kind (001 ()))")
        self.assertIn(("L5", "BLOCK"), verdicts(found))

    def test_l5_quoted_archaeology_is_data_not_execution(self):
        _, found = apply("'(structural-kind ())")
        self.assertEqual(found, [])

    def test_l6_old_three_part_cond_blocks(self):
        _, found = apply("(110 ((010 x) (1) (001 ())))")
        self.assertIn(("L6", "BLOCK"), verdicts(found))

    def test_l7_does_not_guess_missing_parenthesis(self):
        staged, found = apply("(110 ((010 x) (001 ()))")
        self.assertIsNone(staged)
        self.assertIn(("L7", "BLOCK"), verdicts(found))

    def test_sid8_cond_not_implicitly_current(self):
        _, found = apply("(00000111 (t (001 ())))", era="legacy")
        self.assertIn(("L1", "BLOCK"), verdicts(found))

    def test_fail_closed_cli_never_writes_on_parse_failure(self):
        with tempfile.TemporaryDirectory() as dirname:
            base = Path(dirname)
            src, out = base / "broken.lisp", base / "output.sens"
            original = b"(110 (t (001 ()))"
            src.write_bytes(original)
            cmd = [sys.executable, str(PATH), str(src), "--out", str(out)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
            self.assertEqual(src.read_bytes(), original)
            self.assertFalse(out.exists())


    def test_staged_t5_projection_requires_independent_oracle(self):
        with tempfile.TemporaryDirectory() as dirname:
            base = Path(dirname)
            src = base / "candidate.lisp"
            target = base / "forbidden.sens"
            src.write_text("(110 (t (001 ())))", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PATH), str(src), "--out", str(target)],
                capture_output=True, text=True, cwd=ROOT,
            )
            self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
            self.assertFalse(target.exists())
            self.assertEqual(src.read_text(encoding="utf-8"), "(110 (t (001 ())))")
            data = __import__("json").loads(result.stdout)
            self.assertIn(data["status"], {"BLOCK", "STAGED-REVIEW"})
            if "typed_word_sha256" in data:
                self.assertEqual(len(data["typed_word_sha256"]), 64)
                self.assertEqual(len(data["physical_sha256"]), 64)

    def test_complete_existing_emitter_projection_and_oracle_digests(self):
        with tempfile.TemporaryDirectory() as dirname:
            src = Path(dirname) / "source.lisp"
            src.write_text("(110 (t (001 ())))", encoding="utf-8")
            cmd = [sys.executable, str(PATH), str(src)]
            staged = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(staged.returncode, 4, staged.stdout + staged.stderr)
            data = __import__("json").loads(staged.stdout)
            self.assertEqual(data["status"], "STAGED-REVIEW", staged.stdout)
            self.assertTrue(data["exact_domain_projection"])
            self.assertEqual(len(data["typed_word_sha256"]), 64)
            self.assertEqual(len(data["physical_sha256"]), 64)
            pinned = subprocess.run(
                cmd + ["--oracle-typed-sha256", data["typed_word_sha256"],
                       "--oracle-physical-sha256", data["physical_sha256"]],
                capture_output=True, text=True, cwd=ROOT,
            )
            self.assertEqual(pinned.returncode, 0, pinned.stdout + pinned.stderr)
            self.assertEqual(
                __import__("json").loads(pinned.stdout)["status"],
                "STAGED-ORACLE-MATCH",
            )


    def test_digests_cannot_override_semantic_block(self):
        with tempfile.TemporaryDirectory() as dirname:
            src = Path(dirname) / "unknown.lisp"
            src.write_text("(ghost 1)", encoding="utf-8")
            args = [sys.executable, str(PATH), str(src),
                    "--oracle-typed-sha256", "0" * 64,
                    "--oracle-physical-sha256", "0" * 64]
            result = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
            self.assertIn('"law": "L3"', result.stdout)


if __name__ == "__main__":
    unittest.main()
