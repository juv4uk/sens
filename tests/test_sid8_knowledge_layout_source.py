"""Current-domain call-head witnesses for migrated knowledge and pair-layout Lisp.

Checks only source projections. Does not claim runtime parity.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class KnowledgeLayoutSourceTests(unittest.TestCase):
    def test_three_knowledge_modules_use_ratified_quote(self):
        for name in ("astronomy", "physics", "family"):
            with self.subTest(module=name):
                source = (ROOT / "knowledge" / (name + ".lisp")).read_text()
                # Реальне джерело вже використовує український Д4 DEFINE
                # та Д3 QUOTE; старий defmodule/001 більше не є законом.
                self.assertRegex(
                    source,
                    r"\(визначити-модуль\s+" + re.escape(name) + r"\s+\(як-є\s+\(",
                )
                self.assertNotIn("(defmodule ", source)
                self.assertNotRegex(source, r"\(00000001(?=\s|\))")

    def test_guard_reference_is_ukrainian_quoted_data_not_retired_codes(self):
        source = (ROOT / "knowledge/guard-reference.lisp").read_text()
        # Довідник є даними: українські DEFINE/QUOTE, без повернення
        # історичних SID8-подібних викличних слів у джерело.
        self.assertIn("(визначити ", source)
        self.assertIn("(як-є", source)
        self.assertNotIn("(00001001 *guard-reference-directory*", source)
        self.assertNotIn("(00000111", source)
        self.assertIn("reference", source)
        self.assertIn("language-policy", source)

    def test_machine_pair_layout_uses_current_ukrainian_defines_and_quoted_data(self):
        # Першопричина: тест пінив СТАРІШУ форму (літеральні 16/0/8, англійські
        # поля offset-bytes/arena-argument-register як виконувані голови).
        # Джерело легітимно переписали на іменовані D24+ значення й ратифіковані
        # голови. Тепер перевіряється ІНВАРІАНТ, а не конкретний текст.
        source = (ROOT / "lib/machine/layout/pair-x86-64.lisp").read_text()
        d3 = (ROOT / "lib/domains/d3.lisp").read_text()
        d4 = (ROOT / "lib/domains/d4.lisp").read_text()

        self.assertRegex(d3, r"(?m)^\s*\(001\s+\(ук як-є\)\s+\(укр як-є\)")
        self.assertRegex(d4, r"(?m)^\s*\(0011\s+\(ук визначити\)\s+\(укр визначити\)")
        # Ратифіковані голови присутні; жодного сирого двійкового голови.
        for surface in ("визначити", "помножити", "список", "як-є"):
            self.assertIn(f"({surface} ", source)
        self.assertNotRegex(source, r"\(\s*[01]{2,11}(?=\s|\))")
        # Іменовані математичні значення, а не цифрові source-токени.
        for named in ("число-шістнадцять", "число-нуль", "число-вісім"):
            self.assertIn(named, source)
        # Розкладка зберігає структуру полів перше/решта.
        self.assertIn("машинна-пара-розклад", source)
        self.assertIn("(як-є перше)", source)
        self.assertIn("(як-є решта)", source)
        self.assertEqual(source.count("(визначити "), 5)
        self.assertNotRegex(source, r"\((?:0011|001|00001001)(?=\s|\))")
        for legacy in ("x86-pair-cell-bytes", "x86-pair-car-offset",
                       "x86-pair-cdr-offset", "x86-pair-layout"):
            self.assertNotIn(legacy, source)

    def test_machine_pair_layout_wrong_d4_head_is_not_accepted_as_current_source(self):
        source = (ROOT / "lib/machine/layout/pair-x86-64.lisp").read_text()
        valid = "(визначити машинна-пара-зсув-першого число-нуль)"
        self.assertEqual(source.count(valid), 1)
        mutant = source.replace(valid, "(функція машинна-пара-зсув-першого число-нуль)", 1)
        self.assertNotEqual(mutant, source)
        self.assertNotIn(valid, mutant)
        self.assertEqual(mutant.replace("(функція машинна-пара-зсув-першого число-нуль)", valid, 1), source)

    def test_four_live_fixture_source_heads(self):
        # Першопричина: тест пінив конкретні вирази старішої форми. Тепер —
        # інваріант: жодного сирого виконуваного голова; ратифіковані голови є.
        expected = {
            "lisp-fs-conformance.lisp": ("нехай-похідне", "фс-журнал-повторити"),
            "rivnopravnist-uk.lisp": ("визначити", "додати", "за-умовою", "тотожне?"),
            "semantic-registry-self-hosted-witness.lisp": ("визначити", "функція"),
            "semantic-coordinate-matrix-845.lisp": ("визначити",),
        }
        for filename, needles in expected.items():
            with self.subTest(filename=filename):
                source = (ROOT / "tests" / "fixtures" / filename).read_text()
                for snippet in needles:
                    self.assertIn(snippet, source)
                self.assertNotRegex(source, r"\(\s*[01]{2,11}(?=\s|\))")
                self.assertNotRegex(source, r"\(00001001(?=\s|\))")

        ukrainian_example = (ROOT / "tests/fixtures/rivnopravnist-uk.lisp").read_text()
        self.assertIn("(визначити подвоїти", ukrainian_example)
        self.assertIn("(додати число число)", ukrainian_example)
        self.assertIn("(за-умовою", ukrainian_example)
        self.assertIn("(тотожне? (подвоїти", ukrainian_example)
        for bits in ("0011", "0010", "01010", "110", "101", "001"):
            self.assertNotRegex(ukrainian_example, r"\(\s*" + bits + r"(?=\s|\))")

        # Binary-id data is still historical data, NOT an executable call head.
        registry = (ROOT / "tests/fixtures/semantic-registry-self-hosted-witness.lisp").read_text()
        self.assertIn("ratified-domain-handoff", registry)
        self.assertIn("(як-є укр)", registry)

if __name__ == "__main__":
    unittest.main()
