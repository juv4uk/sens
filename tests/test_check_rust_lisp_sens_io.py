#!/usr/bin/env python3
"""Negative controls for the Rust .lisp/.sens I/O guard (no JSON path)."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_rust_lisp_sens_io.py"

MAIN_OK = """// physical .sens requires the Zig transport corridor; no Rust fallback
fn run() {
    let bytes = fs::read(filename);           // .sens as bytes
    let text = fs::read_to_string(lisp);      // .lisp as text
}
"""


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_rust_lisp_sens_io", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RustLispSensIoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        p = self.root / "crates/sens-cli/src/main.rs"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(MAIN_OK, encoding="utf-8")
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_real_shape_passes(self) -> None:
        self.assertEqual(self.module.check(self.root), [])

    def test_sens_as_text_is_blocked(self) -> None:
        p = self.root / "crates/sens-cli/src/main.rs"
        p.write_text("// .sens\nlet s = fs::read_to_string(sens);\n", encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_lisp_as_bytes_is_blocked(self) -> None:
        p = self.root / "crates/sens-cli/src/main.rs"
        p.write_text("// .lisp\nlet s = fs::read(lisp);\n", encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_json_on_path_is_blocked(self) -> None:
        p = self.root / "crates/sens-cli/src/main.rs"
        p.write_text("// .sens .lisp\nuse serde_json;\nlet b = fs::read(x);\n"
                     "let t = fs::read_to_string(y);\n", encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_missing_corridor_statement_is_blocked(self) -> None:
        p = self.root / "crates/sens-cli/src/main.rs"
        p.write_text("let b = fs::read(x); let t = fs::read_to_string(y);\n", encoding="utf-8")
        self.assertTrue(self.module.check(self.root))


if __name__ == "__main__":
    unittest.main()
