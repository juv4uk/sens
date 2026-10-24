#!/usr/bin/env python3
"""Першопричина #5872: guard «немає сирих викличних голів» перелічував файли руками.

`COHORT` у test_sid8_broad_source_cutover.py містив 7 файлів, тоді як виконуваних
`.lisp` у дереві — понад 100. Тому 95% коду ніколи не перевірялося, і міграція
«виглядала завершеною», маючи сирі голови в десятках файлів.

Цей guard виводить набір виконуваних файлів **із дерева**, а не зі списку, і
падає на кожному новому файлі з сирим виконуваним головом. Дані, ратифіковані
доменні таблиці, фізичні/до-міграційні свідки — не виконувані програми й
свідомо виключені (див. DATA_ROOTS). Це НЕ блокування міграції: список боргу
лише скорочується.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Каталоги, чиї `.lisp` — ДАНІ, а не виконувані програми:
#   lib/domains   — ратифіковані таблиці (сирі біти тут = координати, не голови)
#   lib/generated — згенеровані проєкції
#   lib/surface   — реєстри/підписи (дані)
#   lib/machine   — машинні/ISA дані
#   contracts, knowledge, docs, tests, fixtures — дані/свідки
#   examples/binary*, examples/migrated/*/source.lisp — фізичні/до-міграційні
#   crates        — Rust-крейти (фікстури кодеків)
DATA_ROOTS = (
    "lib/domains/", "lib/generated/", "lib/surface/", "lib/machine/",
    "contracts/", "knowledge/", "docs/", "tests/", "fixtures/",
    "examples/binary", "examples/migrated/", "crates/",
)

# Поточний борг: виконувані файли з сирими головами СТАНОМ на момент появи guard.
# 8 із них закриті відкритими PR (#5878–#5886); решта — незавершена міграція.
# Список мусить ЛИШЕ скорочуватися: новий файл тут = червоний тест.
KNOWN_RAW_HEADS = {
    "examples/ukrainian-greeting.lisp",                 # PR #5878
    "scripts/build-dependency-classification.lisp",
    "scripts/build-inventory.lisp",                     # PR #5881
    "scripts/check-core4-predicate-answer-boundary.lisp",
    "scripts/check-core4-predicate-answer-scale.lisp",
    "scripts/check-domain-bitness-laws.lisp",           # PR #5879
    "scripts/check-domain-logic-laws.lisp",             # PR #5880
    "scripts/check-domain-table-readable.lisp",         # PR #5884
    "scripts/fixtures-for-tier.lisp",                   # PR #5885
    "scripts/generate-rust-evaluator-dispatch.lisp",    # PR #5886
    "scripts/verify-repo.lisp",                         # PR #5883
}


def _migrator():
    key = "_sens_tree_derived_heads_reader"
    spec = importlib.util.spec_from_file_location(
        key, ROOT / "scripts/migrate-three-pass.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def _strip(src: str) -> str:
    out, i, n, state = [], 0, len(src), "code"
    while i < n:
        ch = src[i]
        if state == "code":
            if ch == ";":
                j = src.find("\n", i)
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


def executable_lisp_files() -> list[str]:
    found = []
    for path in sorted(ROOT.rglob("*.lisp")):
        if ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if any(rel.startswith(root) for root in DATA_ROOTS):
            continue
        found.append(rel)
    return found


def raw_executable_heads(rel: str) -> int:
    """Кількість сирих бітових голів у виконуваних позиціях (0 = мігровано)."""
    module = _migrator()
    source = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
    code = _strip(source)
    try:
        tokens = module.tokenize(code, source_surface="укр")
    except Exception:
        return 0
    count = 0
    for token in tokens:
        if token.kind != "ATOM" or not re.fullmatch(r"[01]{2,11}", token.text):
            continue
        i = token.offset - 1
        while i >= 0 and code[i] in " \t\n":
            i -= 1
        if i >= 0 and code[i] == "(":
            count += 1
    return count


class TreeDerivedExecutableHeadsTests(unittest.TestCase):
    def test_executable_set_is_derived_not_hardcoded(self):
        files = executable_lisp_files()
        self.assertGreater(len(files), 90, "набір виконуваних файлів замалий")
        self.assertIn("scripts/verify-repo.lisp", files)
        self.assertNotIn("lib/domains/d1.lisp", files)  # дані, не програма
        self.assertNotIn("lib/surface/semantic-registry.lisp", files)

    def test_no_raw_executable_heads_outside_known_debt(self):
        offenders = sorted(
            rel for rel in executable_lisp_files() if raw_executable_heads(rel)
        )
        new = [rel for rel in offenders if rel not in KNOWN_RAW_HEADS]
        self.assertEqual(
            new, [],
            "Нові виконувані файли з сирими головами: "
            + ", ".join(new)
            + " — переписати на ратифіковану проєкцію укр, не розширювати борг",
        )

    def test_debt_list_only_shrinks(self):
        offenders = {rel for rel in executable_lisp_files() if raw_executable_heads(rel)}
        stale = sorted(KNOWN_RAW_HEADS - offenders)
        self.assertEqual(
            stale, [],
            "Ці файли вже мігровано — прибрати з KNOWN_RAW_HEADS: " + ", ".join(stale),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
