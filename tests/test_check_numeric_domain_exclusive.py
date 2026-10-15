#!/usr/bin/env python3
"""Controls for the numeric-domain-exclusive guard (#5789)."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_numeric_domain_exclusive.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_numeric_domain_exclusive", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class NumericDomainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "contracts").mkdir(parents=True, exist_ok=True)
        (self.root / "knowledge").mkdir(parents=True, exist_ok=True)
        (self.root / "crates/sens/src").mkdir(parents=True, exist_ok=True)
        (self.root / "research/zig-codecs/t5").mkdir(parents=True, exist_ok=True)
        (self.root / "contracts/numeric-domains-ratification.lisp").write_text(
            "owner-ratified arithmetic-exclusivity D(24 * 2^n) D24 D48 D96 D192\n", encoding="utf-8")
        (self.root / "knowledge/number-width-ratified.json").write_text(json.dumps({
            "status": "owner-ratified", "growth_law": "width(n) = 24 * 2^n",
            "ratified_prefix_bits": [24, 48, 96, 192], "first_width_bits": 24,
        }), encoding="utf-8")
        (self.root / "crates/sens/src/binary_number.rs").write_text(
            "// None is the historic/unqualified pathway\nnumeric_domain_width: Option<usize>,\n",
            encoding="utf-8")
        (self.root / "research/zig-codecs/t5/t5.zig").write_text(
            "fn encodeWidth(allocator, words, max_width: u8) // max_width = 10\n", encoding="utf-8")
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_real_shape_passes(self) -> None:
        self.assertEqual(self.module.check(self.root), [])

    def test_missing_exclusivity_law_is_blocked(self) -> None:
        p = self.root / "contracts/numeric-domains-ratification.lisp"
        p.write_text("owner-ratified D(24 * 2^n) D24 D48 D96 D192\n", encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_width_drift_is_blocked(self) -> None:
        p = self.root / "knowledge/number-width-ratified.json"
        p.write_text(json.dumps({"status": "owner-ratified", "growth_law": "width(n) = 16 * 2^n",
                                 "ratified_prefix_bits": [24, 48], "first_width_bits": 24}),
                     encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_d11_leak_is_blocked(self) -> None:
        p = self.root / "research/zig-codecs/t5/t5.zig"
        p.write_text("fn f(max_width: u8) // max_width = 10 ; D11 experiment\n", encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_no_d10_cap_is_blocked(self) -> None:
        p = self.root / "research/zig-codecs/t5/t5.zig"
        p.write_text("fn f() {}\n", encoding="utf-8")
        self.assertTrue(self.module.check(self.root))


if __name__ == "__main__":
    unittest.main()
