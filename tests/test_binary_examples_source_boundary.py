#!/usr/bin/env python3
"""Точні бітові програми мають .bits, а людські .lisp — українську поверхню.

Тут доводиться лише фізична T5M оборотність, не SENS-семантика.
"""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sens_t5_t5m_codec import decode_t5m_bytes, encode_t5m_projection

CASES = {
    "examples/binary/d7-first-program.bits":
        "crates/sens/tests/binary_program_e2e.rs",
    "examples/binary-language/current-cond-reference.bits":
        "crates/sens/tests/current_binary_preflight.rs",
}


class BinarySourceExtensionsTests(unittest.TestCase):
    def test_binary_programs_have_correct_extension_and_exact_t5m_words(self):
        for relative, test in CASES.items():
            with self.subTest(source=relative):
                path = ROOT / relative
                source = path.read_text(encoding="ascii")
                self.assertTrue(re.fullmatch(r"[01\s]+", source))
                words = source.split()
                self.assertTrue(words)
                self.assertTrue(all(1 <= len(word) <= 11 for word in words))
                physical = encode_t5m_projection(source)
                self.assertEqual(decode_t5m_bytes(physical), words)
                self.assertEqual(encode_t5m_projection(" ".join(words)), physical)
                self.assertFalse(path.with_suffix(".lisp").exists(),
                                 "машинні біти не можуть удавати українське .lisp")
                self.assertIn(relative, (ROOT / test).read_text(encoding="utf-8"))

    def test_live_ukrainian_examples_are_not_raw_binary_text(self):
        examples = ROOT / "examples"
        for path in examples.rglob("*.lisp"):
            if "history" in path.relative_to(examples).parts:
                continue
            with self.subTest(source=path.relative_to(ROOT).as_posix()):
                source = path.read_text(encoding="utf-8")
                self.assertFalse(re.fullmatch(r"[01\s]+", source),
                                 "для точних бітових слів призначено .bits")


if __name__ == "__main__":
    unittest.main()
