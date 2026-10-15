#!/usr/bin/env python3
"""Fail-closed: zig-transport-gate.yml must require the full sterile migration gate.

The CI assertion of step names must match scripts/migration-zig-gate.py
REQUIRED_STEPS, including check_sterile_zig_corridor (Rust↔SENS only via Zig).
Derived from G6/S2: observable corridor evidence cannot be dropped from release
or migration preparation without an explicit named change.
"""
from __future__ import annotations

import re
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "migration-zig-gate.py"
WORKFLOW = ROOT / ".github" / "workflows" / "zig-transport-gate.yml"


class MigrationZigGateWorkflowTests(unittest.TestCase):
    def test_workflow_asserts_full_required_steps_including_sterile_corridor(self) -> None:
        module = runpy.run_path(str(GATE))
        required = list(module["REQUIRED_STEPS"])
        self.assertIn("check_sterile_zig_corridor", required)
        self.assertIn("check_rust_sens_zig_corridor", required)
        self.assertIn("check_corridor_axiom_binding", required)

        yml = WORKFLOW.read_text(encoding="utf-8")
        match = re.search(
            r'assert \[s\["step"\] for s in data\["steps"\]\] == \[(.*?)\]',
            yml,
            re.S,
        )
        self.assertIsNotNone(match, "zig-transport-gate.yml must assert gate step names")
        listed = re.findall(r'"([a-z0-9_-]+)"', match.group(1))
        self.assertEqual(
            listed,
            required,
            "CI step list drifted from migration-zig-gate REQUIRED_STEPS "
            "(sterile corridor must remain on the release/migration path)",
        )
        self.assertIn("check_sterile_zig_corridor", listed)
        self.assertIn("check_corridor_axiom_binding.py", yml)


if __name__ == "__main__":
    unittest.main(verbosity=2)
