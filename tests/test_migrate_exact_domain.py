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

    def test_legacy_list_successor_is_not_narrowed_into_nonadmitted_d4(self):
        source = "(00100111 evaluator-fallback expression)\n"
        self.assertEqual(mod.plan(source, self.surfaces, self.legacy), [])


if __name__ == "__main__":
    unittest.main()
