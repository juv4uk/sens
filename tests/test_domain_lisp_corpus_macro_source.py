#!/usr/bin/env python3
"""Інваріантний доказ сучасної проєкції `lib/macro.lisp`.

Першопричина. Раніше цей тест фіксував **історичний байт-образ** файла: точний
текст заголовка й точну форму виклику (`OLD_HEADER`/`NEW_HEADER`,
`OLD_CALLS`/`NEW_CALLS`, точний список голів `["make-macro", "01001101", ...]`).
Через це він червонів на **кожній** легітимній переробці файла й не міг
відрізнити законну міграцію від підміни — класичний «зелений тест, що міряє не
те». Файл справді переписали: хост-механізм `make-macro` з сирими 8-бітними
головами замінено на ратифіковану форму `(макрос (функція …))`.

Тепер перевіряється **інваріант**, а не байт-образ:
  * файл — це одна форма `(макрос (функція (сирі-форми) …))`;
  * у виконуваних позиціях немає сирих двійкових голів;
  * цитований шаблон розгортання збережено як дані;
  * негативні контролі провалюються закрито.

Історичний blob лишається лише як provenance у Git, не як пін.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "lib/macro.lisp"
ORIGINAL_BLOB = "b5b18ef9ba2430c1fc102c4ca08d2a33f62383f1"  # provenance, не пін

RAW_HEAD = re.compile(r"\(\s*([01]{2,11})(?=\s|\)|$)")
ENCODED = re.compile(r"#(?:d\d+:[01]+|b[01]+)")


def _reader():
    key = "_sens_macro_invariant_reader"
    spec = importlib.util.spec_from_file_location(
        key, ROOT / "scripts" / "migrate-three-pass.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def _strip_comments(source: str) -> str:
    out, i, n, state = [], 0, len(source), "code"
    while i < n:
        ch = source[i]
        if state == "code":
            if ch == ";":
                j = source.find("\n", i)
                j = n if j < 0 else j
                out.append(" " * (j - i))
                i = j
                continue
            if ch == '"':
                state = "string"
            out.append(ch)
            i += 1
            continue
        if ch == "\\":
            out.append("  ")
            i += 2
            continue
        if ch == '"':
            state = "code"
        out.append(ch)
        i += 1
    return "".join(out)


def raw_executable_heads(source: str) -> list[str]:
    code = _strip_comments(source)
    found = []
    for match in RAW_HEAD.finditer(code):
        found.append(match.group(1))
    return found


def top_head(source: str) -> str:
    module = _reader()
    forms = module.Parser(
        module.tokenize(module.strip_comments(source), source_surface="укр")
    ).parse_program()
    assert len(forms) == 1, f"очікується рівно одна форма, є {len(forms)}"
    head = forms[0].items[0]
    return head.tok.text


def check_invariant(source: str) -> None:
    """Інваріант сучасної проєкції; кидає ValueError, якщо порушено."""
    if top_head(source) != "макрос":
        raise ValueError("TOP_FORM: файл має бути (макрос (функція …))")
    if "(функція сирі-форми" not in source:
        raise ValueError("PARAMS: очікується (функція сирі-форми …)")
    raw = raw_executable_heads(source)
    if raw:
        raise ValueError("RAW_HEAD: сирий виконуваний голів: " + ", ".join(raw))
    if ENCODED.search(_strip_comments(source)):
        raise ValueError("ENCODED: машинний літерал у виконуваному коді")
    for quoted in ("(як-є визначити)", "(як-є макрос)", "(як-є функція)"):
        if quoted not in source:
            raise ValueError(f"QUOTE_DATA: втрачено цитований шаблон {quoted}")


class MacroProjectionInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.current = FILE.read_text(encoding="utf-8")

    def test_current_file_satisfies_invariant(self):
        check_invariant(self.current)

    def test_no_raw_executable_heads(self):
        self.assertEqual(raw_executable_heads(self.current), [])
        self.assertIsNone(ENCODED.search(_strip_comments(self.current)))

    def test_historical_blob_is_provenance_not_pin(self):
        # Файл більше не дорівнює історичному blob — це законна переробка.
        # Перевіряємо лише, що історичний blob існує в Git (provenance).
        import subprocess
        proc = subprocess.run(
            ["git", "cat-file", "-e", ORIGINAL_BLOB],
            cwd=ROOT, capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, "історичний blob відсутній у Git")

    def test_reintroduced_raw_head_fails_closed(self):
        mutant = self.current.replace("(макрос\n", "(01001101\n", 1)
        self.assertNotEqual(mutant, self.current)
        with self.assertRaisesRegex(ValueError, "TOP_FORM|RAW_HEAD"):
            check_invariant(mutant)

    def test_removed_quote_template_fails_closed(self):
        mutant = self.current.replace("(як-є визначити)", "(як-є щось-інше)", 1)
        self.assertNotEqual(mutant, self.current)
        with self.assertRaisesRegex(ValueError, "QUOTE_DATA"):
            check_invariant(mutant)

    def test_injected_encoded_literal_fails_closed(self):
        mutant = self.current.replace("(за-умовою", "(#d1:1", 1)
        self.assertNotEqual(mutant, self.current)
        with self.assertRaises(ValueError):
            check_invariant(mutant)


if __name__ == "__main__":
    unittest.main(verbosity=2)
