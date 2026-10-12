#!/usr/bin/env python3
"""Witnesses for the workflow action/toolchain pin survey (informational)."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "audit-workflow-pins.py"
SPEC = importlib.util.spec_from_file_location("sens_audit_workflow_pins", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

SHA = "fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09"


def materialize(root: Path, workflows: dict[str, str]) -> Path:
    base = root / ".github" / "workflows"
    base.mkdir(parents=True, exist_ok=True)
    for name, body in workflows.items():
        (base / name).write_text(body, encoding="utf-8")
    return root


class AuditTests(unittest.TestCase):
    def test_classifies_pinned_floating_and_toolchain(self):
        body = (
            f"      - uses: actions/checkout@{SHA} # v5\n"
            "      - uses: actions/cache@v4\n"
            "      - uses: dtolnay/rust-toolchain@1.99.0\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = materialize(Path(tmp), {"ci.yml": body})
            rows = MODULE.scan(root)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["pinned_actions"], 1)
            self.assertEqual(row["floating_actions"], 1)
            self.assertEqual(row["toolchains"], ["1.99.0"])
            self.assertEqual(row["floating_refs"], ["actions/cache@v4"])

    def test_local_actions_ignored(self):
        body = "      - uses: ./.github/actions/x\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = materialize(Path(tmp), {"ci.yml": body})
            self.assertEqual(MODULE.scan(root), [])

    def test_strict_flags_gating_floating(self):
        body = "      - uses: actions/checkout@v5\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = materialize(Path(tmp), {"ci-hosted.yml": body})
            rows = MODULE.scan(root)
            self.assertEqual(rows[0]["gating_check"], "portable critical gates")

    def test_real_repo_scan_runs(self):
        rows = MODULE.scan(ROOT)
        self.assertTrue(rows)
        for row in rows:
            self.assertIn("workflow", row)


if __name__ == "__main__":
    unittest.main()
