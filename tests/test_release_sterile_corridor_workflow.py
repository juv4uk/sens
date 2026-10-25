#!/usr/bin/env python3
"""Fail-closed: release workflows must run the full sterile Zig corridor set.

Owner rule (#5777/#5779): Rust↔SENS crosses ONLY the sterile Zig corridor.
Release GO (preflight + tagged release smoke) must exercise the same four
guards as migration-zig-gate: sterile routes, host-neutral R5, host coverage
(C1), and axiom binding — plus the published boundary map (#5779).
A thinner release path is an unnamed gap (S2/G6).
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / ".github" / "workflows" / "release-preflight.yml"
RELEASE = ROOT / ".github" / "workflows" / "release.yml"

REQUIRED_GUARDS = (
    "check_sterile_zig_corridor.py",
    "check_rust_sens_zig_corridor.py",
    "check_rust_sens_corridor_coverage.py",
    "check_corridor_axiom_binding.py",
    "report_rust_zig_sens_boundary.py",
)


class ReleaseSterileCorridorWorkflowTests(unittest.TestCase):
    def _assert_full_set(self, path: Path, label: str) -> None:
        self.assertTrue(path.is_file(), f"{label} missing")
        yml = path.read_text(encoding="utf-8")
        for guard in REQUIRED_GUARDS:
            self.assertIn(
                guard,
                yml,
                f"{label} must invoke {guard} "
                "(Rust↔SENS only via sterile Zig corridor before GO)",
            )

    def test_release_preflight_runs_full_sterile_corridor_set(self) -> None:
        self._assert_full_set(PREFLIGHT, "release-preflight.yml")
        yml = PREFLIGHT.read_text(encoding="utf-8")
        self.assertIn(
            'report_rust_zig_sens_boundary.py --out "$RUNNER_TEMP/rust-zig-sens-boundary.json"',
            yml,
            "the boundary report must not dirty the exact-SHA checkout before physical replay",
        )
        self.assertIn("migration-zig-gate.py --require-zig", yml)
        self.assertIn("test_check_rust_sens_corridor_coverage", yml)
        self.assertIn("test_rust_zig_sens_boundary", yml)

    def test_release_yml_runs_full_sterile_corridor_set(self) -> None:
        self._assert_full_set(RELEASE, "release.yml")
        yml = RELEASE.read_text(encoding="utf-8")
        self.assertIn("Sterile Zig corridor", yml)
        self.assertIn("migration-zig-gate.py --require-zig", yml)
        self.assertIn("test_rust_zig_sens_boundary", yml)


if __name__ == "__main__":
    unittest.main(verbosity=2)
