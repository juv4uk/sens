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
OLD_HEADS = ("0011", "0010", "001000", "101010000", "110",
             "010", "110", "101", "001", "1110", "001", "0100",
             "101", "001", "1110", "001", "0100", "010",
             "1110", "001", "0100", "010", "1110", "001")


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


def validate(forms):
    if len(forms) != 2:
        raise AssertionError("рівно два D4 визначення")
    if not all(isinstance(f, list) and len(f) == 3 and f[0] == "0011"
               for f in forms):
        raise AssertionError("точна D4 DEFINE")
    names = {f[1]: f for f in forms}
    if set(names) != {HELPER, "unify-observe"}:
        raise AssertionError("очікувані лише приватний helper та public wrapper")
    helper = names[HELPER][2]
    public = names["unify-observe"][2]
    if not (helper[:2] == ["0010", ["raw", "left", "right", "substitution"]]
            and public[:2] == ["0010", ["left", "right", "substitution"]]):
        raise AssertionError("D4 LAMBDA параметри / арність")
    if public[2] != [HELPER, ["unify", "left", "right", "substitution"],
                      "left", "right", "substitution"]:
        raise AssertionError("Lisp-owned unify повинен обчислитися рівно раз")
    if helper[2] != [
        "110",
        [["010", "raw"], [
            "110",
            [["101", "raw", ["001", "fail"]],
             ["1110", ["001", "unification-failure"],
              "left", "right", "substitution"]],
            [["010", []], ["1110", ["001", "unified"], "raw"]],
        ]],
        [["010", []], ["1110", ["001", "unified"], "raw"]],
    ]:
        raise AssertionError("порушено 3 класи результатів уніфікації")
    for form in forms:
        if any(head in {"001000", "101010000"} for node in visit(form)
               if isinstance(node, list) and node
               for head in [node[0]] if isinstance(head, str)):
            raise AssertionError("неприпустимий виконавчий D6/D9 head")
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

    def test_source_opcode_heads_bit_budget(self):
        text = SOURCE.read_text(encoding="utf-8")
        code = text[text.index("(0011 "):]
        opheads = tuple(re.findall(r"\(([01]{3,10})(?=[\s(])", code))
        self.assertEqual(sum(map(len, OLD_HEADS)), 90)
        self.assertEqual(sum(map(len, opheads)), 58)
        self.assertEqual(58 - 90, -32)  # не оцінка фізичного T5

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


if __name__ == "__main__":
    unittest.main()
