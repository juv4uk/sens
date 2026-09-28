#!/usr/bin/env python3
"""Контракт генератора workload для #1567."""

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "numeric_buffer_map.py"
SPEC = importlib.util.spec_from_file_location("numeric_buffer_map", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class NumericBufferMapProgramTests(unittest.TestCase):
    def test_program_uses_only_bare_sens_and_checks_last_mapped_element(self):
        source, expected = MODULE.program_for(3)

        self.assertEqual(expected, "1")
        self.assertIn("(01011001", source)
        self.assertIn("(00001000 (x) (00001100 x 1))", source)
        self.assertIn("#i32(0 0 0)", source)
        self.assertIn("01011000", source)
        self.assertIn(" 2)", source)
        self.assertNotIn("numeric-buffer-map", source)
        self.assertNotIn("lambda", source)


if __name__ == "__main__":
    unittest.main()
