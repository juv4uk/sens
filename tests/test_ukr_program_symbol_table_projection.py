"""Статичні exact-domain регресії української проєкції таблиці символів.

Не виконує семантику SENS засобами Python: доводить незмінність початкових
байтів за ратифікованим позиційним перетворенням D3/D4.
"""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/program-symbol-table.lisp"
PINNED = {
  "sha": "431ae284f11982d132ba8dbc518030f9ae7ca270",
  "edits": [
    [
      243,
      '0011'
    ],
    [
      260,
      '001'
    ],
    [
      271,
      '0011'
    ],
    [
      284,
      '0010'
    ],
    [
      303,
      '110'
    ],
    [
      309,
      '110011100'
    ],
    [
      328,
      '110101010'
    ],
    [
      353,
      '010'
    ],
    [
      358,
      '001'
    ],
    [
      376,
      '110011101'
    ],
    [
      397,
      '01010'
    ],
    [
      415,
      '0011'
    ],
    [
      425,
      '0010'
    ],
    [
      437,
      '0100'
    ],
    [
      443,
      '11110111'
    ],
    [
      476,
      '0011'
    ],
    [
      493,
      '0010'
    ],
    [
      505,
      '110100011'
    ],
    [
      520,
      '110100010'
    ],
    [
      538,
      '0011'
    ],
    [
      551,
      '0010'
    ],
    [
      585,
      '0011'
    ],
    [
      599,
      '0010'
    ],
    [
      609,
      '110'
    ],
    [
      615,
      '110101010'
    ],
    [
      662,
      '010'
    ],
    [
      667,
      '001'
    ],
    [
      684,
      '0011'
    ],
    [
      702,
      '0010'
    ],
    [
      714,
      '110'
    ],
    [
      720,
      '110110'
    ],
    [
      730,
      '110100010'
    ],
    [
      758,
      '110100011'
    ],
    [
      773,
      '01010'
    ],
    [
      787,
      '110011110'
    ],
    [
      798,
      '110100011'
    ],
    [
      813,
      '01010'
    ],
    [
      841,
      '01010'
    ],
    [
      857,
      '010'
    ],
    [
      862,
      '001'
    ],
    [
      880,
      '0011'
    ],
    [
      900,
      '0010'
    ],
    [
      912,
      '110'
    ],
    [
      918,
      '110110'
    ],
    [
      928,
      '110100010'
    ],
    [
      957,
      '110101011'
    ],
    [
      977,
      '010'
    ],
    [
      982,
      '001'
    ],
    [
      992,
      '110011110'
    ],
    [
      1003,
      '110101011'
    ],
    [
      1034,
      '01010'
    ],
    [
      1053,
      '0011'
    ],
    [
      1071,
      '0010'
    ],
    [
      1081,
      '110'
    ],
    [
      1087,
      '11110111'
    ],
    [
      1119,
      '111'
    ],
    [
      1126,
      '001'
    ],
    [
      1138,
      '11110111'
    ],
    [
      1153,
      '111'
    ],
    [
      1158,
      '110100011'
    ],
    [
      1219,
      '01010'
    ],
    [
      1255,
      '0011'
    ],
    [
      1273,
      '0010'
    ],
    [
      1289,
      '110'
    ],
    [
      1295,
      '010'
    ],
    [
      1353,
      '010'
    ],
    [
      1358,
      '001'
    ],
    [
      1381,
      '011'
    ],
    [
      1391,
      '111'
    ],
    [
      1396,
      '100'
    ],
    [
      1417,
      '0011'
    ],
    [
      1433,
      '0010'
    ],
    [
      1445,
      '110'
    ],
    [
      1451,
      '010'
    ],
    [
      1501,
      '010'
    ],
    [
      1506,
      '001'
    ],
    [
      1516,
      '01010'
    ],
    [
      1536,
      '011'
    ],
    [
      1553,
      '0011'
    ],
    [
      1566,
      '0010'
    ],
    [
      1579,
      '110'
    ],
    [
      1636,
      '01010'
    ],
    [
      1673,
      '010'
    ],
    [
      1678,
      '001'
    ],
    [
      1696,
      '0011'
    ],
    [
      1711,
      '0010'
    ],
    [
      1724,
      '110'
    ],
    [
      1779,
      '01010'
    ],
    [
      1817,
      '010'
    ],
    [
      1822,
      '001'
    ],
    [
      1840,
      '0011'
    ],
    [
      1856,
      '0010'
    ],
    [
      1876,
      '110'
    ],
    [
      1882,
      '110011100'
    ],
    [
      1903,
      '110011100'
    ],
    [
      1926,
      '010'
    ],
    [
      1931,
      '001'
    ],
    [
      1941,
      '111'
    ],
    [
      1946,
      '111'
    ],
    [
      1970,
      '0011'
    ],
    [
      1993,
      '0010'
    ],
    [
      2059,
      '0011'
    ],
    [
      2083,
      '0010'
    ],
    [
      2101,
      '110'
    ],
    [
      2107,
      '010'
    ],
    [
      2175,
      '010'
    ],
    [
      2180,
      '001'
    ],
    [
      2209,
      '011'
    ],
    [
      2239,
      '100'
    ],
    [
      2262,
      '0011'
    ],
    [
      2277,
      '0010'
    ],
    [
      2332,
      '0011'
    ],
    [
      2346,
      '0010'
    ],
    [
      2427,
      '0011'
    ],
    [
      2442,
      '0010'
    ],
    [
      2459,
      '001000'
    ],
    [
      2514,
      '001000'
    ],
    [
      2570,
      '01010'
    ],
    [
      2580,
      '110100010'
    ],
    [
      2639,
      '0011'
    ],
    [
      2665,
      '0010'
    ],
    [
      2731,
      '0011'
    ],
    [
      2755,
      '0010'
    ],
    [
      2773,
      '110'
    ],
    [
      2779,
      '010'
    ],
    [
      2847,
      '010'
    ],
    [
      2852,
      '001'
    ],
    [
      2881,
      '011'
    ],
    [
      2914,
      '100'
    ],
    [
      2937,
      '0011'
    ],
    [
      2951,
      '0010'
    ],
    [
      2963,
      '110'
    ],
    [
      2969,
      '110101010'
    ],
    [
      2985,
      '110101010'
    ],
    [
      3003,
      '010'
    ],
    [
      3008,
      '001'
    ],
    [
      3034,
      '0011'
    ],
    [
      3052,
      '0010'
    ],
    [
      3068,
      '110'
    ],
    [
      3074,
      '010'
    ],
    [
      3152,
      '100'
    ],
    [
      3157,
      '100'
    ],
    [
      3181,
      '010'
    ],
    [
      3186,
      '001'
    ],
    [
      3212,
      '011'
    ],
    [
      3229,
      '0011'
    ],
    [
      3246,
      '0010'
    ],
    [
      3264,
      '110'
    ],
    [
      3283,
      '100'
    ],
    [
      3307,
      '010'
    ],
    [
      3312,
      '001'
    ],
    [
      3322,
      '111'
    ],
    [
      3343,
      '0011'
    ],
    [
      3359,
      '0010'
    ],
    [
      3378,
      '110'
    ],
    [
      3384,
      '010'
    ],
    [
      3446,
      '010'
    ],
    [
      3451,
      '001'
    ],
    [
      3472,
      '011'
    ],
    [
      3496,
      '100'
    ],
    [
      3520,
      '0011'
    ],
    [
      3535,
      '0010'
    ],
    [
      3547,
      '110'
    ],
    [
      3553,
      '010'
    ],
    [
      3563,
      '001'
    ],
    [
      3611,
      '111'
    ],
    [
      3616,
      '11011011'
    ],
    [
      3626,
      '110011110'
    ],
    [
      3637,
      '110011110'
    ],
    [
      3648,
      '100'
    ],
    [
      3653,
      '100'
    ],
    [
      3669,
      '011'
    ],
    [
      3674,
      '100'
    ],
    [
      3698,
      '011'
    ],
    [
      3714,
      '0011'
    ],
    [
      3725,
      '0010'
    ],
    [
      3751,
      '001000'
    ],
    [
      3816,
      '110110111'
    ],
    [
      3838,
      '001'
    ],
    [
      3848,
      '001'
    ],
    [
      3860,
      '001000'
    ],
    [
      3925,
      '110110111'
    ],
    [
      3947,
      '001'
    ],
    [
      3957,
      '001'
    ],
    [
      3969,
      '001000'
    ],
    [
      4020,
      '111'
    ],
    [
      4075,
      '100'
    ],
    [
      4088,
      '100'
    ],
    [
      4093,
      '011'
    ]
  ],
  "changed": [
    6,
    8,
    10,
    12,
    14,
    16,
    18,
    20,
    22,
    24,
    25,
    27,
    28,
    30,
    32,
    34,
    36,
    38,
    39,
    41,
    43,
    44,
    47,
    48,
    49,
    50,
    53,
    55,
    56,
    58,
    60,
    61,
    63,
    65,
    66,
    68,
    69,
    71,
    73
  ]
}
ROW = re.compile(r"^\s*\(([01]+)\s+\(ук\s+[^()]*\)\s+\(укр\s+([^\s()]+)\)")
NUMERIC_HEAD = re.compile(r"\(\s*[01]+(?=\s|\)|$)")
ENCODED_LITERAL = re.compile(r"#(?:d\d+:[01]+|b[01]+)")
EXPECTED = {'0011': 27, '001': 22, '0010': 26, '110': 17, '110011100': 3, '110101010': 4, '010': 22, '110011101': 1, '01010': 10, '0100': 1, '11110111': 3, '110100011': 4, '110100010': 4, '110110': 2, '110011110': 4, '110101011': 2, '111': 8, '011': 9, '100': 12, '001000': 5, '11011011': 1, '110110111': 2}


