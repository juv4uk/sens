"""Перевірка українського джерела лінтера й точної драбини D1–D10.

Це тест джерельного контракту, а не Python-емулятор SENS. Реальне виконання
покривається нативними SENS-тестами й hosted CI.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/linter.lisp"


def executable_source(source: str) -> str:
    """Strip line comments and string payloads without rewriting live code."""
    lines = []
    for line in source.splitlines():
        out = []
        in_string = False
        escaped = False
        for char in line.split(";", 1)[0]:
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                out.append(" ")
            elif char == '"':
                in_string = True
                out.append(" ")
            else:
                out.append(char)
        lines.append("".join(out))
    return "\n".join(lines)


class UkrainianLinterProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.active = executable_source(cls.text)

    def test_helper_bindings_and_calls_are_fully_ukrainian(self):
        for name in (
            "лінтер-коротка-голова",
            "аналіз-голова",
            "лінтер-максимум-двох",
            "взяти-межу",
        ):
            with self.subTest(name=name):
                self.assertIn("(визначити " + name + "\n", self.active)
                self.assertNotRegex(
                    self.active,
                    r"\(" + re.escape(name) + r"\s+[^\n]*\b(?:lint-short-head|lint-max2|get-threshold)\b",
                )
        for legacy in ("lint-short-head", "lint-max2", "get-threshold"):
            self.assertNotIn(legacy, self.active)

    def test_linter_classifies_ratified_ukrainian_syntax_values_not_numeric_widths(self):
        for snippet in (
            "((тотожне? голова (як-є як-є)) (як-є як-є))",
            "((тотожне? голова (як-є за-умовою)) (як-є за-умовою))",
            "((тотожне? голова (як-є визначити)) (як-є визначити))",
            "((тотожне? голова (як-є функція)) (як-є функція))",
            "((тотожне? голова (як-є нехай)) (як-є нехай))",
            "((тотожне? голова (як-є нехай-послідовно)) (як-є нехай-послідовно))",
        ):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, self.active)
        self.assertNotRegex(self.active, r"(?<![\w-])(?:001|110|0010|0011|001000|001001)(?![\w-])")

    def test_named_values_match_exact_rungs_and_full_ukr_peers(self):
        expected = {
            ("d3.lisp", "001"): "як-є",
            ("d3.lisp", "110"): "за-умовою",
            ("d4.lisp", "0011"): "визначити",
            ("d4.lisp", "0010"): "функція",
            ("d6.lisp", "001000"): "нехай",
            ("d6.lisp", "001001"): "нехай-послідовно",
        }
        for (filename, bits), surface in expected.items():
            table = (ROOT / "lib/domains" / filename).read_text(encoding="utf-8")
            rows = [
                line for line in table.splitlines()
                if line.strip().startswith(f"({bits} (ук ")
            ]
            self.assertEqual(len(rows), 1, f"{filename}:{bits}")
            self.assertIn(f"(укр {surface})", rows[0])

    def test_structural_equal_remains_a_distinct_named_operation(self):
        # The linter handles nested/list structure with the ratified equality
        # operation, not by passing pairs to atom-only D3 identity.
        self.assertIn("(однакові? (аналіз-форма-голова дерево)", self.active)
        self.assertIn("(тотожне? голова (як-є визначити))", self.active)
        self.assertNotIn("(11110111 head ", self.active)
        self.assertNotIn("(11110111 голова ", self.active)

    def test_effect_primitive_registry_has_no_legacy_english_binding(self):
        # Первинна функція визначається в Lisp, а не історичним псевдонімом.
        self.assertIn("(визначити лінтер-примітиви-з-ефектами", self.active)
        self.assertIn(" лінтер-примітиви-з-ефектами)", self.active)
        self.assertNotIn("(визначити effectful-primitives", self.active)

    def test_quoted_data_and_ukrainian_macro_have_explicit_source_witnesses(self):
        # Це охорона джерела та випробувальних даних, НЕ Python-обчислення SENS.
        for literal in (
            "((тотожне? (перше дерево) (як-є як-є)) (як-є ()))",
            "((тотожне? (перше дерево) (як-є quote)) (як-є ()))",
            "(аналіз-форма-голова дерево) (як-є визначити-макрос)",
        ):
            with self.subTest(literal=literal):
                self.assertIn(literal, self.active)
        examples = (ROOT / "tests/fixtures/linter.lisp").read_text(encoding="utf-8")
        for program in (
            "(аналіз-ефекти (як-є (як-є (друкувати 1))))",
            "(аналіз-ефекти (як-є (quote (процес-запустити 1))))",
            "(аналіз-глобальні (як-є (визначити-макрос назва",
            "(аналіз-глобальні (як-є (визначити нова (функція",
        ):
            with self.subTest(program=program):
                self.assertIn(program, examples)
        self.assertGreaterEqual(examples.count('(expected . "()")'), 2)

    def test_wrong_peer_and_reintroduced_binary_head_fail_source_contract(self):
        wrong_peer = self.active.replace(
            "(як-є визначити)) (як-є визначити))",
            "(як-є хибне?)) (як-є хибне?))",
            1,
        )
        self.assertNotEqual(wrong_peer, self.active)
        self.assertNotIn(
            "((тотожне? голова (як-є визначити)) (як-є визначити))",
            wrong_peer,
        )
        forbidden = self.active.replace(
            "(як-є за-умовою)", "110", 1
        )
        self.assertNotEqual(forbidden, self.active)
        self.assertRegex(forbidden, r"(?<![\w-])110(?![\w-])")


if __name__ == "__main__":
    unittest.main(verbosity=2)
