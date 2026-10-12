#!/usr/bin/env python3
"""Регресійна перевірка джерел MAP після переходу до точних доменів.

Восьмибітний історичний запис 00110111 має ДВА різні можливі
нащадки: D6:101000 і D8:11000101. Жодна з цих координат
не стає виконуваним механізмом лише через збіг назви.
Це перевірка джерел, а не доказ виконуваності MAP в Core.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


КОРІНЬ = Path(__file__).resolve().parents[1]
ДЖЕРЕЛА = {
    "lib/yantra.lisp": 4,
    "lib/linter.lisp": 8,
    "lib/core.lisp": 0,
    "lib/knowledge.lisp": 0,
}
ВИКЛИК_Д6 = re.compile(r"\(101000(?=\s|\))")
ВИКЛИК_СТАРИЙ = re.compile(r"\(00110111(?=\s|\))")
ВИКЛИК_Д8 = re.compile(r"\(11000101(?=\s|\))")


class ПеревіркиТочногоДоменуMap(unittest.TestCase):
    def test_окремі_ратифіковані_координати(self):
        foundation = json.loads(
            (КОРІНЬ / "knowledge/d1-d9-foundation.json").read_text(encoding="utf-8")
        )
        self.assertEqual(foundation["domains"]["D6"]["residents"]["101000"], "MAP")
        self.assertEqual(foundation["domains"]["D8"]["residents"]["11000101"], "MAP")
        self.assertNotEqual(("D6", "101000"), ("D8", "11000101"))

    def test_неоднозначний_історичний_код_не_дає_одного_нащадка(self):
        audit = json.loads(
            (КОРІНЬ / "knowledge/sens8-current-coverage-v1.json").read_text(encoding="utf-8")
        )
        rows = [
            row for row in audit["rows"]
            if row["legacy_code"] == "00110111"
        ]
        self.assertEqual(len(rows), 1, "Історична комірка має бути однозначно знайдена")
        targets = set(
            re.findall(r"D[0-9]+:[01]+\s+MAP", rows[0].get("current_target") or "")
        )
        self.assertEqual(
            targets, {"D6:101000 MAP", "D8:11000101 MAP"},
            "Заборонено тихо призначати восьмибітному коду лише D6 або лише D8",
        )

    def test_перевірені_джерела_не_викликають_старий_восьмибітний_map(self):
        for path, кількість_д6 in ДЖЕРЕЛА.items():
            with self.subTest(джерело=path):
                source = (КОРІНЬ / path).read_text(encoding="utf-8")
                self.assertIsNone(
                    ВИКЛИК_СТАРИЙ.search(source),
                    f"{path}: історичний MAP лишився у вигляді виклику",
                )
                self.assertEqual(
                    len(ВИКЛИК_Д6.findall(source)), кількість_д6,
                    f"{path}: змінився перевірений зріз D6 MAP; потрібний новий доказ",
                )
                # Наявність однойменного D8 MAP у таблиці не є дозволом
                # автоматично переписати ці історичні односпискові виклики.
                self.assertIsNone(
                    ВИКЛИК_Д8.search(source),
                    f"{path}: підміна MAP на D8 потребує окремого доказу",
                )


if __name__ == "__main__":
    unittest.main()
