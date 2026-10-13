"""Незалежний AST-свідок для Advice Taker + 2046 доменних координат.

Доводимо 3 D3 guards і незмінність 8 source-функцій після вилучення
трьох нових перших клауз. Механізм виконання перевіряє Rust job окремо.
"""
from copy import deepcopy
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/understand.lisp"
TOKENS = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();]+')
GUARDED = {"strip-article", "understand", "understand-query"}
FROZEN = {
    "strip-article": "db88279d0f09812f",
    "understand-is": "c496864af8ccff2c",
    "understand-relation": "c4e51fdb4bfe9317",
    "understand-universal": "730247ec3b359011",
    "understand": "420149e09343a899",
    "understand-query-is": "12138acbeb6d89f6",
    "understand-query-relation": "6dd63349949d36fd",
    "understand-query": "a267fbc6d7ca58d6",
}
MASK = (1 << 64) - 1


def read_forms(source):
    words = [m.group() for m in TOKENS.finditer(source)
             if not m.group().startswith(";")]
    pos = 0

    def read():
        nonlocal pos
        if pos >= len(words):
            raise AssertionError("неповний S-expression")
        word = words[pos]
        pos += 1
        if word == ")":
            raise AssertionError("зайва )")
        if word != "(":
            return word
        values = []
        while pos < len(words) and words[pos] != ")":
            values.append(read())
        if pos >= len(words):
            raise AssertionError("незакрита форма")
        pos += 1
        return values

    result = []
    while pos < len(words):
        result.append(read())
    return result


def canonical(node):
    return "(" + " ".join(map(canonical, node)) + ")" if isinstance(node, list) else node


def digest(node):
    h = 0xCBF29CE484222325
    for char in canonical(node):
        h = ((h ^ ord(char)) * 0x100000001B3) & MASK
    return f"{h:016x}"


def verify_unchanged_laws(forms):
    if len(forms) != 8:
        raise AssertionError("кількість основних функцій змінилася")
    names = set()
    for form in forms:
        if not (isinstance(form, list) and len(form) == 3
                and form[0] == "0011" and isinstance(form[1], str)):
            raise AssertionError("визначення має лишатися D4:0011")
        name = form[1]
        if name in names or name not in FROZEN:
            raise AssertionError("невідома/дубльована функція")
        names.add(name)
        original = deepcopy(form)
        if name in GUARDED:
            lam = original[2]
            if not (isinstance(lam, list) and lam[0] == "0010"
                    and isinstance(lam[2], list) and lam[2][0] == "110"):
                raise AssertionError("невалідна D4 λ / D3 COND")
            clauses = lam[2][1:]
            if not clauses or clauses[0] != [["010", "words"], ["001", []]]:
                raise AssertionError("непорожній CAR до точного D3 ATOM")
            lam[2].pop(1)
        if digest(original) != FROZEN[name]:
            raise AssertionError("історичне тіло змінено: " + name)
    if names != set(FROZEN):
        raise AssertionError("втрачено визначення")
    return forms


def catalog():
    records = []
    for width in range(1, 11):
        source = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
        rows = re.findall(r"(?m)^  \(([01]+) (.*)$", source)
        records.extend((width, binary, rest) for binary, rest in rows)
    return records


def verify_catalog(records):
    if len(records) != 2046:
        raise AssertionError("не всі D1–D10: 2046")
    seen = set()
    start = 0
    order = ("(ук ", "(укр ", "(san ", "(en ", "(LISP ", "(sym ")
    for width in range(1, 11):
        expected = [format(v, f"0{width}b") for v in range(1 << width)]
        rows = records[start:start + (1 << width)]
        if [b for _, b, _ in rows] != expected or any(w != width for w, _, _ in rows):
            raise AssertionError(f"D{width}: втрачено точні leading zeros/порядок")
        for w, b, body in rows:
            key = w, b
            if key in seen:
                raise AssertionError("дубль доменної координати")
            seen.add(key)
            places = [body.find(s) for s in order]
            if min(places) < 0 or places != sorted(places):
                raise AssertionError("бракує проєкції uk/укр/sa/en/LISP/sym")
        start += 1 << width
    return seen


class UnderstandExactD3Witness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forms = read_forms(SOURCE.read_text(encoding="utf-8"))

    def test_all_eight_functions_preserve_original_laws(self):
        verify_unchanged_laws(self.forms)

    def test_three_empty_guards_are_d3_not_legacy_w8(self):
        verify_unchanged_laws(self.forms)
        self.assertEqual(len(GUARDED), 3)
        self.assertEqual(3 * (len("010") + len("001")), 18)

    def test_negative_missing_guard(self):
        mutated = deepcopy(self.forms)
        mutated[0][2][2].pop(1)
        with self.assertRaisesRegex(AssertionError, "непорожній CAR"):
            verify_unchanged_laws(mutated)

    def test_negative_legacy_8bit_or_wrong_d1_result(self):
        for bad in ["00000101", "1"]:
            mutated = deepcopy(self.forms)
            mutated[0][2][2][1][0][0] = bad
            with self.assertRaisesRegex(AssertionError, "D3 ATOM"):
                verify_unchanged_laws(mutated)

    def test_negative_mutated_original_function_body(self):
        mutated = deepcopy(self.forms)
        mutated[2][2][2][0] = "001"
        with self.assertRaisesRegex(AssertionError, "історичне тіло"):
            verify_unchanged_laws(mutated)

    def test_all_2046_exact_coordinates_and_six_surfaces(self):
        rows = catalog()
        coords = verify_catalog(rows)
        self.assertEqual(len(coords), 2046)
        self.assertEqual(len(set(int(bits, 2) for _, bits in coords)), 1024)

    def test_negative_w10_to_w9_truncation(self):
        rows = catalog()
        verify_catalog(rows)
        mutated = list(rows)
        i = next(i for i, (w, b, _) in enumerate(mutated) if w == 10 and b == "1111111111")
        mutated[i] = (9, "111111111", mutated[i][2])
        with self.assertRaisesRegex(AssertionError, "D10"):
            verify_catalog(mutated)

    def test_negative_missing_linguistic_projection(self):
        rows = catalog()
        w, b, text = rows[-1]
        rows[-1] = (w, b, text.replace("(san ", "(sans ", 1))
        with self.assertRaisesRegex(AssertionError, "проєкції"):
            verify_catalog(rows)


if __name__ == "__main__":
    unittest.main()
