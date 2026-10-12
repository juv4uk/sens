#!/usr/bin/env python3
"""Witnesses for the release-gate required-check resolver.

A check name is a job's ``name:`` when set, otherwise the job id. The guard must
fail closed when a required name resolves to no job or to more than one job.
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "check-required-checks.py"
SPEC = importlib.util.spec_from_file_location("sens_check_required_checks", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

VERIFY = "REQUIRED_CHECKS = ('alpha', 'beta')\n"


def materialize(root: Path, workflows: dict[str, str], verify: str = VERIFY) -> Path:
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / "verify_release_ci.py").write_text(verify, encoding="utf-8")
    base = root / ".github" / "workflows"
    base.mkdir(parents=True, exist_ok=True)
    for name, body in workflows.items():
        (base / name).write_text(body, encoding="utf-8")
    return root


class RequiredChecksTests(unittest.TestCase):
    def test_name_and_job_id_both_resolve(self):
        body = (
            "jobs:\n"
            "  beta:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps: []\n"
            "  gamma:\n"
            "    name: alpha\n"
            "    runs-on: ubuntu-latest\n"
            "    steps: []\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            _, problems, _ = MODULE.check(materialize(Path(tmp), {"ci.yml": body}))
            self.assertEqual(problems, [])

    def test_missing_required_blocks(self):
        body = "jobs:\n  beta:\n    runs-on: ubuntu-latest\n    steps: []\n"
        with tempfile.TemporaryDirectory() as tmp:
            _, problems, _ = MODULE.check(materialize(Path(tmp), {"ci.yml": body}))
            self.assertTrue(any("alpha" in p for p in problems), problems)

    def test_ambiguous_required_blocks(self):
        body = (
            "jobs:\n"
            "  a:\n    name: alpha\n    runs-on: ubuntu-latest\n"
            "  b:\n    name: alpha\n    runs-on: ubuntu-latest\n"
            "  beta:\n    runs-on: ubuntu-latest\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            _, problems, _ = MODULE.check(materialize(Path(tmp), {"ci.yml": body}))
            self.assertTrue(any("ambiguous" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
