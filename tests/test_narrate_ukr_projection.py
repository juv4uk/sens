"""Перевірка вузької міграції двох живих викликів Narrate.

Лише source/identity рівність. Цей Python-тест не імітує виконання SENS,
не надає D9 резидентам механізму виклику та не перевизначає закони.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

from tests.test_ukr_narrate_peers import definitions

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/narrate.lisp"
BASE_BLOB = "e888735c0f24d789f6a5691a3f569632c27f3e0b"

OLD_DERIVED = "(0011 provenance-derived-from (0010 (prov) (1001 (110110101 prov))))"
NEW_DERIVED = "(визначити provenance-derived-from (функція (prov) (друге (п'ятий prov))))"
OLD_SYMBOL_CHECK = "((0100 (110101100 (100 outcome)))"
NEW_SYMBOL_CHECK = "((хибне? (символ? (перше outcome)))"
LOCAL_CURRENT_TO_HISTORY = {
    "список-завершується-порожнім?": "narrate-proper-list?",
    "список-із-рівно-двох-елементів?": "narrate-list-exact-two?",
    "список-із-рівно-трьох-елементів?": "narrate-list-exact-three?",
}

IDENTITIES = (
    (3, "100", "перше"),
    (4, "0011", "визначити"),
    (4, "0010", "функція"),
    (4, "1001", "друге"),
    (4, "0100", "хибне?"),
    (9, "110110101", "п'ятий"),
    (9, "110101100", "символ?"),
)


def restore_local_helper_names(source: str) -> str:
    """Invert only active code symbols; comments and strings are data."""
    token = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();"]+|\s+|.')
    def restore(match: re.Match[str]) -> str:
        value = match.group()
        if value.startswith(";") or value.startswith('"') or value.isspace() or value in ("(", ")"):
            return value
        return LOCAL_CURRENT_TO_HISTORY.get(value, value)
    return token.sub(restore, source)


def _git_blob(source: str) -> str:
    data = source.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def verify(source: str) -> None:
    if source.count(NEW_DERIVED) != 1 or source.count(NEW_SYMBOL_CHECK) != 1:
        raise AssertionError("бракує однієї з двох українських виконуваних форм")
    if OLD_DERIVED in source or OLD_SYMBOL_CHECK in source:
        raise AssertionError("стара цифрова голова повернулася")
    original = source.replace(NEW_DERIVED, OLD_DERIVED).replace(
        NEW_SYMBOL_CHECK, OLD_SYMBOL_CHECK
    )
    original = restore_local_helper_names(original)
    if _git_blob(original) != BASE_BLOB:
        raise AssertionError("змінено щось, крім двох ратифікованих callsite")
    parsed = definitions(source)
    if parsed.get("provenance-derived-from") != [
        "функція", ["prov"], ["друге", ["п'ятий", "prov"]]
    ]:
        raise AssertionError("порушено похідний provenance accessor")


class NarrateProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_two_current_callsite_spelling_changes_only(self):
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
        broken = self.source.replace("п'ятий prov", "четверте prov", 1)
        self.assertNotEqual(broken, self.source)
        with self.assertRaises(AssertionError):
            verify(broken)

    def test_negative_wrong_predicate_rejected(self):
        broken = self.source.replace("(символ? (перше outcome))",
                                     "(текст? (перше outcome))", 1)
        self.assertNotEqual(broken, self.source)
        with self.assertRaises(AssertionError):
            verify(broken)

    def test_negative_quoted_data_or_extra_source_change_rejected(self):
        broken = self.source.replace("(як-є fact)", "(як-є changed-fact)", 1)
        self.assertNotEqual(broken, self.source)
        with self.assertRaisesRegex(AssertionError, "крім двох"):
            verify(broken)


if __name__ == "__main__":
    unittest.main(verbosity=2)
