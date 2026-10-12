#!/usr/bin/env python3
"""Regression tests for the read-only D3 COND/ATOM/EQ stale-logic scanner."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_d3_legacy_logic.py"
SPEC = importlib.util.spec_from_file_location("check_d3_legacy_logic_guard", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class LegacyD3GuardTests(unittest.TestCase):
    def rules(self, source: str) -> list[str]:
        return [f.rule for f in MODULE.scan_lisp(source, "lib/example.lisp")]

    def test_obsolete_w8_atom_eq_cond_heads_are_all_reported(self):
        source = """(00000111
          ((00000010 (001 ())) (001 1))
          ((00000011 (001 x) (001 y)) (001 0)))"""
        findings = MODULE.scan_lisp(source, "lib/a.lisp")
        self.assertEqual([f.operation for f in findings if f.rule == "LEGACY_W8_CALL"],
                         ["COND", "ATOM", "EQ"])
        self.assertEqual({f.line for f in findings}, {1, 2, 3})

    def test_exact_d3_call_and_two_part_cond_are_accepted(self):
        self.assertEqual(self.rules("(110 ((010 ()) 1) ((101 (001 x) (001 x)) 0))"), [])

    def test_three_field_cond_rejected_in_exact_and_surface_forms(self):
        for head in ("110", "за-умовою"):
            with self.subTest(head=head):
                self.assertIn("COND_NOT_TWO_FIELDS", self.rules(f"({head} ((010 ()) 1 0))"))

    def test_host_truthiness_not_treated_as_d1(self):
        for subject in ("t", "NIL", "#t", "false"):
            with self.subTest(subject=subject):
                self.assertIn("COND_HOST_TRUTH", self.rules(f"(110 ({subject} 1))"))

    def test_exact_atom_eq_arity_drift_is_detected(self):
        self.assertEqual(self.rules("(010 0 1) (101 1)"),
                         ["D3_WRONG_ARITY", "D3_WRONG_ARITY"])

    def test_apostrophe_inside_ukrainian_identifier_is_not_a_quote(self):
        source = "(101 (100 (100 секції)) ім'я)"
        self.assertEqual(self.rules(source), [])
        # A quote at token start still marks the following form as data.
        self.assertEqual(self.rules("'(101 x y z)"), [])

    def test_comments_strings_and_quoted_forms_not_execution(self):
        source = """; (00000010 ())
          "(00000011 x y)"
          '(00000111 ((1 1 0)))
          (001 (00000010 x))
          #| (110 ((t 1 0))) |#
          #;(110 ((t 1 0)))
          (110 (1 1))"""
        self.assertEqual(self.rules(source), [])

    def test_guard_runtime_policy_uses_exact_d3_and_d1_fallback(self):
        source = (ROOT / "knowledge" / "guard-runtime-policy.lisp").read_text(encoding="utf-8")
        self.assertEqual(MODULE.scan_lisp(source, "knowledge/guard-runtime-policy.lisp"), [])
        self.assertIn("(1 (guard-unknown subject", source)
        corrupted = source.replace("(1 (guard-unknown subject", "(t (guard-unknown subject", 1)
        self.assertIn("COND_HOST_TRUTH", [f.rule for f in MODULE.scan_lisp(
            corrupted, "knowledge/guard-runtime-policy.lisp")])

    def test_core1_legacy_host_t_fallbacks_are_exact_d1(self):
        source = (ROOT / "lib" / "core1.lisp").read_text(encoding="utf-8")
        self.assertEqual(MODULE.scan_lisp(source, "lib/core1.lisp"), [])
        # Replacing even one exact-D1 fallback with host T must be rejected.
        good = "((010 (001 ())) NIL))))"
        self.assertIn(good, source)
        corrupted = source.replace(good, "(T NIL))))", 1)
        self.assertIn(
            "COND_HOST_TRUTH",
            [f.rule for f in MODULE.scan_lisp(corrupted, "lib/core1.lisp")],
        )

    def test_invalid_lisp_is_incomplete_not_green(self):
        for source in ("(110 (1 1)", "(110 (1 1)))", '"unclosed'):
            with self.subTest(source=source), self.assertRaises(MODULE.Unscannable):
                self.rules(source)

    def test_domain_table_readable_uses_only_d1_cond_fallbacks(self):
        source = (ROOT / "scripts" / "check-domain-table-readable.lisp").read_text(encoding="utf-8")
        self.assertEqual(MODULE.scan_lisp(source, "scripts/check-domain-table-readable.lisp"), [])

    def test_island_math_evidence_guard_uses_only_d1_cond_tests(self):
        source = (ROOT / "scripts" / "check-island-math-evidence.lisp").read_text(encoding="utf-8")
        self.assertEqual(MODULE.scan_lisp(source, "scripts/check-island-math-evidence.lisp"), [])

    def test_build_inventory_uses_only_exact_d1_two_field_cond(self):
        source = (ROOT / "scripts" / "build-inventory.lisp").read_text(encoding="utf-8")
        self.assertEqual(MODULE.scan_lisp(source, "scripts/build-inventory.lisp"), [])

        # Host truth is never a PredicateBit; restoration must fail.
        fallback = "((010 (001 ())) (assoc key (011 alist)))"
        self.assertIn(fallback, source)
        changed = source.replace(fallback, "(t (assoc key (011 alist)))", 1)
        self.assertIn("COND_HOST_TRUTH", [
            f.rule for f in MODULE.scan_lisp(changed, "scripts/build-inventory.lisp")
        ])

        # Historical three-field ATOM-result matching is also forbidden.
        clause = "((010 (0111 v)) ())"
        self.assertIn(clause, source)
        changed = source.replace(clause, "((010 (0111 v)) (1) ())", 1)
        self.assertIn("COND_NOT_TWO_FIELDS", [
            f.rule for f in MODULE.scan_lisp(changed, "scripts/build-inventory.lisp")
        ])

    def test_historical_paths_and_metadata_excluded(self):
        for path in ("docs/research/old.lisp", "research/domain-archive/a.lisp",
                     "tests/fixtures/old.lisp", "lib/domains/d3.lisp",
                     "lib/generated/table.lisp", "lib/surface/semantic-registry.lisp"):
            self.assertFalse(MODULE.is_live(path), path)
        for path in ("lib/core.lisp", "lib/time.lisp", "scripts/build-constitution.lisp"):
            self.assertTrue(MODULE.is_live(path), path)

    def test_runtime_guard_detects_atom_eq_cond_regressions(self):
        good = """
        pub(crate) fn atom_value(value: &Value, _environment: &Environment) -> Value {
            Value::predicate_bit(!matches!(value, Value::Pair(_, _)))
        }
        pub(crate) fn eq_values(left: Value, right: Value, span: Span) -> Result<Value, LanguageError> {
            if !left.is_atom() || !right.is_atom() { return Err(fail(span)); }
            Ok(Value::predicate_bit(left == right))
        }
        fn exact_d3_cond_control(value: &Value, span: Span) -> Result<Control, LanguageError> {
            match value.as_predicate_bit() { Some(true) => Ok(Select), _ => Err(fail(span)) }
        }
        pub(crate) fn evaluate_domain_cond(clauses: &[Expr], env: &Environment, s: Span) -> Result<EvalStep, LanguageError> {
            if parts.len() != 2 { return Err(fail(s)); }
            match exact_d3_cond_control(&value, s) {}
            Ok(EvalStep::Value(Value::Nil))
        }
        """
        self.assertEqual(MODULE.scan_core_rust(good), [])
        bad = good.replace("!matches!(value, Value::Pair(_, _))", "value.is_truthy()")
        bad = bad.replace("!left.is_atom() || !right.is_atom()", "left == right")
        bad = bad.replace("parts.len() != 2", "parts.len() != 3")
        drift = MODULE.scan_core_rust(bad)
        self.assertEqual({item.operation for item in drift}, {"ATOM", "EQ", "COND"})

    def test_live_time_library_uses_only_current_d3_call_heads(self):
        source = (ROOT / "lib/time.lisp").read_text(encoding="utf-8")
        findings = MODULE.scan_lisp(source, "lib/time.lisp")
        rejected = [item for item in findings if item.rule in (
            "LEGACY_W8_CALL", "D3_WRONG_ARITY",
            "COND_NOT_TWO_FIELDS", "COND_HOST_TRUTH")]
        self.assertEqual(rejected, [], "Time loader now uses a path-bound exact D3 reader")

    def test_live_world_library_uses_exact_d3_and_preserves_quote_data(self):
        source = (ROOT / "lib/world.lisp").read_text(encoding="utf-8")
        findings = MODULE.scan_lisp(source, "lib/world.lisp")
        self.assertEqual(
            [item for item in findings if item.rule in
             ("LEGACY_W8_CALL", "D3_WRONG_ARITY",
              "COND_NOT_TWO_FIELDS", "COND_HOST_TRUTH")], [],
            "World was cut over to path-bound exact D3; no W8 regression admitted"
        )
        old = (ROOT / "tests/fixtures/world-d3-before.lisp").read_text(encoding="utf-8")
        self.assertNotEqual(old, source, "world must not silently regress to old W8 source")

    def test_migrated_reasoning_libraries_have_no_old_d3_calls(self):
        for module in ("world", "forward", "knowledge"):
            path = f"lib/{module}.lisp"
            source = (ROOT / path).read_text(encoding="utf-8")
            findings = MODULE.scan_lisp(source, path)
            with self.subTest(module=module):
                self.assertEqual(
                    [f for f in findings if f.rule in (
                        "LEGACY_W8_CALL", "D3_WRONG_ARITY",
                        "COND_NOT_TWO_FIELDS", "COND_HOST_TRUTH"
                    )], [],
                    f"{path} must not silently regress to historical D3 call heads"
                )

    def test_git_audit_reports_files_and_strict_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for directory in ("lib", "docs/research", "crates/sens/src/eval/special_forms"):
                (root / directory).mkdir(parents=True, exist_ok=True)
            (root / "lib/live.lisp").write_text("(00000010 ())\n", encoding="utf-8")
            (root / "docs/research/old.lisp").write_text("(00000111 ((t 1 0)))\n", encoding="utf-8")
            (root / MODULE.CORE).write_text("fn atom_value() {}\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            report = MODULE.audit(root)
            self.assertEqual(report["active_lisp_files_scanned"], 1)
            self.assertEqual([row["rule"] for row in report["findings"]], ["LEGACY_W8_CALL"])
            self.assertGreater(len(report["errors"]), 0, "missing law mechanisms must fail closed")
            run = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--strict"],
                                 text=True, capture_output=True, check=False)
            self.assertEqual(run.returncode, 2, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
