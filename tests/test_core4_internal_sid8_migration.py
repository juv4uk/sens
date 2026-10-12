#!/usr/bin/env python3
"""Побайтовий доказ вузької міграції внутрішніх викликів Core4.

Історичні 8-бітні внутрішні SID не мають власного ратифікованого
доменного викличного закону. Визначені в Lisp функції викликаються за
їхнім ім'ям у тому самому завантаженому середовищі. Це source witness,
не повний доказ runtime-parity.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/core4.lisp"
OLD_BLOB = "38c9c6d7f325f60105988596138d51a1238b68b0"
MIGRATED = {
    "00011111": "nondecreasing-from?",
    "00100000": "nonincreasing-from?",
}
CURRENT_DEFINE = "0011"   # D4 DEFINE, not legacy W8 00001001
CURRENT_LAMBDA = "0010"   # D4 LAMBDA
CURRENT_COND = "110"      # D3 COND

spec = importlib.util.spec_from_file_location(
    "_core4_exact_ast", ROOT / "scripts/cond-modernize.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("AST parser is unavailable")
parser = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parser
spec.loader.exec_module(parser)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\\0" + data).hexdigest()


def active_heads(source: str) -> Counter:
    """Лише виконувані голови: цитата/рядок/коментар не виклик."""
    counts: Counter = Counter()
    stack = list(parser.parse(source))
    while stack:
        node = stack.pop()
        if node.opaque or not node.children:
            continue
        head = node.children[0].atom
        if head is not None:
            counts[head] += 1
        if head in {"001", "00000001", "quote"}:
            continue
        stack.extend(node.children)
    return counts


def require_core4_invariants(source: str) -> None:
    forms = parser.parse(source)
    head_counts = active_heads(source)
    for old, name in MIGRATED.items():
        if head_counts[old] != 0:
            raise ValueError("застаріла виконувана SID8-голова: " + old)
        if head_counts[name] != 3:
            raise ValueError("порушений лічильник Lisp-голови " + name)
        matching = [
            form for form in forms
            if form.children
            and form.children[0].atom == CURRENT_DEFINE
            and len(form.children) >= 3
            and form.children[1].atom == name
            and form.children[2].children
            and form.children[2].children[0].atom == CURRENT_LAMBDA
        ]
        if len(matching) != 1:
            raise ValueError("відсутнє D4-визначення " + name)
    if head_counts[CURRENT_COND] < 1:
        raise ValueError("втрачено D3 COND")


class Core4InternalCutover(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_exact_six_head_migration_and_no_other_byte_changes(self):
        restored = self.source
        for old, name in MIGRATED.items():
            restored = restored.replace("(" + name + " ", "(" + old + " ")
        self.assertEqual(git_blob(restored.encode("utf-8")), OLD_BLOB)
        for old, name in MIGRATED.items():
            self.assertEqual(restored.count("(" + old + " "), 3)
            self.assertEqual(self.source.count("(" + name + " "), 3)

    def test_existing_lisp_defined_functions_replace_legacy_internal_slots(self):
        require_core4_invariants(self.source)

    def test_negative_old_internal_slot_is_rejected(self):
        mutated = self.source.replace("(nondecreasing-from? ", "(00011111 ", 1)
        with self.assertRaisesRegex(ValueError, "застаріла"):
            require_core4_invariants(mutated)

    def test_negative_missing_D4_definition_is_rejected(self):
        mutated = self.source.replace(
            "(0011 nonincreasing-from?", "(0011 disallowed-rename", 1
        )
        with self.assertRaisesRegex(ValueError, "відсутнє"):
            require_core4_invariants(mutated)

    def test_quoted_old_words_are_not_executable_heads(self):
        quoted = "(001 (00011111 x)) (quote (00100000 y))"
        counts = active_heads(quoted)
        self.assertEqual(counts["00011111"], 0)
        self.assertEqual(counts["00100000"], 0)


if __name__ == "__main__":
    unittest.main()
