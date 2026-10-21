"""Чинні регресії українських Lisp-визначень D1/D3/D4/D10.

Жодних зворотних Git-blob реконструкцій: коментарі й пробіли не є
семантикою програми. Справжнє виконання мосту перевіряє тест SENS
crates/wsm-native-result-types/tests/prolog_datalog_bridge.rs.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def executable_source(source: str) -> str:
    # Вилучаємо коментарі й рядкові дані тільки для лексичної перевірки
    # викличних голів, не підміняємо читач або семантичний обчислювач.
    return "\n".join(
        re.sub(r'"(?:\\.|[^"\\])*"', '""', line.split(";", 1)[0])
        for line in source.splitlines()
    )


class ExactDomainMigrationTests(unittest.TestCase):
    def test_bridge_empty_observation_has_named_failure_before_tail_access(self):
        source = read("lib/bridge/prolog-to-datalog.lisp")
        body = source.split(
            "(визначити перетворити-підстановки-пролог-на-факти-даталог", 1
        )[1]
        guard = "((атом? спостереження)\n       (як-є (projection-failure malformed-observation)))"
        self.assertEqual(body.count(guard), 1)
        self.assertLess(body.index(guard), body.index("(решта спостереження)"))
        self.assertIn("(як-є projection-result)", source)
        self.assertIn("(як-є missing-source-ref)", source)

    def test_bridge_does_not_discard_improper_prolog_value_tails(self):
        # Only a structural guard; the separate native SENS test executes
        # actual dotted-tail inputs and checks the named failure.
        source = read("lib/bridge/prolog-to-datalog.lisp")
        self.assertIn("(визначити пролог-значення-правильний-список?", source)
        self.assertIn("((порожній? значення) так)", source)
        self.assertIn("((атом? значення) ні)", source)
        self.assertIn(
            "(пролог-значення-правильний-список? (решта значення))", source
        )
        body = source.split(
            "(визначити перетворити-підстановки-пролог-на-факти-даталог", 1
        )[1]
        self.assertIn(
            "(пролог-значення-правильний-список? (решта рядок-значень))",
            body,
        )
        self.assertLess(
            body.index("(як-є (projection-failure malformed-values))"),
            body.index("(як-є projection-result)"),
        )
        self.assertIn("(як-є prolog-substitutions-to-datalog-facts)", body)

    def test_bridge_preserves_ratified_d10_peers_and_protocol_data(self):
        source = read("lib/bridge/prolog-to-datalog.lisp")
        d10 = read("lib/domains/d10.lisp")
        for bits, name in (
            ("0010011100", "перетворити-значення-пролог-на-факти-даталог"),
            ("0010111001", "перетворити-підстановки-пролог-на-факти-даталог"),
        ):
            with self.subTest(bits=bits):
                row = next(
                    line for line in d10.splitlines()
                    if line.lstrip().startswith(f"({bits} ")
                )
                self.assertIn(f"(укр {name})", row)
                self.assertEqual(source.count("(визначити " + name), 1)
        for old in ("prolog-values-to-datalog-facts",
                    "prolog-substitutions-to-datalog-facts"):
            self.assertNotIn("(визначити " + old, source)
        for field in ("source-ref", "variable", "values"):
            self.assertIn(
                f"(знайти-за-ключем (як-є {field}) (решта спостереження))",
                source,
            )
        self.assertIn("(як-є prolog-substitutions-to-datalog-facts)", source)

    def test_no_raw_binary_callable_heads_or_hidden_numeric_tags(self):
        for path in ("lib/bridge/prolog-to-datalog.lisp",
                     "lib/macro.lisp", "lib/unify-observe.lisp",
                     "lib/machine/lowering/semantic-effects.lisp"):
            with self.subTest(path=path):
                code = executable_source(read(path))
                self.assertNotRegex(code, r"\(\s*[01]{3,10}(?=\s|\))")
                self.assertNotRegex(code, r"#(?:d\d+:[01]+|b[01]+)")

    def test_macro_quote_uses_ratified_ukrainian_d4_names(self):
        src = read("lib/macro.lisp")
        d4 = read("lib/domains/d4.lisp")
        self.assertIn("(0010 (ук функція) (укр функція)", d4)
        self.assertIn("(0011 (ук визначити) (укр визначити)", d4)
        for form in ("(як-є функція)", "(як-є визначити)"):
            self.assertIn(form, src)
        self.assertIn("(функція сирі-форми", src)
        self.assertIn("((атом? (решта-решти сирі-форми))", src)
        self.assertNotIn("(як-є 0010)", src)
        self.assertNotIn("(як-є 0011)", src)
        self.assertNotIn("побудувати-макровизначення", src)

    def test_machine_effect_uses_only_ukrainian_function_names(self):
        src = read("lib/machine/lowering/semantic-effects.lisp")
        for name in ("machine-effect-current-domain-key?",
                     "machine-lower-current-binary-effect"):
            self.assertNotIn("(визначити " + name, src)
        for name in ("машинний-ефект-збігається-поточний-домен?",
                     "машинний-ефект-знизити-поточне-двійкове"):
            self.assertIn("(визначити " + name, src)

    def test_public_names_and_protocol_data_are_not_confused(self):
        checks = {
            "lib/unify-observe.lisp": (
                "спостерігати-уніфікацію", "уніфікація-спостереження-стан"),
            "lib/machine/lowering/semantic-effects.lisp": (
                "машинний-ефект-збігається-поточний-домен?",
                "машинний-ефект-знизити-поточне-двійкове"),
        }
        for path, names in checks.items():
            src = read(path)
            for name in names:
                with self.subTest(path=path, name=name):
                    self.assertIn("(визначити " + name, src)
        src = read("lib/bridge/prolog-to-datalog.lisp")
        self.assertIn("(як-є projection-result)", src)
        self.assertNotIn("(визначити prolog-values-to-datalog-facts", src)

    def test_unify_observer_keeps_one_ukrainian_boundary(self):
        src = read("lib/unify-observe.lisp")
        required = "(визначити спостерігати-уніфікацію"
        self.assertEqual(src.count(required), 1)
        self.assertNotIn("(визначити unify-observe ", src)
        mutated = src.replace(required, "(визначити unify-observe", 1)
        self.assertNotIn(required, mutated)


if __name__ == "__main__":
    unittest.main(verbosity=2)
