#!/usr/bin/env python3
"""Негативні тести єдиної точнодоменної української проєкції."""
from __future__ import annotations
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check_alias_identity.py"


def load():
    spec = importlib.util.spec_from_file_location("sens_alias_identity", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AliasIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        folder = self.root / "lib/domains"
        folder.mkdir(parents=True)
        for width in range(1, 11):
            filename = f"d{width}.lisp"
            shutil.copyfile(ROOT / "lib/domains" / filename, folder / filename)
        self.checker = load()

    def rewrite(self, width, before, after):
        path = self.root / f"lib/domains/d{width}.lisp"
        source = path.read_text(encoding="utf-8")
        self.assertIn(before, source)
        path.write_text(source.replace(before, after, 1), encoding="utf-8")

    def test_actual_domains_have_unique_ukrainian_aliases(self):
        self.assertEqual(self.checker.check(self.root), [])

    def test_duplicate_uk_name_is_rejected(self):
        self.rewrite(3, "(010 (ук атом?)", "(010 (ук як-є)")
        issues = self.checker.check(self.root)
        self.assertTrue(any("(ук як-є)" in problem for problem in issues), issues)

    def test_duplicate_ukr_name_is_rejected(self):
        self.rewrite(3, "(010 (ук атом?) (укр атом?)",
                     "(010 (ук атом?) (укр як-є)")
        issues = self.checker.check(self.root)
        self.assertTrue(any("(укр як-є)" in problem for problem in issues), issues)

    def test_english_display_collisions_do_not_become_function_calls(self):
        # Збіги en у D2/D9 та D6/D8 не створюють адреси.
        self.assertEqual(self.checker.check(self.root), [])

    def test_missing_domain_is_rejected(self):
        (self.root / "lib/domains/d5.lisp").unlink()
        self.assertTrue(any("D5:" in item for item in self.checker.check(self.root)))

    def test_old_eight_bit_head_is_rejected(self):
        self.rewrite(3, "(001 (ук як-є)", "(00000001 (ук як-є)")
        self.assertTrue(any("ширина" in item for item in self.checker.check(self.root)))


if __name__ == "__main__":
    unittest.main()
