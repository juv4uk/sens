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

    def test_signature_generator_kind_and_admission_are_exact_d1(self):
        path = "scripts/generate-rust-function-signatures.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")

        def definition(name: str, next_name: str) -> str:
            newline = chr(10)
            start = source.index(f"(0011 {name}" + newline)
            end = source.index(newline + f"(0011 {next_name}" + newline, start)
            return source[start:end]

        kind = definition("render-kind", "render-arity")
        admitted = definition("render-admitted", "render-row")
        for label, fragment in (("kind", kind), ("admitted", admitted)):
            with self.subTest(label=label):
                self.assertEqual(MODULE.scan_lisp(fragment, path), [])

        # Reinstate an obsolete three-field result-match branch: fail closed.
        good = '((101 kind (001 builtin)) "LanguageItemKind::Builtin")'
        self.assertIn(good, kind)
        old = kind.replace(
            good, '((101 kind (001 builtin)) (1) "LanguageItemKind::Builtin")', 1
        )
        self.assertIn("COND_NOT_TWO_FIELDS", [
            item.rule for item in MODULE.scan_lisp(old, path)
        ])

        # A literal host T cannot stand in for an exact D1 predicate.
        fallback = '((010 (001 ())) "false")'
        self.assertIn(fallback, admitted)
        drift = admitted.replace(fallback, '(t "false")', 1)
        self.assertIn("COND_HOST_TRUTH", [
            item.rule for item in MODULE.scan_lisp(drift, path)
        ])

    def test_signature_generator_atom_case_branches_exact_d1(self):
        path = "scripts/generate-rust-function-signatures.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")

        def segment(name, following):
            start = source.index("(0011 " + name + "\n")
            end = source.index("\n(0011 " + following + "\n", start)
            return source[start:end]

        nonlegacy = (
            segment("has-field?", "render-kind"),
            segment("render-rows", "header"),
        )
        for fragment in nonlegacy:
            with self.subTest(prefix=fragment[:30]):
                self.assertEqual(MODULE.scan_lisp(fragment, path), [])

        arity = segment("render-arity", "render-admitted")
        self.assertEqual(MODULE.scan_lisp(arity, path), [])

        helpers = (
            segment("wire-integer-bits-onto", "render-rust-nat"),
            segment("render-rust-nat", "rows"),
        )
        for fragment in helpers:
            with self.subTest(helper=fragment[:40]):
                self.assertEqual(MODULE.scan_lisp(fragment, path), [])

        helper_substitutions = (
            (helpers[0], '((11110111 (110101011 remaining) "/") acc)',
             '((11110111 (110101011 remaining) "/") (1) acc)'),
            (helpers[0], '((010 (001 ()))\n       (wire-integer-bits-onto',
             '((11110111 (110101011 remaining) "/") (0)\n       (wire-integer-bits-onto'),
            (helpers[1], '((110101010 "#q2:" wire)\n         (str+',
             '((110101010 "#q2:" wire) t\n         (str+'),
            (helpers[1], '((010 (001 ())) (100 (001 ())))',
             '((110101010 "#q2:" wire) () (100 (001 ())))'),
        )
        for fragment, original, invalid in helper_substitutions:
            with self.subTest(helper_clause=original):
                self.assertIn(original, fragment)
                changed = fragment.replace(original, invalid, 1)
                self.assertIn("COND_NOT_TWO_FIELDS", [
                    f.rule for f in MODULE.scan_lisp(changed, path)
                ])

        # Restoring an expected-result field recreates the obsolete three-field clause.
        substitutions = (
            (nonlegacy[0], "((010 (11100 key (011 row))) (001 ()))",
             "((010 (11100 key (011 row))) (1) (001 ()))"),
            (nonlegacy[1], '((010 remaining) "")',
             '((010 remaining) (1) "")'),
            (arity, '((010 arity)\n       (str+',
             '((010 arity) (1)\n       (str+'),
            (arity, '((11110111 (100 arity) (001 at-least))\n          (str+',
             '((11110111 (100 arity) (001 at-least)) (1)\n          (str+'),
            (arity, '((11110111 (100 arity) (001 between))\n          (str+',
             '((11110111 (100 arity) (001 between)) (1)\n          (str+'),
        )
        for fragment, original, invalid in substitutions:
            with self.subTest(original=original):
                self.assertIn(original, fragment)
                changed = fragment.replace(original, invalid, 1)
                self.assertIn("COND_NOT_TWO_FIELDS", [
                    f.rule for f in MODULE.scan_lisp(changed, path)
                ])

        # The unknown-arity default is an unconditional exact-D1 fallback,
        # not a quoted symbol compared against itself in a historical triplet.
        exact_fallback = "((010 (001 ())) (100 (001 ())))"
        legacy_fallback = "((001 unknown-arity) unknown-arity (100 (001 ())))"
        self.assertIn(exact_fallback, arity)
        reverted = arity.replace(exact_fallback, legacy_fallback, 1)
        self.assertIn("COND_NOT_TWO_FIELDS", [
            f.rule for f in MODULE.scan_lisp(reverted, path)
        ])

        fallback = "((010 (001 ())) t)"
        self.assertIn(fallback, nonlegacy[0])
        bad = nonlegacy[0].replace(fallback, "(t t)", 1)
        self.assertIn("COND_HOST_TRUTH", [
            f.rule for f in MODULE.scan_lisp(bad, path)
        ])

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

    def test_dependency_classifier_exact_d1_cond_and_negative_guards(self):
        source = (ROOT / "scripts" / "build-dependency-classification.lisp").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            MODULE.scan_lisp(source, "scripts/build-dependency-classification.lisp"), []
        )

        # A host fallback and a historical ATOM/result-matching clause are
        # independently invalid even when the rest of the generator is current.
        fallback = "((010 (001 ())) rest)"
        self.assertIn(fallback, source)
        bad_truth = source.replace(fallback, "(t rest)", 1)
        self.assertIn(
            "COND_HOST_TRUTH",
            [f.rule for f in MODULE.scan_lisp(bad_truth, "scripts/build-dependency-classification.lisp")],
        )
        clause = "((010 form) rest)"
        self.assertIn(clause, source)
        bad_arity = source.replace(clause, "((010 form) (1) rest)", 1)
        self.assertIn(
            "COND_NOT_TWO_FIELDS",
            [f.rule for f in MODULE.scan_lisp(bad_arity, "scripts/build-dependency-classification.lisp")],
        )

    def test_symbol_table_exact_d1_cond_and_negative_mutations(self):
        path = "scripts/symbol-table.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        self.assertEqual(MODULE.scan_lisp(source, path), [])

        # Both historical ATOM result matches had the SAME branch body. Restoring
        # the obsolete three-field shape must never silently pass.
        exact = "((010 expr) acc)"
        self.assertIn(exact, source)
        old = source.replace(exact, "((010 expr) (1) acc)", 1)
        self.assertIn("COND_NOT_TWO_FIELDS", [
            finding.rule for finding in MODULE.scan_lisp(old, path)
        ])

        # This is exact D1:1, not Lisp host T or numeric one.
        fallback = "((010 (001 ())) (111 expr acc))"
        self.assertIn(fallback, source)
        host = source.replace(fallback, "(t (111 expr acc))", 1)
        self.assertIn("COND_HOST_TRUTH", [
            finding.rule for finding in MODULE.scan_lisp(host, path)
        ])

    def test_oracle_batch_uses_exact_d1_two_field_cond(self):
        path = "scripts/oracle-batch.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        self.assertEqual(MODULE.scan_lisp(source, path), [])

        # Both result-match branches previously produced the same data.
        exact = "((010 entries) (001 ()))"
        self.assertIn(exact, source)
        regression = source.replace(exact, "((010 entries) (1) (001 ()))", 1)
        self.assertIn("COND_NOT_TWO_FIELDS", [
            f.rule for f in MODULE.scan_lisp(regression, path)
        ])

        exact_fallback = "((010 (001 ())) (fixtures-only (011 entries)))"
        self.assertIn(exact_fallback, source)
        regression = source.replace(exact_fallback, "(t (fixtures-only (011 entries)))", 1)
        self.assertIn("COND_HOST_TRUTH", [
            f.rule for f in MODULE.scan_lisp(regression, path)
        ])

    def test_meta_semantic_generator_redundant_atom_paths_retired(self):
        path = "scripts/generate-meta-semantic-registry.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        findings = MODULE.scan_lisp(source, path)
        kinds = [finding.rule for finding in findings]

        # Four obsolete result-match forms were replaced by exact D1
        # two-field D3 clauses. Any reintroduction is a CI regression.
        self.assertEqual(kinds.count("COND_NOT_TWO_FIELDS"), 0)
        self.assertNotIn("COND_HOST_TRUTH", kinds)

        exact = "((010 surface) ())"
        self.assertIn(exact, source)
        reverted = source.replace(exact, "((010 surface) (1) ())", 1)
        self.assertGreater(
            [f.rule for f in MODULE.scan_lisp(reverted, path)].count(
                "COND_NOT_TWO_FIELDS"
            ),
            kinds.count("COND_NOT_TWO_FIELDS"),
        )

        fallback = "((010 (001 ())) t)"
        self.assertIn(fallback, source)
        reverted = source.replace(fallback, "(t t)", 1)
        self.assertIn(
            "COND_HOST_TRUTH",
            [f.rule for f in MODULE.scan_lisp(reverted, path)],
        )

        # Inject historical 3-field result matching in each of the two
        # newly migrated equality sites; strict audit must reject both.
        for predicate in (
            '((101 current generated)',
            '((101 (100 *argv*) "--check")',
        ):
            with self.subTest(predicate=predicate):
                self.assertIn(predicate, source)
                drift = source.replace(predicate, predicate + ' (1)', 1)
                self.assertIn("COND_NOT_TWO_FIELDS", [
                    f.rule for f in MODULE.scan_lisp(drift, path)
                ])

    def test_uk_surface_audit_generator_exact_atom_pairs_with_bounded_debt(self):
        path = "scripts/generate-uk-surface-audit.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        findings = MODULE.scan_lisp(source, path)
        rules = [f.rule for f in findings]

        # Two non-identical old clauses require separate semantic proof.
        # Never convert them by guesswork or hide them in strict audit.
        self.assertLessEqual(rules.count("COND_NOT_TWO_FIELDS"), 2)
        self.assertNotIn("COND_HOST_TRUTH", rules)

        exact = "((010 strings) acc)"
        self.assertIn(exact, source)
        bad = source.replace(exact, "((010 strings) (1) acc)", 1)
        self.assertGreater(
            [f.rule for f in MODULE.scan_lisp(bad, path)].count(
                "COND_NOT_TWO_FIELDS"
            ),
            rules.count("COND_NOT_TWO_FIELDS"),
        )

        fallback = "((010 (001 ())) (join-newline-onto"
        self.assertIn(fallback, source)
        bad = source.replace(fallback, "(t (join-newline-onto", 1)
        self.assertIn(
            "COND_HOST_TRUTH",
            [f.rule for f in MODULE.scan_lisp(bad, path)],
        )

    def test_function_table_generator_safe_d3_migration_is_monotonic(self):
        path = "scripts/generate-function-table.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        rules = [f.rule for f in MODULE.scan_lisp(source, path)]

        # Six non-trivial historical match branches still need independent
        # semantic proof; do not suppress them in the strict project audit.
        self.assertEqual(rules.count("COND_NOT_TWO_FIELDS"), 6)
        self.assertNotIn("COND_HOST_TRUTH", rules)
        self.assertNotIn("LEGACY_W8_CALL", rules)

        pair = "((010 sections) (001 ()))"
        self.assertIn(pair, source)
        regression = source.replace(pair, "((010 sections) (1) (001 ()))", 1)
        new_rules = [f.rule for f in MODULE.scan_lisp(regression, path)]
        self.assertGreater(
            new_rules.count("COND_NOT_TWO_FIELDS"),
            rules.count("COND_NOT_TWO_FIELDS"),
        )

        predicate = "((010 (001 ())) (find-section name (011 sections)))"
        self.assertIn(predicate, source)
        regression = source.replace(predicate, "(t (find-section name (011 sections)))", 1)
        self.assertIn(
            "COND_HOST_TRUTH",
            [f.rule for f in MODULE.scan_lisp(regression, path)],
        )

    def test_fpga_program_symbol_table_exact_d1_migration(self):
        path = "scripts/program-symbol-table.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        rules = [f.rule for f in MODULE.scan_lisp(source, path)]

        # A historical three-field printing clause remains real debt.
        # This negative test must not erase or allow it to silently grow.
        self.assertEqual(rules.count("COND_NOT_TWO_FIELDS"), 1)
        self.assertNotIn("COND_HOST_TRUTH", rules)

        exact = "((010 lst) acc)"
        self.assertIn(exact, source)
        reverted = source.replace(exact, "((010 lst) (1) acc)", 1)
        self.assertGreater(
            [f.rule for f in MODULE.scan_lisp(reverted, path)].count(
                "COND_NOT_TWO_FIELDS"
            ),
            rules.count("COND_NOT_TWO_FIELDS"),
        )

        fallback = "((010 (001 ())) (reverse-acc"
        self.assertIn(fallback, source)
        reverted = source.replace(fallback, "(t (reverse-acc", 1)
        self.assertIn(
            "COND_HOST_TRUTH",
            [f.rule for f in MODULE.scan_lisp(reverted, path)],
        )

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
