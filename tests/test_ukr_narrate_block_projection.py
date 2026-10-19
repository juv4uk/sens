"""Незалежний статичний свідок exact-width української міграції двох бібліотек.

Не виконує семантику SENS: перевіряє AST, quote-data і збереження
попереднього структурного представлення після поверхневої проєкції.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "lib/narrate.lisp": ("ce86818639d2bb14", 26),
    "lib/machine/block-exact.lisp": ("f7db9b992da3ef23", 6),
}
# Історичні виклики на рядках із D9 без доказу callable не переписуються
# за схожими бітами. Залишкові D4 супутники цих самих рядків також
# навмисно незмінні, щоб source-literal guard не отримав нових raw голів.
REMAINING_EXACT_HEADS = {
    "lib/narrate.lisp": Counter(),
    "lib/machine/block-exact.lisp": Counter(),
}
REQUIRED = {
    1: {"0": "ні", "1": "так"},
    3: {"001": "як-є", "010": "атом?", "011": "решта",
        "100": "перше", "101": "тотожне?", "110": "за-умовою",
        "111": "сполучити"},
    4: {"0010": "функція", "0011": "визначити",
        "0100": "хибне?", "0101": "порожній?",
        "1001": "друге", "1110": "список", "1111": "приєднати"},
    5: {"10011": "третє"},
    6: {"001000": "нехай", "100111": "четверте"},
}
LOCAL_HISTORY = {
    "список-завершується-порожнім?": "narrate-proper-list?",
    "список-із-рівно-двох-елементів?": "narrate-list-exact-two?",
    "список-із-рівно-трьох-елементів?": "narrate-list-exact-three?",
}

DOMAIN_ROW = re.compile(
    r"^\s*\(([01]+)\s+\(ук\s+[^()]*\)\s+"
    r"\(укр\s+([^\s()]+)\)"
)


def lexer(source: str) -> list[str]:
    """S-expr токени без коментарів, але зі збереженням рядків як даних."""
    result = []
    i = 0
    while i < len(source):
        char = source[i]
        if char.isspace():
            i += 1
        elif char == ";":
            end = source.find("\n", i)
            i = len(source) if end == -1 else end
        elif char in "()":
            result.append(char)
            i += 1
        elif char == '"':
            start = i
            i += 1
            escaped = False
            terminated = False
            while i < len(source):
                current = source[i]
                i += 1
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == '"':
                    terminated = True
                    break
            if not terminated:
                raise ValueError("Незавершений Lisp-рядок")
            result.append(source[start:i])
        else:
            start = i
            while i < len(source) and not (
                source[i].isspace() or source[i] in '();"'
            ):
                i += 1
            if i == start:
                raise ValueError("Некоректний символ Lisp")
            result.append(source[start:i])
    return result


def parse(source: str) -> list:
    tokens = lexer(source)
    pos = 0

    def one():
        nonlocal pos
        if pos >= len(tokens):
            raise ValueError("Несподіваний EOF")
        tok = tokens[pos]
        pos += 1
        if tok == "(":
            children = []
            while pos < len(tokens) and tokens[pos] != ")":
                children.append(one())
            if pos == len(tokens):
                raise ValueError("Незакритий список")
            pos += 1
            return children
        if tok == ")":
            raise ValueError("Зайва закривальна дужка")
        return tok

    root = []
    while pos < len(tokens):
        root.append(one())
    return root


def projection_index() -> dict[str, str]:
    names = {}
    for d in REQUIRED:
        table = ROOT / "lib" / "domains" / f"d{d}.lisp"
        for line in table.read_text(encoding="utf-8").splitlines():
            match = DOMAIN_ROW.match(line)
            if not match:
                continue
            bits, name = match.groups()
            if len(bits) != d:
                continue
            if name in names and names[name] != bits:
                raise ValueError(f"Неоднозначна укр проєкція: {name}")
            names[name] = bits
    return names


def normalized(node, names: dict[str, str], quoted: bool = False) -> str:
    """Відновити лише exact head/D1 spelling, ніколи не чіпаючи quoted data."""
    if isinstance(node, str):
        if not quoted and node in ("так", "ні"):
            return names[node]
        if not quoted:
            return LOCAL_HISTORY.get(node, node)
        return node
    if not node:
        return "()"
    raw_head = node[0] if isinstance(node[0], str) else None
    head = raw_head
    if not quoted and head in names:
        bits = names[head]
        if len(bits) in (1, 3, 4, 5, 6):
            head = bits
    elif not quoted and head in LOCAL_HISTORY:
        head = LOCAL_HISTORY[head]
    next_quoted = quoted or (raw_head in ("001", "як-є") and not quoted)
    children = []
    for index, child in enumerate(node):
        if index == 0 and isinstance(child, str) and head is not None:
            children.append(head)
        else:
            children.append(normalized(child, names, next_quoted))
    return "(" + " ".join(children) + ")"


def fingerprint(text: str) -> str:
    """FNV-1a-64 тільки для зафіксованого синтаксичного свідка, не безпеки."""
    value = 0xCBF29CE484222325
    for byte in text.encode("utf-8"):
        value = ((value ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016x}"


def numeric_heads(tree: list) -> Counter:
    count = Counter()

    def walk(node, quoted=False):
        if isinstance(node, str) or not node or quoted:
            return
        first = node[0]
        if isinstance(first, str) and re.fullmatch(r"[01]+", first):
            count[first] += 1
        if first in ("001", "як-є"):
            return
        for child in node:
            walk(child, False)

    for form in tree:
        walk(form)
    return count


class UkrainianNarrateBlockProjectionTests(unittest.TestCase):
    def test_local_structural_helpers_use_full_ukr_names(self):
        source = (ROOT / "lib/narrate.lisp").read_text(encoding="utf-8")
        active = "\n".join(
            line for line in source.splitlines()
            if not line.lstrip().startswith(";")
        )
        for current, history in LOCAL_HISTORY.items():
            with self.subTest(helper=current):
                self.assertIn(f"(визначити {current}", active)
                self.assertIn(f"({current} ", active)
                self.assertNotIn(history, active)

    @classmethod
    def setUpClass(cls):
        cls.index = projection_index()

    def test_each_edited_identity_uses_ratified_exact_domain_width(self):
        for width, rows in REQUIRED.items():
            for bits, spelling in rows.items():
                with self.subTest(domain=width, bits=bits):
                    self.assertEqual(len(bits), width)
                    self.assertEqual(self.index[spelling], bits)

    def test_original_canonical_ast_is_preserved_in_both_sources(self):
        for filename, (expected_fingerprint, expected_forms) in SOURCES.items():
            with self.subTest(file=filename):
                parsed = parse((ROOT / filename).read_text(encoding="utf-8"))
                self.assertEqual(len(parsed), expected_forms)
                canonical = "\n".join(normalized(form, self.index) for form in parsed)
                self.assertEqual(fingerprint(canonical), expected_fingerprint)

    def test_only_explicitly_unverified_numeric_heads_remain(self):
        for filename, remaining in REMAINING_EXACT_HEADS.items():
            with self.subTest(file=filename):
                parsed = parse((ROOT / filename).read_text(encoding="utf-8"))
                self.assertEqual(numeric_heads(parsed), remaining)
        # D9 resident codes must not be assigned D3 or D4 semantics by width.
        d9 = (ROOT / "lib/domains/d9.lisp").read_text(encoding="utf-8")
        self.assertIn("(110110101 (ук п'ятий) (укр п'ятий)", d9)
        self.assertIn("(110101100 (ук символ?) (укр символ?)", d9)

    def test_no_new_source_encoded_d1_literals(self):
        for filename in SOURCES:
            with self.subTest(file=filename):
                source = (ROOT / filename).read_text(encoding="utf-8")
                code_only = "\n".join(
                    line.split(";", 1)[0] for line in source.splitlines()
                    if not line.lstrip().startswith(";")
                )
                self.assertNotRegex(code_only, r"#d1:[01]+")

    def test_block_exact_uses_ukrainian_bootstrap(self):
        source = (ROOT / "lib/machine/block-exact.lisp").read_text(
            encoding="utf-8"
        )
        self.assertEqual(source.count("(визначити "), 6)
        self.assertEqual(source.count("(функція "), 6)
        self.assertIn("(як-є ())", source)
        self.assertIn("(список форма)", source)
        self.assertIn("(приєднати блок (список форма))", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
