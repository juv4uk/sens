#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-to-sens-codes.py"
SPEC = importlib.util.spec_from_file_location("sens_migrator", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

FOUNDATION = ROOT / "knowledge" / "d1-d7-foundation.json"

class SensCodeMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data, _ = mod.load_foundation(FOUNDATION)
        cls.code_map = mod.build_map(data, ["D3", "D4", "D5", "D6"])

    def test_current_d3_authority_is_used(self):
        self.assertEqual(self.code_map["CAR"].bits, "100")
        self.assertEqual(self.code_map["CDR"].bits, "011")
        self.assertEqual(self.code_map["EQ"].bits, "101")
        self.assertEqual(self.code_map["COND"].bits, "110")

    def test_call_heads_are_rewritten(self):
        source = "(CONS (CAR x) (CDR y))\n"
        converted, hits, blocked = mod.rewrite(source, self.code_map)
        self.assertEqual(converted, "(111 (100 x) (011 y))\n")
        self.assertEqual(len(hits), 3)
        self.assertFalse(blocked)

    def test_non_head_symbols_are_not_rewritten(self):
        source = "(foo CAR CDR CONS)\n"
        converted, hits, blocked = mod.rewrite(source, self.code_map)
        self.assertEqual(converted, source)
        self.assertFalse(hits)
        self.assertFalse(blocked)

    def test_comments_strings_and_quoted_data_are_preserved(self):
        source = "; (CAR x)\n(foo \"CAR\")\n'(CAR (CDR x))\n(QUOTE (CAR x))\n"
        expected = "; (CAR x)\n(foo \"CAR\")\n'(CAR (CDR x))\n(001 (CAR x))\n"
        converted, hits, blocked = mod.rewrite(source, self.code_map)
        self.assertEqual(converted, expected)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].label, "QUOTE")
        self.assertFalse(blocked)

    def test_package_qualified_surface_is_preserved(self):
        source = "(CL:CAR x)\n"
        converted, hits, blocked = mod.rewrite(source, self.code_map)
        self.assertEqual(converted, source)
        self.assertFalse(hits)
        self.assertFalse(blocked)

    def test_shadowing_fails_closed(self):
        source = "(DEFUN CAR (x) x)\n(CAR y)\n"
        converted, hits, blocked = mod.rewrite(source, self.code_map)
        self.assertEqual(converted, source)
        self.assertFalse(hits)
        self.assertEqual(len(blocked), 1)

if __name__ == "__main__":
    unittest.main()
