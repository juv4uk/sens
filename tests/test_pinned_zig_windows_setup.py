"""Regression checks for the pinned Zig Windows build path."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / ".zig-version").read_text(encoding="utf-8").strip()
SCRIPT = (ROOT / "scripts" / "with-pinned-zig.ps1").read_text(encoding="utf-8")
BUILD_RS = (ROOT / "crates" / "wsm-guard-core" / "build.rs").read_text(encoding="utf-8")


class PinnedZigWindowsSetupTests(unittest.TestCase):
    def test_pin_is_a_stable_version_and_not_duplicated_in_installer(self):
        self.assertRegex(VERSION, r"^\d+\.\d+\.\d+$")
        self.assertIn('Get-Content -LiteralPath $versionFile -Raw', SCRIPT)
        self.assertNotIn('Set-EnvironmentVariable("ZIG"', SCRIPT)
        self.assertIn("ZIG=$env:ZIG", SCRIPT)

    def test_windows_archive_is_selected_from_official_index_and_hash_checked(self):
        self.assertIn("https://ziglang.org/download/index.json", SCRIPT)
        self.assertIn('["x86_64-windows"]', SCRIPT)
        self.assertIn("$asset.tarball -ne $expectedUri", SCRIPT)
        self.assertIn("Get-FileHash -LiteralPath $archive -Algorithm SHA256", SCRIPT)
        self.assertIn("$actualHash -ne $expectedHash", SCRIPT)
        self.assertIn("Expand-Archive -LiteralPath $archive", SCRIPT)

    def test_only_pinned_zig_is_passed_to_child_command(self):
        self.assertIn("if ($actualVersion -ne $version)", SCRIPT)
        self.assertIn("$env:ZIG = $zigExe", SCRIPT)
        self.assertIn('& $Command @CommandArgs', SCRIPT)
        self.assertIn("exit $LASTEXITCODE", SCRIPT)
        self.assertNotIn("setx path", SCRIPT.lower())

    def test_build_error_points_to_windows_helper_and_keeps_fail_closed_pin(self):
        self.assertIn("include_str!(\"../../.zig-version\")", BUILD_RS)
        self.assertIn("with-pinned-zig.ps1 cargo build", BUILD_RS)
        self.assertIn('assert_eq!(actual, pinned, "Guard source transport Zig version mismatch")', BUILD_RS)

    def test_msvc_archive_and_pic_flags_follow_target_platform(self):
        self.assertIn('if target_env == "msvc"', BUILD_RS)
        self.assertIn('"libsens_zig_guard_sources.lib"', BUILD_RS)
        self.assertIn('if target_os != "windows"', BUILD_RS)
        self.assertIn('command.arg("-fPIC")', BUILD_RS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
