"""Точний тест міграції forward: 10 W8-макросів → D4 DEFINE+LAMBDA.

2046 джерельних координат D1–D10 — НЕ 2046 доведених
виконуваних механізмів. Ширина є частиною identity.
"""
from copy import deepcopy
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
FORWARD = ROOT / "lib/forward.lisp"
EXPECTED = [
    ("assert-fact!", ("fact",), "7db7a9f7dff36951"),
    ("assert-facts!", ("facts",), "f211bdbb1a481492"),
    ("retract-fact!", ("fact",), "a7bd2b5b9e9d7db6"),
    ("assert-fact-tms!", ("fact",), "a2b3f8b3f751688c"),
    ("run-tms!", ("rules",), "9dcf96dc4ae45815"),
    ("retract-fact-tms!", ("fact",), "3633a5528cdf3c35"),
    ("assert-fact-jtms!", ("fact",), "55ed218f002d6667"),
    ("run-jtms!", ("rules",), "d4e8ad9ff301eb6f"),
    ("run-jtms-multi!", ("rules",), "f6a9abadf2419f77"),
    ("retract-fact-jtms!", ("fact",), "e1eced4762943cfd"),
]
OLD_OTHER_FINGERPRINT = "9a9b6f936871476d"
TOKENS = re.compile(r'"(?:\\.|[^"\\])*"|;[^\n]*|[()]|[^\s();]+')
MASK64 = (1 << 64) - 1


def parse(text):
    tokens = [match.group() for match in TOKENS.finditer(text)
              if not match.group().startswith(";")]
    pos = 0

    def read():
        nonlocal pos
        if pos == len(tokens):
            raise AssertionError("незавершене S-вираження")
        value = tokens[pos]
        pos += 1
        if value == ")":
            raise AssertionError("зайва закривна дужка")
        if value != "(":
            return value
        items = []
        while pos < len(tokens) and tokens[pos] != ")":
            items.append(read())
        if pos == len(tokens):
            raise AssertionError("не вистачає )")
        pos += 1
        return items

    result = []
    while pos < len(tokens):
        result.append(read())
    return result


def canonical(form):
    if isinstance(form, list):
        return "(" + " ".join(map(canonical, form)) + ")"
    return form


def fingerprint(form):
    value = 0xCBF29CE484222325
    for scalar in canonical(form):
        value = ((value ^ ord(scalar)) * 0x100000001B3) & MASK64
    return f"{value:016x}"


def validate_forward(forms):
    if len(forms) != 83:
        raise AssertionError("втрачена верхньорівнева форма")
    expected = {name: (params, digest) for name, params, digest in EXPECTED}
    found = {}
    other = []
    for form in forms:
        if isinstance(form, list) and form and form[0] == "00001010":
            raise AssertionError("історична W8-DEFMACRO залишилася")
        if (isinstance(form, list) and len(form) > 1
                and isinstance(form[1], str) and form[1] in expected):
            name = form[1]
            if name in found:
                raise AssertionError("подвійне визначення " + name)
            if len(form) != 3 or form[0] != "0011":
                raise AssertionError("потрібна точна D4:0011 DEFINE")
            macro = form[2]
            if not (isinstance(macro, list) and len(macro) == 2
                    and macro[0] == "make-macro"):
                raise AssertionError("втрачено явний Closure→Macro")
            lam = macro[1]
            if not (isinstance(lam, list) and len(lam) == 3
                    and lam[0] == "0010"):
                raise AssertionError("потрібна точна D4:0010 LAMBDA")
            params, digest = expected[name]
            if tuple(lam[1]) != params:
                raise AssertionError("порушений порядок аргументів")
            if fingerprint(lam[2]) != digest:
                raise AssertionError("змінено AST-тіло " + name)
            found[name] = form
        else:
            other.append(form)
    if set(found) != set(expected):
        raise AssertionError("втрачено одне чи більше визначень")
    if len(other) != 73 or fingerprint(other) != OLD_OTHER_FINGERPRINT:
        raise AssertionError("змінено незаймані 73 форми")
    return found


def source_coordinates(root=ROOT):
    result = []
    for width in range(1, 11):
        table = (root / f"lib/domains/d{width}.lisp").read_text(
            encoding="utf-8")
        words = re.findall(r"(?m)^  \(([01]+)\s", table)
        result.extend((width, word) for word in words)
    return result


