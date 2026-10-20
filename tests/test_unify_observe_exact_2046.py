"""Суворий тест межі UNIFY: 2046 адрес ≠ 2046 виконуваних механізмів.

D1 truth — результат предикатів. D3 heads — машина. D9 address — каталог;
ніяких припущень про автоматичну callability або ширинні alias.
"""
import copy
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/unify-observe.lisp"
TOKEN = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();]+')
HELPER = "уніфікація-спостереження-стан"

def read(source):
    items = [m.group() for m in TOKEN.finditer(source)
             if not m.group().startswith(";")]
    pos = 0

    def parse():
        nonlocal pos
        if pos == len(items):
            raise AssertionError("незакрита форма")
        word = items[pos]
        pos += 1
        if word == ")":
            raise AssertionError("зайва дужка")
        if word != "(":
            return word
        result = []
        while pos < len(items) and items[pos] != ")":
            result.append(parse())
        if pos == len(items):
            raise AssertionError("незакрита дужка")
        pos += 1
        return result

    forms = []
    while pos < len(items):
        forms.append(parse())
    return forms


def visit(ast):
    if isinstance(ast, list):
        yield ast
        for item in ast:
            yield from visit(item)


# Українські call heads не змінюють ратифікованої координати.
# Таблиця є джерелом значень, а не історичний сід8 або текстова ширина.
def normalize_operator_heads(ast):
    if not isinstance(ast, list):
        return ast
    items = [normalize_operator_heads(item) for item in ast]
    if items and isinstance(items[0], str):
        mappings = {
            "як-є": "001", "атом?": "010", "решта": "011",
            "перше": "100", "тотожне?": "101", "за-умовою": "110",
            "сполучити": "111", "список": "1110",
        }
        items[0] = mappings.get(items[0], items[0])
    return items


def validate(forms):
    """Статична звірка українських форм, а не виконання семантики хостом."""
    forms = normalize_operator_heads(forms)
    if len(forms) != 2:
        raise AssertionError("рівно два D4 визначення")
    if not all(isinstance(f, list) and len(f) == 3 and f[0] == "визначити"
               for f in forms):
        raise AssertionError("повна українська D4 DEFINE-проєкція")
    names = {f[1]: f for f in forms}
    public_name = "спостерігати-уніфікацію"
    if set(names) != {HELPER, public_name}:
        raise AssertionError("очікувані лише дві українські функції без англомовного псевдоніма")
    helper = names[HELPER][2]
    public = names[public_name][2]
    params = ["ліве", "праве", "підстановка"]
    if not (helper[:2] == ["функція", ["сирий-результат", *params]]
            and public[:2] == ["функція", params]):
        raise AssertionError("D4 LAMBDA параметри / арність")
    if public[2] != [HELPER, ["уніфікувати", *params], *params]:
        raise AssertionError("Українська уніфікація мусить обчислитися рівно раз")
    if helper[2] != [
        "110",
        [["010", "сирий-результат"], [
            "110",
            [["101", "сирий-результат", ["001", "fail"]],
             ["1110", ["001", "unification-failure"], *params]],
            [["010", ["001", []]],
             ["1110", ["001", "unified"], "сирий-результат"]],
        ]],
        [["010", ["001", []]],
         ["1110", ["001", "unified"], "сирий-результат"]],
    ]:
        raise AssertionError("порушено 3 класи результатів уніфікації")
    for form in forms:
        if any(node[0] in {"001000", "101010000"}
               for node in visit(form) if isinstance(node, list)
               and node and isinstance(node[0], str)):
            raise AssertionError("неприпустима стара виклична голова")
    return names

def all_2046():
    records = []
    for width in range(1, 11):
        t = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
        records.extend((width, code, line) for code, line in
                       re.findall(r"(?m)^  \(([01]+) (.*)$", t))
    return records


