"""Перевірки українських викличних голів encoder coverage — не host-оракул SENS.

Обернене переведення лише executable D3/D4 heads відновлює оригінальний
Git blob. Не мігрує дані під QUOTE, D6 LET, D8/D9 чи T5M-кодування.
"""
from collections import Counter
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "lib/machine/encoding/coverage-generator.lisp"
ORIGINAL_BLOB = "65f99d80597d047c8a0380b1200f110ecafc7891"
EXPECTED = {
    "100": ("перше", 36), "101": ("тотожне?", 3),
    "110": ("за-умовою", 28), "111": ("сполучити", 4),
    "1001": ("друге", 26), "1110": ("список", 18),
    "0011": ("визначити", 40), "0010": ("функція", 25),
    "001": ("як-є", 49), "010": ("атом?", 3), "011": ("решта", 40),
}
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
    for width in (3, 4):
        src = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
        for line in src.splitlines():
            row = re.match(
                r"^\s*\(([01]+)\s+\(ук [^\s()]+\)\s+\(укр ([^()\s]+)\)",
                line,
            )
            if row and len(row.group(1)) == width:
                result[row.group(1)] = row.group(2)
    return result


def git_blob(source):
    data = source.encode("utf-8")
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def verify(text):
    authority = ratified()
    for bits, (name, _) in EXPECTED.items():
        if authority.get(bits) != name:
            raise AssertionError("доменна проєкція змінилася: " + bits)
    inverse = {name: bits for bits, (name, _) in EXPECTED.items()}
    edits = []
    census = Counter()
    for head, start, end in call_heads(text):
        if head in EXPECTED:
            raise AssertionError("залишився виконуваний двійковий D3/D4 head: " + head)
        if head in inverse:
            bits = inverse[head]
            census[bits] += 1
            edits.append((start, end, bits))
    target = Counter({b: n for b, (_name, n) in EXPECTED.items()})
    if census != target:
        raise AssertionError(f"помилка census: {census} != {target}")
    restored = text
    for start, end, bits in reversed(edits):
        restored = restored[:start] + bits + restored[end:]
    if git_blob(restored) != ORIGINAL_BLOB:
        raise AssertionError("зміна цитати, операнда чи вихідного AST")
    return census


class EncoderCoverageProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PATH.read_text(encoding="utf-8")

    def test_exact_272_heads_and_original_blob(self):
        self.assertEqual(sum(verify(self.text).values()), 272)

    def test_other_domain_heads_and_quoted_data_untouched(self):
        self.assertIn("(110011110 acc s)", self.text)
        self.assertIn("(001000 ", self.text)
        self.assertIn("(як-є encoder-coverage-yes)", self.text)
        verify(self.text)

    def test_wrong_ukrainian_operator_fails(self):
        broken = self.text.replace("(тотожне?", "(сполучити", 1)
        self.assertNotEqual(broken, self.text)
        with self.assertRaisesRegex(AssertionError, "census|зміна"):
            verify(broken)

    def test_wrong_quoted_data_fails(self):
        broken = self.text.replace(
            "(як-є encoder-coverage-yes)", "(як-є encoder-coverage-no)", 1
        )
        self.assertNotEqual(broken, self.text)
        with self.assertRaisesRegex(AssertionError, "зміна"):
            verify(broken)

    def test_unbalanced_source_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "незакр"):
            parse("(визначити f (функція (x) x)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
