#!/usr/bin/env python3
"""Fail-closed: sens-rust-zig-corridor-guard.yml must run the full sterile set.

Owner rule (#5777/#5779): Rust\u2194SENS crosses ONLY the sterile Zig corridor.
The manual guard must exercise sterile routes, host-neutral R5, host coverage,
and axiom binding \u2014 the same four guards migration-zig-gate and release-preflight
require. A thinner workflow would be an unnamed gap (S2).
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sens-rust-zig-corridor-guard.yml"

# Exact guard scripts the owner rule demands on the corridor path.
REQUIRED_GUARDS = (
    "check_sterile_zig_corridor.py",
    "check_rust_sens_zig_corridor.py",
    "check_rust_sens_corridor_coverage.py",
    "check_corridor_axiom_binding.py",
)


class SensRustZigCorridorGuardWorkflowTests(unittest.TestCase):
    def test_workflow_runs_full_sterile_corridor_set(self) -> None:
        self.assertTrue(WORKFLOW.is_file(), "sens-rust-zig-corridor-guard.yml missing")
        yml = WORKFLOW.read_text(encoding="utf-8")
        for guard in REQUIRED_GUARDS:
            self.assertIn(
                guard,
                yml,
                f"corridor-guard workflow must invoke {guard} "
                "(Rust\u2194SENS only via sterile Zig corridor)",
            )
        # Negative-control unit tests for each guard must stay on the path.
        for test_mod in (
            "test_sterile_zig_corridor",
            "test_check_rust_sens_zig_corridor",
            "test_check_rust_sens_corridor_coverage",
            "test_check_corridor_axiom_binding",
        ):
            self.assertIn(
                test_mod,
                yml,
                f"corridor-guard workflow must run negative controls for {test_mod}",
            )
        self.assertIn("workflow_dispatch", yml)
        self.assertNotIn("push:", yml.split("on:")[1].split("jobs:")[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