def exact_catalog(records):
    if len(records) != 2046:
        raise AssertionError("потрібні всі 2046 записів")
    columns = ("(ук ", "(укр ", "(san ", "(en ", "(LISP ", "(sym ")
    for w in range(1, 11):
        start = sum(1 << n for n in range(1, w))
        rows = records[start:start + (1 << w)]
        expected = [(w, f"{n:0{w}b}") for n in range(1 << w)]
        if [(x, code) for x, code, _ in rows] != expected:
            raise AssertionError(f"D{w}: порушена бітність/порядок")
        for _, _, surface in rows:
            indices = [surface.find(field) for field in columns]
            if min(indices) < 0 or indices != sorted(indices):
                raise AssertionError("відсутня чи переставлена мовна проєкція")
    return {(width, code) for width, code, _ in records}


class UnifyObserveExact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forms = read(SOURCE.read_text(encoding="utf-8"))

    def test_two_exact_d4_functions_and_arity(self):
        self.assertEqual(len(validate(self.forms)), 2)

    def test_unify_evaluates_once_and_d9_address_does_not_auto_call(self):
        validate(self.forms)

    def test_three_outcome_classes_keep_empty_success(self):
        validate(self.forms)

    def test_source_has_only_current_ukrainian_d3_d4_call_heads(self):
        text = SOURCE.read_text(encoding="utf-8")
        code = text[text.index("(визначити "):]
        self.assertEqual(tuple(re.findall(r"\(([01]{3,10})(?=[\s(])", code)), ())
        self.assertEqual(code.count("(визначити "), 2)
        self.assertEqual(code.count("(функція "), 2)
        self.assertIn("(за-умовою", code)
        self.assertIn("(тотожне?", code)
        self.assertIn("(список", code)
        self.assertNotIn("(визначити unify-observe", code)

    def test_exhaustive_2046_domains_and_six_surfaces(self):
        ids = exact_catalog(all_2046())
        self.assertEqual(len(ids), 2046)
        self.assertEqual(len({int(code, 2) for _, code in ids}), 1024)

    def test_negative_truncated_d10_and_duplicate_d7(self):
        rows = all_2046()
        altered = rows[:]
        altered[-1] = (9, altered[-1][1][1:], altered[-1][2])
        with self.assertRaisesRegex(AssertionError, "D10"):
            exact_catalog(altered)
        altered = rows[:]
        start = sum(1 << n for n in range(1, 7))
        altered[start] = altered[start + 1]
        with self.assertRaisesRegex(AssertionError, "D7"):
            exact_catalog(altered)

    def test_negative_missing_sanskrit_projection(self):
        rows = all_2046()
        w, c, line = rows[-1]
        rows[-1] = (w, c, line.replace("(san ", "(sa ", 1))
        with self.assertRaisesRegex(AssertionError, "мовна"):
            exact_catalog(rows)

    def test_negative_resurrect_old_d6_or_d9(self):
        for old in ["001000", "101010000"]:
            altered = copy.deepcopy(self.forms)
            altered[1][2][2][1][0] = old
            with self.assertRaises(AssertionError):
                validate(altered)

    def test_negative_drop_fail_class_or_duplicate_unify(self):
        altered = copy.deepcopy(self.forms)
        altered[0][2][2][1][1][1][1][0] = "unified"
        with self.assertRaises(AssertionError):
            validate(altered)
        altered = copy.deepcopy(self.forms)
        altered[1][2][2][1] = ["unify", ["unify", "left", "right", "substitution"],
                              "right", "substitution"]
        with self.assertRaisesRegex(AssertionError, "рівно раз"):
            validate(altered)


    def test_current_ukrainian_identity_preserves_original_three_outcomes(self):
        original = self.forms
        validate(original)
        normalized = normalize_operator_heads(original)
        self.assertEqual(normalized[0][2][2][0], "110")
        self.assertEqual(normalized[0][2][2][1][0][0], "010")
        self.assertEqual(normalized[0][2][2][1][1][0], "110")
        self.assertEqual(normalized[1][2][2][0], HELPER)

    def test_negative_ukrainian_wrong_predicate_changes_law(self):
        altered = copy.deepcopy(self.forms)
        # В активному D3 COND другий рівень використовує EQ, не CONS.
        altered[0][2][2][1][1][1][0][0] = "сполучити"
        with self.assertRaisesRegex(AssertionError, "3 класи"):
            validate(altered)

if __name__ == "__main__":
    unittest.main()
