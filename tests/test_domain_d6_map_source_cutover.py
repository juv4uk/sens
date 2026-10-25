#!/usr/bin/env python3
"""Регресійна перевірка джерел D6 MAP після переходу до точних доменів.

Чинний D8 окремо ратифіковано 2026-10-06 (#3960). Історичний
SID8 не був його попередньою версією і не визначає D8-координат.
Це механічна перевірка джерел, не семантичний оракул чи HOLD для D8.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


КОРІНЬ = Path(__file__).resolve().parents[1]
ДЖЕРЕЛА = {
    "lib/yantra.lisp": 0,  # оновлено 2026-10-25: старих викликів (101000 немає; другий ассерт тесту це підтверджує
    "lib/linter.lisp": 0,  # оновлено 2026-10-25: старих викликів (101000 немає
    "lib/core.lisp": 0,
    "lib/knowledge.lisp": 0,
}
ВИКЛИК_Д6 = re.compile(r"\(101000(?=\s|\))")
ВИКЛИК_СТАРИЙ = re.compile(r"\(00110111(?=\s|\))")


class ПеревіркиТочногоДоменуMap(unittest.TestCase):
    def test_чинні_D6_та_D8_ратифіковані_незалежно(self):
        foundation = json.loads(
            (КОРІНЬ / "knowledge/d1-d9-foundation.json").read_text(encoding="utf-8")
        )
        current_d8 = json.loads(
            (КОРІНЬ / "knowledge/d8-ratified.json").read_text(encoding="utf-8")
        )
        self.assertEqual(foundation["domains"]["D6"]["residents"]["101000"], "MAP")
        self.assertEqual(current_d8["authority"], "#3960")
        self.assertEqual(current_d8["date"], "2026-10-06")
        self.assertEqual(current_d8["status"], "owner-ratified")
        self.assertEqual(current_d8["width"], 8)
        self.assertEqual(current_d8["occupancy"], 256)
        self.assertEqual(current_d8["residents"]["11000101"], "MAP")

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


if __name__ == "__main__":
    unittest.main()
