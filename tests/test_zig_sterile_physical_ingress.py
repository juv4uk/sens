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
    if ("return zig_transport::decode_t5_words(bytes);" not in entry or
            '#[cfg(feature = "zig-transport")]' not in entry or
            "no Rust fallback" not in entry or
            "sens::decode_ternary_words(bytes)" in entry):
        raise ValueError("ZIG_CORRIDOR_BYPASS default physical ingress is not exclusively Zig")
    if ("let words = decode_physical_t5_words(bytes)?;" not in evaluator or
            "sens::parse_canonical_word_sequence(&words)" not in evaluator or
            "Session::bare()" not in evaluator):
        raise ValueError("ZIG_CORRIDOR_BYPASS direct typed words do not reach pure SENS")
    if "sens_zig_t5_decode_be3(" not in bridge or "sens_zig_codec_abi_version()" not in bridge:
        raise ValueError("ZIG_CORRIDOR_BYPASS ABI v2 not present")
    # One bounds check for each of the four mechanical returns (T5/F3C).
    checks = re.findall(
        r"if len <= 0 \|\| usize::try_from\(len\)\.ok\(\)\.filter\(\|&n\| n <= "
        r"(?:output|be3|bytes|t5)\.len\(\)\)\.is_none\(\)", bridge)
    if len(checks) != 4:
        raise ValueError("ZIG_CORRIDOR_BYPASS Zig ABI returned an unbounded output length")
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
            "return zig_transport::decode_t5_words(bytes);",
            "return sens::decode_ternary_words(bytes).map_err(|e| format!(\"{e:?}\"));", 1)
        with self.assertRaisesRegex(ValueError, "ZIG_CORRIDOR_BYPASS"):
            check_sterile_ingress(bad, self.bridge)

    def test_negative_hidden_rust_reference_fallback(self):
        bad = self.main.replace(
            "return zig_transport::decode_t5_words(bytes);",
            "return zig_transport::decode_t5_words(bytes).or_else(|_| rust_t5(bytes));", 1)
        with self.assertRaisesRegex(ValueError, "ZIG_CORRIDOR_BYPASS"):
            check_sterile_ingress(bad, self.bridge)

    def test_negative_zig_return_exceeds_caller_buffer(self):
        bad = self.bridge.replace(
            "if len <= 0 || usize::try_from(len).ok().filter(|&n| n <= be3.len()).is_none() {",
            "if len <= 0 {", 1)
        with self.assertRaisesRegex(ValueError, "ZIG_CORRIDOR_BYPASS"):
            check_sterile_ingress(self.main, bad)

    def test_negative_sens_reader_was_removed(self):
        bad = self.main.replace(
            "sens::parse_canonical_word_sequence(&words)",
            "sens::parse_canonical_binary(&surface)", 1)
        with self.assertRaisesRegex(ValueError, "ZIG_CORRIDOR_BYPASS"):
            check_sterile_ingress(bad, self.bridge)


if __name__ == "__main__":
    unittest.main()
