#!/usr/bin/env python3
"""Перевірка українських викличних голів після міграції SID8.

Це лише перевірка поверхні джерел, не доказ виконання SENS чи T5M.
"""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ukr_callsite_audit_for_sid8_witness",
    ROOT / "scripts/check_ukr_callsite_migration.py",
)
assert SPEC and SPEC.loader
parser = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = parser
SPEC.loader.exec_module(parser)
# Першопричина: раніше тут був РУЧНИЙ перелік 7 файлів — інваріант «немає
# старих виконуваних голів» перевірявся лише для них, а не для дерева. Тепер
# набір виконуваних файлів виводиться з дерева (дані/таблиці/свідки — винятки).
NONPROGRAM_TREE_PATHS = (
    "lib/domains/", "lib/generated/", "contracts/", "knowledge/", "docs/",
    "tests/", "fixtures/", "examples/binary", "examples/migrated/", "crates/",
)


def executable_lisp_files():
    for path in sorted(ROOT.rglob("*.lisp")):
        if ".git" in path.parts or not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if any(rel.startswith(prefix) for prefix in NONPROGRAM_TREE_PATHS):
            continue
        yield rel, path


def executable_sites(source: str):
    """Відокремити викличні голови від коментарів, рядків та цитованих даних."""
    forms = parser.parse(source)

    def walk(node):
        if isinstance(node, parser.Prefix):
            # Цитата, квазіцитата і відкинута форма — не виконувані виклики.
            if node.marker in ("'", "#;", "`"):
                return
            if node.marker in (",", ",@"):
                yield from walk(node.datum)
            return
        if not isinstance(node, parser.Form) or not node.values:
            return
        head = parser.atom(node.values[0])
        if head in ("як-є", "quote", "001"):
            return
        if head in ("відобразити", "101000", "00110111", "00001001"):
            yield head, len(node.values) - 1, node.pos.line
        for child in node.values:
            yield from walk(child)

    for form in forms:
        yield from walk(form)


class TestBroaderSid8LispCutover(unittest.TestCase):
    def test_current_map_residents_have_separate_ratifed_domain_authority(self):
        # D6 and D8 are separately ratified current domains. Historical
        # сід8 MAP source cells cannot act as D8's earlier authority.
        foundation = json.loads((ROOT / "knowledge/d1-d9-foundation.json").read_text())
        current_d8 = json.loads((ROOT / "knowledge/d8-ratified.json").read_text())
        self.assertEqual(foundation["domains"]["D6"]["residents"]["101000"], "MAP")
        self.assertEqual(current_d8["status"], "owner-ratified")
        self.assertEqual(current_d8["authority"], "#3960")
        self.assertEqual(current_d8["date"], "2026-10-06")
        self.assertEqual(current_d8["width"], 8)
        self.assertEqual(current_d8["occupancy"], 256)
        self.assertEqual(current_d8["residents"]["11000101"], "MAP")
        self.assertEqual(
            foundation["domains"]["D8"]["residents"]["11000101"],
            current_d8["residents"]["11000101"],
        )

    def test_current_ukr_map_heads_keep_two_arguments(self):
        total = 0
        for rel, path in executable_lisp_files():
            with self.subTest(path=rel):
                source = path.read_text(encoding="utf-8")
                sites = list(executable_sites(source))
                old = [site for site in sites if site[0] != "відобразити"]
                self.assertFalse(old, f"{rel}: старі виконувані голови: {old}")
                maps = [site for site in sites if site[0] == "відобразити"]
                for head, arguments, line in maps:
                    self.assertEqual(arguments, 2, f"{rel}:{line}: {head}")
                total += len(maps)
        self.assertGreater(total, 0)

    def test_quoted_old_heads_are_data_not_migration_regressions(self):
        source = """
        ; (101000 a b) — коментар, не виклик
        (як-є ((101000 a b) (00001001 дані)))
        '(00110111 a b)
        #| вкладений #| (101000 a b) |# коментар |#
        (відобразити функція послідовність)
        """
        self.assertEqual([(head, argc) for head, argc, _ in executable_sites(source)], [("відобразити", 2)])

    def test_no_old_definition_call_heads_in_executable_cohort(self):
        for rel, path in executable_lisp_files():
            with self.subTest(path=rel):
                source = path.read_text(encoding="utf-8")
                old = [site for site in executable_sites(source) if site[0] == "00001001"]
                self.assertFalse(old, f"{rel}: застаріле виконуване визначення: {old}")

if __name__ == "__main__":
    unittest.main()
