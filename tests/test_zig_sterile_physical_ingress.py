#!/usr/bin/env python3
"""Fail-closed source regression for Rust→Zig ABI v2→SENS physical ingress.

This is a mechanical code-route guard, NOT a SENS semantic execution receipt.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "crates/sens-cli/src/main.rs"
BRIDGE = ROOT / "crates/sens-cli/src/zig_transport.rs"

def check_sterile_ingress(main: str, bridge: str) -> None:
    entry = main.split("fn decode_physical_t5_words(", 1)[1].split("\nfn eval_physical_t5(", 1)[0]
    evaluator = main.split("fn eval_physical_t5(", 1)[1].split("\nfn main()", 1)[0]
    if ("return zig_transport::decode_t5_exact_words(bytes)?" not in entry or
            '#[cfg(feature = "zig-transport")]' not in entry or
            "no Rust fallback" not in entry or
            "sens::decode_ternary_words(bytes)" in entry):
        raise ValueError("ZIG_CORRIDOR_BYPASS default physical ingress is not exclusively Zig")
    if ("let words = decode_physical_t5_words(bytes)?;" not in evaluator or
            "sens::PhysicalT5Program::from_exact_domain_words(&words)" not in evaluator or
            "Session::bare()" not in evaluator):
        raise ValueError("ZIG_CORRIDOR_BYPASS direct typed words do not reach pure SENS")
    if "sens_zig_t5_decode_be3(" not in bridge or "sens_zig_codec_abi_version()" not in bridge:
        raise ValueError("ZIG_CORRIDOR_BYPASS ABI v2 not present")
    # The four ABI boundaries must enforce exact counts (T5) or bounded
    # positive counts (F3C), not merely call Vec::truncate on a return.
    def function(name: str) -> str:
        # Anchor at the line start so a mirror string inside a test body
        # (e.g. .split("pub fn encode_f3(")) is never counted as a definition.
        anchor = "\npub fn " + name + "("
        if bridge.count(anchor) != 1:
            raise ValueError("ZIG_CORRIDOR_BYPASS missing or duplicate " + name)
        tail = bridge.split(anchor, 1)[1]
        return tail.split("\npub fn ", 1)[0].split("\n#[cfg(test)]", 1)[0]

    encode = function("encode_t5_direct")
    decode = function("decode_t5_words")
    pack = function("encode_f3")
    unpack = function("decode_f3")
    if ("usize::try_from(len).ok() != Some(bytes.len())" not in encode
            or "if len < 0" not in encode):
        raise ValueError("ZIG_CORRIDOR_BYPASS T5 encode length is not exact")
    if ("written <= 0" not in decode
            or ".filter(|&n| n <= be3.len())" not in decode
            or "written % 3 != 0" not in decode):
        raise ValueError("ZIG_CORRIDOR_BYPASS T5 decode BE3 length unbounded")
    # The F3C bound is now enforced inline (the checked_f3c_output_len helper was
    # removed): fail closed on non-positive or overreported length before truncate.
    if ("if len <= 0 || usize::try_from(len).ok().filter(|&n| n < legacy.len() && n <= bytes.len()).is_none()"
            not in pack):
        raise ValueError("ZIG_CORRIDOR_BYPASS F3C pack length/size not checked")
    if ("if len <= 0 || usize::try_from(len).ok().filter(|&n| n <= output.len()).is_none()"
            not in unpack):
        raise ValueError("ZIG_CORRIDOR_BYPASS F3C unpack length not checked")
    if "fn checked_f3c_output_len(" in bridge:
        raise ValueError("ZIG_CORRIDOR_BYPASS retired F3C helper reintroduced")
    if "sens::parse_canonical_word_sequence" in bridge:
        raise ValueError("ZIG_CORRIDOR_BYPASS Zig gained SENS semantic authority")


class SterileRustSensCorridor(unittest.TestCase):
    def setUp(self):
        self.main = MAIN.read_text(encoding="utf-8")
        self.bridge = BRIDGE.read_text(encoding="utf-8")

    def test_positive_default_zig_ingress_and_bounded_be3_f3c(self):
        check_sterile_ingress(self.main, self.bridge)

    def test_negative_rust_t5_codec_substituted(self):
        bad = self.main.replace(
            "return zig_transport::decode_t5_exact_words(bytes)?",
            "return sens::decode_ternary_words(bytes).map_err(|e| format!(\"{e:?}\"));", 1)
        with self.assertRaisesRegex(ValueError, "ZIG_CORRIDOR_BYPASS"):
            check_sterile_ingress(bad, self.bridge)

    def test_negative_hidden_rust_reference_fallback(self):
        bad = self.main.replace(
            "return zig_transport::decode_t5_exact_words(bytes)?",
            "return zig_transport::decode_t5_words(bytes).or_else(|_| rust_t5(bytes));", 1)
        with self.assertRaisesRegex(ValueError, "ZIG_CORRIDOR_BYPASS"):
            check_sterile_ingress(bad, self.bridge)

    def test_negative_zig_return_exceeds_caller_buffer(self):
        bad = self.bridge.replace(
            ".filter(|&n| n <= be3.len())",
            ".filter(|&n| n > 0)", 1)
        with self.assertRaisesRegex(ValueError, "ZIG_CORRIDOR_BYPASS"):
            check_sterile_ingress(self.main, bad)

    def test_negative_f3c_pack_accepts_unbounded_abi_length(self):
        bad = self.bridge.replace(
            "usize::try_from(len).ok().filter(|&n| n < legacy.len() && n <= bytes.len()).is_none()",
            "usize::try_from(len).ok().filter(|&n| n <= bytes.len()).is_none()", 1)
        with self.assertRaisesRegex(ValueError, "ZIG_CORRIDOR_BYPASS"):
            check_sterile_ingress(self.main, bad)

    def test_negative_f3c_unpack_accepts_unbounded_abi_length(self):
        bad = self.bridge.replace(
            "usize::try_from(len).ok().filter(|&n| n <= output.len()).is_none()",
            "usize::try_from(len).ok().is_some()", 1)
        with self.assertRaisesRegex(ValueError, "ZIG_CORRIDOR_BYPASS"):
            check_sterile_ingress(self.main, bad)

    def test_negative_f3c_retired_helper_reintroduced(self):
        bad = self.bridge + "\nfn checked_f3c_output_len("
        with self.assertRaisesRegex(ValueError, "ZIG_CORRIDOR_BYPASS"):
            check_sterile_ingress(self.main, bad)

    def test_negative_sens_reader_was_removed(self):
        bad = self.main.replace(
            "sens::PhysicalT5Program::from_exact_domain_words(&words)",
            "sens::parse_canonical_binary(&surface)", 1)
        with self.assertRaisesRegex(ValueError, "ZIG_CORRIDOR_BYPASS"):
            check_sterile_ingress(bad, self.bridge)


if __name__ == "__main__":
    unittest.main()
