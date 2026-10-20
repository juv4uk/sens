"""Чинні українські Lisp-голови інвентаризатора, без історичного Git-blob шаблону.

Доменні тотожності беруться з D3/D4, а токени — з діючого читача
source-аудиту. Це перевірка форми джерела, НЕ виконання семантики SENS.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/build-inventory.lisp"
sys.path.insert(0, str(ROOT / "scripts"))
from check_ukr_callsite_migration import SourceError, parse, tokenize, candidate_heads
from domain_tables import read_domain_table

# Лише підтверджені українські імена з ратифікованих D3/D4.
# Жодних SID8, рядкових номерів, історичних line:column-пінів.
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
    "решта-решти": ("D4", "0111"),
    "перше-першого": ("D4", "1000"),
    "друге": ("D4", "1001"),
    "список": ("D4", "1110"),
    "приєднати": ("D4", "1111"),
}


def syntactic_heads(source: str) -> set[str]:
    """Лексичні голови форм, без рядків/коментарів та байтової інверсії."""
    tokens = tokenize(source)
    return {
        tokens[index + 1].text
        for index, token in enumerate(tokens[:-1])
        if token.kind == "paren" and token.text == "("
        and tokens[index + 1].kind == "atom"
    }


def verify_current_peers(source: str) -> None:
    """Перевірити актуальну програму, а не позиції зі старого Lisp-файла."""
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


class InventoryUkrProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_current_ukrainian_program_not_old_blob(self):
        verify_current_peers(self.source)
        self.assertIn("(визначити знайти-пару", self.source)
        self.assertIn("(знайти-пару ключ (решта список-пар))", self.source)
        self.assertNotIn("(визначити знайти-за-ключем знайти-пару)", self.source)

    def test_all_surface_mappings_are_current_ratified(self):
        tables = {
            (row.domain, row.bits): row.ukr
            for width in (3, 4)
            for row in read_domain_table(ROOT / f"lib/domains/d{width}.lisp")
        }
        for name, coordinate in RATIFIED.items():
            with self.subTest(name=name, coordinate=coordinate):
                self.assertEqual(tables[coordinate], name)

    def test_quoted_protocol_values_are_data_not_executable_aliases(self):
        for datum in ("quote", "lambda", "def", "cond"):
            self.assertIn(f"(як-є {datum})", self.source)
        self.assertIn("(знайти-пару ключ (решта список-пар))", self.source)
        verify_current_peers(self.source)

    def test_mutated_peer_fails_current_projection(self):
        mutated = self.source.replace("(тотожне?", "(хибна-назва")
        self.assertNotEqual(mutated, self.source)
        # Коментар не має маскувати відсутню виконувану голову.
        mutated += "\n; (тотожне? x y)\n"
        with self.assertRaisesRegex(ValueError, "peer drift"):
            verify_current_peers(mutated)

    def test_unbalanced_source_fails_without_semantic_fallback(self):
        with self.assertRaisesRegex(ValueError, "invalid Lisp syntax"):
            verify_current_peers(self.source + "\n(незавершене")

    def test_local_recursion_never_claims_d5_association_identity(self):
        self.assertIn("(знайти-пару ключ (решта список-пар))", self.source)
        self.assertNotIn("(11100 ключ (решта список-пар))", self.source)
        self.assertNotIn("OLD_BLOB_SHA1", self.source)


if __name__ == "__main__":
    unittest.main()
