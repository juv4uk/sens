#!/usr/bin/env python3
"""Регресії статичної української проєкції, НЕ семантичний Python-oracle."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "result_status_d1_current", SCRIPTS / "test-result-status-d1-bitness.py"
)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = guard
SPEC.loader.exec_module(guard)


class ResultStatusCurrentSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "lib/result-status.lisp").read_text(encoding="utf-8")

    def test_real_ukrainian_lisp_source_and_all_current_widths(self):
        self.assertEqual(guard.check_status_text(self.source), [])
        for width in range(1, 11):
            with self.subTest(width=width):
                self.assertEqual(guard.check_domain(width), [])

    def test_old_width_and_host_truth_are_rejected_only_in_code(self):
        for bad, diagnostic in (("#d1:1", "застарілий літерал"),
                                ("NIL", "істинність хоста")):
            with self.subTest(bad=bad):
                changed = self.source.replace(
                    "(функція (предмет)", f"(функція (предмет) {bad}", 1
                )
                self.assertNotEqual(changed, self.source)
                self.assertIn(diagnostic, " ".join(guard.check_status_text(changed)))

    def test_quoted_protocol_data_and_comments_are_not_executable(self):
        example = self.source + (
            "\n; old #d1:1 NIL / description outside the program\n"
            "(визначити перевірити-цитату (як-є (NIL #d1:1 00001001)))\n"
        )
        self.assertEqual(guard.check_status_text(example), [])

    def test_legacy_executable_head_and_define_rejected(self):
        for bad, diagnostic in (
            ("(00001001 результат)", "сирий виконуваний"),
            ("(old-result-status результат)", "історична латинська голова"),
        ):
            with self.subTest(bad=bad):
                changed = self.source.replace(
                    "(функція (предмет)", f"(функція (предмет) {bad}", 1
                )
                self.assertIn(diagnostic, " ".join(guard.check_status_text(changed)))
        duplicate = self.source + "\n(визначити результат-стан (як-є ()))\n"
        self.assertIn("дубльоване", " ".join(guard.check_status_text(duplicate)))

    def test_no_claim_of_semantic_or_release_admission(self):
        from contextlib import redirect_stdout
        from io import StringIO
        buffer = StringIO()
        with redirect_stdout(buffer):
            self.assertEqual(guard.main(), 0)
        self.assertIn("SEMANTIC_UNVERIFIED", buffer.getvalue())
        self.assertNotIn("RELEASE_READY", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
