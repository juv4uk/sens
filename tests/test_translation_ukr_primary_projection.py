"""Точкова перевірка первинної проєкції укр для бібліотеки перекладу."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = "lib/translation.lisp"
PROJECTIONS = (
    (9, "translation-status", "переклад-стан", "000000101"),
    (9, "translation-kind", "переклад-вид", "000101100"),
    (9, "translation-source", "переклад-джерело", "000010100"),
    (9, "translation-payload", "переклад-вміст", "000101110"),
    (10, "translation-status-valid?", "статус-запису-перекладу-коректний?", "0010110000"),
    (10, "translation-kind-valid?", "вид-кандидата-перекладу-коректний?", "0010111000"),
    (10, "translation-envelope-valid?", "структура-обгортки-перекладу-коректна?", "0010011101"),
    (10, "translation-batch-valid?", "пакет-кандидатів-перекладу-коректний?", "0010100111"),
    (10, "translation-candidate-payload-valid?", "вміст-кандидата-перекладу-коректний?", "0010100101"),
    (10, "translation-alternatives-valid?", "альтернативні-варіанти-перекладу-коректні?", "0010101100"),
    (10, "translation-ambiguity-valid?", "опис-неоднозначності-перекладу-коректний?", "0010011110"),
    (9, "make-translation-review", "створити-переклад-перевірка", "000011010"),
    (9, "translation-review-status", "переклад-перевірка-стан", "000111100"),
    (9, "translation-review-code", "переклад-перевірка-код", "000100011"),
    (9, "translation-review-proposal", "переклад-перевірка-пропозиція", "000100101"),
    (9, "translation-review-detail", "переклад-перевірка-деталь", "000101111"),
    (10, "translation-review-status-valid?", "статус-огляду-кандидата-перекладу-коректний?", "0010111110"),
    (10, "translation-review-valid?", "запис-огляду-перекладу-коректний?", "0010100011"),
    (10, "translation-review-advice-decision", "рішення-на-основі-огляду-перекладу-й-поради", "0010101001"),
    (10, "translation-review-candidate", "отримати-кандидата-на-огляд-перекладу", "0010111010"),
    (9, "translation-review", "переклад-перевірка", "000101000"),
    (9, "translation-admittable?", "переклад-допустимий?", "000110111"),
    (9, "translation-admission-payload", "переклад-допуск-вміст", "000000010"),
    (9, "translation-evidence-worthy?", "переклад-доказ-вартий?", "000111011"),
    (9, "translation-evidence-entry", "переклад-доказ-запис", "000000011"),
    (9, "translation-evidence-next", "переклад-доказ-наступний", "000001110"),
    (9, "translation-review-with-evidence", "переклад-перевірка-з-доказ", "000010010"),
)


def read_source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class TranslationUkrPrimaryProjectionTests(unittest.TestCase):
    def test_no_legacy_english_define_bindings_remain(self):
        source = read_source(SOURCE_PATH)
        self.assertNotRegex(
            source,
            r"(?m)^\(визначити\s+[^\s()]*[A-Za-z][^\s()]*",
            "Активний Lisp не повинен повертати історичні англомовні DEFINE",
        )
        # Мітки протоколу — українські дані, а не викличні імена.
        self.assertIn("(як-є переклад-версія-1)", source)
        self.assertIn("(як-є огляд-перекладу-версія-1)", source)
        self.assertIn("(як-є доказ-перекладу-версія-1)", source)
        self.assertIn("(як-є кандидат)", source)
        self.assertNotRegex(source, r"\(як-є\s+[A-Za-z][A-Za-z0-9_/-]*\)")

    def test_translation_names_match_ratified_d9_d10_projection_and_keep_width(self):
        source = read_source(SOURCE_PATH)

        for width, english, ukrainian, bits in PROJECTIONS:
            with self.subTest(english=english, domain=width, bits=bits):
                self.assertEqual(
                    len(bits), width,
                    f"D{width}: ключ {bits} має неправильну ширину",
                )
                table_path = f"lib/domains/d{width}.lisp"
                rows = [
                    line for line in read_source(table_path).splitlines()
                    if line.lstrip().startswith(f"({bits} ")
                ]
                self.assertEqual(
                    len(rows), 1,
                    f"{table_path}: очікував один ратифікований рядок {bits}",
                )
                self.assertRegex(rows[0], rf"\(en\s+{re.escape(english)}\)")
                self.assertRegex(rows[0], rf"\(укр\s+{re.escape(ukrainian)}\)")

                primary = re.compile(
                    rf"^\(визначити\s+{re.escape(ukrainian)}(?=\s|\))",
                    re.MULTILINE,
                )
                old_primary = re.compile(
                    rf"^\(визначити\s+{re.escape(english)}\s*\n",
                    re.MULTILINE,
                )
                self.assertEqual(
                    len(primary.findall(source)), 1,
                    f"{english}: повна укр-назва має бути єдиним первинним визначенням",
                )
                self.assertIsNone(
                    old_primary.search(source),
                    f"{english}: старе англійське первинне визначення ще лишилося",
                )
                self.assertNotIn(
                    f"(визначити {english} {ukrainian})",
                    source,
                    f"{english}: застарілий англомовний DEFINE-дубль має бути вилучений",
                )
                self.assertNotRegex(
                    source,
                    rf"(?m)^\s*\({bits}(?:\s|\))",
                    f"D{width}:{bits}: проєкція не повинна створювати прямий бінарний call-head",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
