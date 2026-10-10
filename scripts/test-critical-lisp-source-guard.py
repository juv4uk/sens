#!/usr/bin/env python3
"""Negative mutation tests for the critical Lisp source integrity gate.

Each fixture is syntactically balanced but is a truncated placeholder. The
real repository guard must reject it by path-specific structure, not just by
paren balance.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "check-lisp-paren-balance.py"

CASES = (
    ("lib/machine/admission/x86-64.lisp", "; see next\n"),
    ("lib/machine/encoding/x86-64.lisp", "; PLACEHOLDER\n"),
    ("lib/machine/lowering/semantic-x86-64.lisp", "RESTORED_FULL_FILE_SEE_CD5C362\n"),
)


def main() -> int:
    failures: list[str] = []
    for relative_path, placeholder in CASES:
        with tempfile.TemporaryDirectory(prefix="sens-critical-source-") as directory:
            root = pathlib.Path(directory)
            fixture = root / relative_path
            fixture.parent.mkdir(parents=True, exist_ok=True)
            fixture.write_text(placeholder, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(GUARD),
                    "--root",
                    str(root),
                    "--paths",
                    relative_path,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 or "INTEGRITY-FAIL" not in result.stdout:
                failures.append(
                    f"{relative_path}: balanced placeholder was not rejected; "
                    f"exit={result.returncode}; stdout={result.stdout!r}; "
                    f"stderr={result.stderr!r}"
                )
            else:
                print(f"PASS: rejects truncated placeholder for {relative_path}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print(f"critical-source guard mutation self-test: PASS ({len(CASES)} mutations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
