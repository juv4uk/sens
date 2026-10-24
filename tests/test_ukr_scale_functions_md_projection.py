"""Exact-width Ukrainian call-head projection regressions for two active scripts.

No host Lisp semantics, domain-table writes, file mutation or CI workflow edits.
The original blob is reconstructed by reversing ONLY proven D3/D4 executable
head substitutions; byte-for-byte Git blob equality proves scope and data safety.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
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
# D5/D6/D8/D9 поверхні, додані під час повної міграції generate-functions-md.
# Окремо від PEERS: той набір лишається доведеним 3/4-бітним ядром D3/D4.
WIDE_PEERS = {
    "01010": "додати", "11010": "менше?", "10111": "частка", "101110": "згорнути",
    "001000": "нехай", "00101100": "модульна-остача",
    "01000111": "відобразити-доки-істина",
    "110011100": "рядок-порожній?", "110011101": "рядок-решта",
    "110011110": "рядок-додати", "110100010": "рядок-довжина",
    "110100011": "рядок-зріз", "110101001": "читати-всі",
    "110101010": "рядок-префікс?", "11011011": "друкувати",
    "110110111": "читати-файл", "110111100": "записати-файл",
    "11101110": "символ-у-текст", "11110111": "однакові?",
}
INVERSE = {v: k for k, v in {**PEERS, **WIDE_PEERS}.items()}
SPECS = {
    "scripts/check-core4-predicate-answer-scale.lisp": {
        "sha": "e3dc929c6c9d92f8d19124f460a44252ea83549a",
        "counts": {"100": 4, "110": 1, "1001": 2, "1110": 5,
                   "001": 59, "011": 2, "0010": 4, "0011": 15},
    },
    "scripts/generate-functions-md.lisp": {
        "sha": "dac56932a768d3ea69a3901290a1c7a7fd3113f8",
        "counts": {"001": 7, "0010": 13, "0011": 18, "010": 12, "011": 8,
                   "100": 10, "101": 4, "110": 15, "111": 1, "1001": 4,
                   "1110": 3, "001000": 6, "01010": 5, "10111": 1, "101110": 1,
                   "11010": 4, "00101100": 1, "01000111": 1, "110011100": 1,
                   "110011101": 1, "110011110": 2, "110100010": 1,
                   "110100011": 2, "110101001": 1, "110101010": 1,
                   "11011011": 4, "110110111": 2, "110111100": 2,
                   "11101110": 1, "11110111": 7},
    },
}


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
                text = (ROOT / path).read_text(encoding="utf-8")
                count = verify(path, text)
                self.assertEqual(count, sum(expected["counts"].values()))

    def test_quoted_numeric_data_left_untouched(self):
        source = (ROOT / "scripts" /
                  "check-core4-predicate-answer-scale.lisp").read_text(
                      encoding="utf-8"
                  )
        self.assertIn("(001 (00000000 11111111))", source)
        self.assertIn("(001 ((0) () (1)))", source)
        self.assertEqual(source.count("(001 (1))"), 7)
        self.assertNotIn("(як-є (00000000 11111111))", source)

    def test_wrong_ukr_peer_is_rejected_by_inverse(self):
        path = "scripts/generate-functions-md.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
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
        self.assertEqual(len(set(INVERSE)), len(PEERS) + len(WIDE_PEERS))
        # Neither scripts nor this test edit the ratified table.
        self.assertTrue(all(re.fullmatch("[01]{3,4}", b) for b in PEERS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
