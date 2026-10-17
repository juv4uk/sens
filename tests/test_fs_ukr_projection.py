"""Перевірки українських D3/D4 голів файлів, без host-імітації виконання SENS.

Порівнюємо AST з тією самою точною структурою, що була до зміни surface.
Реальне семантичне виконання лишається за SENS/Rust source-pinned тестами.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/fs.lisp"
D3 = ROOT / "lib/domains/d3.lisp"
D4 = ROOT / "lib/domains/d4.lisp"

# Незмінний точний закон двох власних функцій, до заміни лише call surface.
EXACT_LAW = """
(0011 read-file
  (0010 (path)
    ((0010 (decoded)
      (110
        ((101 (100 decoded) (001 decoded))
         (1001 decoded))
        (#d1:1
         decoded)))
     (read-file-utf8-raw path))))
(0011 write-file
  (0010 (path text)
    (1001 (1110 (write-file-bytes path (utf8-encode-string text)) text))))
"""

REQUIRED = {
    "001": "як-є", "100": "перше", "101": "тотожне?",
    "110": "за-умовою", "1001": "друге", "1110": "список",
}

def parse(source: str):
    source = re.sub(r";[^\n]*", "", source)
    toks = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', source)
    pos = 0
    def expr():
        nonlocal pos
        if pos >= len(toks):
            raise ValueError("незакрита форма")
        value = toks[pos]; pos += 1
        if value == ")":
            raise ValueError("зайва )")
        if value != "(":
            return value
        items = []
        while pos < len(toks) and toks[pos] != ")":
            items.append(expr())
        if pos >= len(toks):
            raise ValueError("незакрита форма")
        pos += 1
        return items
    out = []
    while pos < len(toks):
        out.append(expr())
    return out


def old_identity(node):
    if not isinstance(node, list):
        return node
    items = [old_identity(item) for item in node]
    if items and isinstance(items[0], str):
        reverse = {name: bits for bits, name in REQUIRED.items()}
        items[0] = reverse.get(items[0], items[0])
    return items


def verify(forms):
    if [old_identity(form) for form in forms] != parse(EXACT_LAW):
        raise AssertionError("FS: змінився точний D3/D4 закон, arity чи quote-data")
    for form in forms:
        if form[0] != "0011" or form[2][0] != "0010":
            raise AssertionError("FS: owner-bound D4 DEFINE/LAMBDA зруйновано")
    return True


class FsUkrProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = SOURCE.read_text(encoding="utf-8")
        cls.forms = parse(cls.content)

    def test_current_ratified_ukrainian_spellings(self):
        for n, table in [(3, D3), (4, D4)]:
            rows = dict(re.findall(r"(?m)^  \(([01]+) \(ук ([^()\s]+)\)", table.read_text(encoding="utf-8")))
            for bits, name in REQUIRED.items():
                if len(bits) == n:
                    self.assertEqual(rows[bits], name)
        self.assertTrue(verify(self.forms))

    def test_no_unmigrated_old_call_heads(self):
        code = self.content[self.content.index("(0011 "):]
        found = re.findall(r"\(([01]{3,9})(?=[\s(])", code)
        self.assertEqual(found, ["0011", "0010", "0010", "0011", "0010"])
        self.assertIn("(за-умовою", code)
        self.assertIn("(тотожне?", code)

    def test_negative_wrong_operation_or_fallback(self):
        mutated = parse(self.content.replace("(тотожне?", "(сполучити", 1))
        with self.assertRaisesRegex(AssertionError, "змінився точний"):
            verify(mutated)
        mutated = parse(self.content.replace("#d1:1", "#d1:0", 1))
        with self.assertRaisesRegex(AssertionError, "змінився точний"):
            verify(mutated)

    def test_negative_bare_eight_bit_identity(self):
        mutated = parse(self.content.replace("(перше", "(00000101", 1))
        with self.assertRaisesRegex(AssertionError, "змінився точний"):
            verify(mutated)


if __name__ == "__main__":
    unittest.main(verbosity=2)
