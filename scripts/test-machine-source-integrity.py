#!/usr/bin/env python3
"""Negative witnesses for the critical machine-source integrity guard.

The #5423 forensics showed the critical machine sources
(`lib/machine/{admission,encoding,lowering}/`) were replaced by short,
*formally balanced* pointers that the old paren guard accepted. This test
builds an isolated temporary corpus from the current, real sources and then
mutates it. It proves the guard fails closed:

  * the untouched real corpus passes;
  * each critical source replaced by a balanced placeholder fails;
  * each critical source deleted fails;
  * a committed pointer marker appended to admission fails.

Run: python3 scripts/test-machine-source-integrity.py
"""
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

# The exact placeholder shapes observed in the #5423 git history, plus the
# bare balanced list. All are `scan()`-balanced, so only the structural
# integrity checks can reject them.
PLACEHOLDERS = (
    "SEE_LOCAL_FIX_B4j\n",
    "LOAD_FROM_FILE:/tmp/sem_join.lisp\n",
    "RESTORED_FULL_FILE_SEE_CD5C362\n",
    "; PLACEHOLDER\n",
    "; see next\n",
    "()\n",
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
            for placeholder in PLACEHOLDERS:
                with self.subTest(path=str(relative), placeholder=placeholder.strip() or "<empty>"):
                    result = run_fixture(replacement=(relative, placeholder))
                    self.assertNotEqual(result.returncode, 0, f"{relative} :: {placeholder!r}")
                    self.assertIn("INTEGRITY-FAIL", result.stdout)

    def test_each_missing_authority_rejected(self) -> None:
        for relative in CRITICAL:
            with self.subTest(path=str(relative)):
                result = run_fixture(missing=relative)
                self.assertNotEqual(result.returncode, 0, str(relative))
                self.assertIn("mandatory machine authority file missing", result.stdout)

    def test_admission_pointer_marker_rejected(self) -> None:
        source = (ROOT / CRITICAL[0]).read_text(encoding="utf-8")
        result = run_fixture(replacement=(CRITICAL[0], source + "\n; SEE_LOCAL_FIX_bad\n"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SEE_LOCAL_FIX_", result.stdout)


if __name__ == "__main__":
    unittest.main()
