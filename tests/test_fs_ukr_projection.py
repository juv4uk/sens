"""Доказова проєкція FS: D1/D4 на повне укр, без Python-SENS evaluator.

Точний попередній Git blob і семантична S-форма — незалежні свідки.
Фізичне виконання належить існуючим SENS fixture/CI, не цим unittest.
"""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/fs.lisp"
D1 = ROOT / "lib/domains/d1.lisp"
D3 = ROOT / "lib/domains/d3.lisp"
D4 = ROOT / "lib/domains/d4.lisp"
PRE_MIGRATION_BLOB = "59b18e3dfdc10bb33036448dc4d3eb33efefec59"

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
    "0010": "функція", "0011": "визначити",
}


def parse(source: str):
    text = re.sub(r";[^\n]*", "", source)
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    index = 0

    def expr():
        nonlocal index
        if index >= len(tokens):
            raise ValueError("незавершена SENS форма")
        value = tokens[index]
        index += 1
        if value == ")":
            raise ValueError("зайва )")
        if value != "(":
            return value
        items = []
        while index < len(tokens) and tokens[index] != ")":
            items.append(expr())
        if index >= len(tokens):
            raise ValueError("незакрита SENS форма")
        index += 1
        return items

    result = []
    while index < len(tokens):
        result.append(expr())
    return result


def old_identity(node):
    if not isinstance(node, list):
        return "#d1:1" if node == "так" else node
    items = [old_identity(value) for value in node]
    if items and isinstance(items[0], str):
        reversed_peers = {value: key for key, value in REQUIRED.items()}
        items[0] = reversed_peers.get(items[0], items[0])
    return items


def source_to_previous(text: str) -> str:
    """Обернути тільки ратифіковані слова у коді; коментарі не редагувати."""
    result = []
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith(";"):
            result.append(line)
            continue
        line = re.sub(r"\(визначити(?=\s)", "(0011", line)
        line = re.sub(r"\(функція(?=\s)", "(0010", line)
        line = re.sub(r"\(так(?=\s|$)", "(#d1:1", line)
        result.append(line)
    return "".join(result)


def git_blob(text: str) -> str:
    data = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def verify(source: str) -> None:
    forms = parse(source)
    if [old_identity(form) for form in forms] != parse(EXACT_LAW):
        raise AssertionError("FS: порушено початковий D1/D3/D4 закон, арність або I/O")
    if len(forms) != 2 or any(
        form[0] != "визначити" or form[2][0] != "функція" for form in forms
    ):
        raise AssertionError("FS: не повна українська D4:0011/0010 проєкція")
    if git_blob(source_to_previous(source)) != PRE_MIGRATION_BLOB:
        raise AssertionError("FS: незворотна правка поза ратифікованими проєкціями")


class FsUkrProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_ratified_exact_d1_d3_d4(self):
        self.assertIn("(1 (ук так) (укр так)", D1.read_text(encoding="utf-8"))
        for domain, path in ((3, D3), (4, D4)):
            rows = dict(re.findall(
                r"(?m)^\s*\(([01]+) \(ук [^()]*\) \(укр ([^()\s]+)\)",
                path.read_text(encoding="utf-8"),
            ))
            for bits, name in REQUIRED.items():
                if len(bits) == domain:
                    self.assertEqual(rows[bits], name, f"D{domain}:{bits}")

    def test_exact_original_git_blob_and_full_sens_ast(self):
        verify(self.source)

    def test_no_legacy_numeric_heads_or_d1_literals(self):
        code = "\n".join(line for line in self.source.splitlines()
                         if not line.lstrip().startswith(";"))
        self.assertNotRegex(code, r"\([01]{3,9}(?=\s|\))")
        self.assertNotIn("#d1:1", code)
        self.assertEqual(code.count("(визначити "), 2)
        self.assertEqual(code.count("(функція "), 3)
        self.assertIn("(так", code)

    def test_host_io_boundary_and_public_names_untouched(self):
        for literal in ("(визначити read-file", "(визначити write-file",
                        "(read-file-utf8-raw path)",
                        "(write-file-bytes path (utf8-encode-string text))"):
            self.assertIn(literal, self.source)
        verify(self.source)

    def test_negative_wrong_operation_or_d1_semantics(self):
        for changed in (
            self.source.replace("(тотожне?", "(сполучити", 1),
            self.source.replace("(так", "(ні", 1),
            self.source.replace("(визначити read-file", "(функція read-file", 1),
            self.source.replace("read-file-utf8-raw", "read-file-bytes", 1),
        ):
            with self.assertRaises(AssertionError):
                verify(changed)

    def test_negative_wrong_domain_word_or_malformed_file(self):
        with self.assertRaises(AssertionError):
            verify(self.source.replace("(перше", "(00000101", 1))
        with self.assertRaises(ValueError):
            parse("(визначити read-file (функція (path)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
