#!/usr/bin/env python3
"""Regression: sterile Zig corridor contract stays fail-closed."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_sterile_zig_corridor.py"


class SterileZigCorridorTests(unittest.TestCase):
    def test_script_passes_on_tree(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("STERILE_ZIG_CORRIDOR_PASS", completed.stdout)

    def test_corridor_file_has_no_local_t5_codec(self) -> None:
        body = (ROOT / "crates/sens-cli/src/zig_corridor.rs").read_text(encoding="utf-8")
        self.assertIn("sens_zig_t5_decode_be3", body)
        self.assertIn("turnstile", body.lower())
        self.assertNotIn("PhysicalT5Program", body)
        self.assertNotIn("ternary_transport", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
