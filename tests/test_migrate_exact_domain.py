#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SCRIPT = SCRIPTS / "migrate-exact-domain.py"
SPEC = importlib.util.spec_from_file_location("migrate_exact_domain", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class ExactDomainMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.surfaces, cls.legacy = mod.load_authority()

    def rewrite(self, source: str) -> str:
        edits = mod.plan(source, self.surfaces, self.legacy)
        return mod.apply_edits(source, edits)

    def test_current_d3_surfaces_and_legacy_sid_resolve_to_same_successor(self):
        for source in ("(car x)", "(CAR x)", "(перше x)", "(00000101 x)"):
            self.assertEqual(self.rewrite(source), "(100 x)", source)

    def test_comments_quotes_strings_and_arguments_are_not_migrated(self):
        source = """; (car x)
'(car x)
("car" car)
(car (quote car) x)
"""
        expected = """; (car x)
'(car x)
("car" car)
(100 (001 car) x)
"""
        self.assertEqual(self.rewrite(source), expected)

    def test_already_exact_heads_are_idempotent(self):
        source = """(100 x)
(011 (100 x))
"""
        self.assertEqual(self.rewrite(source), source)
        self.assertEqual(mod.plan(source, self.surfaces, self.legacy), [])

    def test_unbalanced_source_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unterminated list"):
            mod.plan("(car x", self.surfaces, self.legacy)

    def test_unknown_heads_are_left_for_semantic_review(self):
        source = """(user-defined x)
"""
        self.assertEqual(mod.plan(source, self.surfaces, self.legacy), [])

    def test_shadowed_lambda_parameter_blocks_domain_head_rewrite(self):
        for source in (
            "(lambda (car) (car x))",
            "(0010 (перше) (перше x))",
            "(lambda (eq?) (eq? x y))",
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "SHADOWED_SURFACE_BLOCK"):
                    self.rewrite(source)

    def test_shadowed_global_definition_blocks_domain_head_rewrite(self):
        for source in (
            "(define car (lambda (x) x)) (car y)",
            "(0011 перше (0010 (x) x)) (перше y)",
            "(def car (lambda (x) x)) (car y)",
            "(define (car x) x) (car y)",
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "SHADOWED_SURFACE_BLOCK"):
                    self.rewrite(source)

    def test_let_binding_shadows_domain_surface_without_rewriting(self):
        for source in (
            "(let ((car f)) (car x))",
            "(let* ((eq? f)) (eq? x y))",
            "(001000 ((перше f)) (перше x))",
            "(001001 ((тотожне? f)) (тотожне? x y))",
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "SHADOWED_SURFACE_BLOCK"):
                    self.rewrite(source)

    def test_local_function_binders_cannot_be_misread_as_builtins(self):
        for source in (
            "(flet ((car (x) x)) (car x))",
            "(labels ((car (x) x)) (car x))",
            "(macrolet ((car (x) x)) (car x))",
            "(defun car (x) x) (car x)",
            "(defmacro car (x) x) (car x)",
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "SHADOWED_SURFACE_BLOCK"):
                    self.rewrite(source)

    def test_callable_parameters_in_all_binder_forms_are_shadowed(self):
        for source in (
            "(define (f car) (car x))",
            "(0011 (f перше) (перше x))",
            "(defun f (car) (car x))",
            "(defmacro f (car) (car x))",
            "(flet ((f (car) (car x))) (f z))",
            "(labels ((f (car) (car x))) (f z))",
            "(macrolet ((f (car) (car x))) (f z))",
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "SHADOWED_SURFACE_BLOCK"):
                    self.rewrite(source)

    def test_unproved_parameter_destructuring_stays_blocked(self):
        for source in (
            "(lambda x (car x))",
            "(defun f ((car x)) (car x))",
            "(flet ((f ((car x)) (car x))) (f z))",
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "BINDING_FORM_BLOCK"):
                    self.rewrite(source)

    def test_unproved_binding_syntax_fails_closed(self):
        for source in ("(let bad (car x))", "(flet (bad) (car x))"):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "BINDING_FORM_BLOCK"):
                    self.rewrite(source)

    def test_unshadowed_let_and_quoted_let_remain_safe(self):
        self.assertEqual(
            self.rewrite("(let ((x f)) (car x))"),
            "(let ((x f)) (100 x))",
        )
        self.assertEqual(
            self.rewrite("'(let ((car f)) (car x)) (car y)"),
            "'(let ((car f)) (car x)) (100 y)",
        )

    def test_quoted_definitions_are_data_not_shadowing(self):
        for source in (
            "'(define car (lambda (x) x)) (car x)",
            "(quote (define car (lambda (x) x))) (car x)",
        ):
            with self.subTest(source=source):
                self.assertTrue(self.rewrite(source).endswith("(100 x)"))

    def test_unshadowed_lambda_still_migrates_exactly(self):
        self.assertEqual(
            self.rewrite("(lambda (x) (car x))"),
            "(0010 (x) (100 x))",
        )

    def test_legacy_list_successor_is_not_narrowed_into_nonadmitted_d4(self):
        source = "(00100111 evaluator-fallback expression)\n"
        self.assertEqual(mod.plan(source, self.surfaces, self.legacy), [])


if __name__ == "__main__":
    unittest.main()
