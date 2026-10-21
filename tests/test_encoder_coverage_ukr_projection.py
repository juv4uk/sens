"""Перевірки українських викличних голів encoder coverage.

Порівнюємо структуру чинної програми та її викличні голови, а не Git blob:
коментарі й форматування не є семантикою. Це статичний тест джерела,
а не доказ виконання SENS чи фізичного T5M-переходу.
"""
from collections import Counter
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "lib/machine/encoding/coverage-generator.lisp"
EXPECTED = {
    "100": ("перше", 36), "101": ("тотожне?", 3),
    "110": ("за-умовою", 28), "111": ("сполучити", 4),
    "1001": ("друге", 26), "1110": ("список", 18),
    "0011": ("визначити", 40), "0010": ("функція", 25),
    "001": ("як-є", 49), "010": ("атом?", 3), "011": ("решта", 40),
}
# Додаткові перевірені домени D5/D6/D8/D9 (крім reader-unsafe FIFTH).
HIGH = {
    "10011": ("третє", 11),
    "10100": ("зворот", 3),
    "10101": ("зворот-до", 1),
    "100111": ("четверте", 3),
    "101000": ("відобразити", 1),
    "101110": ("згорнути", 1),
    "11101110": ("символ-у-текст", 2),
    "11110100": ("значення-у-текст", 4),
    "110011110": ("рядок-додати", 2),
    "110101001": ("читати-всі", 4),
    "110110111": ("читати-файл", 3),
    "01010": ("додати", 2),
    "11010": ("менше?", 2),
    "001001": ("нехай-послідовно", 3),
    "001000": ("нехай", 3),
}
# D9:110110101 FIFTH: ратифікований рядок має апостроф у друкованій
# поверхні, яку поточний reader читає як quote; використовуємо точно
# ту саму композицію D3 CAR(CDR(CDR(CDR(CDR(list))))).
FIFTH_WITNESS = "(перше (решта (решта (решта (решта coverage-row)))))"
FIFTH_BINARY = "(110110101 coverage-row)"
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


def ratified():
    result = {}
    for width in (3, 4, 5, 6, 8, 9):
        src = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
        for line in src.splitlines():
            row = re.match(
                r"^\s*\(([01]+)\s+\(ук [^\s()]+\)\s+\(укр ([^()\s]+)\)",
                line,
            )
            if row and len(row.group(1)) == width:
                result[row.group(1)] = row.group(2)
    return result


def verify(text):
    """Точні чинні українські викличні голови й протокол без відтворення Git blob.

    Структурна охорона джерела, не обчислювач SENS і не доказ релізу.
    """
    authority = ratified()
    for bits, (name, _historical_count) in {**EXPECTED, **HIGH}.items():
        if authority.get(bits) != name:
            raise AssertionError("зміна ратифікованої проєкції: " + bits)
    # Зміст QUOTE — дані, не виконавчі атоми. Лексичний пошук
    # хибно забороняв (як-є так) і рядки з D1-мітками.
    # Ця перевірка лише структурна: семантику виконує SENS.
    def unbound_d1(node):
        if node[0] == "atom":
            return node[1] in ("так", "ні")
        if node[0] == "quoted" or node[0] != "list":
            return False
        items = node[1]
        if items and items[0][0] == "atom" and items[0][1] == "як-є":
            return False
        return any(unbound_d1(item) for item in items)

    if any(unbound_d1(form) for form in parse(text)):
        raise AssertionError("незв'язане D1 так/ні в генераторі")
    heads = list(call_heads(text))
    if not heads:
        raise AssertionError("втрачено викличні голови SENS")
    binary = [name for name, _start, _end in heads if re.fullmatch(r"[01]+", name)]
    if binary:
        raise AssertionError("залишилися сирі числові викличні голови: " + str(binary))
    # Пряме атомне порівняння D3, а не заміна його на конструктор CONS.
    witnesses = (
        "(визначити покриття-кодувальника-числа-рівні?",
        "((менше? ліве праве) (атом? (як-є (стан))))",
        "((менше? праве ліве) (атом? (як-є (стан))))",
        "(визначити покриття-кодувальника-тотожні-атоми?",
        "(тотожне? ліве-значення праве-значення)",
        "(покриття-кодувальника-тотожні-структури? (перше ліве-значення) (перше праве-значення))",
        "(покриття-кодувальника-тотожні-структури? (решта ліве-значення) (решта праве-значення))",
        "(визначити покриття-кодувальника-збігається-збережений-рядок?",
        "(визначити покриття-кодувальника-сформувати-звіт",
        "(як-є x86-encoder-coverage/1)",
        "(як-є coverage)",
        "(як-є status)",
    )
    for witness in witnesses:
        if text.count(witness) < 1:
            raise AssertionError("зміна чинного Lisp-закону або цитованих даних: " + witness)
    return Counter(name for name, _start, _end in heads)


class EncoderCoverageProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PATH.read_text(encoding="utf-8")

    def test_d1_outcomes_execute_as_predicate_expressions_not_unbound_names(self):
        self.assertGreater(self.text.count("(атом? (як-є ()))"), 20)
        self.assertGreater(self.text.count("(хибне? (атом? (як-є ())))"), 10)
        verify(self.text)
        mutant = self.text.replace("(атом? (як-є ()))", "так", 1)
        self.assertNotEqual(mutant, self.text)
        with self.assertRaisesRegex(AssertionError, "D1"):
            verify(mutant)

    def test_current_ukrainian_call_heads_and_exact_d3_law(self):
        # Перевіряємо актуальний AST, а не давній SHA/snapshot.
        self.assertGreater(sum(verify(self.text).values()), 100)

    def test_other_domain_heads_and_quoted_data_untouched(self):
        self.assertIn("(рядок-додати накопичене фрагмент)", self.text)
        self.assertIn("(нехай ", self.text)
        self.assertIn("(як-є x86-encoder-coverage/1)", self.text)
        verify(self.text)

    def test_wrong_ukrainian_operator_fails(self):
        broken = self.text.replace(
            "(тотожне? ліве-значення праве-значення)",
            "(сполучити ліве-значення праве-значення)", 1,
        )
        self.assertNotEqual(broken, self.text)
        with self.assertRaisesRegex(AssertionError, "зміна"):
            verify(broken)

    def test_d24_counts_use_strict_d5_order_not_d3_identity(self):
        # Статична перевірка канонічних викличних голів, не Python-eval.
        self.assertIn(
            "(покриття-кодувальника-числа-рівні? покриття-кодувальника-кількість-сиріт 0)",
            self.text,
        )
        self.assertNotIn("(тотожне? двійкова-кількість", self.text)
        self.assertNotIn("(тотожне? покриття-кодувальника-кількість-сиріт 0)", self.text)
        for old, new in (
            ("(менше? ліве праве)", "(тотожне? ліве праве)"),
            ("(менше? праве ліве)", "(тотожне? праве ліве)"),
        ):
            broken = self.text.replace(old, new, 1)
            self.assertNotEqual(broken, self.text)
            with self.assertRaisesRegex(AssertionError, "Lisp-закону"):
                verify(broken)

    def test_wrong_quoted_data_fails(self):
        broken = self.text.replace(
            "(як-є x86-encoder-coverage/1)",
            "(як-є пошкоджена-проєкція/1)", 1,
        )
        self.assertNotEqual(broken, self.text)
        with self.assertRaisesRegex(AssertionError, "зміна"):
            verify(broken)

    def test_wrong_structural_cdr_recursion_is_detected(self):
        witness = (
            "(покриття-кодувальника-тотожні-структури? "
            "(решта ліве-значення) (решта праве-значення))"
        )
        broken = self.text.replace(
            witness,
            "(покриття-кодувальника-тотожні-структури? "
            "(перше ліве-значення) (решта праве-значення))", 1,
        )
        self.assertNotEqual(broken, self.text)
        with self.assertRaisesRegex(AssertionError, "зміна"):
            verify(broken)

    def test_comments_and_whitespace_do_not_change_program_tree(self):
        # Статичний AST без позицій токенів; це НЕ SENS-виконання.
        def tree(node):
            if node[0] == "list":
                return ("list", tuple(tree(child) for child in node[1]))
            if node[0] == "quoted":
                return ("quoted", tree(node[1]))
            return (node[0], node[1])

        original = tuple(tree(form) for form in parse(self.text))
        decorated = (
            "; Коментар перед джерелом не є частиною програми\n"
            + self.text.replace("(визначити ", "(визначити   ", 1)
            + "\n; Коментар після джерела також не змінює програму\n"
        )
        self.assertEqual(original, tuple(tree(form) for form in parse(decorated)))
        changed = self.text.replace(
            "(тотожне? ліве-значення праве-значення)",
            "(сполучити ліве-значення праве-значення)", 1,
        )
        self.assertNotEqual(original, tuple(tree(form) for form in parse(changed)))

    def test_quoted_d1_tags_are_data_not_unbound_expressions(self):
        # Позитивне й негативне свідчення AST, не Python-eval Lisp.
        verify(self.text + "\n(як-є (так ні))\n")
        broken = self.text + "\n(визначити проба так)\n"
        with self.assertRaisesRegex(AssertionError, "D1"):
            verify(broken)

    def test_unbalanced_source_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "незакр"):
            parse("(визначити f (функція (x) x)")


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
