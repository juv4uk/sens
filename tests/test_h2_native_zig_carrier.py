#!/usr/bin/env python3
"""Native H2 T5 comes from Zig's attested physical carrier, not Python.

Mutation tests inspect H2's evidence verifier. They are NOT a synthetic
SENS semantic evaluator or substitute for real Zig/C/Rust H2 execution.
"""
import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/zig-codecs/host-c/verify_h2_cross_host.py"
SPEC = importlib.util.spec_from_file_location("h2_zig_native_carry", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
h2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(h2)

PROFILE = "D1-D10_COORDINATES_NOT_EXECUTION"
BINARY = "a" * 64


def sample(source, suffix, physical=b"\xa1", carrier=BINARY):
    digest = hashlib.sha256(physical).hexdigest()
    return (
        f"{digest} /tmp/sens-native/{suffix}",
        f"ZIG_NATIVE_T5_CARRY source={source} physical_sha256={digest} "
        f"zig_binary_sha256={carrier} profile={PROFILE} semantic_authority=SENS",
        digest,
    )


class H2ZigNativeCarrier(unittest.TestCase):
    def setUp(self):
        self.source_a = "tests/semantic/retired-d3-cond-law.bits"
        self.source_b = "tests/semantic/retired-d3-cond-mutant.bits"
        self.a = sample(self.source_a, "cond-law.sens")
        self.b = sample(self.source_b, "cond-mutant.sens", b"\x35")
        self.proof = {
            self.source_a: {"sha256": self.a[2]},
            self.source_b: {"sha256": self.b[2]},
        }

    def check(self, lines, files=None):
        h2.verify_native_physical(
            "\n".join(lines), self.proof,
            files or ((self.source_a, "cond-law.sens"),
                      (self.source_b, "cond-mutant.sens")),
        )

    def blocked(self, lines, reason="H2_ZIG_NATIVE_CARRY"):
        with self.assertRaisesRegex(h2.AuditFailure, reason):
            self.check(lines)

    def all_lines(self):
        return [self.a[0], self.a[1], self.b[0], self.b[1]]

    def test_two_exact_Zig_carry_receipts_pass(self):
        self.check(self.all_lines())

    def test_missing_Zig_carry_rejects_python_written_same_sha(self):
        self.blocked([self.a[0], self.b[0], self.b[1]])

    def test_duplicate_Zig_carry_receipt_rejected(self):
        lines = self.all_lines()
        self.blocked([*lines, self.a[1]])

    def test_spoofed_wrong_physical_digest_rejected(self):
        lines = self.all_lines()
        lines[1] = lines[1].replace(self.a[2], "0" * 64)
        self.blocked(lines)

    def test_wrong_width_profile_rejected(self):
        lines = self.all_lines()
        lines[1] = lines[1].replace(PROFILE, "D1-D9_EXECUTION")
        self.blocked(lines)

    def test_Rust_cannot_be_declared_semantic_authority(self):
        lines = self.all_lines()
        lines[1] = lines[1].replace("semantic_authority=SENS", "semantic_authority=Rust")
        self.blocked(lines)

    def test_unverifiable_carrier_digest_rejected(self):
        lines = self.all_lines()
        lines[1] = lines[1].replace(BINARY, "unknown")
        self.blocked(lines)

    def test_changed_C_to_native_T5_hash_rejected(self):
        lines = self.all_lines()
        lines[0] = lines[0].replace(self.a[2], "f" * 64)
        self.blocked(lines, "H2_T5_PARITY")

    def test_mixed_Zig_executables_in_one_suite_rejected(self):
        lines = self.all_lines()
        lines[3] = lines[3].replace(BINARY, "b" * 64)
        self.blocked(lines, "mixed_carriers")

    def test_helper_is_pinned_with_BOTH_native_drivers(self):
        for required in (
            "scripts/prepare_h2_zig_t5.py",
            "scripts/zig_codec_bridge.py",
            *h2.RUST_DRIVERS,
        ):
            self.assertIn(required, h2.H2_TRACKED_INPUTS)

    def test_h2_source_pin_contains_the_default_t5m_import_closure(self):
        closure = h2.verify_zig_import_closure(ROOT, h2.H2_TRACKED_INPUTS)
        self.assertIn("research/zig-codecs/t5m.zig", closure)

    def test_native_shells_no_longer_write_T5_in_python(self):
        for source in h2.RUST_DRIVERS:
            script = (ROOT / source).read_text(encoding="utf-8")
            self.assertIn("scripts/prepare_h2_zig_t5.py", script)
            self.assertNotIn("encode_projection(", script)
            self.assertNotIn("decode_bytes(", script)

    def test_helper_delegates_physical_authority_to_Zig(self):
        source = (ROOT / "scripts/prepare_h2_zig_t5.py").read_text(
            encoding="utf-8")
        self.assertIn("build_transport(", source)
        self.assertIn("carry_t5(", source)
        self.assertIn("verify_t5(", source)
        self.assertNotIn("encode_projection(", source)
        self.assertNotIn("decode_bytes(", source)


if __name__ == "__main__":
    unittest.main()