def authority():
    peers = {}
    for width in (3, 4, 5, 6, 7, 8, 9, 10, 11):
        for line in (ROOT / f"lib/domains/d{width}.lisp").read_text(
            encoding="utf-8"
        ).splitlines():
            found = ROW.match(line)
            if found and len(found[1]) == width:
                peers[found[1]] = found[2]
    return peers


def inverse(text, edits, peers):
    movements, shift, previous = [], 0, -1
    for original_pos, old in edits:
        if original_pos <= previous:
            raise AssertionError("Повторені або невпорядковані позиції")
        previous = original_pos
        if old not in peers or not (3 <= len(old) <= 11):
            raise AssertionError(f"Немає доведеної доменної identity: {old}")
        projected = peers[old]
        movements.append((original_pos + shift, old, projected))
        shift += len(projected) - len(old)
    for position, old, projected in reversed(movements):
        if text[position:position + len(projected)] != projected:
            raise AssertionError(f"Втрачено exact укр-проєкцію {old}, {position}")
        text = (text[:position] + old +
                text[position + len(projected):])
    return text


PROBE_OLD = "(111 (11011011 (110011110 tag (11110100 value))) value)))"
PROBE_UKR = "(сполучити (друкувати (рядок-додати tag (значення-у-текст value))) value)))"


