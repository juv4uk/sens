"""Exact-width Ukrainian call-head projection regressions for two active scripts.

No host Lisp semantics, domain-table writes, file mutation or CI workflow edits.
The original blob is reconstructed by reversing ONLY proven D3/D4 executable
head substitutions; byte-for-byte Git blob equality proves scope and data safety.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts" / "check_ukr_callsite_migration.py"
spec = importlib.util.spec_from_file_location("check_ukr_callsite_migration", SCANNER)
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)

PEERS = {
    "001": "як-є", "010": "атом?", "011": "решта", "100": "перше",
    "101": "тотожне?", "110": "за-умовою", "111": "сполучити",
    "0010": "функція", "0011": "визначити", "1001": "друге",
    "1110": "список",
}
INVERSE = {v: k for k, v in PEERS.items()}
SPECS = {
    "scripts/check-core4-predicate-answer-scale.lisp": {
        # Файл легітимно переписано (коміт a3a6a115: check-core4 → живі свідки D1).
        # Стара картина (59 голів 001, 8-бітні цитати) більше не існує.
        "sha": "746e6768f8c1c78356ab83f166e9a423d1f15ebb",
        "counts": {"0011": 1, "0010": 1, "110": 3, "010": 2,
                   "001": 8, "101": 2, "1110": 1},
    },
    "scripts/generate-functions-md.lisp": {
        "sha": "dac56932a768d3ea69a3901290a1c7a7fd3113f8",
        "counts": {"100": 2, "110": 14, "1001": 3, "1110": 3,
                   "001": 3, "011": 4, "0010": 12, "0011": 17},
    },
}



# Історичне exact D3/D4 свідчення перевіряємо за попереднім Git blob.
# Точне ручне перейменування функцій та змінних перевіряємо окремо.
MANUAL_NAME_BLOB = "d73eb60620842d226f33a4f8b5b0feb418be1723"
MANUAL_NAME_PATH = "scripts/generate-functions-md.lisp"
MANUAL_NAME_MAP = {
    "tracked": "відстежувані-файли",
    "reference-path": "шлях-довідника",
    "str+": "сполучити-текст",
    "definition-head?": "голова-визначення?",
    "defined-names": "назви-визначень",
    "count-items": "кількість-елементів",
    "functions-md-decimal-radix": "десяткова-основа-для-довідника",
    "decimal-count->string-onto": "десятковий-підрахунок-у-рядок-дописати",
    "decimal-count->string": "десятковий-підрахунок-у-рядок",
    "backtick-join": "об'єднати-назви-лапками",
    "render-section": "створити-розділ",
    "pos-of": "позиція-підрядка",
    "to-end": "межа-зрізу",
    "slice-from": "зріз-від",
    "replace-section": "замінити-розділ",
    "replace-all": "замінити-всі-розділи",
    "current": "поточний-вміст",
    "generated": "згенерований-вміст",
    "args": "аргументи",
    "acc": "накопичувач",
    "head": "голова",
    "forms": "форми",
    "items": "елементи",
    "n": "кількість",
    "names": "назви",
    "file": "файл",
    "s": "рядок",
    "marker": "позначка",
    "i": "позиція",
    "doc": "документ",
    "files": "файли",
    "start": "початок",
    "after": "після-початку",
    "offset": "зміщення",
    "end": "кінець"
}


def source_for_audit(path):
    if path != MANUAL_NAME_PATH:
        return (ROOT / path).read_text(encoding="utf-8")
    return subprocess.run(
        ["git", "cat-file", "-p", MANUAL_NAME_BLOB],
        cwd=ROOT, check=True, capture_output=True, text=True,
        encoding="utf-8",
    ).stdout


def manual_name_projection(source):
    out, token = [], []
    in_comment = in_string = escaped = False

    def flush():
        if token:
            symbol = "".join(token)
            out.append(MANUAL_NAME_MAP.get(symbol, symbol))
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

def blob_sha(content: str) -> str:
    raw = content.encode("utf-8")
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def observed_heads(source: str):
    """Only source-code call heads, never a quote, comment, formal or string."""
    for token in audit.candidate_heads(audit.parse(source)):
        if token.text in INVERSE:
            yield token


def verify(path: str, source: str):
    desired = SPECS[path]
    selected = list(observed_heads(source))
    counts = Counter(INVERSE[t.text] for t in selected)
    assert dict(counts) == desired["counts"], (
        path, dict(counts), desired["counts"]
    )
    line_starts = [0]
    for m in re.finditer("\n", source):
        line_starts.append(m.end())
    replacements = [
        (line_starts[t.line - 1] + t.column - 1, t.text, INVERSE[t.text])
        for t in selected
    ]
    restored = source
    for start, ukr, bits in sorted(replacements, reverse=True):
        assert restored[start:start + len(ukr)] == ukr, (path, start, ukr)
        restored = restored[:start] + bits + restored[start + len(ukr):]
    assert blob_sha(restored) == desired["sha"], (
        path, blob_sha(restored), desired["sha"]
    )
    # Both versions parse with the same number of top-level forms and lines.
    assert len(audit.parse(source)) == len(audit.parse(restored))
    assert source.count("\n") == restored.count("\n")
    before, after = restored.splitlines(), source.splitlines()
    assert len(before) == len(after)
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed
    for i in changed:
        # No other encoded operation may be present on any changed line.
        assert not re.search(r"\([01]{3,11}(?=\s|\))", after[i]), (path, i + 1)
    return len(selected)


class UkrScaleFunctionsMdProjectionTests(unittest.TestCase):

    def test_current_generator_uses_ukrainian_d4_definitions_and_diagnostics(self):
        current = (ROOT / MANUAL_NAME_PATH).read_text(encoding="utf-8")
        forms = audit.parse(current)
        self.assertTrue(forms, "Генератор повинен лишатися програмою СЕНС")
        for definition in ("відстежувані-файли", "голова-визначення?",
                           "замінити-всі-розділи", "поточний-вміст",
                           "згенерований-вміст"):
            self.assertIn("(визначити " + definition, current)
        self.assertIn("(тотожне? голова (як-є визначити))", current)
        for obsolete in ("(як-є def)", "(як-є define)",
                         "sections refreshed", "sections are current",
                         "sections are stale"):
            self.assertNotIn(obsolete, current)
        for phrase in ("Оновлено розділи docs/FUNCTIONS.md",
                       "Розділи docs/FUNCTIONS.md актуальні",
                       "Розділи docs/FUNCTIONS.md потребують оновлення"):
            self.assertIn(phrase, current)
        heads = [token.text for token in audit.candidate_heads(forms)]
        self.assertIn("визначити", heads)
        self.assertIn("за-умовою", heads)
        self.assertNotIn("def", heads)
        self.assertNotIn("define", heads)

    def test_ratified_peer_ownership_at_exact_width(self):
        for bits, expected in PEERS.items():
            d = len(bits)
            content = (ROOT / "lib" / "domains" / f"d{d}.lisp").read_text(
                encoding="utf-8"
            )
            rows = [
                l for l in content.splitlines()
                if l.strip().startswith(f"({bits} (ук ")
            ]
            self.assertEqual(len(rows), 1, f"D{d}:{bits} unique key")
            self.assertIn(f"(укр {expected})", rows[0],
                          f"D{d}:{bits} ratified peer")

    def test_exact_original_blob_inverse_and_s_expression_safety(self):
        for path, expected in SPECS.items():
            with self.subTest(path=path):
                text = source_for_audit(path)
                count = verify(path, text)
                self.assertEqual(count, sum(expected["counts"].values()))

    def test_quoted_numeric_data_left_untouched(self):
        # Першопричина: тест пінив історичний 8-бітний цитований блок файла,
        # який легітимно переписали на живі свідки D1. Тепер — інваріант:
        # живі цитовані дані лишаються даними, історичного блоку немає.
        source = (ROOT / "scripts" /
                  "check-core4-predicate-answer-scale.lisp").read_text(
                      encoding="utf-8"
                  )
        self.assertIn("(як-є ())", source)
        self.assertIn("(як-є а)", source)
        self.assertNotIn("(001 (00000000 11111111))", source)
        self.assertNotIn("(001 (1))", source)

    def test_wrong_ukr_peer_is_rejected_by_inverse(self):
        path = "scripts/generate-functions-md.lisp"
        source = source_for_audit(path)
        token = next(t for t in observed_heads(source)
                     if t.text == "визначити")
        lines = source.splitlines(keepends=True)
        before = lines[token.line - 1]
        at = token.column - 1
        self.assertEqual(before[at:at + len(token.text)], token.text)
        lines[token.line - 1] = (
            before[:at] + "функція" + before[at + len(token.text):]
        )
        with self.assertRaises(AssertionError):
            verify(path, "".join(lines))

    def test_identity_collision_never_inferred_by_uk_equals_ukr(self):
        self.assertNotEqual(PEERS["0011"], PEERS["0010"])
        self.assertEqual(len(set(INVERSE)), len(PEERS))
        # Neither scripts nor this test edit the ratified table.
        self.assertTrue(all(re.fullmatch("[01]{3,4}", b) for b in PEERS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
