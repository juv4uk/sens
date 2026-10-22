#!/usr/bin/env python3
"""Read-only negative regressions for code-only Lisp migration safety."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "audit_lisp_migration_edits.py"
spec = importlib.util.spec_from_file_location("sens_migration_edit_safety", PATH)
mod = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class MigrationLexicalSafety(unittest.TestCase):
    def blocked(self, old, new, reason):
        with self.assertRaisesRegex(mod.Blocked, reason):
            mod.audit_edit(old, new)

    def test_d3_heads_are_allowed_only_in_real_code_position(self):
        witness = "(CAR (CDR x))"
        result = mod.audit_edit(witness, "(100 (011 x))")
        self.assertEqual(result["status"], "LEXICAL_CONTEXT_ONLY")
        self.assertEqual(result["semantic_parity"], "NOT_CHECKED")

    def test_ukrainian_heads_preserve_exact_d3_identity(self):
        result = mod.audit_edit("(CAR (CDR x))", "(перше (решта x))")
        self.assertEqual(result["status"], "LEXICAL_CONTEXT_ONLY")
        self.assertEqual(result["semantic_parity"], "NOT_CHECKED")

    def test_matching_width_is_not_matching_program(self):
        self.blocked("(CAR x)", "(011 x)", "call-head identity")
        self.blocked("(CAR x)", "(решта x)", "call-head identity")
        self.blocked("(CDR x)", "(100 x)", "call-head identity")
        self.blocked("(CAR x)", "(вигадана-операція x)", "call-head identity")

    def test_quoted_ukrainian_function_names_remain_data(self):
        self.blocked("'(CAR x)", "'(перше x)", "quoted/data")
        self.blocked("(як-є (перше x))", "(як-є (100 x))", "quoted/data")
        self.blocked("(визначити зразок (як-є (перше x)))",
                     "(визначити зразок (як-є (100 x)))", "quoted/data")

    def test_ukrainian_definition_and_binder_names_are_protected(self):
        for old, new in (
            ("(визначити перше (функція (x) (перше x)))",
             "(визначити перше (функція (x) (100 x)))"),
            ("(функція (перше) (перше x))",
             "(функція (перше) (100 x))"),
            ("(нехай ((перше x)) (перше y))",
             "(нехай ((перше x)) (100 y))"),
            ("(нехай-послідовно ((перше x)) (перше y))",
             "(нехай-послідовно ((перше x)) (100 y))"),
        ):
            with self.subTest(source=old):
                self.blocked(old, new, "locally bound callable")

    def test_actual_machine_pair_schema_keys_are_data(self):
        old = (ROOT / "lib/machine/layout/pair-x86-64.lisp").read_text()
        self.assertIn("((перше (offset-bytes 0)", old)
        changed = old.replace("((перше (offset-bytes 0)", "((100 (offset-bytes 0)")
        changed = changed.replace("((решта (offset-bytes 8)", "((011 (offset-bytes 8)")
        self.blocked(old, changed, "quoted/data atom")

    def test_actual_local_map_recursion_is_not_domain_d5_assoc(self):
        # Чинний виконуваний файл, не колишній build-inventory.lisp:
        # його вміст нині лише якір, а не визначення рекурсивного пошуку.
        # D5:11100 ASSOC не має права заміняти власне D4 визначення.
        old = (ROOT / "lib/persistent-map.lisp").read_text(encoding="utf-8")
        recursive_call = "(мапа-отримати ключ (решта записи))"
        self.assertIn("(визначити мапа-отримати", old)
        self.assertIn(recursive_call, old)
        self.assertNotIn("(визначити знайти-за-ключем мапа-отримати)", old)
        changed = old.replace(
            recursive_call,
            "(11100 ключ (решта записи))", 1,
        )
        self.assertNotEqual(changed, old, "мутація мусить змінювати живий виклик")
        self.blocked(old, changed, "locally bound callable")

    def test_actual_local_recursion_is_not_domain_d6_scan(self):
        # Перевіряємо актуальну власну функцію SENS, а не вилучений
        # історичний код semantic-authority-guard.
        old = (ROOT / "scripts/gen-functions.lisp").read_text(encoding="utf-8")
        self.assertIn("(визначити видати", old)
        local_call = "(видати (решта записи))"
        self.assertIn(local_call, old)
        changed = old.replace(local_call, "(101111 (решта записи))", 1)
        self.blocked(old, changed, "locally bound callable")

    def test_lambda_parameter_shadows_builtin_name(self):
        old = "(00001000 (scan) (scan 000))"
        self.blocked(old, "(00001000 (scan) (101111 000))", "locally bound callable")

    def test_quoted_function_words_must_not_be_translated(self):
        self.blocked("(00000001 (CAR x))", "(00000001 (100 x))", "quoted/data")
        self.blocked("'(CAR x)", "'(100 x)", "quoted/data")

    def test_argument_and_string_rewrites_are_not_code_only(self):
        self.blocked("(CAR x)", "(CAR 100)", "non-head atom")
        self.blocked('(CAR "x")', '(CAR "y")', "string payload")

    def test_structural_edits_fail_closed(self):
        self.blocked("(CAR x)", "(CAR x y)", "structure or argument")
        self.blocked("(CAR x)", "(CAR)", "structure or argument")

    def test_unchanged_quoted_data_and_current_source_allowed(self):
        src = "(00001001 item (00000001 (fields ((car 0) (cdr 8)))))"
        self.assertEqual(mod.audit_edit(src, src)["status"], "LEXICAL_CONTEXT_ONLY")
        self.assertEqual(mod.audit_edit("(100 (011 x))", "(100 (011 x))")["forms"], 1)

    def test_cli_blocks_and_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            before = Path(directory) / "old.lisp"
            after = Path(directory) / "new.lisp"
            before.write_text("(00000001 (car x))")
            after.write_text("(00000001 (100 x))")
            result = subprocess.run(
                [sys.executable, str(PATH), "--before", str(before), "--after", str(after)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn('"status": "BLOCKED"', result.stdout)


if __name__ == "__main__":
    unittest.main()
