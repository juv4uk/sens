#!/usr/bin/env python3
"""H2 compares actual Zig archive/C executable bytes, not only H1 stdout.

These are physical-provenance unit tests. Native Zig 0.16/C + SENS parity
remains the responsibility of the existing H1/H2 real --run path.
"""
import hashlib
import os
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research" / "zig-codecs" / "host-c" / "verify_h2_cross_host.py"
SPEC = importlib.util.spec_from_file_location("h2_artifact_provenance", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
h2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(h2)


class H2ActualZigArtifactBytes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sens-h2-proof-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.out = self.root / "real"
        self.out.mkdir()
        self.exe = self.out / "sens-c-host-d3"
        self.archive = self.out / "libsens_zig_transport.a"
        self.exe.write_bytes(b"\x7fELF\x02C-ZIG-H1")
        self.archive.write_bytes(b"!<arch>\nZIG")
        self.proof = {
            "c_binary_sha256": hashlib.sha256(self.exe.read_bytes()).hexdigest(),
            "zig_archive_sha256": hashlib.sha256(self.archive.read_bytes()).hexdigest(),
        }

    def blocked(self, directory=None, proof=None, reason="H2_H1_ARTIFACT"):
        with self.assertRaisesRegex(h2.AuditFailure, reason):
            h2.verify_h1_artifact_bytes(
                directory if directory is not None else self.out,
                proof if proof is not None else self.proof)

    def test_valid_artifacts_match_two_independent_sha_digests(self):
        result = h2.verify_h1_artifact_bytes(self.out, self.proof)
        self.assertEqual(result["sens-c-host-d3"], self.proof["c_binary_sha256"])
        self.assertEqual(result["libsens_zig_transport.a"],
                         self.proof["zig_archive_sha256"])

    def test_c_executable_modified_after_h1_report_is_rejected(self):
        self.exe.write_bytes(self.exe.read_bytes() + b"\x00")
        self.blocked(reason="expected_sha256=")

    def test_zig_archive_modified_after_h1_report_is_rejected(self):
        self.archive.write_bytes(self.archive.read_bytes() + b"\x01")
        self.blocked(reason="expected_sha256=")

    def test_replayed_c_binary_sha_of_other_bytes_is_rejected(self):
        old = dict(self.proof, c_binary_sha256="0" * 64)
        self.blocked(proof=old, reason="expected_sha256=")

    def test_replayed_zig_archive_sha_of_other_bytes_is_rejected(self):
        old = dict(self.proof, zig_archive_sha256="0" * 64)
        self.blocked(proof=old, reason="expected_sha256=")

    def test_missing_archive_is_rejected(self):
        self.archive.unlink()
        self.blocked(reason="missing_or_nonregular")

    def test_missing_c_executable_is_rejected(self):
        self.exe.unlink()
        self.blocked(reason="missing_or_nonregular")

    def test_alias_directory_cannot_authenticate_same_bytes(self):
        alias = self.root / "linked"
        alias.symlink_to(self.out, target_is_directory=True)
        self.assertEqual((alias / self.exe.name).read_bytes(), self.exe.read_bytes())
        self.blocked(directory=alias, reason="symlink_component")

    def test_alias_executable_leaf_cannot_authenticate_same_bytes(self):
        self.exe.rename(self.out / "actual-executable")
        self.exe.symlink_to(self.out / "actual-executable")
        self.blocked(reason="symlink_component")

    def test_noncanonical_parent_segment_rejected(self):
        path = self.out / ".." / self.out.name
        self.blocked(directory=path, reason="absolute_canonical_output")

    def test_relative_output_directory_rejected(self):
        self.blocked(directory=Path("relative-build"), reason="absolute_canonical_output")

    def test_non_sha_digest_claim_rejected(self):
        bad = dict(self.proof, zig_archive_sha256="yes")
        self.blocked(proof=bad, reason="valid_reported_SHA")

    def test_large_zig_archive_is_streamed_from_open_inode(self):
        self.archive.write_bytes(b"!<arch>\n" + b"z" * (2 * 1024 * 1024 + 5))
        self.proof["zig_archive_sha256"] = hashlib.sha256(
            self.archive.read_bytes()).hexdigest()
        self.assertEqual(h2.verify_h1_artifact_bytes(self.out, self.proof)[
            "libsens_zig_transport.a"], self.proof["zig_archive_sha256"])

    def test_hardlinked_c_binary_is_rejected_even_when_sha_matches(self):
        os.link(self.exe, self.root / "hardlink-c")
        self.blocked(reason="unique_nonempty_regular_file")

    def test_hardlinked_zig_archive_is_rejected_even_when_sha_matches(self):
        os.link(self.archive, self.root / "hardlink-zig")
        self.blocked(reason="unique_nonempty_regular_file")

    def test_fifo_is_not_a_trusted_elf_and_does_not_block_on_open(self):
        self.exe.unlink()
        os.mkfifo(self.exe)
        self.blocked(reason="unique_nonempty_regular_file")

    def test_inode_modified_during_sha_stream_is_rejected(self):
        original_read = os.read
        modified = False

        def tamper(fd, count):
            nonlocal modified
            chunk = original_read(fd, count)
            if chunk and not modified:
                with self.exe.open("ab") as handle:
                    handle.write(b"changed_during_read")
                modified = True
            return chunk

        with mock.patch.object(h2.os, "read", side_effect=tamper):
            self.blocked(reason="changed_during_hash")
        self.assertTrue(modified)

    def test_native_host_digest_uses_same_open_inode_guard(self):
        self.exe.chmod(0o755)
        target, digest = h2.verify_native_host_artifact(
            self.root, str(self.exe.relative_to(self.root)))
        self.assertEqual(target, self.exe)
        self.assertEqual(digest, self.proof["c_binary_sha256"])
        os.link(self.exe, self.root / "native-alias")
        with self.assertRaisesRegex(h2.AuditFailure, "unique_nonempty_regular_file"):
            h2.verify_native_host_artifact(
                self.root, str(self.exe.relative_to(self.root)))


if __name__ == "__main__":
    unittest.main()
