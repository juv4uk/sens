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
        self.module = load_checker()
        for rel in self.module.CORE:
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(MAIN_OK if rel.endswith("/main.rs") else "", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_real_shape_passes(self) -> None:
        self.assertEqual(self.module.check(self.root), [])

    def test_missing_one_required_core_file_fails_closed(self) -> None:
        missing = self.module.CORE[2]
        (self.root / missing).unlink()
        problems = self.module.check(self.root)
        self.assertTrue(any(problem.startswith("J0:") and missing in problem
                            for problem in problems), problems)

    def test_symlink_required_core_file_fails_closed(self) -> None:
        linked = self.module.CORE[2]
        path = self.root / linked
        target = self.root / "outside-core.rs"
        target.write_text("", encoding="utf-8")
        path.unlink()
        path.symlink_to(target)
        problems = self.module.check(self.root)
        self.assertTrue(any(problem.startswith("J0:") and linked in problem
                            for problem in problems), problems)

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

    def test_zig_corridor_lisp_bytes_pass(self) -> None:
        """Opaque .lisp over sterile Zig byte carrier is legal (not read_to_string)."""
        p = self.root / "crates/sens-cli/src/zig_transport.rs"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "// lib/linter.lisp exact bytes via Zig ABI; no Rust include_str\n"
            "fn linter_source_bytes() -> Result<Vec<u8>, String> {\n"
            "    asset_ffi::sens_zig_linter_bytes_copy(...)\n"
            "}\n",
            encoding="utf-8",
        )
        problems = self.module.check(self.root)
        self.assertEqual(problems, [], problems)

    def test_extension_constant_only_passes(self) -> None:
        p = self.root / "crates/sens/src/source_words.rs"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            'pub const CANONICAL_SOURCE_EXTENSION: &str = ".lisp";\n',
            encoding="utf-8",
        )
        self.assertEqual(self.module.check(self.root), [])


if __name__ == "__main__":
    unittest.main()
