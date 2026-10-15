#!/usr/bin/env python3
"""H2 native SENS executable provenance against Rust↔Zig corridor migration.

This suite verifies real file paths, executable bits and SHA stability.
It does NOT replace real Zig 0.16 native/independent C execution.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "zig-codecs" / "host-c" / "verify_h2_cross_host.py"
SPEC = importlib.util.spec_from_file_location("sens_h2_native_host", SOURCE)
assert SPEC is not None and SPEC.loader is not None
h2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(h2)


class ExactNativeSENSExecutor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sens-h2-native-executor-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.build = self.root / "target" / "debug"
        self.build.mkdir(parents=True)
        self.exe = self.build / "sens"
        self.exe.write_bytes(b"\x7fELF\x02SENS-ZIG-CORRIDOR")
        self.exe.chmod(0o755)
        self.good_sha = hashlib.sha256(self.exe.read_bytes()).hexdigest()

    def verify(self, path="target/debug/sens", expected=None):
        return h2.verify_native_host_artifact(self.root, path, expected)

    def reject(self, path="target/debug/sens", expected=None, reason="H2_NATIVE_EXECUTOR"):
        with self.assertRaisesRegex(h2.AuditFailure, reason):
            self.verify(path, expected)

    def test_regular_native_executable_matches_exact_digest(self):
        path, digest = self.verify(expected=self.good_sha)
        self.assertEqual(path, self.exe)
        self.assertEqual(digest, self.good_sha)

    def test_absolute_path_within_checkout_keeps_compatibility(self):
        path, digest = self.verify(str(self.exe), self.good_sha)
        self.assertEqual(path, self.exe)
        self.assertEqual(digest, self.good_sha)

    def test_mutated_executable_between_native_runs_is_rejected(self):
        self.verify(expected=self.good_sha)
        self.exe.write_bytes(self.exe.read_bytes() + b"\x01")
        self.reject(expected=self.good_sha, reason="expected_sha256=")

    def test_linked_parent_to_same_sha_is_rejected(self):
        alias = self.root / "alias-debug"
        alias.symlink_to(self.build, target_is_directory=True)
        self.assertEqual((alias / "sens").read_bytes(), self.exe.read_bytes())
        self.reject(str(alias / "sens"), reason="linked_component")

    def test_linked_executable_leaf_is_rejected(self):
        alias = self.build / "linked-sens"
        alias.symlink_to(self.exe)
        self.reject("target/debug/linked-sens", reason="linked_component")

    def test_noncanonical_dotdot_is_rejected(self):
        self.reject("target/debug/../debug/sens", reason="canonical_path")

    def test_absolute_path_outside_checkout_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="foreign-sens-host-") as tmp:
            foreign = Path(tmp) / "sens"
            foreign.write_bytes(self.exe.read_bytes())
            foreign.chmod(0o755)
            self.reject(str(foreign), reason="within_checkout")

    def test_relative_path_escaping_checkout_is_rejected(self):
        self.reject("../native-sens", reason="canonical_path")

    def test_absent_executable_is_rejected(self):
        self.exe.unlink()
        self.reject(reason="missing_or_nonexecutable")

    def test_nonexecutable_native_file_is_rejected(self):
        self.exe.chmod(0o644)
        self.reject(reason="missing_or_nonexecutable")


if __name__ == "__main__":
    unittest.main()
