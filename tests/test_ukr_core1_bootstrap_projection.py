"""Exact-domain source witness for Core1's late bootstrap Ukrainian projection.

Static source/identity checks ONLY; no Python emulation of SENS evaluator or
native T5 proof. The early Core1 evaluator and physical law slices are frozen
as the byte-identical prefix of the original Git blob.
"""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/core1.lisp"
PINNED = {
  "sha": "6f1cfecc3d75fd323fe9120a59b37f084d4947d3",
  "edits": [
    [
      15127,
      "0010"
    ],
    [
      15148,
      "110"
    ],
    [
      15162,
      "101"
    ],
    [
      15174,
      "001"
    ],
    [
      15184,
      "001"
    ],
    [
      15203,
      "101"
    ],
    [
      15208,
      "100"
    ],
    [
      15277,
      "100"
    ],
    [
      15393,
      "0010"
    ],
    [
      15414,
      "110"
    ],
    [
      15428,
      "101"
    ],
    [
      15440,
      "001"
    ],
    [
      15450,
      "001"
    ],
    [
      15469,
      "101"
    ],
    [
      15474,
      "100"
    ],
    [
      15537,
      "100"
    ],
    [
      15542,
      "011"
    ],
    [
      15581,
      "111"
    ],
    [
      15595,
      "100"
    ],
    [
      15637,
      "011"
    ],
    [
      15803,
      "0010"
    ],
    [
      15829,
      "110"
    ],
    [
      15843,
      "101"
    ],
    [
      15854,
      "001"
    ],
    [
      15908,
      "011"
    ],
    [
      15951,
      "100"
    ],
    [
      16017,
      "0010"
    ],
    [
      16041,
      "110"
    ],
    [
      16055,
      "101"
    ],
    [
      16064,
      "001"
    ],
    [
      16090,
      "101"
    ],
    [
      16101,
      "001"
    ],
    [
      16700,
      "0010"
    ],
    [
      16727,
      "110"
    ],
    [
      16741,
      "101"
    ],
    [
      16752,
      "001"
    ],
    [
      16762,
      "001"
    ],
    [
      16839,
      "111"
    ],
    [
      16844,
      "100"
    ],
    [
      16873,
      "011"
    ],
    [
      16990,
      "011"
    ],
    [
      18558,
      "0010"
    ],
    [
      18582,
      "110"
    ],
    [
      18596,
      "101"
    ],
    [
      18607,
      "001"
    ],
    [
      18617,
      "001"
    ],
    [
      18644,
      "101"
    ],
    [
      18649,
      "100"
    ],
    [
      18654,
      "100"
    ],
    [
      18681,
      "100"
    ],
    [
      18786,
      "0010"
    ],
    [
      18804,
      "110"
    ],
    [
      18818,
      "101"
    ],
    [
      18825,
      "001"
    ],
    [
      19526,
      "0010"
    ],
    [
      19548,
      "110"
    ],
    [
      19562,
      "101"
    ],
    [
      19570,
      "001"
    ],
    [
      19580,
      "001"
    ],
    [
      19610,
      "100"
    ],
    [
      19642,
      "011"
    ],
    [
      19725,
      "011"
    ],
    [
      19870,
      "0010"
    ],
    [
      19895,
      "110"
    ],
    [
      19909,
      "101"
    ],
    [
      19919,
      "001"
    ],
    [
      19929,
      "001"
    ],
    [
      19948,
      "101"
    ],
    [
      19953,
      "100"
    ],
    [
      19958,
      "100"
    ],
    [
      21039,
      "0010"
    ],
    [
      21062,
      "110"
    ],
    [
      21076,
      "101"
    ],
    [
      21264,
      "0010"
    ],
    [
      21286,
      "110"
    ],
    [
      21300,
      "101"
    ],
    [
      21312,
      "100"
    ],
    [
      21418,
      "0010"
    ],
    [
      21444,
      "110"
    ],
    [
      21458,
      "101"
    ],
    [
      21470,
      "111"
    ],
    [
      21479,
      "011"
    ],
    [
      21515,
      "111"
    ],
    [
      21520,
      "100"
    ],
    [
      21539,
      "011"
    ]
  ],
  "changed": [
    470,
    471,
    472,
    473,
    474,
    480,
    481,
    482,
    483,
    484,
    486,
    487,
    495,
    496,
    497,
    499,
    500,
    504,
    505,
    506,
    507,
    528,
    529,
    530,
    532,
    534,
    592,
    593,
    594,
    595,
    596,
    601,
    602,
    603,
    625,
    626,
    627,
    628,
    629,
    631,
    639,
    640,
    641,
    642,
    678,
    679,
    680,
    689,
    690,
    691,
    696,
    697,
    698,
    700
  ],
  "boundary_line": 462
}
ROW = re.compile(r"^\s*\(([01]+)\s+\(ук\s+[^()]*\)\s+\(укр\s+([^\s()]+)\)")
NUMERIC_HEAD = re.compile(r"\(\s*[01]+(?=\s|\)|$)")
ENCODED_LITERAL = re.compile(r"#(?:d\d+:[01]+|b[01]+)")
BOUNDARY = "Bootstrap additions: reader + reclamation"
COUNTS = {"0010": 12, "110": 12, "101": 17, "001": 16,
          "100": 15, "011": 9, "111": 4}


