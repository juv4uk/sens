#!/usr/bin/env python3
"""Регресії старих Python-команд: жодної фізичної публікації SENS.

Це перевірка межі Zig/T5M, не імітація семантики обчислювача.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / "tests/fixtures/migration-d4-selector-cohort/caar"
PHYSICAL = VIEW.with_suffix(".sens")
TYPED = ROOT / "scripts/sens_typed_program.py"
SPACED = ROOT / "scripts/sens_view.py"


def call(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT, capture_output=True, text=True, timeout=20,
    )


class RetiredPythonSensEmissionTests(unittest.TestCase):
    def test_spaced_view_parse_never_publishes_physical_sens(self):
        before = PHYSICAL.read_bytes()
        with tempfile.TemporaryDirectory(prefix="sens-retired-view-") as temp:
            out = Path(temp) / "unexpected.sens"
            result = call(SPACED, "parse", str(VIEW), "--out", str(out))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("LEGACY_PYTHON_T5M_PUBLICATION_DISABLED", result.stderr)
            self.assertFalse(out.exists())
        self.assertEqual(PHYSICAL.read_bytes(), before)

    def test_old_typed_emitter_never_publishes_physical_sens(self):
        before = PHYSICAL.read_bytes()
        with tempfile.TemporaryDirectory(prefix="sens-retired-typed-") as temp:
            typed = Path(temp) / "example.typed"
            typed.write_text("D2 10\nD3 000\nD2 00\n", encoding="utf-8")
            out = Path(temp) / "unexpected.sens"
            result = call(TYPED, "emit", str(typed), str(out))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("LEGACY_PYTHON_T5M_PUBLICATION_DISABLED", result.stderr)
            self.assertFalse(out.exists())
        self.assertEqual(PHYSICAL.read_bytes(), before)

    def test_wire_reads_current_t5m_without_writing(self):
        expected = VIEW.read_text(encoding="ascii")
        before = PHYSICAL.read_bytes()
        result = call(TYPED, "wire", str(PHYSICAL))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, expected)
        self.assertEqual(PHYSICAL.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
