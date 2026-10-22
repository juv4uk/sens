"""Перевірка актуальних даних покриття та виведеного з ужитку генератора.

Це лише структурний свідок джерел, а не Python-виконання Lisp і не
доказ нативного SENS/Zig. Старі викличні голови з уже вилученої програми
не відновлюються фіктивним AST-тестом.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
RETIRED = ROOT / "lib/machine/encoding/coverage-generator.lisp"
LEDGER = ROOT / "lib/machine/encoding/coverage.lisp"

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



def _tag(node):
    if node[0] != "list" or not node[1] or node[1][0][0] != "atom":
        raise AssertionError("некоректна форма покриття")
    return node[1][0][1]


def _field(node, label, kind="atom"):
    if _tag(node) != label or len(node[1]) != 2 or node[1][1][0] != kind:
        raise AssertionError("некоректне поле покриття: " + label)
    return node[1][1][1]


def verify_ledger(source):
    """Перевірити структуру збережених ДАНИХ, без оцінювання Lisp через Python.

    Числа та рядки взяті з самого файлу; не видавати це за native PASS.
    """
    forms = parse(source)
    if len(forms) != 1 or _tag(forms[0]) != "x86-encoder-coverage-1":
        raise AssertionError("повинен бути один кореневий запис покриття")
    header, partial_header, *records = forms[0][1][1:]
    count = _field(header, "form-count")
    partial_count = _field(partial_header, "partial-count")
    if not count.isdecimal() or not partial_count.isdecimal():
        raise AssertionError("пошкоджений лічильник покриття")
    if len(records) != int(count):
        raise AssertionError("кількість записів покриття не відповідає даним")
    known_statuses = {"partial", "not-yet-implemented"}
    addresses = set()
    partial = 0
    for rec in records:
        if _tag(rec) != "coverage" or len(rec[1]) != 5:
            raise AssertionError("пошкоджений запис покриття")
        iclass = _field(rec[1][1], "iclass", "string")
        extension = _field(rec[1][2], "extension")
        status = _field(rec[1][3], "status")
        reason = _field(rec[1][4], "reason", "string")
        if not iclass or not extension or not reason:
            raise AssertionError("порожній опис покриття")
        if status not in known_statuses:
            raise AssertionError("невідомий статус: " + status)
        identity = (extension, iclass)
        if identity in addresses:
            raise AssertionError("повтор ICLASS+extension")
        addresses.add(identity)
        partial += status == "partial"
    if partial != int(partial_count):
        raise AssertionError("partial-count не відповідає даним")
    if not 0 < partial < len(records):
        raise AssertionError("неправдиве твердження про повний допуск")
    return len(records), partial


class EncoderCoverageCurrentDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retired = RETIRED.read_text(encoding="utf-8")
        cls.ledger = LEDGER.read_text(encoding="utf-8")

    def test_old_generator_is_only_comments_not_executable_sens(self):
        # Відсутній код не може бути доказовим якорем чи runtime PASS.
        self.assertEqual(parse(self.retired), [])
        self.assertIn("ФАЙЛ ВИВЕДЕНО З УЖИТКУ", self.retired)
        self.assertIn("Не свідок. Не якір.", self.retired)
        self.assertNotIn("(status pass)", self.retired)
        self.assertNotIn("(визначити ", self.retired)

    def test_executable_reintroduction_is_not_invisible(self):
        mutant = self.retired + "\n(визначити бутафорія (функція () так))\n"
        self.assertNotEqual(parse(mutant), [])
        # Немає автоматичного ратифікування з нової текстової форми.
        self.assertIn("(визначити бутафорія", mutant)

    def test_real_ledger_has_self_consistent_qualified_rows(self):
        n, partial = verify_ledger(self.ledger)
        self.assertGreater(n, 1000)
        self.assertGreater(partial, 0)

    def test_ledger_rejects_fake_all_pass_and_wrong_count(self):
        changed = self.ledger.replace("(status partial)", "(status pass)", 1)
        self.assertNotEqual(changed, self.ledger)
        with self.assertRaisesRegex(AssertionError, "невідомий статус"):
            verify_ledger(changed)
        changed = self.ledger.replace("(form-count 1176)", "(form-count 1175)", 1)
        self.assertNotEqual(changed, self.ledger)
        with self.assertRaisesRegex(AssertionError, "кількість"):
            verify_ledger(changed)

    def test_ledger_rejects_duplicate_identity_and_partial_drift(self):
        original = self.ledger
        # Кожен фізичний рядок починається з (coverage; повтор
        # першого рядка невидимий лише для помилкового поверхового grep.
        start = original.index("  (coverage\n")
        stop = original.index("  (coverage\n", start + 1)
        duplicate = original[start:stop]
        broken = original[:stop] + duplicate + original[stop:]
        with self.assertRaisesRegex(AssertionError, "кількість"):
            verify_ledger(broken)
        broken = original.replace("(partial-count 122)", "(partial-count 121)", 1)
        self.assertNotEqual(broken, original)
        with self.assertRaisesRegex(AssertionError, "partial-count"):
            verify_ledger(broken)


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
