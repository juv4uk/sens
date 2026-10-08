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

    def test_actual_machine_pair_schema_keys_are_data(self):
        old = (ROOT / "lib/machine/layout/pair-x86-64.lisp").read_text()
        self.assertIn("(car (offset-bytes 0)", old)
        changed = old.replace("(car (offset-bytes 0)", "(100 (offset-bytes 0)")
        changed = changed.replace("(cdr (offset-bytes 8)", "(011 (offset-bytes 8)")
        self.blocked(old, changed, "quoted/data atom")

    def test_actual_local_assoc_recursion_is_not_domain_d5_assoc(self):
        old = (ROOT / "scripts/build-inventory.lisp").read_text()
        self.assertIn("(00001001 assoc", old)
        self.assertIn("(t (assoc key (00000110 alist)))", old)
        changed = old.replace(
            "(t (assoc key (00000110 alist)))",
            "(t (11100 key (00000110 alist)))", 1,
        )
        self.blocked(old, changed, "locally bound callable")

    def test_actual_local_scan_is_not_domain_d6_scan(self):
        old = (ROOT / "scripts/semantic-authority-guard.lisp").read_text()
        self.assertIn("(00001001 scan", old)
        changed = old.replace("(scan (00000110 rows))", "(101111 (00000110 rows))")
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
