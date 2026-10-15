#!/usr/bin/env python3
"""Focused negative mutants for Zig F3C SENS-only semantic authority."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "corridor", ROOT / "scripts" / "check_sterile_zig_corridor.py")
assert SPEC is not None and SPEC.loader is not None
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
ZIG = ROOT / "research" / "zig-codecs" / "f3c" / "f3c.zig"


class NoD3ZigAuthority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ZIG.read_text(encoding="utf-8")

    def blocked(self, candidate):
        with self.assertRaisesRegex(gate.CorridorBlocked, "F3C_SEMANTIC_FIREWALL"):
            gate.check_zig_f3c_semantic_firewall(candidate)

    def inject(self, line):
        marker = "const Parser = struct {\n"
        self.assertEqual(self.source.count(marker), 1)
        return self.source.replace(marker, marker + line, 1)

    def test_01_real_source_is_physical_only(self):
        gate.check_zig_f3c_semantic_firewall(self.source)

    def test_02_reject_d3_opcode_bits(self):
        self.blocked(self.inject("    fn d3(w: Word) bool { return w.bits == 6; }\n"))

    def test_03_reject_arity_registry(self):
        self.blocked(self.inject("    fn d3(argc: usize) bool { return argc == 2; }\n"))

    def test_04_reject_quote_specific_meaning(self):
        self.blocked(self.inject("    fn d3(w: Word) bool { return same(w, 3, 1); }\n"))

    def test_05_reject_missing_decode_structure(self):
        old = "if (!canonicalStructure(words)) return Error.InvalidProgram;"
        self.assertIn(old, self.source)
        self.blocked(self.source.replace(old, "if (false) return Error.InvalidProgram;", 1))

    def test_06_reject_missing_physical_replay(self):
        old = "std.mem.eql(u8, canonical_f3, carrier)"
        self.assertIn(old, self.source)
        self.blocked(self.source.replace(old, "true", 1))

    def test_07_comment_only_mentions_do_not_block(self):
        gate.check_zig_f3c_semantic_firewall(self.inject(
            "    // QUOTE admittedHead argc same(w, 3, 1)\n"))


if __name__ == "__main__":
    unittest.main()
