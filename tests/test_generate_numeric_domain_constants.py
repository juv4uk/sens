#!/usr/bin/env python3
"""Механічний регресійний тест: чинний D12+ закон ≠ фізичний профіль Zig D24+."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_generator():
    path = SCRIPTS / "generate-numeric-domain-constants.py"
    spec = importlib.util.spec_from_file_location("sens_numeric_generator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class NumericGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()

    def test_current_d12_law_does_not_inherit_historical_d24_start(self):
        current = self.generator.read_contract()
        self.assertEqual(current["first"], 12)
        self.assertEqual(current["widths"], [12, 24, 48, 96, 192])
        self.assertEqual(current["physical_widths"], [24, 48, 96, 192])

    def test_generated_mechanism_mirrors_do_not_claim_d12_physical_support(self):
        current = self.generator.read_contract()
        rust = self.generator.rust(current)
        tooling = self.generator.python(current)
        self.assertIn("FIRST_NUMERIC_DOMAIN_WIDTH: u16 = 12;", rust)
        self.assertIn("FIRST_PHYSICAL_NUMERIC_WIDTH: u16 = 24;", rust)
        self.assertIn("FIRST_WIDTH = 12", tooling)
        self.assertIn("FIRST_PHYSICAL_WIDTH = 24", tooling)

    def test_zig_physical_profile_rejects_semantic_d12_promotion(self):
        current = self.generator.read_contract()
        source = self.generator.ZIG_OUT.read_text(encoding="utf-8")
        self.generator.validate_zig_profile(source, current["physical_widths"])
        mutated = source.replace(
            "24, 48, 96, 192", "12, 24, 48, 96, 192", 1
        )
        self.assertNotEqual(mutated, source)
        with self.assertRaisesRegex(ValueError, "Zig physical widths"):
            self.generator.validate_zig_profile(mutated, current["physical_widths"])

    def test_generated_outputs_match_current_contract(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "generate-numeric-domain-constants.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