def validate_coordinates(cells):
    if len(cells) != 2046:
        raise AssertionError("не 2046 адрес")
    if len(set(cells)) != 2046:
        raise AssertionError("міждоменна колізія / дубль")
    offset = 0
    for width in range(1, 11):
        size = 1 << width
        actual = cells[offset:offset + size]
        target = [(width, format(value, f"0{width}b"))
                  for value in range(size)]
        if actual != target:
            raise AssertionError(f"D{width}: втрата бітності або порядку")
        offset += size
    return cells


class ForwardMacroD4Witness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forms = parse(FORWARD.read_text(encoding="utf-8"))

    def test_ten_forward_macros_have_exact_d4_composition(self):
        self.assertEqual(len(validate_forward(self.forms)), 10)

    def test_all_ten_historical_ast_bodies_and_other_73_forms_unchanged(self):
        forms = validate_forward(self.forms)
        self.assertEqual(
            [fingerprint(forms[name][2][1][2]) for name, _, _ in EXPECTED],
            [hash_ for _, _, hash_ in EXPECTED]
        )

    def test_exact_opcode_bit_budget_is_not_fake_wire_compression(self):
        forms = validate_forward(self.forms)
        self.assertEqual(sum(len(form[0]) + len(form[2][1][0])
                             for form in forms.values()), 80)
        self.assertEqual(10 * len("00001010"), 80)
        self.assertEqual(len("0011"), 4)
        self.assertEqual(len("0010"), 4)
        self.assertEqual(len("00011"), 5)  # D5 MACRO ≠ старий W8

    def test_exhaustive_2046_exact_domain_keys(self):
        coords = validate_coordinates(source_coordinates())
        self.assertEqual(len(coords), sum(1 << w for w in range(1, 11)))
        self.assertEqual(len(set(code for _, code in coords)), 2046)
        self.assertEqual(len({int(code, 2) for _, code in coords}), 1024)
        self.assertIn((3, "001"), coords)
        self.assertIn((4, "0001"), coords)
        self.assertIn((8, "00000001"), coords)
        self.assertIn((10, "0000000001"), coords)
        # D7 v2 128 ключів — це поверхня, не дозвіл callable для 128.

    def test_negative_domain_truncation_and_duplicate(self):
        cells = validate_coordinates(source_coordinates())
        broken = list(cells)
        pos = broken.index((10, "1111111111"))
        broken[pos] = (9, "111111111")
        with self.assertRaisesRegex(AssertionError, "колізія"):
            validate_coordinates(broken)
        broken = list(cells)
        pos = broken.index((7, "0100001"))
        broken[pos] = (7, "0100010")
        with self.assertRaisesRegex(AssertionError, "колізія"):
            validate_coordinates(broken)

    def test_negative_w8_resurrection_or_fake_d5(self):
        altered = deepcopy(self.forms)
        forms = validate_forward(altered)
        forms["assert-fact!"][0] = "00001010"
        with self.assertRaisesRegex(AssertionError, "історична W8"):
            validate_forward(altered)
        altered = deepcopy(self.forms)
        forms = validate_forward(altered)
        forms["assert-fact!"][2][1][0] = "00011"
        with self.assertRaisesRegex(AssertionError, "D4:0010"):
            validate_forward(altered)

    def test_negative_body_and_parameter_mutation(self):
        altered = deepcopy(self.forms)
        forms = validate_forward(altered)
        forms["run-tms!"][2][1][2][0] = "1111"
        with self.assertRaisesRegex(AssertionError, "AST-тіло"):
            validate_forward(altered)
        altered = deepcopy(self.forms)
        forms = validate_forward(altered)
        forms["run-tms!"][2][1][1][0] = "facts"
        with self.assertRaisesRegex(AssertionError, "аргументів"):
            validate_forward(altered)

    def test_negative_unrelated_module_drift(self):
        altered = deepcopy(self.forms)
        validate_forward(altered)
        for form in altered:
            if isinstance(form, list) and form and form[0] == "0011":
                if len(form) > 1 and form[1] not in {p[0] for p in EXPECTED}:
                    form[0] = "0010"
                    break
        with self.assertRaisesRegex(AssertionError, "незаймані 73"):
            validate_forward(altered)


if __name__ == "__main__":
    unittest.main()
