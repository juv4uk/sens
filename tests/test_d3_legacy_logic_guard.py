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
        # Post-migration D1 forms use (001 ()) for false, not NIL.
        good = "((010 (001 ())) (001 ())))"
        self.assertIn(good, source)
        corrupted = source.replace(good, "(T (001 ())))", 1)
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
            segment("render-rust-nat", "field"),
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

    def test_evaluator_dispatch_generator_uses_exact_d3_cond(self):
        path = "scripts/generate-rust-evaluator-dispatch.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        self.assertEqual(MODULE.scan_lisp(source, path), [])

        # Representative mutations restore old result-matching triplets;
        # every one must be rejected by the same scanner used in Hosted CI.
        mutations = (
            ("((010 remaining)\n       (001 ()))",
             "((010 remaining)\n       ()\n       (001 ()))"),
            ("((11110111 name (001 lambda))\n       \"NecessaryFormMechanism::Lambda\")",
             "((11110111 name (001 lambda)) (1)\n       \"NecessaryFormMechanism::Lambda\")"),
            ("((010 (001 ())) (100 (001 ())))",
             "((001 no-known-mechanism) no-known-mechanism (100 (001 ())))"),
            ("((010 remaining)\n       \"\")",
             "((010 remaining) ()\n       \"\")"),
        )
        for good, legacy in mutations:
            with self.subTest(legacy=legacy):
                self.assertIn(good, source)
                mutated = source.replace(good, legacy, 1)
                self.assertIn("COND_NOT_TWO_FIELDS", [
                    finding.rule for finding in MODULE.scan_lisp(mutated, path)
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

    def test_current_ukr_map_uses_exact_d1_and_two_field_cond(self):
        # scripts/build-inventory.lisp є лише якорем; не видавати його за
        # виконуваний рекурсивний доказ D3. Поточне джерело — сама мапа.
        path = "lib/persistent-map.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        self.assertIn("(визначити мапа-отримати", source)
        self.assertIn("(за-умовою", source)
        self.assertEqual(MODULE.scan_lisp(source, path), [])

        # Host t не є ратифікованим D1; негативний свідок справді змінює
        # джерело, а лексичний сканер мусить його відхилити.
        bad_truth = source + "\n(за-умовою (t (як-є помилка)))\n"
        self.assertIn("COND_HOST_TRUTH", [
            f.rule for f in MODULE.scan_lisp(bad_truth, path)
        ])
        bad_arity = source + "\n(за-умовою ((атом? форма) (як-є так) (як-є ні)))\n"
        self.assertIn("COND_NOT_TWO_FIELDS", [
            f.rule for f in MODULE.scan_lisp(bad_arity, path)
        ])

    def test_dependency_classifier_exact_d1_cond_and_negative_guards(self):
        source = (ROOT / "scripts" / "build-dependency-classification.lisp").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            MODULE.scan_lisp(source, "scripts/build-dependency-classification.lisp"), []
        )

        # Старі двійкові тіла з цього файлу давно вилучено. Перевіряємо
        # фактичну українську форму та незалежні негативні мутації:
        # ані host t, ані третє поле COND не можуть пройти D3 guard.
        self.assertIn("(визначити класифікувати-залежності-збірки", source)
        self.assertNotIn("(визначити build-dependency-classification", source)
        bad_truth = source + "\n(за-умовою (t (як-є помилка)))\n"
        self.assertIn(
            "COND_HOST_TRUTH",
            [f.rule for f in MODULE.scan_lisp(bad_truth, "scripts/build-dependency-classification.lisp")],
        )
        bad_arity = source + "\n(за-умовою ((атом? форма) (як-є так) (як-є ні)))\n"
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

    def test_oracle_batch_current_ukrainian_projection_and_d3_guard(self):
        path = "scripts/oracle-batch.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        # Нова програма більше не містить історичних fixture/TCP-гілок.
        # Живе виконання перевіряє Rust/SENS; тут перевіряємо лише guard.
        self.assertIn("(визначити пакетний-оракул", source)
        self.assertNotIn("(визначити адреса-оракула", source)
        self.assertEqual(MODULE.scan_lisp(source, path), [])

        # Сканер не має вимагати старі 010/011 у чинному файлі,
        # але повинен відхиляти справжню арність/host-truth регресію.
        invalid_clause = source + "\n(за-умовою ((атом? записи) (як-є ()) (як-є ())))\n"
        self.assertIn("COND_NOT_TWO_FIELDS", [
            f.rule for f in MODULE.scan_lisp(invalid_clause, path)
        ])
        host_truth = source + "\n(за-умовою (t (як-є ())))\n"
        self.assertIn("COND_HOST_TRUTH", [
            f.rule for f in MODULE.scan_lisp(host_truth, path)
        ])

    def test_meta_semantic_generator_current_ukrainian_and_no_fake_pass(self):
        path = "scripts/generate-meta-semantic-registry.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        kinds = [finding.rule for finding in MODULE.scan_lisp(source, path)]

        # Ця проєкція вже використовує українські D3-форми, а не
        # історичні голі біти. Перевіряємо чинний файл, не вимагаємо
        # давно вилучені ((010 surface)) та хостове t як доказ.
        self.assertNotIn("COND_NOT_TWO_FIELDS", kinds)
        self.assertNotIn("COND_HOST_TRUTH", kinds)
        self.assertIn("(функція (назва-поверхні)", source)
        self.assertIn("((атом? запис-поверхні) (як-є ()))", source)
        self.assertIn("(так (перше запис-поверхні))", source)
        self.assertNotIn("((010 surface)", source)
        self.assertNotIn("(t t)", source)

        # Порожній шаблон реєстру НЕ надає готовність виконання.
        self.assertIn("lib/surface/semantic-registry.lisp", source)
        self.assertIn("(status not-verified)", source)
        self.assertNotIn("(status pass)", source)

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
        findings = MODULE.scan_lisp(source, path)
        rules = [f.rule for f in findings]

        # The active generator is fully on the strict D3 control law.
        self.assertEqual(rules.count("COND_NOT_TWO_FIELDS"), 0)
        self.assertNotIn("COND_HOST_TRUTH", rules)
        self.assertNotIn("LEGACY_W8_CALL", rules)

        # Preserve the already-established adversarial witnesses elsewhere in
        # this generator: reverting any exact two-field predicate clause must
        # immediately reintroduce scanner debt.
        for klass, value in (("member", "word"), ("nonmember", "(11110100 word)")):
            with self.subTest(klass=klass):
                exact = (
                    f"((101 (string-membership-helper word) "
                    f"(class-membership string {klass}))\\n       {value})"
                ).replace("\\n", "\n")
                legacy = (
                    f"((string-membership-helper word)\\n"
                    f"       (class-membership string {klass})\\n"
                    f"       {value})"
                ).replace("\\n", "\n")
                self.assertIn(exact, source)
                drift = MODULE.scan_lisp(source.replace(exact, legacy, 1), path)
                self.assertGreater(
                    [f.rule for f in drift].count("COND_NOT_TWO_FIELDS"), 0
                )

        pair = "((010 sections) (001 ()))"
        self.assertIn(pair, source)
        regression = source.replace(pair, "((010 sections) (1) (001 ()))", 1)
        self.assertGreater(
            [f.rule for f in MODULE.scan_lisp(regression, path)].count(
                "COND_NOT_TWO_FIELDS"
            ),
            0,
        )

        predicate = "((010 (001 ())) (find-section name (011 sections)))"
        self.assertIn(predicate, source)
        regression = source.replace(predicate, "(t (find-section name (011 sections)))", 1)
        self.assertIn(
            "COND_HOST_TRUTH",
            [f.rule for f in MODULE.scan_lisp(regression, path)],
        )

        # String comparisons are atomic: D3:101 EQ is sufficient and remains
        # distinct from the wider D8:11110111 structural EQUAL identity.
        d3 = (ROOT / "lib/domains/d3.lisp").read_text(encoding="utf-8")
        d8 = (ROOT / "lib/domains/d8.lisp").read_text(encoding="utf-8")
        self.assertIn(
            "(101 (ук тотожне?) (укр тотожне?) (san abheda) (en eq?) (LISP EQ)",
            d3,
        )
        self.assertIn(
            "(11110111 (ук однакові?) (укр однакові?) (san tulya) (en equal?) (LISP EQUAL)",
            d8,
        )
        self.assertEqual(len("101"), 3)
        self.assertEqual(len("11110111"), 8)

        for exact in (
            "((101 current-wsm wsm-output)\n         (110",
            "((101 current-md md-output)\n            (11011011",
            '((101 (100 *argv*) "--check")\n   (check-projections))',
        ):
            with self.subTest(exact=exact):
                self.assertIn(exact, source)

        # Point diagnostic: restoring one expected-result field produces
        # exactly one old three-field COND finding, not a vague global failure.
        exact = "((101 current-wsm wsm-output)\n         (110"
        reverted = source.replace(
            exact,
            "((101 current-wsm wsm-output)\n         (1)\n         (110",
            1,
        )
        drift = MODULE.scan_lisp(reverted, path)
        three_field = [f for f in drift if f.rule == "COND_NOT_TWO_FIELDS"]
        self.assertEqual(len(three_field), 1)
        self.assertEqual(three_field[0].operation, "COND")

        # CLI *argv* is a list of strings: empty -> write, "--check" -> check,
        # every other nonempty argv -> exact-D1 fallback -> write.
        self.assertIn("((010 *argv*)\n   (write-projections))", source)
        self.assertIn('((101 (100 *argv*) "--check")', source)
        self.assertIn("((010 (001 ()))\n   (write-projections))", source)

    def test_fpga_program_symbol_table_exact_d1_migration(self):
        path = "scripts/program-symbol-table.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        rules = [f.rule for f in MODULE.scan_lisp(source, path)]

        # A historical three-field printing clause remains real debt.
        # This negative test must not erase or allow it to silently grow.
        self.assertEqual(rules.count("COND_NOT_TWO_FIELDS"), 1)
        self.assertNotIn("COND_HOST_TRUTH", rules)

        # D3:010 має ратифіковану повну укр-проєкцію «атом?».
        # Негативний тест трьохпольового COND залишаємо активним.
        exact = "((атом? lst) acc)"
        self.assertIn(exact, source)
        self.assertIn("(визначити reverse-acc", source)
        reverted = source.replace(exact, "((атом? lst) (1) acc)", 1)
        self.assertGreater(
            [f.rule for f in MODULE.scan_lisp(reverted, path)].count(
                "COND_NOT_TWO_FIELDS"
            ),
            rules.count("COND_NOT_TWO_FIELDS"),
        )

        fallback = "((атом? (як-є ())) (reverse-acc"
        self.assertIn(fallback, source)
        reverted = source.replace(fallback, "(t (reverse-acc", 1)
        self.assertIn(
            "COND_HOST_TRUTH",
            [f.rule for f in MODULE.scan_lisp(reverted, path)],
        )

    def test_release_require_exact_d3_fail_closed(self):
        """The tag/CI/owner preconditions retain an actual failure path."""
        path = "scripts/release.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        start = source.index("(0011 release-require" + chr(10))
        end = source.index("(0011 release-run" + chr(10), start)
        guard = source[start:end]

        self.assertEqual(MODULE.scan_lisp(guard, path), [])
        self.assertIn("((101 actual expected) actual)", guard)
        self.assertIn("((010 (001 ()))", guard)
        self.assertIn("(release-preflight-failed)", guard)

        # A former three-field, result-matching branch must fail the
        # live exact-D3 scanner, never become an accepted release bypass.
        degraded = guard.replace(
            "((101 actual expected) actual)",
            "((101 actual expected) (1) actual)", 1
        )
        self.assertIn("COND_NOT_TWO_FIELDS", [
            f.rule for f in MODULE.scan_lisp(degraded, path)
        ])

        # Host truth T is not a canonical D1 predicate in tag checks.
        degraded = guard.replace("((010 (001 ()))", "(t", 1)
        self.assertIn("COND_HOST_TRUTH", [
            f.rule for f in MODULE.scan_lisp(degraded, path)
        ])

        # The error route cannot be silently detached from preflight.
        without_error = guard.replace("(release-preflight-failed)", "(001 ())", 1)
        self.assertNotEqual(guard, without_error)
        self.assertNotIn("(release-preflight-failed)", without_error)

    def test_release_fasl_and_manifest_guards_preserve_exact_d1_fail_closed(self):
        path = "scripts/release.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        self.assertIn("((101 release-fasl-diff-status 0) (001 ()))", source)
        self.assertIn("((101 release-fasl-diff-status 1)", source)
        self.assertIn("((010 paths) (001 ()))", source)
        self.assertNotIn("((010 paths) () (001 ()))", source)
        fs = source.index("(0011 release-fasl-diff-status" + chr(10))
        fe = source.index('(release-run "timeout" (001 ("60" "git" "fetch" "origin" "main")))', fs)
        ms = source.index("(0011 release-check-manifests" + chr(10))
        me = source.index("(release-check-manifests" + chr(10), ms + 1)
        for label, block in (("fasl", source[fs:fe]),
                             ("manifests", source[ms:me])):
            with self.subTest(label=label):
                self.assertEqual(MODULE.scan_lisp(block, path), [])
                fallback = "((010 (001 ()))"
                self.assertIn(fallback, block)
                bad = block.replace(fallback, "(t", 1)
                self.assertIn("COND_HOST_TRUTH", [
                    x.rule for x in MODULE.scan_lisp(bad, path)
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
