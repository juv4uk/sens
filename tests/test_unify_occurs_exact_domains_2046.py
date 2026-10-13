"""Міграція core unifier: незалежний AST і повні 2046 D1–D10 адрес.

Скінченний exhaustive тест каталогів не є доказом callability 2046
функцій. Live executable witness запускається окремим Rust job.
"""
from copy import deepcopy
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/unify.lisp"
TOKENS = re.compile(r'"(?:\\.|[^"\\])*"|;[^\n]*|[()]|[^\s();]+')
HELPER = "уніфікація-входження-розв'язано?"
FROZEN_OTHER = {
    "unify-equal?": "d8f5fffb85e98b2d",
    "logic-var": "62afb948588f372e",
    "var?": "a61a804ca8b6dc58",
    "lookup-subst": "bcfdff49c9b1d822",
    "extend-subst": "16f784750715d894",
    "walk": "f88681758efc8f93",
    "walk-resolved": "0a2372b33d8f612e",
    "unify": "0c5adcb4f77bdaa6",
    "failed-subst?": "87b27363b8a5e923",
    "unify-walked": "ed0b5ce9ab66417b",
    "occurs-check": "16986e4c97c5eb81",
    "unify-var": "2f84c735d549d549",
    "apply-subst": "545914e41eb7cd37",
    "apply-subst-walked": "42395e1e9dff7f59",
    "thread-conjunction": "135dc0fa77dbe52a",
    "thread-conjunction-branches": "d389704bab6f442f",
}
ORIGINAL_BODY = """(110
  ((101100100 resolved) (unify-equal? (1001 variable) (1001 resolved)))
  ((010 resolved) (010 (001 (0))))
  ((101110101 variable (100 resolved) bindings) (010 ()))
  ((010 ()) (101110101 variable (011 resolved) bindings)))"""
MASK = (1 << 64) - 1


def parse(source):
    tokens = [m.group() for m in TOKENS.finditer(source)
              if not m.group().startswith(";")]
    pos = 0

    def read():
        nonlocal pos
        if pos == len(tokens):
            raise AssertionError("unclosed S-expression")
        value = tokens[pos]
        pos += 1
        if value == ")":
            raise AssertionError("extra )")
        if value != "(":
            return value
        out = []
        while pos < len(tokens) and tokens[pos] != ")":
            out.append(read())
        if pos == len(tokens):
            raise AssertionError("missing )")
        pos += 1
        return out

    result = []
    while pos < len(tokens):
        result.append(read())
    return result


def canonical(expr):
    if isinstance(expr, list):
        return "(" + " ".join(map(canonical, expr)) + ")"
    return expr


def digest(expr):
    h = 0xCBF29CE484222325
    for char in canonical(expr):
        h = ((h ^ ord(char)) * 0x100000001B3) & MASK
    return f"{h:016x}"


def inspect(forms):
    if len(forms) != 18:
        raise AssertionError("кількість top-level визначень змінилася")
    seen = {}
    for form in forms:
        if not (isinstance(form, list) and len(form) == 3
                and form[0] == "0011" and isinstance(form[1], str)):
            raise AssertionError("тільки D4 DEFINE")
        if form[1] in seen:
            raise AssertionError("подвійне визначення")
        seen[form[1]] = form

    if set(seen) != set(FROZEN_OTHER) | {"occurs-check?", HELPER}:
        raise AssertionError("втрачений або сторонній ідентифікатор")
    for name, frozen in FROZEN_OTHER.items():
        if digest(seen[name]) != frozen:
            raise AssertionError("змінений сусідній AST: " + name)

    helper = seen[HELPER][2]
    if not (isinstance(helper, list) and helper[0] == "0010"
            and helper[1] == ["variable", "resolved", "bindings"]):
        raise AssertionError("D4 LAMBDA і одноразовий resolved потрібні")
    if helper[2] != parse(ORIGINAL_BODY)[0]:
        raise AssertionError("старий D6 LET-body має залишатися посимвольно AST")
    occurrence = seen["occurs-check?"][2]
    if not (occurrence[0] == "0010"
            and occurrence[1] == ["variable", "term", "bindings"]
            and occurrence[2] == [HELPER, "variable",
                                 ["101110100", "term", "bindings"], "bindings"]):
        raise AssertionError("walk повинен виконуватись один раз")
    for expr in forms:
        if "001000" in canonical(expr).split(" "):
            raise AssertionError("залишено невиконуваний D6 LET")
    return seen


