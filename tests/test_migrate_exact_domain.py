#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
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
        cls.surfaces = mod.load_authority()

    def rewrite(self, source: str) -> str:
        edits = mod.plan(source, self.surfaces)
        return mod.apply_edits(source, edits)

    def test_only_current_d1_d11_foundation_is_used_for_isolated_migration(self):
        # Негативна фікстура не повинна випадково взяти застарілу D1–D9
        # основу із робочого репозиторію.
        with tempfile.TemporaryDirectory(prefix="sens-current-domains-") as td:
            isolated = Path(td)
            (isolated / "knowledge").mkdir()
            domain_dir = isolated / "lib/domains"
            domain_dir.mkdir(parents=True)
            (isolated / "knowledge/d1-d11-foundation.json").write_bytes(
                (ROOT / "knowledge/d1-d11-foundation.json").read_bytes()
            )
            for domain in ("d3", "d4"):
                (domain_dir / f"{domain}.lisp").write_bytes(
                    (ROOT / "lib/domains" / f"{domain}.lisp").read_bytes()
                )
            surfaces = mod.load_authority(isolated)
            self.assertEqual((surfaces["перше"].domain,
                              surfaces["перше"].bits), ("D3", "100"))
            (isolated / "knowledge/d1-d11-foundation.json").write_text(
                "{}", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "owner authority"):
                mod.load_authority(isolated)

    def test_current_d3_ratified_ukrainian_projection(self):
        for source in ("(car x)", "(CAR x)", "(перше x)"):
            self.assertEqual(self.rewrite(source), "(перше x)", source)
        self.assertEqual(self.surfaces["перше"].domain, "D3")
        self.assertEqual(self.surfaces["перше"].bits, "100")

    def test_comments_quotes_strings_and_arguments_are_not_migrated(self):
        source = """; (car x)
'(car x)
("car" car)
(car (quote car) x)
"""
        expected = """; (car x)
'(car x)
("car" car)
(перше (як-є car) x)
"""
        self.assertEqual(self.rewrite(source), expected)

    def test_prefixed_quote_in_list_head_is_data_not_an_executable_head(self):
        # Source apostrophe and CL function-quote must not be rewritten as
        # executable SENS D3:100, even when occupying list-head position.
        for source in ("('car x)", "(#'car x)", "('перше x)",
                       "('00000101 x)"):
            with self.subTest(source=source):
                self.assertEqual(self.rewrite(source), source)

    def test_unquoted_nested_call_after_quoted_head_remains_migratable(self):
        # A quoted datum blocks only its own head, not an independent call.
        self.assertEqual(
            self.rewrite("('car (car x))"),
            "('car (перше x))",
        )
        self.assertEqual(
            self.rewrite("(#'car (car x))"),
            "(#'car (перше x))",
        )

    def test_already_exact_heads_are_idempotent(self):
        source = """(перше x)
(решта (перше x))
"""
        self.assertEqual(self.rewrite(source), source)
        self.assertEqual(mod.plan(source, self.surfaces), [])

    def test_unbalanced_source_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unterminated list"):
            mod.plan("(car x", self.surfaces)

    def test_unknown_heads_are_left_for_semantic_review(self):
        source = """(user-defined x)
"""
        self.assertEqual(mod.plan(source, self.surfaces), [])

    def test_shadowed_lambda_parameter_remains_local_without_global_hold(self):
        self.assertEqual(
            self.rewrite("(lambda (car) (car x))"),
            "(функція (car) (car x))",
        )
        self.assertEqual(
            self.rewrite("(lambda (car) (car x)) (car y)"),
            "(функція (car) (car x)) (перше y)",
        )
        for source in (
            "(lambda (car) (car x))",
            "(0010 (перше) (перше x))",
            "(lambda (eq?) (eq? x y))",
        ):
            with self.subTest(source=source):
                converted = self.rewrite(source)
                # A local binding keeps its original spelling and calls.
                for head in ("car", "eq?", "перше", "тотожне?"):
                    self.assertEqual(
                        source.count(f"({head} "),
                        converted.count(f"({head} "),
                        f"невиправдано переписано локальне ім'я {head}",
                    )

    def test_shadowed_global_definition_blocks_domain_head_rewrite(self):
        for source in (
            "(define car (lambda (x) x)) (car y)",
            "(0011 перше (0010 (x) x)) (перше y)",
            "(def car (lambda (x) x)) (car y)",
            "(define (car x) x) (car y)",
        ):
            with self.subTest(source=source):
                converted = self.rewrite(source)
                # A local binding keeps its original spelling and calls.
                for head in ("car", "eq?", "перше", "тотожне?"):
                    self.assertEqual(
                        source.count(f"({head} "),
                        converted.count(f"({head} "),
                        f"невиправдано переписано локальне ім'я {head}",
                    )

    def test_let_binding_shadows_domain_surface_without_rewriting(self):
        for source in (
            "(let ((car f)) (car x))",
            "(let* ((eq? f)) (eq? x y))",
            "(001000 ((перше f)) (перше x))",
            "(001001 ((тотожне? f)) (тотожне? x y))",
        ):
            with self.subTest(source=source):
                converted = self.rewrite(source)
                # A local binding keeps its original spelling and calls.
                for head in ("car", "eq?", "перше", "тотожне?"):
                    self.assertEqual(
                        source.count(f"({head} "),
                        converted.count(f"({head} "),
                        f"невиправдано переписано локальне ім'я {head}",
                    )

    def test_local_function_binders_cannot_be_misread_as_builtins(self):
        for source in (
            "(flet ((car (x) x)) (car x))",
            "(labels ((car (x) x)) (car x))",
            "(macrolet ((car (x) x)) (car x))",
            "(defun car (x) x) (car x)",
            "(defmacro car (x) x) (car x)",
        ):
            with self.subTest(source=source):
                converted = self.rewrite(source)
                # A local binding keeps its original spelling and calls.
                for head in ("car", "eq?", "перше", "тотожне?"):
                    self.assertEqual(
                        source.count(f"({head} "),
                        converted.count(f"({head} "),
                        f"невиправдано переписано локальне ім'я {head}",
                    )

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
                converted = self.rewrite(source)
                # A local binding keeps its original spelling and calls.
                for head in ("car", "eq?", "перше", "тотожне?"):
                    self.assertEqual(
                        source.count(f"({head} "),
                        converted.count(f"({head} "),
                        f"невиправдано переписано локальне ім'я {head}",
                    )

    def test_runtime_supported_bare_and_dotted_lambda_lists_migrate(self):
        self.assertEqual(
            self.rewrite("(lambda x (car x))"),
            "(функція x (перше x))",
        )
        # A bare rest parameter that shadows a canonical surface stays local.
        self.assertEqual(
            self.rewrite("(lambda car (car x))"),
            "(функція car (car x))",
        )
        # Dotted rest is supported by the evaluator; shadowing is lexical.
        self.assertEqual(
            self.rewrite("(lambda (car . rest) (car x) (cdr rest))"),
            "(функція (car . rest) (car x) (решта rest))",
        )

    def test_nested_parameter_destructuring_stays_rejected_by_runtime_grammar(self):
        for source in (
            "(lambda ((car x)) (car x))",
            "(defun f ((car x)) (car x))",
            "(flet ((f ((car x)) (car x))) (f z))",
            "(lambda (car . (rest)) (car x))",
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "SOURCE_FORM_ERROR"):
                    self.rewrite(source)

    def test_unproved_binding_syntax_fails_closed(self):
        for source in ("(let bad (car x))", "(flet (bad) (car x))"):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "SOURCE_FORM_ERROR"):
                    self.rewrite(source)

    def test_unshadowed_let_and_quoted_let_remain_safe(self):
        self.assertEqual(
            self.rewrite("(let ((x f)) (car x))"),
            "(let ((x f)) (перше x))",
        )
        self.assertEqual(
            self.rewrite("'(let ((car f)) (car x)) (car y)"),
            "'(let ((car f)) (car x)) (перше y)",
        )

    def test_quoted_definitions_are_data_not_shadowing(self):
        for source in (
            "'(define car (lambda (x) x)) (car x)",
            "(quote (define car (lambda (x) x))) (car x)",
        ):
            with self.subTest(source=source):
                self.assertTrue(self.rewrite(source).endswith("(перше x)"))

    def test_unshadowed_lambda_still_migrates_exactly(self):
        self.assertEqual(
            self.rewrite("(lambda (x) (car x))"),
            "(функція (x) (перше x))",
        )

    def test_legacy_W8_rewrite_preserves_quotes_and_exact_ukr(self):
        # Це тест механічного сканера, НЕ Python-evaluator SENS.
        old = "00000101"  # історичний сід8: CAR, не D8:00000101
        proven = {old: mod.Identity("D3", "100", "CAR", "перше")}
        source = (
            "; (00000101 дані)\\n"
            "(00000101 аргумент)\\n"
            "(як-є (00000101 дані))\\n"
            "'(00000101 теж-дані)\\n"
            "(визначити сі:назва (як-є 3))\\n"
        ).replace("\\n", "\n")
        untouched = []
        edits = mod.plan(source, {}, legacy_heads=proven, unresolved=untouched)
        self.assertEqual(untouched, [])
        self.assertEqual(len(edits), 1)
        expected = source.replace("(00000101 аргумент)", "(перше аргумент)")
        self.assertEqual(mod.apply_edits(source, edits), expected)

    def test_explicit_sid8_sens8_heads_use_historical_bridge_not_d8(self):
        # Лише механічна міграція ратифікованої укр-проєкції,
        # а не удаване Python-виконання SENS.
        original = (
            "; (sid8:00001100 коментар)\n"
            "(sid8:00001100 2 3)\n"
            "(SeNs8:00001100 4 5)\n"
            "(як-є (sens8:00001100 дані))\n"
            "'(sid8:00001100 теж-дані)\n"
            '"(sid8:00001100 рядок)"\n'
        )
        replacement = mod.Identity("D5", "01010", "PLUS", "додати")
        pending = []
        edits = mod.plan(
            original, {}, legacy_heads={"00001100": replacement},
            unresolved=pending
        )
        self.assertEqual(pending, [])
        self.assertEqual(len(edits), 2)
        converted = mod.apply_edits(original, edits)
        self.assertEqual(converted.count("(додати "), 2)
        self.assertIn("(як-є (sens8:00001100 дані))", converted)
        self.assertIn("'(sid8:00001100 теж-дані)", converted)
        self.assertIn("; (sid8:00001100 коментар)", converted)
        self.assertIn('"(sid8:00001100 рядок)"', converted)
        self.assertEqual(mod.plan(converted, {}, legacy_heads={
            "00001100": replacement}), [])

    def test_prefixed_old_word_without_proof_fails_closed(self):
        for old in ("sid8:00001100", "sens8:00001100"):
            with self.subTest(old=old):
                with self.assertRaisesRegex(ValueError, "UNQUALIFIED_W8_HEAD"):
                    mod.plan(f"({old} 1)", {})
                missing = []
                edits = mod.plan(f"({old} 1)", {}, legacy_heads={},
                                 unresolved=missing)
                self.assertEqual(edits, [])
                self.assertEqual(missing, [(1, old)])

    def test_legacy_audit_checks_real_ukr_si_source_without_invented_w8(self):
        # #5872 не має позначати будь-який файл із namespaced-symbol
        # або довільною формою LAMBDA як невдалу міграцію старого байта.
        for path in ("lib/si-derived.lisp", "lib/repl-core.lisp"):
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                unproved = []
                edits = mod.plan(source, {}, legacy_heads={}, unresolved=unproved)
                self.assertEqual(edits, [])
                self.assertEqual(unproved, [])

    def test_unqualified_eight_bit_head_never_infers_d8(self):
        for source in ("(00100111 evaluator-fallback expression)",
                       "(00000101 x)", "(00000001 (car x))", "(11110001 x)"):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "UNQUALIFIED_W8_HEAD"):
                    self.rewrite(source)

    def test_ukrainian_decimal_comma_is_one_numeric_operand(self):
        # Перевірка сканера, НЕ доказ виконання арифметики SENS/D24+.
        source = "(додати 3,14 -7,25)\n"
        self.assertEqual(self.rewrite(source), source)
        for invalid in ("(додати 1,2,3 4)", "(додати число,інше 0)"):
            with self.subTest(source=invalid):
                with self.assertRaises(ValueError):
                    self.rewrite(invalid)

    def test_quoted_eight_bit_is_data_not_a_call(self):
        for source in ("'(00000101 x)", "(як-є (00000101 x))", "('00000101 x)"):
            self.assertEqual(self.rewrite(source), source)

    def test_batch_preflight_prevents_partial_write(self):
        with tempfile.TemporaryDirectory() as folder:
            good, bad = Path(folder) / "good.lisp", Path(folder) / "bad.lisp"
            good.write_text("(car x)\n", encoding="utf-8")
            bad.write_text("(00000101 x)\n", encoding="utf-8")
            mod.main([str(good)])
            self.assertEqual(good.read_text(encoding="utf-8"), "(car x)\n")
            with self.assertRaisesRegex(ValueError, "UNQUALIFIED_W8_HEAD"):
                mod.main(["--write", str(good), str(bad)])
            self.assertEqual(good.read_text(encoding="utf-8"), "(car x)\n")

    def test_write_is_ukrainian_and_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.lisp"
            path.write_text("(car (cdr x))\n", encoding="utf-8")
            mod.main(["--write", str(path)])
            self.assertEqual(path.read_text(encoding="utf-8"), "(перше (решта x))\n")
            mod.main(["--write", str(path)])
            self.assertEqual(path.read_text(encoding="utf-8"), "(перше (решта x))\n")


if __name__ == "__main__":
    unittest.main()
