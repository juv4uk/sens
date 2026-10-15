#!/usr/bin/env python3
"""Controls for the Rust->project dependency ledger + burndown ratchet (#5779)."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "report_rust_project_deps.py"


def load():
    spec = importlib.util.spec_from_file_location("sens_rust_project_deps", CHECKER)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


class DepsLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        d = self.root / "crates/sens/src"
        d.mkdir(parents=True, exist_ok=True)
        (d / "lib.rs").write_text(
            'let m = include_str!("../../../lib/macro.lisp");\n'
            'let z = include_str!("../../.zig-version");\n', encoding="utf-8")
        self.m = load()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_scan_finds_project_dep_not_zig_pin(self) -> None:
        deps = self.m.scan(self.root)
        targets = [d["target"] for d in deps]
        self.assertIn("../../../lib/macro.lisp", targets)
        self.assertNotIn("../../.zig-version", targets)   # corridor pin is not a dep

    def test_check_passes_when_equal(self) -> None:
        import subprocess
        subprocess.run([sys.executable, str(CHECKER), str(self.root)], check=True)
        p = subprocess.run([sys.executable, str(CHECKER), str(self.root), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertIn("RUST_PROJECT_DEPS_OK", p.stdout)

    def test_check_fails_on_growth(self) -> None:
        import subprocess
        subprocess.run([sys.executable, str(CHECKER), str(self.root)], check=True)
        (self.root / "crates/sens/src/lib.rs").write_text(
            'let m = include_str!("../../../lib/macro.lisp");\n'
            'let f = include_str!("../../../lib/fs.lisp");\n', encoding="utf-8")
        p = subprocess.run([sys.executable, str(CHECKER), str(self.root), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertIn("RUST_PROJECT_DEPS_GREW", p.stdout)

    def test_burndown_retiring_a_dep_is_ok(self) -> None:
        import subprocess
        subprocess.run([sys.executable, str(CHECKER), str(self.root)], check=True)
        (self.root / "crates/sens/src/lib.rs").write_text(
            'let z = include_str!("../../.zig-version");\n', encoding="utf-8")
        p = subprocess.run([sys.executable, str(CHECKER), str(self.root), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertIn("retired", p.stdout)


if __name__ == "__main__":
    unittest.main()
