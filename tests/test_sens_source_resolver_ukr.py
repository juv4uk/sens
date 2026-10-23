#!/usr/bin/env python3
"""Точна українська identity резолвера; історичний SID8 не надає викличності."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from sens_source_resolver import (
    HistoricalRow,
    SourceResolver,
    load_current_foundation,
    load_domain_surfaces,
)


class CurrentUkrainianResolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.labels, cls.words = load_current_foundation(
            ROOT / "knowledge" / "d1-d7-foundation.json"
        )
        cls.surfaces = load_domain_surfaces(
            [ROOT / "lib" / "domains" / f"d{width}.lisp" for width in range(3, 7)],
            cls.words,
        )
        cls.resolver = SourceResolver(
            # Умисно небезпечний історичний рядок: НЕ authority.
            [HistoricalRow("00000101", "старе-перше", "OLD-CAR", "history", "yes", "old")],
            cls.labels,
            cls.words,
            cls.surfaces,
            {"00000101": [("ук", "фальшиве-перше")]},
            {"фальшиве-перше": {"00000101"}},
        )

    def test_current_ukr_projection_matches_ratified_d3(self):
        actual = self.resolver.resolve_head("перше")
        self.assertEqual(actual.current, self.words[(3, "100")])
        self.assertEqual(actual.current.domain, "D3")
        self.assertEqual(actual.pass_number, 2)

    def test_current_ukr_projection_matches_ratified_d6(self):
        actual = self.resolver.resolve_head("відобразити")
        self.assertEqual(actual.current, self.words[(6, "101000")])
        self.assertEqual(actual.current.domain, "D6")

    def test_current_wide_ukr_surfaces_preserve_domain_and_never_promote_sid8(self):
        # Діагностика, не runtime-допуск: кожне ім'я береться з колонки укр.
        labels, words = load_current_foundation(
            ROOT / "knowledge" / "d1-d11-foundation.json"
        )
        surfaces = load_domain_surfaces(
            [ROOT / "lib" / "domains" / f"d{width}.lisp"
             for width in (3, 4, 5, 6, 8, 9, 10)],
            words,
        )
        resolver = SourceResolver([], labels, words, surfaces, {}, {})
        for name, width, bits in (
            ("символ-за-кодом", 8, "00000000"),
            ("пояснити-відповідь", 9, "000000001"),
            ("відсутня-можливість-виконання", 10, "0000000000"),
        ):
            with self.subTest(name=name):
                result = resolver.resolve_head(name)
                self.assertEqual(result.current, words[(width, bits)])
                self.assertTrue(result.resolved)
        # D6:MAP і D8:MAP не повинні зливатися за історичною міткою.
        self.assertNotIn("MAP", labels)
        self.assertEqual(words[(6, "101000")].domain, "D6")
        with self.assertRaisesRegex(ValueError, "retired SID8-era head"):
            resolver.resolve_head("00000000")
        self.assertNotIn((7, "0000000"), words)

    def test_exact_current_d3_word_is_not_a_legacy_byte(self):
        actual = self.resolver.resolve_head("100")
        self.assertEqual(actual.current, self.words[(3, "100")])
        self.assertEqual(actual.kind, "current-exact")

    def test_historical_sid8_cannot_infer_current_car_identity(self):
        with self.assertRaisesRegex(ValueError, "retired SID8-era head"):
            self.resolver.resolve_head("00000101")

    def test_eight_bit_d8_collision_is_not_interpreted_as_historical_identity(self):
        # D8:10110001 належить чинній таблиці D8; цей D3–D6
        # resolver НЕ має D8-контексту і не вгадує identity за шириною.
        with self.assertRaisesRegex(ValueError, "retired SID8-era head"):
            self.resolver.resolve_head("10110001")

    def test_historical_name_does_not_promote_new_resident(self):
        name = self.resolver.resolve_head("OLD-CAR")
        self.assertIsNone(name.current)
        self.assertFalse(name.resolved)
        self.assertEqual(name.pass_number, 3)

    def test_old_my_lisp_name_does_not_become_ukrainian_alias(self):
        name = self.resolver.resolve_head("старе-перше")
        self.assertIsNone(name.current)
        self.assertFalse(name.resolved)
        self.assertEqual(name.pass_number, 2)

    def test_registry_sid_surface_does_not_create_ukrainian_alias(self):
        name = self.resolver.resolve_head("фальшиве-перше")
        self.assertIsNone(name.current)
        self.assertFalse(name.resolved)
        # Старий SID8-реєстр сам по собі не є навіть підставою
        # позначати сучасний динамічний виклик як legacy-unmapped.
        self.assertEqual(name.kind, "dynamic-symbol-head")
        self.assertEqual(name.pass_number, 0)
        self.assertFalse(name.legacy_unmapped)
        self.assertFalse(any(item.startswith("legacy-sid:") for item in name.evidence))

    def test_existing_ratified_lisp_spelling_remains_current(self):
        name = self.resolver.resolve_head("CAR")
        self.assertEqual(name.current, self.words[(3, "100")])

    def test_unqualified_decimal_text_is_not_a_math_operand(self):
        name = self.resolver.resolve_head("24")
        self.assertIsNone(name.current)
        self.assertEqual(name.kind, "dynamic-symbol-head")


if __name__ == "__main__":
    unittest.main()
