#!/usr/bin/env python3
"""Негативні свідки захисту повних machine-визначень SENS."""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "check-lisp-paren-balance.py"
CRITICAL = (
    pathlib.Path("lib/machine/admission/x86-64.lisp"),
    pathlib.Path("lib/machine/encoding/x86-64.lisp"),
    pathlib.Path("lib/machine/lowering/semantic-x86-64.lisp"),
)


def run_fixture(
    replacement: tuple[pathlib.Path, str] | None = None,
    missing: pathlib.Path | None = None,
) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="sens-machine-integrity-") as tmp:
        root = pathlib.Path(tmp)
        for relative in CRITICAL:
            source = ROOT / relative
            if not source.is_file():
                raise AssertionError(f"missing baseline fixture source: {relative}")
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        if replacement is not None:
            relative, text = replacement
            (root / relative).write_text(text, encoding="utf-8")
        if missing is not None:
            (root / missing).unlink()
        return subprocess.run(
            [sys.executable, str(GUARD), "--root", str(root), "--paths", "lib"],
            capture_output=True,
            text=True,
            check=False,
        )


class MachineIntegrityWitnesses(unittest.TestCase):
    def test_full_current_sources_pass(self) -> None:
        result = run_fixture()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_each_balanced_placeholder_rejected(self) -> None:
        for relative in CRITICAL:
            with self.subTest(path=str(relative)):
                result = run_fixture(replacement=(relative, "()\n"))
                self.assertNotEqual(result.returncode, 0, str(relative))
                self.assertIn("INTEGRITY-FAIL", result.stdout)

    def test_each_missing_authority_rejected(self) -> None:
        for relative in CRITICAL:
            with self.subTest(path=str(relative)):
                result = run_fixture(missing=relative)
                self.assertNotEqual(result.returncode, 0, str(relative))
                self.assertIn("mandatory machine authority file missing", result.stdout)

    def test_admission_intermediate_marker_rejected(self) -> None:
        source = (ROOT / CRITICAL[0]).read_text(encoding="utf-8")
        result = run_fixture(replacement=(CRITICAL[0], source + "\n; SEE_LOCAL_FIX_bad\n"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SEE_LOCAL_FIX_", result.stdout)


if __name__ == "__main__":
    unittest.main()
