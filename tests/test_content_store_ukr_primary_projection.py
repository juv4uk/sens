"""Точкова перевірка повної укр-проєкції content-store без нової семантики."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "lib" / "content-store.lisp"
D9_PATH = ROOT / "lib" / "domains" / "d9.lisp"

RESIDENTS = {
    "000010111": ("вміст-сховище-розмір", "content-store-size"),
    "000011110": ("вміст-сховище-містить?", "content-store-contains?"),
    "000100000": ("вміст-сховище-отримати", "content-store-get"),
    "000100001": ("порожній-вміст-сховище", "empty-content-store"),
    "000101101": ("вміст-сховище-покласти", "content-store-put"),
    "000111111": ("вміст-сховище-покласти-світ", "content-store-put-world"),
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


class ContentStoreUkrPrimaryProjectionTests(unittest.TestCase):
    def test_exact_nine_bit_residents_match_d9_table(self):
        source, d9 = read_sources()
        rows = {
            match.group("bits"): (match.group("ukr"), match.group("en"))
            for match in DOMAIN_ROW.finditer(d9)
        }
        for bits, expected in RESIDENTS.items():
            with self.subTest(bits=bits):
                self.assertEqual(len(bits), 9)
                self.assertEqual(rows.get(bits), expected)

    def test_full_ukr_definitions_are_primary_lisp_closures(self):
        source, _ = read_sources()
        primary = source
        for _bits, (ukr, _english) in RESIDENTS.items():
            with self.subTest(name=ukr):
                self.assertRegex(
                    primary,
                    rf"(?m)^\(визначити\s+{re.escape(ukr)}\s+\(функція\b",
                )

    def test_full_file_is_ukrainian_without_duplicate_english_definitions(self):
        source, _ = read_sources()
        self.assertIsNone(re.search(r"[A-Za-z]", source))
        for _bits, (_ukr, english) in RESIDENTS.items():
            with self.subTest(name=english):
                self.assertNotRegex(
                    source,
                    rf"(?m)^\\(визначити\\s+{re.escape(english)}(?=\\s|\\))",
                )

    def test_no_raw_binary_call_heads_or_reinferred_width(self):
        source, _ = read_sources()
        self.assertNotRegex(source, r"\(\s*[01]{9}(?:\s|\))")
        self.assertIn("не вводить нових координат", source)
        self.assertNotIn("(визначити 168 ", source)
        self.assertNotIn("(binary 9)", source)

    def test_composition_still_uses_existing_address_and_map_laws(self):
        source, _ = read_sources()
        for required in (
            "(функція () мапа-порожній)",
            "(внутрішня-мапа-вставити (знання-вміст-адреса значення) значення сховище)",
            "(внутрішня-мапа-отримати адреса сховище)",
            "(внутрішня-мапа-містить адреса сховище)",
            "(довжина сховище)",
            "(світ-адреса-вміст світ)",
        ):
            with self.subTest(expression=required):
                self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