def reverse_probe_ukr(source):
    if source.count(PROBE_UKR) != 1:
        raise AssertionError("Немає єдиної української викличної форми probe")
    return source.replace(PROBE_UKR, PROBE_OLD, 1)


def git_blob(text):
    raw = text.encode("utf-8")
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + bytes((0,)) + raw
    ).hexdigest()


def without_string_comments(line):
    return re.sub(
        r'"(?:\\.|[^"\\])*"|;[^\n]*',
        lambda match: " " * len(match.group()), line
    )


class ProgramSymbolTableUkrProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.peers = authority()

    def test_ratified_coordinates_and_exact_count(self):
        self.assertEqual(Counter(old for _, old in PINNED["edits"]), EXPECTED)
        self.assertEqual(len(PINNED["edits"]), 189)
        for old in EXPECTED:
            self.assertTrue(3 <= len(old) <= 11)
            self.assertIn(old, self.peers)
        self.assertEqual(self.peers["0011"], "визначити")
        self.assertEqual(self.peers["0010"], "функція")
        self.assertEqual(self.peers["010"], "атом?")
        self.assertEqual(self.peers["110"], "за-умовою")

    def test_exact_original_git_blob_reconstructed(self):
        source = SOURCE.read_text(encoding="utf-8")
        restored = inverse(reverse_probe_ukr(source), PINNED["edits"], self.peers)
        self.assertEqual(git_blob(restored), PINNED["sha"])

    def test_changed_lines_have_no_numeric_head(self):
        source = SOURCE.read_text(encoding="utf-8")
        old = inverse(reverse_probe_ukr(source), PINNED["edits"], self.peers)
        lines_before, lines_after = old.splitlines(), source.splitlines()
        self.assertEqual(len(lines_before), len(lines_after))
        changed = [i + 1 for i, (before, after) in
                   enumerate(zip(lines_before, lines_after)) if before != after]
        self.assertEqual(changed, sorted([*PINNED["changed"], 45]))
        for line in changed:
            mask = without_string_comments(lines_after[line - 1])
            self.assertIsNone(NUMERIC_HEAD.search(mask), f"line {line}")
            self.assertIsNone(ENCODED_LITERAL.search(mask), f"line {line}")

    def test_unproved_domain_words_and_historical_cond_debt_preserved(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("(визначити nil-marker (як-є ()))", source)
        self.assertIn("(визначити reverse-acc", source)
        self.assertIn("((атом? lst) acc)", source)
        self.assertIn("(додати i 1)", source)  # D5:01010 -> ратифікована поверхня додати
        self.assertIn("(t (сполучити (друкувати", source)  # гілка на ратифікованих D3/D8 поверхнях
        self.assertIn("(main (перше *argv*)", source)
        self.assertNotIn("(0011 nil-marker", source)

    def test_negative_wrong_peer_fails_inverse(self):
        source = SOURCE.read_text(encoding="utf-8")
        mutated = source.replace(
            "(визначити nil-marker", "(функція nil-marker", 1
        )
        self.assertNotEqual(mutated, source)
        with self.assertRaises(AssertionError):
            inverse(reverse_probe_ukr(mutated), PINNED["edits"], self.peers)


if __name__ == "__main__":
    unittest.main(verbosity=2)
