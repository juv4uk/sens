"""Статичні exact-domain регресії української проєкції таблиці символів.

Не виконує семантику SENS засобами Python: доводить незмінність початкових
байтів за ратифікованим позиційним перетворенням D3/D4.
"""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/program-symbol-table.lisp"
PINNED = {
  "sha": "431ae284f11982d132ba8dbc518030f9ae7ca270",
  "edits": [
    [
      243,
      "0011"
    ],
    [
      260,
      "001"
    ],
    [
      538,
      "0011"
    ],
    [
      551,
      "0010"
    ],
    [
      1255,
      "0011"
    ],
    [
      1273,
      "0010"
    ],
    [
      1289,
      "110"
    ],
    [
      1295,
      "010"
    ],
    [
      1353,
      "010"
    ],
    [
      1358,
      "001"
    ],
    [
      1381,
      "011"
    ],
    [
      1391,
      "111"
    ],
    [
      1396,
      "100"
    ],
    [
      1417,
      "0011"
    ],
    [
      1433,
      "0010"
    ],
    [
      1445,
      "110"
    ],
    [
      1451,
      "010"
    ],
    [
      1970,
      "0011"
    ],
    [
      1993,
      "0010"
    ],
    [
      2059,
      "0011"
    ],
    [
      2083,
      "0010"
    ],
    [
      2101,
      "110"
    ],
    [
      2107,
      "010"
    ],
    [
      2175,
      "010"
    ],
    [
      2180,
      "001"
    ],
    [
      2209,
      "011"
    ],
    [
      2239,
      "100"
    ],
    [
      2262,
      "0011"
    ],
    [
      2277,
      "0010"
    ],
    [
      2332,
      "0011"
    ],
    [
      2346,
      "0010"
    ],
    [
      2427,
      "0011"
    ],
    [
      2442,
      "0010"
    ],
    [
      2639,
      "0011"
    ],
    [
      2665,
      "0010"
    ],
    [
      2731,
      "0011"
    ],
    [
      2755,
      "0010"
    ],
    [
      2773,
      "110"
    ],
    [
      2779,
      "010"
    ],
    [
      2847,
      "010"
    ],
    [
      2852,
      "001"
    ],
    [
      2881,
      "011"
    ],
    [
      2914,
      "100"
    ],
    [
      3034,
      "0011"
    ],
    [
      3052,
      "0010"
    ],
    [
      3068,
      "110"
    ],
    [
      3074,
      "010"
    ],
    [
      3152,
      "100"
    ],
    [
      3157,
      "100"
    ],
    [
      3181,
      "010"
    ],
    [
      3186,
      "001"
    ],
    [
      3212,
      "011"
    ],
    [
      3229,
      "0011"
    ],
    [
      3246,
      "0010"
    ],
    [
      3264,
      "110"
    ],
    [
      3283,
      "100"
    ],
    [
      3307,
      "010"
    ],
    [
      3312,
      "001"
    ],
    [
      3322,
      "111"
    ],
    [
      3343,
      "0011"
    ],
    [
      3359,
      "0010"
    ],
    [
      3378,
      "110"
    ],
    [
      3384,
      "010"
    ],
    [
      3446,
      "010"
    ],
    [
      3451,
      "001"
    ],
    [
      3472,
      "011"
    ],
    [
      3496,
      "100"
    ],
    [
      3520,
      "0011"
    ],
    [
      3535,
      "0010"
    ],
    [
      3547,
      "110"
    ],
    [
      3553,
      "010"
    ],
    [
      3563,
      "001"
    ],
    [
      4075,
      "100"
    ],
    [
      4088,
      "100"
    ],
    [
      4093,
      "011"
    ]
  ],
  "changed": [
    6,
    14,
    24,
    25,
    27,
    36,
    38,
    39,
    41,
    43,
    44,
    47,
    48,
    53,
    55,
    56,
    60,
    61,
    63,
    65,
    66,
    68,
    73
  ]
}

