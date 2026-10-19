"""Regression checks for the pinned Zig Windows build path."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / ".zig-version").read_text(encoding="utf-8").strip()
SCRIPT = (ROOT / "scripts" / "with-pinned-zig.ps1").read_text(encoding="utf-8")
BUILD_RS = (ROOT / "crates" / "wsm-guard-core" / "build.rs").read_text(encoding="utf-8")
CLI_BUILD_RS = (ROOT / "crates" / "sens-cli" / "build.rs").read_text(encoding="utf-8")


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
        self.assertIn("$indexHash -ne $expectedHash", SCRIPT)
        self.assertIn("68659eb5f1e4eb1437a722f1dd889c5a322c9954607f5edcf337bc3684a75a7e", SCRIPT)
        self.assertIn("Expand-Archive -LiteralPath $archive", SCRIPT)

    def test_truncated_archive_is_rejected_before_extraction(self):
        self.assertIn('$expectedSize = [long]$asset.size', SCRIPT)
        self.assertIn('$actualSize = (Get-Item -LiteralPath $archive).Length', SCRIPT)
        self.assertIn('$actualSize -ne $expectedSize', SCRIPT)
        self.assertIn('Zig archive size mismatch:', SCRIPT)

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
        self.assertIn('"sens_zig_guard_sources.lib"', BUILD_RS)
        self.assertIn('if target_os != "windows"', BUILD_RS)
        self.assertIn('command.arg("-fPIC")', BUILD_RS)

    def test_msvc_builds_pass_cargo_target_to_both_zig_compilers(self):
        for source in (BUILD_RS, CLI_BUILD_RS):
            self.assertIn('env::var("CARGO_CFG_TARGET_ENV")', source)
            self.assertIn('env::var("CARGO_CFG_TARGET_ARCH")', source)
            self.assertIn('format!("{target_arch}-windows-msvc")', source)
            self.assertIn('.arg("-target")', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
