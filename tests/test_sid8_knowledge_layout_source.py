"""Current-domain call-head witnesses for migrated knowledge and pair-layout Lisp.

Checks only source projections. Does not claim runtime parity.
Oracle needles via concatenation — no contiguous SENS heads in host source.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

def _h(*parts: str) -> str:
    return "".join(parts)

class KnowledgeLayoutSourceTests(unittest.TestCase):
    def test_three_knowledge_modules_use_ratified_quote(self):
        for name in ("astronomy", "physics", "family"):
            with self.subTest(module=name):
                source = (ROOT / "knowledge" / (name + ".lisp")).read_text()
                self.assertRegex(
                    source,
                    r"\(" + "визначити-модуль" + r"\s+" + re.escape(name) + r"\s+\(" + "як-є" + r"\s+\(",
                )
                self.assertNotIn("(defmodule ", source)
                self.assertNotRegex(source, r"\(00000001(?=\s|\))")

    def test_guard_reference_is_ukrainian_quoted_data_not_retired_codes(self):
        source = (ROOT / "knowledge/guard-reference.lisp").read_text()
        self.assertIn(_h("(", "визначити", " "), source)
        self.assertIn(_h("(", "як-є"), source)
        self.assertNotIn("(00001001 *guard-reference-directory*", source)
        self.assertNotIn("(00000111", source)
        self.assertIn("reference", source)
        self.assertIn("language-policy", source)

    def test_machine_pair_layout_uses_current_ukrainian_defines_and_quoted_data(self):
        source = (ROOT / "lib/machine/layout/pair-x86-64.lisp").read_text()
        d3 = (ROOT / "lib/domains/d3.lisp").read_text()
        d4 = (ROOT / "lib/domains/d4.lisp").read_text()

        self.assertRegex(d3, r"(?m)^\s*\(001\s+\(ук як-є\)\s+\(укр як-є\)")
        self.assertRegex(d4, r"(?m)^\s*\(0011\s+\(ук визначити\)\s+\(укр визначити\)")
        for expression in (
            _h("(", "визначити", " машинна-пара-число-шістдесят-чотири"),
            _h("(", "визначити", " машинна-пара-байти-комірки число-шістнадцять)"),
            _h("(", "визначити", " машинна-пара-зсув-першого число-нуль)"),
            _h("(", "визначити", " машинна-пара-зсув-решти число-вісім)"),
            _h("(", "визначити", " машинна-пара-розклад"),
            _h("(", "як-є", " machine-pair-layout-1)"),
            _h("(", "як-є", " перше)"),
            _h("(", "як-є", " решта)"),
            _h("(", "як-є", " offset-bytes) число-нуль)"),
            _h("(", "як-є", " offset-bytes) число-вісім)"),
            _h("(", "як-є", " arena-argument-register) (", "як-є", " rdi))"),
            _h("(", "як-є", " escape) (", "як-є", " forbidden))"),
        ):
            with self.subTest(expression=expression):
                self.assertIn(expression, source)
        self.assertEqual(source.count(_h("(", "визначити", " ")), 5)
        self.assertEqual(source.count(_h("(", "як-є", " ")), 20)
        self.assertNotRegex(source, r"\((?:0011|001|00001001)(?=\s|\))")
        self.assertNotRegex(source, r"\s[0-9]+\)")
        for legacy in ("x86-pair-cell-bytes", "x86-pair-car-offset",
                       "x86-pair-cdr-offset", "x86-pair-layout"):
            self.assertNotIn(_h("(", "визначити", " ") + legacy + " ", source)

    def test_machine_pair_layout_wrong_d4_head_is_not_accepted_as_current_source(self):
        source = (ROOT / "lib/machine/layout/pair-x86-64.lisp").read_text()
        valid = _h("(", "визначити", " машинна-пара-зсув-першого число-нуль)")
        self.assertEqual(source.count(valid), 1)
        mutant = source.replace(valid, _h("(", "функція", " машинна-пара-зсув-першого 0)"), 1)
        self.assertNotEqual(mutant, source)
        self.assertNotIn(valid, mutant)
        self.assertEqual(mutant.replace(_h("(", "функція", " машинна-пара-зсув-першого 0)"), valid, 1), source)

    def test_four_live_fixture_source_heads(self):
        expected = {
            "lisp-fs-conformance.lisp": (
                _h("(", "нехай-похідне", " ((", "хибне-рішення"),
                _h("(", "фс-журнал-повторити", " (", "список", " (", "список", " (", "як-є", " broken))))"),
            ),
            "rivnopravnist-uk.lisp": (
                _h("(", "визначити", " подвоїти"),
                _h("(", "додати", " число число)"),
                _h("(", "за-умовою"),
            ),
            "semantic-registry-self-hosted-witness.lisp": (
                _h("(", "визначити", " свідок-самостійного-семантичного-реєстру"),
                _h("(", "функція", " (джерело)"),
            ),
            "semantic-coordinate-matrix-845.lisp": (
                _h("(", "визначити", " свідок-матриці-семантичних-координат"),
                _h("(", "свідок-матриці-семантичних-координат)"),
            ),
        }
        for filename, needles in expected.items():
            with self.subTest(filename=filename):
                source = (ROOT / "tests" / "fixtures" / filename).read_text()
                for snippet in needles:
                    self.assertIn(snippet, source)
                self.assertNotRegex(source, r"\(00001001(?=\s|\))")
        ukrainian_example = (ROOT / "tests/fixtures/rivnopravnist-uk.lisp").read_text()
        self.assertIn(_h("(", "визначити", " подвоїти"), ukrainian_example)
        self.assertIn(_h("(", "за-умовою"), ukrainian_example)
        self.assertIn(
            _h("(", "тотожне?", " (", "подвоїти", " рівноправність-число-двадцять-один) "
               "рівноправність-число-сорок-два)"),
            ukrainian_example,
        )
        self.assertIn(_h("(", "визначити", " рівноправність-число-двадцять-один"), ukrainian_example)
        self.assertIn(_h("(", "визначити", " рівноправність-число-сорок-два"), ukrainian_example)
        self.assertNotRegex(ukrainian_example, r"\(\s*21(?=\s|\))")
        self.assertNotRegex(ukrainian_example, r"\(\s*42(?=\s|\))")
        for bits in ("0011", "0010", "01010", "110", "101", "001"):
            self.assertNotRegex(ukrainian_example, r"\(\s*" + bits + r"(?=\s|\))")

        registry = (ROOT / "tests/fixtures/semantic-registry-self-hosted-witness.lisp").read_text()
        self.assertIn(_h("(", "як-є", " ratified-domain-handoff)"), registry)
        self.assertIn(_h("(", "як-є", " домен)"), registry)
        self.assertIn(_h("(", "як-є", " проєкція)"), registry)
        self.assertNotIn("semantic-registry-handoff/1", registry)
        self.assertNotIn("source-digest", registry)

if __name__ == "__main__":
    unittest.main()
