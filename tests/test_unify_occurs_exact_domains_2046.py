"""Структурний свідок чинного українського джерела unifier.

Цей тест не імітує семантику. Поведінка occurs-check перевіряється в
crates/sens/tests/unify_occurs_exact_d3.rs через справжній SENS evaluator.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/unify.lisp"
TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|;[^\\n]*|[()]|[^\\s();]+')


def parse(source):
    tokens = [m.group() for m in TOKEN.finditer(source)
              if not m.group().startswith(";")]
    pos = 0

    def read():
        nonlocal pos
        if pos == len(tokens):
            raise AssertionError("незавершена SENS-форма")
        value = tokens[pos]
        pos += 1
        if value == ")":
            raise AssertionError("зайва закривальна дужка")
        if value != "(":
            return value
        out = []
        while pos < len(tokens) and tokens[pos] != ")":
            out.append(read())
        if pos == len(tokens):
            raise AssertionError("незакрита SENS-форма")
        pos += 1
        return out

    result = []
    while pos < len(tokens):
        result.append(read())
    return result


class UkrainianUnifySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.forms = parse(cls.source)
        cls.definitions = {
            form[1]: form for form in cls.forms
            if isinstance(form, list) and len(form) == 3
            and form[0] == "визначити"
        }

    def test_all_live_top_level_definitions_use_ukr_names(self):
        self.assertEqual(len(self.forms), 17)
        self.assertEqual(len(self.definitions), 17)
        for name in self.definitions:
            with self.subTest(name=name):
                self.assertIsInstance(name, str)
                self.assertFalse(re.search(r"[A-Za-z]", name),
                                 f"неукраїнське визначення: {name}")
        self.assertEqual(
            set(self.definitions),
            {
                "уніфікація-рівні?", "логічна-змінна", "змінна?",
                "отримати-значення-з-підстановки", "розширити-підстановку",
                "пройти", "розв'язати-один-раз", "обійти-розв'язаний",
                "уніфікувати", "підстановка-позначає-невдачу?",
                "уніфікувати-обійдений", "входить-перевірити?",
                "уніфікувати-змінна", "застосувати-підстановка",
                "застосувати-підстановку-обійдений",
                "потік-виконання-кон'юнкція", "потік-виконання-кон'юнкція-гілки",
            },
        )

    def test_legacy_executable_aliases_are_absent(self):
        aliases = (
            "unify-equal?", "logic-var", "var?", "lookup-subst",
            "extend-subst", "walk", "resolve-once", "walk-resolved",
            "unify", "failed-subst?", "unify-walked", "occurs-check?",
            "unify-var", "apply-subst", "apply-subst-walked",
            "thread-conjunction", "thread-conjunction-branches", "occurs-check",
        )
        for alias in aliases:
            with self.subTest(alias=alias):
                self.assertNotIn(f"(визначити {alias} ", self.source)

    def test_occurs_check_is_defined_by_the_exact_full_ukr_peer(self):
        domain = (ROOT / "lib/domains/d9.lisp").read_text(encoding="utf-8")
        row = next(
            line for line in domain.splitlines()
            if line.lstrip().startswith("(101110101 ")
        )
        self.assertIn("(укр входить-перевірити?)", row)
        body = self.definitions["входить-перевірити?"][2]
        self.assertEqual(body[0], "функція")
        self.assertEqual(body[1], ["змінна", "терм", "підстановки"])
        # The resolved term is computed once, then checked recursively.
        self.assertEqual(body[2][0], "нехай")
        self.assertEqual(body[2][1][0][1], "розв'язаний")
        self.assertEqual(body[2][1][0][2], ["пройти", "терм", "підстановки"])
        self.assertIn("уніфікація-рівні?", str(body))
        self.assertIn("змінна?", str(body))


if __name__ == "__main__":
    unittest.main(verbosity=2)
