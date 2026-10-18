#!/usr/bin/env python3
"""Регресія побайтової D3/D4→укр міграції native-first.

Static receipt, NOT a substitute for runtime SENS semantic evidence.
A projected source can be inverted to the exact Git blob of the old file;
quotes, comments, tags and direct D1:0/1 remain byte-identical.
"""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UKR_TO_BITS = {
    "як-є": "001",
    "атом?": "010",
    "решта": "011",
    "перше": "100",
    "тотожне?": "101",
    "за-умовою": "110",
    "сполучити": "111",
    "обчислити": "0001",
    "функція": "0010",
    "визначити": "0011",
    "порожній?": "0101",
}
RX = re.compile(
    r"\((" + "|".join(map(re.escape, sorted(UKR_TO_BITS, key=len, reverse=True)))
    + r")(?=\s|\))"
)
BASELINE = {
    "lib/machine/dispatch/native-first.lisp": (
        "b3411d2514fb9be55dbaf1ed9410fa556991320a", 131, 17, 24, 6
    ),
    "lib/machine/dispatch/native-first-execute.lisp": (
        "64b8fa69d1ecb507da506efb3a6b520d69cebdb8", 121, 13, 12, 7
    ),
}


def undo_ukr_heads(text: str) -> str:
    return RX.sub(lambda m: "(" + UKR_TO_BITS[m.group(1)], text)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


class NativeFirstUkrProjection(unittest.TestCase):
    def test_exact_ratified_D3_D4_peer_names(self):
        for name, bits in UKR_TO_BITS.items():
            with self.subTest(name=name, bits=bits):
                width = len(bits)
                table = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
                pattern = (rf"(?m)^\s*\({bits}\s+\(ук [^()]+\)"
                           rf"\s+\(укр {re.escape(name)}\)")
                self.assertRegex(table, pattern)

    def test_original_git_blobs_and_all_252_head_rewrites(self):
        count = 0
        for path, (sha, expected, definitions, yes, no) in BASELINE.items():
            with self.subTest(path=path):
                data = (ROOT / path).read_text(encoding="utf-8")
                old = undo_ukr_heads(data).encode("utf-8")
                self.assertEqual(git_blob(old), sha, "невідновлюваний source")
                self.assertEqual(len(list(RX.finditer(data))), expected)
                self.assertEqual(data.count("(визначити "), definitions)
                self.assertEqual((data.count("#d1:1"), data.count("#d1:0")),
                                 (yes, no))
                count += expected
        self.assertEqual(count, 252)

    def test_no_raw_D3_D4_callable_heads_remain(self):
        pattern = r"\((?:001|010|011|100|101|110|111|0001|0010|0011|0101)(?=\s|\))"
        for path in BASELINE:
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                code = "\n".join(line.split(";", 1)[0] for line in text.splitlines())
                self.assertNotRegex(code, pattern)

    def test_quoted_tags_D1_values_and_eval_surface(self):
        first = (ROOT / "lib/machine/dispatch/native-first.lisp").read_text()
        second = (ROOT / "lib/machine/dispatch/native-first-execute.lisp").read_text()
        self.assertIn("(як-є evaluator-fallback)", first)
        self.assertIn("(як-є native-plan)", first)
        self.assertIn("(як-є malformed-source-form-tail)", second)
        self.assertIn("(як-є source-execution)", second)
        self.assertIn("(обчислити (перше (решта plan)))", second)

    def test_mutation_of_one_callable_head_is_rejected(self):
        for path, (sha, *_rest) in BASELINE.items():
            with self.subTest(path=path):
                source = (ROOT / path).read_text()
                mutation = source.replace("(визначити ", "(визначити-неправильно ", 1)
                self.assertNotEqual(git_blob(undo_ukr_heads(mutation).encode()), sha)

    def test_mutation_of_quoted_data_is_rejected(self):
        path, (sha, *_rest) = next(iter(BASELINE.items()))
        text = (ROOT / path).read_text()
        mutation = text.replace("evaluator-fallback", "evaluator-fallback-неправильно", 1)
        self.assertNotEqual(git_blob(undo_ukr_heads(mutation).encode()), sha)


if __name__ == "__main__":
    unittest.main(verbosity=2)
