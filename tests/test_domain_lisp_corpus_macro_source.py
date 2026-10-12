#!/usr/bin/env python3
"""Незалежний доказ точного перенесення нецитованих голів lib/macro.lisp.

Це source-delta/AST proof, а НЕ доведення виконуваності історичного макро.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_BLOB = "b5b18ef9ba2430c1fc102c4ca08d2a33f62383f1"
FILE = ROOT / "lib/macro.lisp"

OLD_HEADER = """; lib/macro.lisp — bootstrap derivation on exact 8-bit function identities.
;
; #1325: the language has one function-identity space: 00000000..11111111.
; Human words are not function identities.
;
; SID 00001010 is derived here from mechanisms already selected by:
;   00001001 + 00001000 + 00000100 + the narrow host Closure->Macro mechanism.
;
; `make-macro` below is NOT a my-lisp function identity. It is an explicit
; temporary host substrate with no SID and is tracked by #1330/#1328 until that
; boundary is removed or represented without creating a second function ontology.
;
; Every actual my-lisp function used below is invoked only by its eight bits.
; No SID is wrapped in a string, symbol, quote-label, or named identity.
"""
NEW_HEADER = """; lib/macro.lisp — часткова міграція bootstrap на точну драбину D3/D4.
;
; Зовнішні виконувані голови EVAL, CONS і QUOTE використовують ратифіковані
; D4:0001, D3:111, D3:001 відповідно. Історичні 8-бітні слова всередині
; (001 <шаблон>) є ЦИТОВАНИМИ ДАНИМИ, а не дозволом виконувати старий SID8.
; Їхню заміну разом зі старою COND треба довести окремим runtime-оракулом.
;
; make-macro — тимчасовий host-механізм без власної доменної тотожності
; (#1330/#1328); не створювати прихованої семантики макровизначення.
"""
OLD_CALLS = """(make-macro
  (01001101
    (00000100 (00000001 00001000)
      (00000100 (00000001 args)
        (00000001
"""
NEW_CALLS = """(make-macro
  (0001
    (111 (001 00001000)
      (111 (001 args)
        (001
"""


def original_blob() -> str:
    proc = subprocess.run(
        ["git", "cat-file", "blob", ORIGINAL_BLOB],
        cwd=ROOT, capture_output=True, check=True,
    )
    raw = proc.stdout
    calculated = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if calculated != ORIGINAL_BLOB:
        raise ValueError("PIN_DRIFT: оригінальний Git blob не збігається")
    return raw.decode("utf-8")


def expected_source() -> str:
    original = original_blob()
    if original.count(OLD_HEADER) != 1 or original.count(OLD_CALLS) != 1:
        raise ValueError("PIN_DRIFT: історичні call heads не тотожні еталону")
    return original.replace(OLD_HEADER, NEW_HEADER).replace(OLD_CALLS, NEW_CALLS)


def check_exact_source(source: str) -> None:
    if source != expected_source():
        raise ValueError("SOURCE_DELTA_BLOCK: змінено щось поза шістьма executable heads/коментарем")
    # Ці 8-бітні слова належать цитованому шаблону й лишаються даними.
    if "(00000111" not in source or "(00000010 args)" not in source:
        raise ValueError("QUOTE_DATA_BLOCK: шаблон макровизначення змінено")


class MacroDomainCutoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.current = FILE.read_text(encoding="utf-8")

    def test_exact_pinned_original_to_domain_delta(self):
        check_exact_source(self.current)

    def test_witness_rejects_quote_data_mutation(self):
        mutant = self.current.replace("(00000111", "(110", 1)
        self.assertNotEqual(mutant, self.current)
        with self.assertRaisesRegex(ValueError, "SOURCE_DELTA_BLOCK"):
            check_exact_source(mutant)

    def test_witness_rejects_reintroduced_flat_evaluator_head(self):
        mutant = self.current.replace("(0001\n", "(01001101\n", 1)
        self.assertNotEqual(mutant, self.current)
        with self.assertRaisesRegex(ValueError, "SOURCE_DELTA_BLOCK"):
            check_exact_source(mutant)

    def test_exact_owner_ratified_coordinates(self):
        import json
        foundation = json.loads(
            (ROOT / "knowledge/d1-d9-foundation.json").read_text(encoding="utf-8")
        )
        self.assertEqual(foundation["status"], "owner-ratified")
        for d, bits, name in (
            ("D4", "0001", "EVAL"),
            ("D3", "111", "CONS"),
            ("D3", "001", "QUOTE"),
        ):
            self.assertEqual(foundation["domains"][d]["residents"][bits], name)

    def test_executable_heads_only_never_traverse_quote_data(self):
        key = "_sens_migration_macro_ast_reader"
        spec = importlib.util.spec_from_file_location(
            key, ROOT / "scripts/migrate-three-pass.py"
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[key] = module
        spec.loader.exec_module(module)
        nodes = module.Parser(
            module.tokenize(module.strip_comments(self.current))
        ).parse_program()

        heads = []

        def walk(node):
            if not isinstance(node, module.ListNode) or not node.items:
                return
            first = node.items[0]
            if not isinstance(first, module.Atom):
                raise ValueError("UNKNOWN_HEAD: немає точного atom-голови")
            heads.append(first.tok.text)
            if first.tok.text in {"001", "00000001"}:
                return  # quote payload не є виконуваними Lisp call heads
            for child in node.items[1:]:
                walk(child)
            if node.tail is not None:
                walk(node.tail)

        for node in nodes:
            walk(node)
        self.assertEqual(
            heads, ["make-macro", "0001", "111", "001", "111", "001", "001"]
        )


if __name__ == "__main__":
    unittest.main()
