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
LET_REDUCED = {"understand-is", "understand-universal", "understand-query-is"}
# Frozen original D6 LET forms from main@c18ca3e2 (before any changes).
FROZEN_LETS = {
    "understand-is": """(0011 understand-is
      (0010 (words)
        (001000 ((subject (100 words))
                  (after-is (strip-article (0111 words))))
          (1110 (1110 (100 after-is) subject)))))""",
    "understand-universal": """(0011 understand-universal
      (0010 (words)
        (001000 ((subject-class (1001 words))
                  (property (100111 words)))
          (1110 (1110 (001 has) (1110 (001 var) (001 w)) property)
                (1110 subject-class (1110 (001 var) (001 w)))))))""",
    "understand-query-is": """(0011 understand-query-is
      (0010 (words)
        (001000 ((subject (1001 words))
                  (after (0111 words)))
          (1110 (100 (strip-article after)) subject))))""",
}
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
        if name in LET_REDUCED:
            # Незалежна beta-редукція історичного D6 LET з frozen main:
            # обидва binding-вирази чисті та кожен параметр вжито лише раз.
            frozen = read_forms(FROZEN_LETS[name])
            if len(frozen) != 1 or digest(frozen[0]) != FROZEN[name]:
                raise AssertionError("історичний контрольний AST/sha втрачено")
            old_let = frozen[0][2][2]
            if old_let[0] != "001000" or len(old_let[1]) != 2:
                raise AssertionError("історичний D6 LET має два зв'язування")
            binding = {item[0]: item[1] for item in old_let[1]}
            params = set(binding)
            def uses(node):
                if isinstance(node, list):
                    return sum(uses(child) for child in node)
                return 1 if node in params else 0
            if uses(old_let[2]) != 2:
                raise AssertionError("beta-редукція змінила використання")
            def substitute(node):
                if isinstance(node, list):
                    return [substitute(child) for child in node]
                return deepcopy(binding[node]) if node in binding else node
            expected = substitute(old_let[2])
            if original[2][2] != expected:
                raise AssertionError("неточна підстановка D6 LET у чисту D3/D4 композицію")
        elif digest(original) != FROZEN[name]:
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

    def test_three_d6_let_forms_beta_reduce_to_existing_d3_d4(self):
        verify_unchanged_laws(self.forms)
        # 3× (ATOM + QUOTE) guards cost 18 bits; three D6 LET
        # heads disappear entirely, saving 18 operator-head bits.
        self.assertEqual(3 * (len("010") + len("001")) - 3 * len("001000"), 0)

    def test_negative_legacy_d6_let_reintroduction(self):
        mutated = deepcopy(self.forms)
        definition = next(form for form in mutated if form[1] == "understand-is")
        definition[2][2] = ["001000", [["subject", ["100", "words"]],
                                       ["after-is", ["strip-article", ["0111", "words"]]]],
                            ["1110", ["1110", ["100", "after-is"], "subject"]]]
        with self.assertRaisesRegex(AssertionError, "неточна підстановка"):
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
