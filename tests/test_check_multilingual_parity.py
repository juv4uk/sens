#!/usr/bin/env python3
"""Регресія читання builtin count у чинній шапці довідника."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_multilingual_parity", ROOT / "scripts/check-multilingual-parity.py"
)
assert SPEC and SPEC.loader
parity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parity)


class RecordedBuiltinCountTests(unittest.TestCase):
    def test_reads_current_english_header_form(self):
        config = parity.GENERATED_TABLES[0]
        header = "**Builtin count:** 30 root builtins (down from 35)."

        self.assertEqual(
            parity.find_recorded_count(header, config["count_re"]),
            30,
        )

    def test_keeps_reading_existing_ukrainian_header_form(self):
        config = parity.GENERATED_TABLES[0]
        header = "**Всього:** 23 builtin'ів + 421 бібліотечних функцій"

        self.assertEqual(
            parity.find_recorded_count(header, config["count_re"]),
            23,
        )


if __name__ == "__main__":
    unittest.main()
