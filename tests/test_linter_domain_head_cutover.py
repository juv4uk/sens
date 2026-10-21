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

    def test_quoted_cond_is_not_live_complexity(self):
        # Виконувана формула з lib/linter.lisp, а не Python-eval.
        start = self.active.index("(визначити аналіз-складність")
        end = self.active.index("(визначити лінтер-примітиви-з-ефектами", start)
        body = self.active[start:end]
        self.assertIn(
            "(тотожне? (аналіз-форма-голова дерево) (як-є як-є))",
            body,
        )
        self.assertIn(
            "(тотожне? (аналіз-форма-голова дерево) (як-є quote))",
            body,
        )
        self.assertLess(body.index("(як-є як-є)"), body.index("(як-є за-умовою)"))
        self.assertNotIn(" так)", body)
        self.assertNotIn(" ні)", body)
        witness = (ROOT / "tests/fixtures/linter.lisp").read_text(
            encoding="utf-8"
        )
        for expression in (
            "(аналіз-складність (як-є (як-є (за-умовою",
            "(аналіз-складність (як-є (quote (за-умовою",
            "(аналіз-складність (як-є (список (як-є (за-умовою",
        ):
            with self.subTest(expression=expression):
                self.assertIn(expression, witness)

    def test_d1_truth_values_do_not_require_unbound_global_names(self):
        # Синтаксична охорона; справжній вердикт дає SENS CLI.
        # Рядки в таблиці даних залишаються незмінними.
        self.assertNotRegex(self.active, r"(?<![\w-])(?:так|ні)(?![\w-])")
        self.assertIn("(атом? (як-є ()))", self.active)
        self.assertIn("(хибне? (атом? (як-є ())))", self.active)
        self.assertIn('"так" "ні"', self.text)
        mutant = self.active.replace("(атом? (як-є ()))", "так", 1)
        self.assertRegex(mutant, r"(?<![\w-])так(?![\w-])")

    def test_d1_atom_predicate_does_not_call_multivalued_answer_negation(self):
        # D1: атом? уже повертає однобітний вердикт. Функція
        # відповідь-не очікує СКЛАДЕНУ шкалу, тому перше(атом?) — помилка.
        self.assertNotIn("(відповідь-не ", self.active)
        self.assertIn("((атом? дерево)", self.active)
        start = self.active.index("(визначити аналіз-форма-голова")
        end = self.active.index("(визначити лінтер-коротка-голова", start)
        head_reader = self.active[start:end]
        self.assertIn("((атом? (решта дерево))", head_reader)
        # Тільки ця функція: інші аналізатори законно можуть мати два CDR.
        self.assertIn("((тотожне? (решта дерево) (як-є ()))", head_reader)
        self.assertNotIn("((атом? (решта (решта дерево)))", head_reader)
        samples = (ROOT / "tests/fixtures/linter.lisp").read_text(encoding="utf-8")
        self.assertIn("(нехай-послідовно ((x 1) (y x)) (додати x y z))", samples)

    def test_lexical_scope_branches_reachable_for_let_star_and_letrec(self):
        # Це перевірка досяжності мовних гілок, НЕ Python-емуляція SENS.
        # Для повної (голова зв'язування тіло) перші два стани atom?/not
        # взаємовиключні; стара пара поглинала гілку роботи з прив'язками.
        for name in (
            "зібрати-вільні-змінні-з-послідовного-зв'язування",
            "зібрати-вільні-змінні-з-рекурсивного-зв'язування",
        ):
            with self.subTest(name=name):
                start = self.active.index("(визначити " + name)
                next_definition = self.active.find("(визначити ", start + 1)
                body = self.active[start:next_definition if next_definition >= 0 else None]
                self.assertNotIn("((хибне? (атом? (решта дерево)))", body)
                self.assertNotIn("((хибне? (атом? (решта (решта дерево))))", body)
                self.assertIn("((атом? (решта дерево))", body)
                self.assertIn("((атом? (решта (решта дерево)))", body)
                self.assertIn("(нехай ((привязки", body)
        # Дійсні приклади з очікуваними результатами належать SENS.
        fixture = (ROOT / "tests/fixtures/linter.lisp").read_text(encoding="utf-8")
        self.assertIn("(нехай-послідовно ((x 1) (y x)) (додати x y z))", fixture)
        self.assertIn("(letrec ((even? (lambda (n)", fixture)

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
