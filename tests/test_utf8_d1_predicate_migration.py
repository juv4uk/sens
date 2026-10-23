#!/usr/bin/env python3
"""Лише статичний контроль українського джерела UTF-8, не емулятор SENS.

Семантичні позитивні/негативні свідки виконуються через власний SENS
у crates/sens/tests/utf8.rs; Python не визначає значення предикатів.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/utf8.lisp"
NAMES = (
    "кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні?",
    "це-байт-продовження-кодування-юнікод-8?",
    "це-допустимий-байт-кодування-юнікод-8?",
    "усі-елементи-є-байтами-кодування-юнікод-8?",
    "наявні-два-байти-продовження-кодування-юнікод-8?",
    "кодування-юнікод-8-декодувати",
    "кодування-юнікод-8-декодувати-рядок",
    "кодування-юнікод-8-кодувати-рядок",
)


def перевірити(джерело: str) -> None:
    код = "\n".join(рядок for рядок in джерело.splitlines()
                    if not рядок.lstrip().startswith(";"))
    for назва in NAMES:
        if not re.search(r"(?m)^\s*\(визначити\s+" + re.escape(назва) + r"(?=\s|\))", код):
            raise ValueError(f"відсутнє українське визначення: {назва}")
    if re.search(r"\(\s*[01]{3,10}(?=\s|\))", код):
        raise ValueError("бітова виклична голова замість української")
    if re.search(r"#(?:[dD][0-9]+:|[bB][01]+|[qQ]2:)", код):
        raise ValueError("історичний текстовий носій замість проєкції")
    if not re.search(r"\(атом\?\s+\(як-є\s+\(\)\)\)", код):
        raise ValueError("відсутнє похідне D1:YES")
    if not re.search(r"\(атом\?\s+\(як-є\s+\(\(\)\)\)\)", код):
        raise ValueError("відсутнє похідне D1:NO")


class Utf8UkrSourceAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_ukrainian_projection_without_historic_sid8(self):
        перевірити(self.source)

    def test_exact_domain_owners_not_flat_byte_aliases(self):
        for width, bits, surface in (
            (3, "101", "тотожне?"),
            (4, "0011", "визначити"),
            (5, "01010", "додати"),
            (5, "11010", "менше?"),
            (8, "00101100", "модульна-остача"),
            (9, "000001001", "кодування-юнікод-8-декодувати"),
            (9, "000001010", "кодування-юнікод-8-декодувати-рядок"),
            (9, "000010101", "кодування-юнікод-8-кодувати-рядок"),
        ):
            table = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
            self.assertRegex(
                table,
                r"(?m)^\s*\(" + bits + r"\s+\(ук\s+[^()\s]+\)\s+\(укр\s+"
                + re.escape(surface) + r"\)",
                f"D{width}:{bits} не дорівнює {surface}",
            )
        self.assertIn("(тотожне?", self.source)
        self.assertIn("(модульна-остача", self.source)

    def test_legacy_mutations_are_detected(self):
        for before, after in (
            ("(визначити ", "(0011 "),
            ("(модульна-остача ", "(00101100 "),
            ("(визначити ", "(визначити #d1:1 "),
        ):
            self.assertIn(before, self.source)
            with self.subTest(legacy=after), self.assertRaises(ValueError):
                перевірити(self.source.replace(before, after, 1))


if __name__ == "__main__":
    unittest.main()
