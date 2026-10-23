#!/usr/bin/env python3
"""Статичний контроль чинної української TCP-проєкції.

Не обчислює предикати через Python: SENS виконує D1/COND і фізичний
свідок у crates/sens/tests/tcp_d1_fallback.rs.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/tcp.lisp"
NAMES = (
    "протокол-передавання-слухати-на",
    "протокол-передавання-слухати",
    "протокол-передавання-читати-байти-текст",
    "протокол-передавання-читати",
    "протокол-передавання-записати-текст-байти",
    "протокол-передавання-записати-через-сирий",
    "протокол-передавання-записати",
)


def перевірити(джерело: str):
    код = "\n".join(рядок for рядок in джерело.splitlines()
                    if not рядок.lstrip().startswith(";"))
    for назва in NAMES:
        if not re.search(r"(?m)^\s*\(визначити\s+" + re.escape(назва) + r"(?=\s|\))", код):
            raise ValueError(f"відсутня українська TCP-функція: {назва}")
    if re.search(r"\(\s*[01]{3,10}(?=\s|\))", код):
        raise ValueError("виклична голова старого бітового представлення")
    if re.search(r"#(?:[dD][0-9]+:|[bB][01]+|[qQ]2:)", код):
        raise ValueError("доменний літерал у людській проєкції")
    if "(атом? (як-є ()))" not in код:
        raise ValueError("відсутня обчислювана D1:YES замість старого #d1:1")
    if "(кодування-юнікод-8-декодувати-рядок " not in код:
        raise ValueError("відсутній власний кодек SENS")
    return код


class TcpCurrentUkrProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_live_tcp_is_ukrainian_and_has_derived_d1(self):
        код = перевірити(self.source)
        self.assertEqual(код.count("(визначити "), len(NAMES))
        self.assertEqual(код.count("(атом? (як-є ()))"), 2)

    def test_ratified_core_coordinates(self):
        for width, bits, surface in (
            (3, "001", "як-є"),
            (3, "010", "атом?"),
            (3, "101", "тотожне?"),
            (3, "110", "за-умовою"),
            (4, "0010", "функція"),
            (4, "0011", "визначити"),
        ):
            table = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
            self.assertRegex(
                table,
                r"(?m)^\s*\(" + bits + r"\s+\(ук\s+[^()\s]+\)\s+\(укр\s+"
                + re.escape(surface) + r"\)",
            )

    def test_historical_carrier_mutations_are_rejected(self):
        for before, after in (
            ("(визначити ", "(0011 "),
            ("(атом? (як-є ()))", "#d1:1"),
            ("(кодування-юнікод-8-декодувати-рядок ", "(010 "),
        ):
            self.assertIn(before, self.source)
            with self.subTest(after=after), self.assertRaises(ValueError):
                перевірити(self.source.replace(before, after, 1))


if __name__ == "__main__":
    unittest.main()
