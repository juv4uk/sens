"""Актуальна українська проєкція виконуваної незмінної мапи СЕНС.

Колишній scripts/build-inventory.lisp сьогодні лише якір, не джерело
рекурсивного пошуку. Перевіряємо живу lib/persistent-map.lisp та
ратифіковані D3/D4 координати; це лексичний аудит, не симуляція SENS.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/persistent-map.lisp"
sys.path.insert(0, str(ROOT / "scripts"))
from check_ukr_callsite_migration import SourceError, parse, tokenize, candidate_heads
from domain_tables import read_domain_table

RATIFIED = {
    "як-є": ("D3", "001"),
    "атом?": ("D3", "010"),
    "решта": ("D3", "011"),
    "перше": ("D3", "100"),
    "тотожне?": ("D3", "101"),
    "за-умовою": ("D3", "110"),
    "сполучити": ("D3", "111"),
    "функція": ("D4", "0010"),
    "визначити": ("D4", "0011"),
    "хибне?": ("D4", "0100"),
    "порожній?": ("D4", "0101"),
    "список": ("D4", "1110"),
}


def syntactic_heads(source: str) -> set[str]:
    tokens = tokenize(source)
    return {
        tokens[index + 1].text
        for index, token in enumerate(tokens[:-1])
        if token.kind == "paren" and token.text == "("
        and tokens[index + 1].kind == "atom"
    }


def verify_current_peers(source: str) -> None:
    try:
        forms = parse(source)
        heads = syntactic_heads(source)
    except SourceError as exc:
        raise ValueError(f"invalid Lisp syntax: {exc}") from exc
    for name in RATIFIED:
        if name not in heads:
            raise ValueError(f"peer drift: missing Ukrainian head {name!r}")
    executable = {token.text for token in candidate_heads(forms)}
    for historical in ("car", "cdr", "cons", "eq", "atom", "cond"):
        if historical in executable:
            raise ValueError(f"historical executable head {historical!r}")


class PersistentMapUkrProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_current_ukrainian_program_not_old_blob(self):
        verify_current_peers(self.source)
        self.assertIn("(визначити мапа-отримати", self.source)
        self.assertIn("(мапа-отримати ключ (решта записи))", self.source)
        self.assertNotIn("(визначити знайти-за-ключем мапа-отримати)", self.source)

    def test_all_surface_mappings_are_current_ratified(self):
        tables = {
            (row.domain, row.bits): row.ukr
            for width in (3, 4)
            for row in read_domain_table(ROOT / f"lib/domains/d{width}.lisp")
        }
        for name, coordinate in RATIFIED.items():
            with self.subTest(name=name, coordinate=coordinate):
                self.assertEqual(tables[coordinate], name)

    def test_quoted_structural_values_are_data_not_executable_aliases(self):
        self.assertIn("(як-є ())", self.source)
        self.assertIn("(мапа-отримати ключ (решта записи))", self.source)
        verify_current_peers(self.source)

    def test_mutated_peer_fails_current_projection(self):
        mutated = self.source.replace("(тотожне?", "(хибна-назва")
        self.assertNotEqual(mutated, self.source)
        mutated += "\n; (тотожне? x y)\n"
        with self.assertRaisesRegex(ValueError, "peer drift"):
            verify_current_peers(mutated)

    def test_unbalanced_source_fails_without_semantic_fallback(self):
        with self.assertRaisesRegex(ValueError, "invalid Lisp syntax"):
            verify_current_peers(self.source + "\n(незавершене")

    def test_local_recursion_never_claims_d5_association_identity(self):
        self.assertIn("(мапа-отримати ключ (решта записи))", self.source)
        self.assertNotIn("(11100 ключ (решта записи))", self.source)
        self.assertNotIn("OLD_BLOB_SHA1", self.source)


if __name__ == "__main__":
    unittest.main()