# Історичний source-only свідок фіксує стан ДО наступного ручного
# перейменування локальних імен. Живий файл додатково перевіряється
# як його точна, виключно лексична українська проєкція.
PRE_RENAME_BLOB = "e6eba54d1078e556124fb82a57fd57d53dffe5f4"
ALPHA_RENAMES = {
    "nil-marker": "ознака-порожнього",
    "pos-of": "позиція-підрядка",
    "has": "містить-підрядок?",
    "slice-from": "зріз-від",
    "digit?": "цифра?",
    "skip-ws": "пропустити-пробіли",
    "word-digits": "послідовність-цифр",
    "word-nonspace": "слово-до-пробілу",
    "split-lines": "розділити-рядки",
    "reverse-acc": "зворот-накопичувача",
    "count-lst": "довжина-списку",
    "asm-id": "асемблер-ідентифікатор",
    "asm-name": "асемблер-назва",
    "keep-pair": "зберегти-пару",
    "process-asm-line": "обробити-рядок-асемблера",
    "process-lines-asm": "обробити-рядки-асемблера",
    "inc-name": "назва-з-включення",
    "probe": "спостерігати-значення",
    "inc-id": "ідентифікатор-з-включення",
    "process-define-line": "обробити-рядок-визначення",
    "process-lines-inc": "обробити-рядки-включення",
    "str-eq?": "однакові-рядки?",
    "id-in-base?": "ідентифікатор-у-базі?",
    "merge-pair": "злити-пару",
    "merge-all": "злити-всі",
    "emit-all": "вивести-всі",
    "main": "головна",
    "s": "рядок",
    "marker": "позначка",
    "i": "позиція",
    "m": "підрядок",
    "c": "символ",
    "lst": "елементи",
    "acc": "накопичувач",
    "line": "рядок-джерела",
    "lines": "рядки-джерела",
    "tag": "позначка-спостереження",
    "value": "значення",
    "name": "назва",
    "tail": "залишок",
    "id": "ідентифікатор",
    "base": "база",
    "pair": "пара",
    "pairs": "пари",
    "a": "ліве",
    "b": "праве",
    "asm-path": "шлях-асемблера",
    "inc-path": "шлях-включення",
    "asm-pairs": "асемблерні-пари",
    "inc-pairs": "пари-включення",
    "merged": "злиті"
}


def source_before_manual_names():
    return subprocess.run(
        ["git", "cat-file", "-p", PRE_RENAME_BLOB],
        cwd=ROOT, check=True, capture_output=True, text=True,
        encoding="utf-8",
    ).stdout


def manually_renamed_code(source):
    out, token = [], []
    in_comment = in_string = escaped = False

    def flush():
        if token:
            word = "".join(token)
            out.append(ALPHA_RENAMES.get(word, word))
            token.clear()

    for char in source:
        if in_comment:
            out.append(char)
            if char == "\n":
                in_comment = False
            continue
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char.isspace() or char in ("(", ")", "'", '"', ";"):
            flush()
            out.append(char)
            if char == ";":
                in_comment = True
            elif char == '"':
                in_string = True
        else:
            token.append(char)
    flush()
    return "".join(out)

ROW = re.compile(r"^\s*\(([01]+)\s+\(ук\s+[^()]*\)\s+\(укр\s+([^\s()]+)\)")
NUMERIC_HEAD = re.compile(r"\(\s*[01]+(?=\s|\)|$)")
ENCODED_LITERAL = re.compile(r"#(?:d\d+:[01]+|b[01]+)")
EXPECTED = {"0011": 15, "001": 8, "0010": 14, "110": 8,
            "010": 13, "011": 6, "111": 2, "100": 9}


def authority():
    peers = {}
    for width in (3, 4):
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
        if old not in peers or len(old) not in (3, 4):
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


    def test_manual_ukrainian_names_are_exact_source_projection(self):
        original = source_before_manual_names()
        self.assertEqual(git_blob(original), PRE_RENAME_BLOB)
        actual = SOURCE.read_text(encoding="utf-8")
        self.assertEqual(manually_renamed_code(original), actual)
        self.assertIn("(визначити ознака-порожнього (як-є ()))", actual)
        self.assertIn("(головна (перше *argv*)", actual)
        self.assertNotIn("(визначити nil-marker", actual)

    def test_ratified_coordinates_and_exact_count(self):
        self.assertEqual(Counter(old for _, old in PINNED["edits"]), EXPECTED)
        self.assertEqual(len(PINNED["edits"]), 75)
        for old in EXPECTED:
            self.assertEqual(len(old), 3 if len(old) == 3 else 4)
            self.assertIn(old, self.peers)
        self.assertEqual(self.peers["0011"], "визначити")
        self.assertEqual(self.peers["0010"], "функція")
        self.assertEqual(self.peers["010"], "атом?")
        self.assertEqual(self.peers["110"], "за-умовою")

    def test_exact_original_git_blob_reconstructed(self):
        source = source_before_manual_names()
        restored = inverse(reverse_probe_ukr(source), PINNED["edits"], self.peers)
        self.assertEqual(git_blob(restored), PINNED["sha"])

    def test_changed_lines_have_no_numeric_head(self):
        source = source_before_manual_names()
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
        source = source_before_manual_names()
        self.assertIn("(визначити nil-marker (як-є ()))", source)
        self.assertIn("(визначити reverse-acc", source)
        self.assertIn("((атом? lst) acc)", source)
        self.assertIn("(01010 i 1)", source)  # D5 без окремого admission
        self.assertIn("(t (111 (11011011", source)  # стара трьохпольова гілка
        self.assertIn("(main (перше *argv*)", source)
        self.assertNotIn("(0011 nil-marker", source)

    def test_negative_wrong_peer_fails_inverse(self):
        source = source_before_manual_names()
        mutated = source.replace(
            "(визначити nil-marker", "(функція nil-marker", 1
        )
        self.assertNotEqual(mutated, source)
        with self.assertRaises(AssertionError):
            inverse(reverse_probe_ukr(mutated), PINNED["edits"], self.peers)


if __name__ == "__main__":
    unittest.main(verbosity=2)
