"""Точкова перевірка первинної D9-проєкції persistent-vector."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "lib" / "persistent-vector.lisp"
D9_PATH = ROOT / "lib" / "domains" / "d9.lisp"
ALIAS_MARKER = "; opt-in повна укр-поверхня"

RESIDENTS = {
    "101010111": ("вектор-кількість", "vec-count"),
    "101011000": ("вектор-список", "vec->list"),
    "101011101": ("вектор-додати", "vec-conj"),
    "101101101": ("вектор-порожній", "vec-empty"),
    "101111011": ("вектор-з-список", "vec-from-list"),
    "110000010": ("вектор-н-тий", "vec-nth"),
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


class PersistentVectorUkrPrimaryProjectionTests(unittest.TestCase):
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

    def test_full_ukr_bindings_are_primary_definitions(self):
        source, _ = read_sources()
        self.assertIn(ALIAS_MARKER, source)
        primary = source.split(ALIAS_MARKER, 1)[0]
        for bits, (ukr, _english) in RESIDENTS.items():
            with self.subTest(bits=bits, name=ukr):
                self.assertRegex(primary, rf"(?m)^\(визначити\s+{re.escape(ukr)}\s+")
        # vec-empty deliberately stores an immutable empty-vector value.
        self.assertIn("(визначити вектор-порожній (сполучити", primary)
        for ukr, _english in (
            ("вектор-кількість", "vec-count"),
            ("вектор-список", "vec->list"),
            ("вектор-додати", "vec-conj"),
            ("вектор-з-список", "vec-from-list"),
            ("вектор-н-тий", "vec-nth"),
        ):
            with self.subTest(function=ukr):
                self.assertRegex(primary, rf"(?m)^\(визначити\s+{re.escape(ukr)}\s+\(функція\b")

    def test_english_names_are_compatibility_aliases(self):
        source, _ = read_sources()
        aliases = source.split(ALIAS_MARKER, 1)[1]
        for _bits, (ukr, english) in RESIDENTS.items():
            with self.subTest(name=english):
                self.assertRegex(
                    aliases,
                    rf"(?m)^\(визначити\s+{re.escape(english)}\s+{re.escape(ukr)}\)\s*$",
                )

    def test_exact_width_without_raw_binary_heads_or_new_internal_residents(self):
        source, _ = read_sources()
        self.assertNotRegex(source, r"\(\s*[01]{9}(?:\s|\))")
        for helper in ("vtree-insert", "vtree-get", "vtree->list", "vnode-index", "vrotate-left"):
            with self.subTest(helper=helper):
                self.assertRegex(source, rf"(?m)^\(визначити\s+{re.escape(helper)}\s")
        self.assertIn("Exact 9-bit identities", source)
        self.assertNotIn("(визначити 168 ", source)
        self.assertNotIn("(binary 9)", source)

    def test_internal_call_heads_use_primary_ukr_names(self):
        source, _ = read_sources()
        primary = source.split(ALIAS_MARKER, 1)[0]
        primary_code = "\n".join(
            line for line in primary.splitlines()
            if not line.lstrip().startswith(";")
        )
        for call in ("(вектор-кількість ", "(вектор-додати ", "вектор-порожній"):
            with self.subTest(call=call):
                self.assertIn(call, primary_code)
        for old_call in ("(vec-count ", "(vec-conj ", "(vec-empty)"):
            with self.subTest(old_call=old_call):
                self.assertNotIn(old_call, primary_code)


if __name__ == "__main__":
    unittest.main(verbosity=2)
