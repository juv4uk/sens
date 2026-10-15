#!/usr/bin/env python3
"""Zig 0.16 migration artifact provenance: path alias is not a trusted binary.

No Zig executable needed for these preflight-only tests. This does not
establish semantics or certify a Zig compiler/toolchain installation.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "zig_codec_bridge.py"
SPEC = importlib.util.spec_from_file_location("zig_binary_path_guard", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)


class ZigBinaryPhysicalPathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sens-zig-binary-path-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.real_dir = self.root / "real-build"
        self.real_dir.mkdir()
        self.binary = self.real_dir / "sens-zig-transport"
        self.binary.write_bytes(bytes.fromhex("63 89 06 a1"))
        self.digest = hashlib.sha256(self.binary.read_bytes()).hexdigest()
        bridge._BUILT_TRANSPORT_DIGESTS[self.binary.resolve()] = self.digest
        self.addCleanup(bridge._BUILT_TRANSPORT_DIGESTS.pop,
                        self.binary.resolve(), None)
        self.alias = self.root / "linked-build"
        self.alias.symlink_to(self.real_dir, target_is_directory=True)

    def test_regular_attested_file_returns_exact_binary_sha(self):
        self.assertEqual(bridge._built_executable_digest(self.binary), self.digest)

    def test_same_sha_hardlink_of_attested_binary_is_rejected(self):
        hardlink = self.root / "same-inode-second-name"
        os.link(self.binary, hardlink)
        self.assertEqual(hashlib.sha256(hardlink.read_bytes()).hexdigest(),
                         self.digest)
        with self.assertRaisesRegex(bridge.ZigCodecError,
                                    "ZIG_CODEC_BINARY_HARDLINKED nlink=2"):
            bridge._built_executable_digest(self.binary)
        hardlink.unlink()
        self.assertEqual(bridge._built_executable_digest(self.binary),
                         self.digest)

    def test_newly_built_hardlinked_binary_cannot_be_attested(self):
        def fake_zig_build(argv):
            binary_arg = next(arg for arg in argv
                              if arg.startswith("-femit-bin="))
            generated = Path(binary_arg.removeprefix("-femit-bin="))
            generated.write_bytes(self.binary.read_bytes())
            os.link(generated, generated.with_name("untrusted-second-name"))

        with mock.patch.object(bridge, "pinned_compiler",
                               return_value="zig"), mock.patch.object(
                                   bridge, "_command", side_effect=fake_zig_build):
            with self.assertRaisesRegex(bridge.ZigCodecError,
                                        "ZIG_CODEC_BINARY_HARDLINKED nlink=2"):
                bridge.build_transport(self.root / "fresh-build")

    def test_alias_parent_to_same_sha_is_rejected(self):
        aliased_binary = self.alias / self.binary.name
        self.assertEqual(hashlib.sha256(aliased_binary.read_bytes()).hexdigest(),
                         self.digest)
        with self.assertRaisesRegex(bridge.ZigCodecError,
                                    "ZIG_CODEC_BINARY_NOT_REGULAR"):
            bridge._built_executable_digest(aliased_binary)

    def test_build_destination_parent_alias_fails_before_compiler_probe(self):
        with mock.patch.object(
            bridge, "pinned_compiler",
            side_effect=AssertionError("Zig compiler must not run"),
        ):
            with self.assertRaisesRegex(bridge.ZigCodecError,
                                        "ZIG_CODEC_BINARY_NOT_REGULAR"):
                bridge.build_transport(self.alias)

    def test_linked_binary_leaf_still_rejected(self):
        leaf = self.root / "linked-binary"
        leaf.symlink_to(self.binary)
        with self.assertRaisesRegex(bridge.ZigCodecError,
                                    "ZIG_CODEC_BINARY_NOT_REGULAR"):
            bridge._built_executable_digest(leaf)

    def test_noncanonical_dotdot_path_rejected_even_for_same_bytes(self):
        noncanonical = self.real_dir / ".." / self.real_dir.name / self.binary.name
        with self.assertRaisesRegex(bridge.ZigCodecError,
                                    "ZIG_CODEC_BINARY_NONCANONICAL_PATH"):
            bridge._built_executable_digest(noncanonical)

    def test_unattested_regular_binary_stays_untrusted(self):
        other = self.root / "other-zig"
        other.write_bytes(self.binary.read_bytes())
        with self.assertRaisesRegex(bridge.ZigCodecError,
                                    "ZIG_CODEC_UNATTESTED_BINARY"):
            bridge._built_executable_digest(other)

    def test_changed_bytes_stay_rejected(self):
        self.binary.write_bytes(self.binary.read_bytes() + b"\x00")
        with self.assertRaisesRegex(bridge.ZigCodecError,
                                    "ZIG_CODEC_BINARY_CHANGED"):
            bridge._built_executable_digest(self.binary)


if __name__ == "__main__":
    unittest.main()
