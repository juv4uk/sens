#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
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

    def test_local_shadowing_does_not_silently_become_domain_call(self):
        for source in (
            "(lambda (car) (car x))",
            "(0010 (CAR) (CAR x))",
            "(let ((car value)) (car x))",
            "(let* ((quote value)) (quote x))",
            "(letrec ((car (lambda (x) x))) (car x))",
            "(001000 ((перше value)) (перше x))",
            "(define car (lambda (x) x))",
            "(0011 (CAR x) (CAR x))",
            "((lambda (car) (car x)) y)",
            "(defmacro rewrite (car) (car x))",
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "scope|binder|зв'язування|перетинається"):
                    self.rewrite(source)

    def test_unrelated_binders_and_quoted_shadow_names_are_safe(self):
        self.assertEqual(
            self.rewrite("(lambda (value) (car value))"),
            "(0010 (value) (100 value))",
        )
        self.assertEqual(
            self.rewrite("'(lambda (car) (car x))\n(car x)"),
            "'(lambda (car) (car x))\n(100 x)",
        )
        self.assertEqual(
            self.rewrite("(quote (let ((car x)) (car x)))\n(car x)"),
            "(001 (let ((car x)) (car x)))\n(100 x)",
        )

    def test_unbalanced_source_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unterminated list"):
            mod.plan("(car x", self.surfaces, self.legacy)

    def test_unknown_heads_are_left_for_semantic_review(self):
        source = """(user-defined x)
"""
        self.assertEqual(mod.plan(source, self.surfaces, self.legacy), [])

    def test_table_migration_blocks_nonexact_duplicate_or_missing_d3_rows(self):
        # Only migrator/authority integrity: semantic verdicts remain SENS-owned.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            required = (
                "knowledge/d1-d9-foundation.json",
                "knowledge/sens8-current-coverage-v1.json",
                "lib/domains/d3.lisp",
                "lib/domains/d4.lisp",
            )
            for rel in required:
                destination = root / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / rel).read_bytes())
            d3 = root / "lib/domains/d3.lisp"
            pristine = d3.read_text(encoding="utf-8")
            self.assertIn("(100 (ук", pristine)
            for label, changed in (
                ("extra-bit", pristine.replace("(100 (ук", "(1000 (ук", 1)),
                ("duplicate", pristine.replace("(101 (ук", "(100 (ук", 1)),
                ("missing", "".join(
                    line for line in pristine.splitlines(keepends=True)
                    if not line.lstrip().startswith("(100 ")
                )),
            ):
                with self.subTest(case=label):
                    d3.write_text(changed, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "D3:"):
                        mod.load_authority(root)
            d3.write_text(pristine, encoding="utf-8")
            self.assertEqual(mod.load_authority(root), (self.surfaces, self.legacy))

    def test_historical_d3_successor_requires_exact_width_and_proved_role(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            required = (
                "knowledge/d1-d9-foundation.json",
                "knowledge/sens8-current-coverage-v1.json",
                "lib/domains/d3.lisp",
                "lib/domains/d4.lisp",
            )
            for rel in required:
                destination = root / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / rel).read_bytes())
            path = root / "knowledge/sens8-current-coverage-v1.json"
            original = json.loads(path.read_text(encoding="utf-8"))
            for candidate in ("D3:1001 CAR", "D3:100 WRONG", "D3:100 CAR extra"):
                with self.subTest(target=candidate):
                    changed = json.loads(json.dumps(original))
                    row = next(row for row in changed["rows"]
                               if row["legacy_code"] == "00000101")
                    row["current_target"] = candidate
                    path.write_text(json.dumps(changed), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "historical 00000101"):
                        mod.load_authority(root)

    def test_legacy_list_successor_is_not_narrowed_into_nonadmitted_d4(self):
        source = "(00100111 evaluator-fallback expression)\n"
        self.assertEqual(mod.plan(source, self.surfaces, self.legacy), [])


if __name__ == "__main__":
    unittest.main()
