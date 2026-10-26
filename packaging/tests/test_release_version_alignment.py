#!/usr/bin/env python3
"""Regression: release version alignment gate stays fail-closed."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check-release-version-alignment.py"


def load():
    spec = importlib.util.spec_from_file_location("release_version_alignment", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class ReleaseVersionAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load()

    def test_audit_passes_on_current_tree(self) -> None:
        report = self.mod.audit()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["expected"], "0.42.1")
        self.assertEqual(len(report["crates"]), 7)

    def test_expected_tag_is_s_prefix(self) -> None:
        self.assertEqual(self.mod.TAG, "s0.42.1")

    def test_release_crates_list_is_stable(self) -> None:
        self.assertIn("sens-cli", self.mod.RELEASE_CRATES)
        self.assertIn("sens-wasm", self.mod.RELEASE_CRATES)

    def test_release_yml_runs_mechanical_gates(self) -> None:
        yml = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("check-release-version-alignment.py", yml)
        self.assertIn("check-release-pins.py", yml)

    def test_preflight_yml_runs_mechanical_gates(self) -> None:
        yml = (
            ROOT / ".github" / "workflows" / "release-preflight.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("check-release-version-alignment.py", yml)
        self.assertIn("check-release-pins.py", yml)


if __name__ == "__main__":
    unittest.main(verbosity=2)