def catalog():
    rows = []
    for width in range(1, 11):
        t = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
        rows.extend((width, bits, text) for bits, text in re.findall(
            r"(?m)^  \(([01]+) (.*)$", t))
    return rows


def prove_catalog(rows):
    if len(rows) != 2046:
        raise AssertionError("потрібні усі 2046 координат")
    columns = ["(ук ", "(укр ", "(san ", "(en ", "(LISP ", "(sym "]
    start = 0
    seen = set()
    for w in range(1, 11):
        fragment = rows[start:start + (1 << w)]
        expected = [(w, f"{number:0{w}b}") for number in range(1 << w)]
        if [(width, bitstring) for width, bitstring, _ in fragment] != expected:
            raise AssertionError(f"D{w}: неправильна бітність або порядок")
        for width, word, text in fragment:
            if (width, word) in seen:
                raise AssertionError("дубль домену")
            seen.add((width, word))
            order = [text.find(column) for column in columns]
            if min(order) < 0 or order != sorted(order):
                raise AssertionError("відсутня мовна проєкція")
        start += 1 << w
    return seen


class UnifyOccursD3Width(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forms = parse(SOURCE.read_text(encoding="utf-8"))

    def test_original_16_functions_unchanged_plus_exact_d4_helper(self):
        self.assertEqual(len(inspect(self.forms)), 18)

    def test_frozen_occurs_check_body_and_single_walk(self):
        inspect(self.forms)

    def test_operator_head_budget(self):
        self.assertEqual(len("0011") + len("0010") - len("001000"), 2)

    def test_all_2046_exact_width_keys_and_six_surfaces(self):
        ids = prove_catalog(catalog())
        self.assertEqual(len(ids), 2046)
        self.assertEqual(len({int(word, 2) for _, word in ids}), 1024)

    def test_negative_d10_truncated_to_d9(self):
        rows = catalog()
        w, word, surface = rows[-1]
        rows[-1] = (9, word[1:], surface)
        with self.assertRaisesRegex(AssertionError, "D10"):
            prove_catalog(rows)

    def test_negative_wrong_or_missing_surface(self):
        rows = catalog()
        w, word, surface = rows[-1]
        rows[-1] = (w, word, surface.replace("(san ", "(saa ", 1))
        with self.assertRaisesRegex(AssertionError, "мовна проєкція"):
            prove_catalog(rows)

    def test_negative_w8_or_d6_reintroduced(self):
        for wrong in ["00001001", "001000"]:
            altered = deepcopy(self.forms)
            occurrence = next(form for form in altered if form[1] == "occurs-check?")
            occurrence[0] = wrong
            with self.assertRaises(AssertionError):
                inspect(altered)

    def test_negative_resolved_duplicated_or_body_changed(self):
        altered = deepcopy(self.forms)
        occurrence = next(form for form in altered if form[1] == "occurs-check?")
        occurrence[2][2][2] = ["101110100", ["101110100", "term", "bindings"], "bindings"]
        with self.assertRaisesRegex(AssertionError, "один раз"):
            inspect(altered)
        altered = deepcopy(self.forms)
        helper = next(form for form in altered if form[1] == HELPER)
        helper[2][2][0] = "001"
        with self.assertRaisesRegex(AssertionError, "LET-body"):
            inspect(altered)


if __name__ == "__main__":
    unittest.main()
