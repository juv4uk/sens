#!/usr/bin/env python3
"""Domain-ladder cutover authority witnesses (lane CI/TESTS, #5608).

Enforces, from repo state only and without guessing any semantics:

* the canonical domain-ladder guard still passes its own negative self-test
  (Rust/Python/C/Lisp old-identity controls);
* no workflow *invokes* a script path that does not exist (acceptance #3);
* the retired eight-bit identity guard is neither present nor referenced by any
  workflow (so a flat W8 identity path cannot be silently reintroduced).

Historical/provenance references (comments, trigger ``paths:`` filters, docs)
are deliberately NOT treated as invocations.
"""

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "check-domain-ladder-identity.py"
RETIRED_GUARD = "sid-binary-identity-guard.sh"
INVOKE = re.compile(r"(?:python3?|bash|sh)\s+([A-Za-z0-9_./-]+\.(?:py|sh))")
SCRIPT_ROOTS = ("scripts/", ".github/scripts/")


def workflow_files(root: Path = ROOT) -> list[Path]:
    return sorted((root / ".github" / "workflows").glob("*.yml"))


def broken_invocations(root: Path = ROOT) -> list[tuple[str, str]]:
    """Workflow script invocations whose target does not exist."""
    broken: list[tuple[str, str]] = []
    for path in workflow_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for target in sorted(set(INVOKE.findall(text))):
            if target.startswith(SCRIPT_ROOTS) and not (root / target).exists():
                broken.append((path.name, target))
    return broken


class CutoverAuthorityTests(unittest.TestCase):
    def test_guard_self_test_passes(self):
        result = subprocess.run(
            [sys.executable, str(GUARD), "--self-test"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_no_workflow_invokes_a_missing_script(self):
        self.assertEqual(broken_invocations(), [])

    def test_retired_eight_bit_guard_absent_and_unreferenced(self):
        self.assertFalse((ROOT / "scripts" / RETIRED_GUARD).exists())
        for path in workflow_files():
            self.assertNotIn(
                RETIRED_GUARD, path.read_text(encoding="utf-8", errors="ignore"), path.name
            )

    def test_detector_flags_a_missing_invocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / ".github" / "workflows"
            base.mkdir(parents=True)
            (base / "x.yml").write_text(
                "      run: python3 scripts/does-not-exist.py\n", encoding="utf-8"
            )
            self.assertTrue(broken_invocations(root))

    def test_detector_ignores_a_trigger_path_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / ".github" / "workflows"
            base.mkdir(parents=True)
            (base / "x.yml").write_text(
                "    paths:\n      - \"scripts/gone.py\"\n", encoding="utf-8"
            )
            self.assertEqual(broken_invocations(root), [])


if __name__ == "__main__":
    unittest.main()
