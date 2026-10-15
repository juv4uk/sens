#!/usr/bin/env python3
"""Controls for the release GO-gate aggregator (#4196)."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "release_go_gate.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_release_go_gate", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GoGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir(parents=True, exist_ok=True)
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write(self, name: str, rc: int, msg: str) -> None:
        (self.root / "scripts" / name).write_text(
            f"import sys\nprint({msg!r})\nsys.exit({rc})\n", encoding="utf-8")

    def test_all_go(self) -> None:
        for _, script, _ in self.module.GATES:
            self._write(Path(script).name, 0, "OK")
        proc = subprocess.run([sys.executable, str(CHECKER), str(self.root)],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("RELEASE_GATE_GO", proc.stdout)

    def test_one_red_is_no_go(self) -> None:
        for _, script, _ in self.module.GATES:
            self._write(Path(script).name, 0, "OK")
        self._write("check_rust_isolated_only_zig.py", 1, "RED")
        proc = subprocess.run([sys.executable, str(CHECKER), str(self.root)],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("RELEASE_GATE_NO_GO", proc.stdout)
        self.assertIn("rust-isolated", proc.stdout)

    def test_missing_script_is_unverified_not_pass(self) -> None:
        # only one gate present -> the rest are UNVERIFIED, never a fake PASS
        self._write("check_numeric_domain_exclusive.py", 0, "OK")
        proc = subprocess.run([sys.executable, str(CHECKER), str(self.root)],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("UNVERIFIED", proc.stdout)
        self.assertIn("RELEASE_GATE_PARTIAL", proc.stdout)


if __name__ == "__main__":
    unittest.main()
