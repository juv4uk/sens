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
        (self.root / "Cargo.toml").write_text(
            '[workspace]\nmembers = ["crates/sens"]\n', encoding="utf-8")
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

    def test_physical_t5m_execution_entry_must_not_decode_in_rust(self) -> None:
        source = self.root / "crates/sens/src/binary_execution.rs"
        source.write_text(
            "pub fn decode(physical: &[u8]) { decode_ternary_words(physical); }\n"
            "pub fn eval_t5_program(physical: &[u8]) { decode(physical); }\n",
            encoding="utf-8",
        )

        problems = self.module.check(self.root)

        self.assertTrue(any("I3:" in problem for problem in problems), problems)

    def test_include_within_crate_is_forbidden(self) -> None:
        (self.root / "crates/sens/src/lib.rs").write_text(
            'let s = include_str!("embedded.lisp");\n', encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_include_bytes_sens_is_forbidden(self) -> None:
        (self.root / "crates/sens/src/lib.rs").write_text(
            'let s = include_bytes!("../../../tests/fixture.sens");\n',
            encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_std_fs_read_project_sens_is_forbidden(self) -> None:
        (self.root / "crates/sens/src/lib.rs").write_text(
            'let s = std::fs::read("lib/binary.sens");\n', encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_repl_sources_are_outside_runtime_isolation_boundary(self) -> None:
        repl = self.root / "crates/sens-cli/src/repl"
        repl.mkdir(parents=True, exist_ok=True)
        (repl / "surface_catalog.rs").write_text(
            'const D1: &str = include_str!("../../../../lib/domains/d1.lisp");\n',
            encoding="utf-8",
        )
        runtime = self.root / "crates/sens/src/runtime.rs"
        runtime.write_text(
            'const CORE: &str = include_str!("../../../lib/core4.lisp");\n',
            encoding="utf-8",
        )

        problems = self.module.check(self.root)

        self.assertEqual(len(problems), 1, problems)
        self.assertIn("crates/sens/src/runtime.rs", problems[0])
        self.assertNotIn("repl", problems[0])

    def test_non_workspace_backup_crate_is_not_isolation_debt(self) -> None:
        backup = self.root / "crates/xtask.bak/src"
        backup.mkdir(parents=True)
        (backup / "checks.rs").write_text(
            'const DOC: &str = include_str!("../../../README.md");\n',
            encoding="utf-8",
        )

        self.assertEqual(self.module.check(self.root), [])


    def test_test_only_scopes_are_not_production_but_unknown_cfg_is_red(self) -> None:
        source = (
            'const FIRST: &str = include_str!("lib/core.lisp");\n'
            '// #[cfg(test)] mod fake { const X: &str = include_str!("lib/core.lisp"); }\n'
            'const GHOST: &str = r##"#[cfg(test)] mod fake { include_str!("lib/core.lisp"); }"##;\n'
            '#[cfg(test)] mod tests {\n'
            '   fn nested() { let _ = { include_str!("lib/core.lisp") }; }\n'
            '   fn project_read() { let _ = std::fs::read("lib/core.lisp"); }\n'
            '}\n'
            '#[cfg(test)] fn test_only() { let _ = include_bytes!("lib/core.sens"); }\n'
            '#[cfg(test)] const TEST_ONLY: &str = include_str!("lib/core.lisp");\n'
            '#[cfg(any(test, feature = "production"))] mod uncertain {\n'
            '  const X: &str = include_str!("lib/core.lisp");\n'
            '}\n'
            'const LAST: &[u8] = include_bytes!("lib/core.sens");\n'
        )
        (self.root / "crates/sens/src/lib.rs").write_text(
            source, encoding="utf-8")
        problems = self.module.check(self.root)
        self.assertEqual(len(problems), 3, problems)
        self.assertTrue(all("I1:" in p for p in problems))
        self.assertTrue(all("lib/core" in p for p in problems))

    def test_live_production_filesystem_read_survives_test_only_mask(self) -> None:
        (self.root / "crates/sens/src/lib.rs").write_text(
            '#[cfg(test)] mod tests { let x = fs::read("lib/core.lisp"); }\n'
            'fn production() { let y = std::fs::read_to_string("lib/core.lisp"); }\n',
            encoding="utf-8")
        problems = self.module.check(self.root)
        self.assertEqual(len(problems), 1, problems)
        self.assertTrue(problems[0].startswith("I2:"), problems)


if __name__ == "__main__":
    unittest.main()
