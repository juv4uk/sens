#!/usr/bin/env python3
"""Controls for the Rust-isolation guard (#5777/#5779)."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_rust_isolated_only_zig.py"

ISOLATED = """// only the Zig corridor
extern "C" { fn sens_zig_t5_encode_be3(); }
fn run() { let _ = sens_zig_t5_encode_be3; }
"""


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_rust_isolated_only_zig", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RustIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        d = self.root / "crates/sens/src"
        d.mkdir(parents=True, exist_ok=True)
        (d / "lib.rs").write_text(ISOLATED, encoding="utf-8")
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_isolated_passes(self) -> None:
        self.assertEqual(self.module.check(self.root), [])

    def test_include_project_source_is_blocked(self) -> None:
        (self.root / "crates/sens/src/lib.rs").write_text(
            'let c = include_str!("../../../language-contract.lisp");\n', encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_read_project_file_is_blocked(self) -> None:
        (self.root / "crates/sens/src/lib.rs").write_text(
            'let m = fs::read_to_string("lib/macro.lisp");\n', encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_include_within_crate_passes(self) -> None:
        (self.root / "crates/sens/src/lib.rs").write_text(
            'let s = include_str!("embedded.lisp");\n', encoding="utf-8")
        self.assertEqual(self.module.check(self.root), [])


if __name__ == "__main__":
    unittest.main()
