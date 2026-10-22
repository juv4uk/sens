"""Клавіатурна УКР-проєкція, неактивний генератор і статичний синтаксис.

Виконуваність доводить лише справжній SENS, не цей Python-тест.
Після виведення старого генератора з ужитку не можна вимагати
неіснуючих функцій, позитивних witness чи змагатися в кількості тестів.
"""
from collections import Counter
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "lib/machine/encoding/coverage-generator.lisp"
TOKEN = re.compile(r""";[^\n]*|"(?:\\.|[^"\\])*"|[()]|['\x60,]|[^\s()'";\x60,]+""")


def parse(text):
    tokens = []
    for match in TOKEN.finditer(text):
        value = match.group()
        if value.startswith(";"):
            continue
        kind = ("open" if value == "(" else "close" if value == ")"
                else "prefix" if value in ("'", chr(96), ",")
                else "string" if value.startswith('"') else "atom")
        tokens.append((kind, value, match.start(), match.end()))
    cursor = 0

    def expr():
        nonlocal cursor
        if cursor == len(tokens):
            raise AssertionError("незакрита форма")
        kind, value, start, end = tokens[cursor]
        cursor += 1
        if kind == "open":
            items = []
            while cursor < len(tokens) and tokens[cursor][0] != "close":
                items.append(expr())
            if cursor >= len(tokens):
                raise AssertionError("незакрита дужка")
            cursor += 1
            return ("list", items)
        if kind == "close":
            raise AssertionError("зайва дужка")
        if kind == "prefix":
            return ("quoted", expr())
        return (kind, value, start, end)

    forms = []
    while cursor < len(tokens):
        forms.append(expr())
    return forms


def call_heads(source):
    def walk(node):
        if node[0] == "quoted" or node[0] != "list":
            return
        kids = node[1]
        head = kids[0] if kids else None
        name = head[1] if head and head[0] == "atom" else ""
        if name:
            yield (name, head[2], head[3])
        if name in ("001", "як-є", "quote"):
            return
        for kid in kids:
            yield from walk(kid)
    for form in parse(source):
        yield from walk(form)



class EncoderCoverageProjectionTests(unittest.TestCase):
    """Перевіряти поточну реальність, а не історичні 100+ виклики."""

    @classmethod
    def setUpClass(cls):
        cls.retired = PATH.read_text(encoding="utf-8")
        cls.generated = (ROOT / "lib/machine/encoding/coverage.lisp").read_text(encoding="utf-8")
        cls.checker = (ROOT / "scripts/check-encoder-coverage.lisp").read_text(encoding="utf-8")
        cls.driver = (ROOT / "scripts/generate-encoder-coverage.lisp").read_text(encoding="utf-8")

    def test_retired_generator_is_not_a_program_or_executable_credit(self):
        # Цей файл виведено з ужитку: його НЕ можна оживляти, щоб старі
        # тести стали зеленими, і не можна оголошувати .sens без Zig/SENS.
        self.assertIn("ФАЙЛ ВИВЕДЕНО З УЖИТКУ", self.retired)
        self.assertIn("Не свідок. Не якір.", self.retired)
        self.assertEqual(parse(self.retired), [])
        self.assertFalse(PATH.with_suffix(".sens").exists())
        self.assertNotIn("(status pass)", self.retired)

    def test_existing_report_is_data_not_executable_lisp(self):
        # Сотні рядків coverage — дані; жодного права приписати їм
        # викличність D8/D9 або runtime PASS.
        self.assertIn("(x86-encoder-coverage-1", self.generated)
        self.assertIn("(form-count 1176)", self.generated)
        self.assertIn("(partial-count 122)", self.generated)
        self.assertIn("(status not-yet-implemented)", self.generated)
        self.assertIn("(status partial)", self.generated)
        self.assertNotIn("(status pass)", self.generated)

    def test_current_drivers_have_only_ukrainian_executable_heads(self):
        # Це лише статична поверхня двох скриптів. Не видаємо її
        # за виконання: завантажена старша бібліотека може бути списаною.
        for script in (self.driver, self.checker):
            heads = list(call_heads(script))
            self.assertTrue(heads)
            self.assertIn("завантажити-файл", [h[0] for h in heads])
            self.assertIn("за-умовою", [h[0] for h in heads])
            self.assertFalse([h for h, _, _ in heads if re.fullmatch(r"[01]+", h)])
            self.assertNotIn("(так ", script)
            self.assertNotIn("(status pass)", self.retired)

    def test_comments_and_whitespace_leave_script_tree_unchanged(self):
        # Python тут розпізнає тільки дужки й токени, не виконує SENS.
        def tree(node):
            if node[0] == "list":
                return ("list", tuple(tree(child) for child in node[1]))
            if node[0] == "quoted":
                return ("quoted", tree(node[1]))
            return (node[0], node[1])

        original = tuple(tree(n) for n in parse(self.checker))
        decorated = "; доданий коментар\n" + self.checker.replace(
            "(визначити ", "(визначити   ", 1
        ) + "\n; ще коментар\n"
        self.assertEqual(original, tuple(tree(n) for n in parse(decorated)))
        mutant = self.checker.replace("(за-умовою", "(сполучити", 1)
        self.assertNotEqual(original, tuple(tree(n) for n in parse(mutant)))

    def test_reader_rejects_invalid_structure(self):
        with self.assertRaisesRegex(AssertionError, "незакр"):
            parse("(визначити ф (функція (а) а)")


class EncoderCoverageLispDiagnosticsTests(unittest.TestCase):
    """Діагностика формується самою SENS, без повторного розбору тексту."""

    CASES = (
        (
            "scripts/check-encoder-coverage.lisp",
            (
                "(як-є (encoder-coverage-check (status pass)))",
                "(як-є (encoder-coverage-check (status fail) (reason projection-mismatch)))",
                "(як-є (reason invalid-coverage-input-projection))",
            ),
            1,
        ),
        (
            "scripts/generate-encoder-coverage.lisp",
            (
                "(як-є (status written))",
                "(як-є (encoder-coverage-generate (status rejected) (reason invalid-coverage-input-projection)))",
            ),
            0,
        ),
    )

    def test_direct_quoted_positive_and_negative_diagnostics(self):
        for path, forms, file_readers in self.CASES:
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                parse(text)  # Відсутність зламаних дужок або рядків.
                for form in forms:
                    # Додатні й від'ємні випадки перевіряємо за токенами,
                    # не за форматуванням багаторядкової Lisp-форми.
                    tokens = re.findall(r"[()]|[^()\s]+", form)
                    expression = r"\s*".join(re.escape(token) for token in tokens)
                    self.assertEqual(len(re.findall(expression, text)), 1, (path, form))
                    mutant = re.sub(
                        expression, "(як-є (пошкоджене-повідомлення))", text, count=1
                    )
                    self.assertNotRegex(mutant, expression)
                self.assertNotIn('(перше (читати-всі "', text)
                self.assertEqual(text.count("(читати-всі"), file_readers)
                # Викличні гілки D1 повертають точні бітові предикати SENS,
                # а не покладаються на незв'язаний глобальний атом «так».
                count = 2 if path.endswith("/check-encoder-coverage.lisp") else 1
                self.assertEqual(text.count("((атом? (як-є ()))"), count)
                self.assertNotIn("(так", text)
                mutant = text.replace("((атом? (як-є ()))", "(так", 1)
                self.assertIn("(так", mutant)
                self.assertNotEqual(mutant, text)



if __name__ == "__main__":
    unittest.main(verbosity=2)
