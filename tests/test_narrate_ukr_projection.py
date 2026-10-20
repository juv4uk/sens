"""Точкова перевірка чинного укр-контракту Narrate й exact D9 identity."""
from __future__ import annotations

from pathlib import Path
import unittest

from tests.test_ukr_narrate_peers import call_heads, definitions

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/narrate.lisp"

# Historical raw encodings must never return as executable heads.
OLD_DERIVED = "(0011 provenance-derived-from (0010 (prov) (1001 (110110101 prov))))"
OLD_SYMBOL_CHECK = "((0100 (110101100 (100 outcome)))"
ЗАСТАРІЛИЙ_ПСЕВДОНІМ = "(визначити provenance-derived-from походження-похідний-з)"

IDENTITIES = (
    (3, "100", "перше"),
    (4, "0011", "визначити"),
    (4, "0010", "функція"),
    (4, "1001", "друге"),
    (4, "0100", "хибне?"),
    (9, "000011100", "походження-похідний-з"),
    (9, "110110101", "п'ятий"),
    (9, "110101100", "символ?"),
)


def verify(source: str) -> None:
    if ЗАСТАРІЛИЙ_ПСЕВДОНІМ in source:
        raise AssertionError("англійський псевдонім походження повернувся")
    if OLD_DERIVED in source or OLD_SYMBOL_CHECK in source:
        raise AssertionError("застаріла сира бітова голова повернулася")
    parsed = definitions(source)
    if parsed.get("походження-похідний-з") != [
        "функція", ["походження"], ["друге", ["п'ятий", "походження"]]
    ]:
        raise AssertionError("порушено український D9 accessor походження")
    if "provenance-derived-from" in parsed:
        raise AssertionError("англійський псевдонім походження повернувся")
    if parsed.get("пояснити-підсумок") is None:
        raise AssertionError("втрачено повну укр-функцію підсумку")
    heads = call_heads(parsed["пояснити-підсумок"])
    if "символ?" not in heads or "текст?" in heads:
        raise AssertionError("перевірка форми підсумку змінила D9 predicate")


class NarrateProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_current_ukr_contract_and_no_raw_heads(self):
        verify(self.source)

    def test_exact_domain_projection_authority(self):
        for width, bits, ukr in IDENTITIES:
            with self.subTest(domain=width, bits=bits):
                rows = [
                    line.strip() for line in
                    (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8").splitlines()
                    if line.lstrip().startswith(f"({bits} ")
                ]
                self.assertEqual(len(rows), 1)
                self.assertIn(f"(укр {ukr})", rows[0])

    def test_negative_wrong_d9_successor_rejected(self):
        broken = self.source.replace("п'ятий походження", "четверте походження", 1)
        self.assertNotEqual(broken, self.source)
        with self.assertRaisesRegex(AssertionError, "accessor походження"):
            verify(broken)

    def test_negative_wrong_predicate_rejected(self):
        broken = self.source.replace("(символ? (перше підсумок))",
                                     "(текст? (перше підсумок))", 1)
        self.assertNotEqual(broken, self.source)
        with self.assertRaisesRegex(AssertionError, "D9 predicate"):
            verify(broken)

    def test_negative_return_of_english_alias_rejected(self):
        broken = self.source + "\n(визначити provenance-derived-from пояснити-факт)\n"
        self.assertNotEqual(broken, self.source)
        with self.assertRaisesRegex(AssertionError, "англійський псевдонім"):
            verify(broken)


if __name__ == "__main__":
    unittest.main(verbosity=2)
