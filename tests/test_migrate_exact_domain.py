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

    def test_quoted_head_is_data_and_cannot_be_rewritten(self):
        source = "('car x)\n'(00100111 x)\n(quote (00100111 x))\n"
        self.assertEqual(
            self.rewrite(source),
            "('car x)\n'(00100111 x)\n(001 (00100111 x))\n",
        )
        # Цитована W8-голова не є виконуваною навіть у режимі запису.
        mod.plan(source, self.surfaces, self.legacy, reject_unmapped_w8=True)

    def test_unknown_eight_bit_executable_head_blocks_write(self):
        source = "(00100111 evaluator-fallback expression)\n"
        self.assertEqual(mod.plan(source, self.surfaces, self.legacy), [])
        with self.assertRaisesRegex(ValueError, "неоднозначна виконувана W8/D8"):
            mod.plan(source, self.surfaces, self.legacy, reject_unmapped_w8=True)

    def test_entire_batch_is_preflighted_before_first_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.lisp"
            second = Path(temporary) / "second.lisp"
            first.write_text("(car x)\n", encoding="utf-8")
            second.write_text("(00100111 x)\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "неоднозначна виконувана W8/D8"):
                mod.prepare_batch([first, second], self.surfaces, self.legacy, for_write=True)
            self.assertEqual(first.read_text(encoding="utf-8"), "(car x)\n")
            self.assertEqual(second.read_text(encoding="utf-8"), "(00100111 x)\n")

    def test_old_byte_requires_source_era_certificate(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "before.lisp"
            path.write_text("(00000101 x)\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "епоху джерела"):
                mod.prepare_batch([path], self.surfaces, self.legacy, for_write=True)
            staged = mod.prepare_batch(
                [path], self.surfaces, self.legacy,
                for_write=True, legacy_source_era_proved=True,
            )
            mod.write_batch(staged)
            self.assertEqual(path.read_text(encoding="utf-8"), "(100 x)\n")

    def test_stale_source_blocks_whole_batch_before_any_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.lisp"
            second = Path(temporary) / "second.lisp"
            first.write_text("(car x)\n", encoding="utf-8")
            second.write_text("(quote x)\n", encoding="utf-8")
            staged = mod.prepare_batch([first, second], self.surfaces, self.legacy, for_write=True)
            second.write_text("(quote y)\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "змінилося після планування"):
                mod.write_batch(staged)
            self.assertEqual(first.read_text(encoding="utf-8"), "(car x)\n")
            self.assertEqual(second.read_text(encoding="utf-8"), "(quote y)\n")

    def test_unbalanced_source_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unterminated list"):
            mod.plan("(car x", self.surfaces, self.legacy)

    def test_unknown_heads_are_left_for_semantic_review(self):
        source = """(user-defined x)
"""
        self.assertEqual(mod.plan(source, self.surfaces, self.legacy), [])

    def test_legacy_list_successor_is_not_narrowed_into_nonadmitted_d4(self):
        source = "(00100111 evaluator-fallback expression)\n"
        self.assertEqual(mod.plan(source, self.surfaces, self.legacy), [])


if __name__ == "__main__":
    unittest.main()
