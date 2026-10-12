#!/usr/bin/env python3
"""Ratchet for already-observed three-field COND migration debt.

This guard DOES NOT rewrite clauses, infer D1 polarity, or grant callability.
It reuses the repository's AST-aware, quote/comment-aware migration inventory.
Current machine-host legacy debt may shrink; it may never silently grow.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "cond-modernize.py"
spec = importlib.util.spec_from_file_location("cond_stability_inventory", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

# Historical upper bounds observed on main@79e85d2a45f6, NOT allowed laws.
# Removal of an obsolete clause is allowed. A new one is not.
DEBT_CAPS = {
    "lib/time.lisp": 0,
    "lib/machine/admission/x86-64.lisp": 42,
    "lib/machine/lowering/semantic-x86-64.lisp": 2,
}


def old_cond_clauses(source: str):
    findings, _ = module.inspect(source)
    return [f for f in findings if f.cond in ("110", "00000111")
            and f.status in ("AUTO_YES", "HOLD")]


class CondStabilityWindowTests(unittest.TestCase):
    def test_current_active_files_do_not_increase_legacy_cond_debt(self):
        for name, limit in DEBT_CAPS.items():
            with self.subTest(path=name):
                path = ROOT / name
                source = path.read_text(encoding="utf-8")
                legacy = old_cond_clauses(source)
                self.assertLessEqual(
                    len(legacy), limit,
                    f"{name} has {len(legacy)} old three-field clauses "
                    f"(cap {limit}); first: {legacy[0] if legacy else 'none'}. "
                    "No automatic truthiness/0/1 conversion is authorized.",
                )

    def test_new_three_field_exact_cond_is_detected(self):
        example = "(110 ((010 (001 ())) 1 (001 ())))"
        violations = old_cond_clauses(example)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].status, "AUTO_YES")

    def test_unsafe_negative_case_stays_hold(self):
        example = "(110 ((010 (001 ())) 0 (001 ())))"
        violations = old_cond_clauses(example)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].status, "HOLD")

    def test_two_field_and_quoted_data_do_not_create_debt(self):
        source = """
        (110 ((010 (001 ())) (001 ())))
        (001 (110 ((010 (001 ())) 1 (001 ()))))
        ; (110 ((010 (001 ())) 1 (001 ())))
        """
        self.assertEqual(old_cond_clauses(source), [])

    def test_malformed_syntax_fails_instead_of_being_skipped(self):
        with self.assertRaises(module.Blocked):
            old_cond_clauses("(110 ((010 (001 ())) 1 (001 ()))")


if __name__ == "__main__":
    unittest.main()