def ratified_peers():
    peers = {}
    for width in (3, 4):
        content = (ROOT / f"lib/domains/d{width}.lisp").read_text(
            encoding="utf-8"
        )
        for line in content.splitlines():
            match = ROW.match(line)
            if match and len(match[1]) == width:
                peers[match[1]] = match[2]
    return peers


def inverse_projection(text, edits, peers):
    movements, shift, last_position = [], 0, -1
    for original_position, original_bits in edits:
        if original_position <= last_position:
            raise AssertionError("Порядок source offsets порушений")
        last_position = original_position
        if original_bits not in peers or len(original_bits) not in (3, 4):
            raise AssertionError(f"Немає канонічної identity {original_bits}")
        ukr = peers[original_bits]
        movements.append((original_position + shift, original_bits, ukr))
        shift += len(ukr) - len(original_bits)
    for position, original_bits, ukr in reversed(movements):
        if text[position:position + len(ukr)] != ukr:
            raise AssertionError(
                f"Змінена укр-проєкція D{len(original_bits)}:{original_bits} @ {position}"
            )
        text = text[:position] + original_bits + text[position + len(ukr):]
    return text


def git_blob_sha(text):
    data = text.encode("utf-8")
    return hashlib.sha1(
        b"blob " + str(len(data)).encode() + bytes((0,)) + data
    ).hexdigest()


def mask_comment_and_string(line):
    return re.sub(
        r'"(?:\\.|[^"\\])*"|;[^\n]*',
        lambda match: " " * len(match.group()), line,
    )


class Core1LateBootstrapUkrProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.peers = ratified_peers()

    def test_exact_ratifed_domain_keys_and_head_counts(self):
        self.assertEqual(Counter(bits for _, bits in PINNED["edits"]), COUNTS)
        self.assertEqual(len(PINNED["edits"]), 85)
        for bits in COUNTS:
            self.assertIn(bits, self.peers)
        self.assertEqual(self.peers["001"], "як-є")
        self.assertEqual(self.peers["101"], "тотожне?")
        self.assertEqual(self.peers["110"], "за-умовою")
        self.assertEqual(self.peers["0010"], "функція")

    def test_inverse_exact_pre_migration_git_blob_and_earlier_prefix(self):
        current = SOURCE.read_text(encoding="utf-8")
        original = inverse_projection(current, PINNED["edits"], self.peers)
        self.assertEqual(git_blob_sha(original), PINNED["sha"])
        self.assertEqual(original.count(BOUNDARY), 1)
        marker = original.index(BOUNDARY)
        self.assertEqual(current[:marker], original[:marker])
        self.assertEqual(
            original[:marker].count("#d1:1"),
            current[:marker].count("#d1:1"),
        )

    def test_all_changed_lines_are_late_and_do_not_contain_raw_heads(self):
        current = SOURCE.read_text(encoding="utf-8")
        original = inverse_projection(current, PINNED["edits"], self.peers)
        a, b = original.splitlines(), current.splitlines()
        self.assertEqual(len(a), len(b))
        changed = [index + 1 for index, (old, new) in
                   enumerate(zip(a, b)) if old != new]
        self.assertEqual(changed, PINNED["changed"])
        self.assertTrue(all(line > PINNED["boundary_line"] for line in changed))
        for line_number in changed:
            code = mask_comment_and_string(b[line_number - 1])
            self.assertIsNone(NUMERIC_HEAD.search(code), f"рядок {line_number}")
            self.assertIsNone(ENCODED_LITERAL.search(code), f"рядок {line_number}")

    def test_d1_legacy_reader_and_unadmitted_d5_words_unchanged(self):
        current = SOURCE.read_text(encoding="utf-8")
        original = inverse_projection(current, PINNED["edits"], self.peers)
        for old in ("#d1:0", "#d1:1", "(00100 C1-READ",
                    "(10011 X)", "(01010 A B"):
            self.assertEqual(current.count(old), original.count(old), old)
        self.assertIn("(визначити C1-READ", current)
        self.assertIn("(визначити C1-MAKE-ARRAY", current)
        self.assertIn("(за-умовою", current)
        # Quoted names and value bits remain untouched by construction.
        self.assertIn("(як-є C1-MISSING)", current)

    def test_negative_wrong_peer_is_rejected(self):
        current = SOURCE.read_text(encoding="utf-8")
        bad = current.replace("(функція (TOKENS)", "(функція-хибно (TOKENS)", 1)
        self.assertNotEqual(current, bad)
        with self.assertRaises(AssertionError):
            inverse_projection(bad, PINNED["edits"], self.peers)


if __name__ == "__main__":
    unittest.main(verbosity=2)
