#!/usr/bin/env python3
"""Independent source-form evidence for the migrated SID8 policy and small-program cohort.

This is a source-level guard only; it does not claim T5 file admission or
runtime parity. It refuses historical call heads and malformed exact D3 logic.
"""
import importlib.util
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_d3_legacy_logic.py"
SPEC = importlib.util.spec_from_file_location("sid8_policy_d3_guard", SCRIPT)
assert SPEC and SPEC.loader
GUARD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GUARD
SPEC.loader.exec_module(GUARD)

POLICIES = (
    "knowledge/foreign-tools-census.lisp",
    "knowledge/language-policy.lisp",
    "knowledge/swarm-legacy-deprecation.lisp",
    "knowledge/swarm-no-live-callers-audit.lisp",
    "knowledge/file-authority-policy.lisp",
)
EXECUTABLE = (
    "knowledge/guard-runtime-policy.lisp",
    "lib/machine/lowering/semantic-effects.lisp",
    "examples/ukrainian-greeting.lisp",
)
LEGACY_HEAD = re.compile(r"\(\s*(00001001|00001000|00000001|00000010|00000011|00000111)(?=\s|\))")


class AuditedPolicySourceCutover(unittest.TestCase):
    def test_five_policy_declarations_are_current_exact_domains(self):
        for relative in POLICIES:
            with self.subTest(path=relative):
                source = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIsNone(LEGACY_HEAD.search(source))
                self.assertEqual(len(re.findall(r"\(0011(?=\s|\))", source)), 1)
                self.assertEqual(len(re.findall(r"\(001(?=\s|\))", source)), 1)
                self.assertEqual(GUARD.scan_lisp(source, relative), [])

    def test_small_executable_modules_have_no_old_d3_or_host_truth(self):
        for relative in EXECUTABLE:
            with self.subTest(path=relative):
                source = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIsNone(LEGACY_HEAD.search(source))
                self.assertEqual(GUARD.scan_lisp(source, relative), [])

    def test_negative_obsolete_form_and_host_truth_witnesses(self):
        source = (ROOT / "knowledge/guard-runtime-policy.lisp").read_text(encoding="utf-8")
        old = source.replace("(110", "(00000111", 1)
        self.assertEqual(
            [f.rule for f in GUARD.scan_lisp(old, "knowledge/guard-runtime-policy.lisp")
             if f.rule == "LEGACY_W8_CALL"], ["LEGACY_W8_CALL"])
        old_t = source.replace("(1 (guard-unknown subject", "(t (guard-unknown subject", 1)
        self.assertIn("COND_HOST_TRUTH",
                      [f.rule for f in GUARD.scan_lisp(old_t, "knowledge/guard-runtime-policy.lisp")])


if __name__ == "__main__":
    unittest.main()
