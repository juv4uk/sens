"""Точкова перевірка первинної D9-проєкції основних World-законів."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "lib" / "world.lisp"
D9_PATH = ROOT / "lib" / "domains" / "d9.lisp"
# Межу визначає перший реальний сумісний аліас, а не змінний коментар у Lisp.
ALIAS_MARKER = "(визначити advise-all-world порадити-всі-світ)"

RESIDENTS = {
    "111100001": ("створити-світ", "make-world"),
    "111001000": ("порожній-світ", "empty-world"),
    "111111000": ("світ-батько", "world-parent"),
    "111010100": ("світ-журнал", "world-journal"),
    "111000111": ("світ-метадані", "world-metadata"),
    "111111011": ("світ-запис", "world-record"),
    "111010101": ("світ-повідомити", "world-tell"),
    "111001010": ("світ-відкликати", "world-retract"),
    "111111111": ("знання-вміст-адреса", "knowledge-content-address"),
    "111110000": ("світ-адреса-вміст", "world-address-content"),
    "111100010": ("світ-вміст-адреса", "world-content-address"),
}

DOMAIN_ROW = re.compile(
    r"^\s*\((?P<bits>[01]{9})\s+"
    r"\(ук\s+[^()\s]+\)\s+"
    r"\(укр\s+(?P<ukr>[^()\s]+)\)\s+"
    r"\(san\s+[^()\s]+\)\s+"
    r"\(en\s+(?P<en>[^()\s]+)\)",
    re.MULTILINE,
)


def read_sources() -> tuple[str, str]:
    return (
        SOURCE_PATH.read_text(encoding="utf-8"),
        D9_PATH.read_text(encoding="utf-8"),
    )


class WorldUkrPrimaryProjectionTests(unittest.TestCase):
    def test_exact_nine_bit_residents_match_d9_table(self):
        _, d9 = read_sources()
        rows = {
            match.group("bits"): (match.group("ukr"), match.group("en"))
            for match in DOMAIN_ROW.finditer(d9)
        }
        for bits, expected in RESIDENTS.items():
            with self.subTest(bits=bits):
                self.assertEqual(len(bits), 9)
                self.assertEqual(rows.get(bits), expected)

    def test_full_ukr_names_are_primary_definitions(self):
        source, _ = read_sources()
        self.assertIn(ALIAS_MARKER, source)
        primary = source.split(ALIAS_MARKER, 1)[0]
        for bits, (ukr, _english) in RESIDENTS.items():
            with self.subTest(bits=bits, name=ukr):
                self.assertRegex(
                    primary,
                    rf"(?m)^\(визначити\s+{re.escape(ukr)}\s+\(функція\b",
                )

    def test_english_names_are_compatibility_aliases(self):
        source, _ = read_sources()
        aliases = source.split(ALIAS_MARKER, 1)[1]
        for _bits, (ukr, english) in RESIDENTS.items():
            with self.subTest(name=english):
                self.assertRegex(
                    aliases,
                    rf"(?m)^\(визначити\s+{re.escape(english)}\s+{re.escape(ukr)}\)\s*$",
                )

    def test_world_operations_compose_through_ukr_primary_names(self):
        source, _ = read_sources()
        primary = source.split(ALIAS_MARKER, 1)[0]
        primary_code = "\n".join(
            line for line in primary.splitlines()
            if not line.lstrip().startswith(";")
        )
        for required in (
            "(створити-світ (як-є ()) (як-є ()) (як-є ()))",
            "(світ-запис світ (список (як-є tell) назва-модуля клауза))",
            "(світ-запис світ (список (як-є retract) назва-модуля клауза))",
            "(світ-журнал світ)",
            "(світ-метадані світ)",
            "(значення-у-текст знання)",
            "(світ-адреса-вміст світ)",
            "(знання-вміст-адреса (світ-адреса-вміст світ))",
        ):
            with self.subTest(expression=required):
                self.assertIn(required, primary_code)

    def test_no_raw_binary_heads_or_unratified_helper_renames(self):
        source, _ = read_sources()
        self.assertNotRegex(source, r"\(\s*[01]{9}(?:\s|\))")
        primary = source.split(ALIAS_MARKER, 1)[0]
        for helper in (
            "світ?",
            "внутрішній-світ-прибрати-перше",
            "внутрішній-світ-застосувати-подію",
            "внутрішній-світ-розгорнути-історичний-перехід",
            "світ-різниця",
        ):
            with self.subTest(helper=helper):
                self.assertRegex(primary, rf"(?m)^\(визначити\s+{re.escape(helper)}\s")
        self.assertNotIn("(визначити 168 ", source)
        self.assertNotIn("(binary 9)", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
