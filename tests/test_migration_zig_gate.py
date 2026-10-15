#!/usr/bin/env python3
"""Fail-closed regression for the migration \u2194 Zig preparation gate."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migration-zig-gate.py"


def load():
    spec = importlib.util.spec_from_file_location("migration_zig_gate", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class MigrationZigGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load()

    def test_zig_pin_matches_0160(self) -> None:
        report = self.mod.check_zig_pin()
        self.assertEqual(report["status"], "PASS")
        self.assertIn("0.16.0", report["detail"])

    def test_self_test_passes_without_zig_binary(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--self-test"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("verdict=SELF_TEST_ONLY", completed.stdout)
        self.assertNotIn("verdict=PASS", completed.stdout)

    def test_self_test_report_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "gate.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--self-test",
                    "--report",
                    str(report_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            data = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(data["schema"], "sens-migration-zig-gate/v1")
            self.assertEqual(data["verdict"], "SELF_TEST_ONLY")
            self.assertIs(data["transport_verified"], False)
            self.assertEqual(data["scope"], "SELF_TEST_NOT_PHYSICAL")
            self.assertEqual(data["zig_pin"], "0.16.0")
            self.assertIn("zig-is-turnstile-not-registry", data["axioms"])
            steps = {s["step"]: s["status"] for s in data["steps"]}
            self.assertEqual(steps.get("zig-pin"), "PASS")
            self.assertEqual(steps.get("ci_zig_purity"), "PASS")
            self.assertEqual(steps.get("test_zig_codec_bridge"), "SKIP")


if __name__ == "__main__":
    unittest.main(verbosity=2)
