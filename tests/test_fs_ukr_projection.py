"""Доказова проєкція FS: D1/D4 на повне укр, без Python-SENS evaluator.

Порівнюємо вихідну програму з первісним законом і перевіряємо зовнішній тег.
Фізичне виконання належить існуючим SENS fixture/CI, не цим unittest.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from scripts.report_ukr_projection_progress import ALLOWED

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/fs.lisp"
D1 = ROOT / "lib/domains/d1.lisp"
D3 = ROOT / "lib/domains/d3.lisp"
D4 = ROOT / "lib/domains/d4.lisp"
D9 = ROOT / "lib/domains/d9.lisp"

EXACT_LAW = """
(0011 файл-обробити-декодоване
  (0010 (decoded)
    (110
      ((успішно-декодовано? decoded)
       (1001 decoded))
      ((010 (001 ()))
       decoded))))
(0011 read-file
  (0010 (path)
    (файл-обробити-декодоване
      (read-file-utf8-raw path))))
(0011 write-file
  (0010 (path text)
    (1001 (1110 (write-file-bytes path (utf8-encode-string text)) text))))
"""

REQUIRED = {
    "001": "як-є", "010": "атом?", "100": "перше", "101": "тотожне?",
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
        return {"шлях": "path", "декодоване": "decoded", "текст": "text",
                "читати-файл": "read-file", "записати-файл": "write-file",
                "читати-сирий-текст-файла": "read-file-utf8-raw",
                "записати-байти-файла": "write-file-bytes"}.get(node, node)
    items = [old_identity(value) for value in node]
    if items and isinstance(items[0], str):
        reversed_peers = {value: key for key, value in REQUIRED.items()}
        reversed_peers["кодування-юнікод-8-кодувати-рядок"] = "utf8-encode-string"  # D9:000010101
        items[0] = reversed_peers.get(items[0], items[0])
    return items


def verify(source: str) -> None:
    # Забороняємо старі прямі двійкові викличні голови навіть там,
    # де історичний receipt навмисно зіставляє їхню тотожність.
    executable = "\n".join(line for line in source.splitlines()
                           if not line.lstrip().startswith(";"))
    if re.search(r"\([01]{3,9}(?=\s|\))", executable):
        raise AssertionError("FS: старий двійковий викличний голов замість укр проєкції")
    forms = parse(source)
    # Після трьох українських DEFINE тепер існує справжній кінцевий
    # виклик-свідок SENS. Структурний тест не виконує семантики замість SENS.
    if len(forms) != 4 or forms[-1] != ["атом?", ["як-є", []]]:
        raise AssertionError("FS: відсутній або змінений кінцевий D1-виклик-свідок")
    definitions = forms[:-1]
    if [old_identity(form) for form in definitions] != parse(EXACT_LAW):
        raise AssertionError("FS: порушено початковий D1/D3/D4 закон, арність або I/O")
    if len(definitions) != 3 or any(
        form[0] != "визначити" or form[2][0] != "функція" for form in definitions
    ):
        raise AssertionError("FS: не повна українська D4:0011/0010 проєкція")
    # Зовнішній тег не перейменовується: кодек зберігає стару семантику.
    codec_source = (ROOT / "lib/utf8.lisp").read_text(encoding="utf-8")
    tag = "ознака-успішного-декодування"
    if codec_source.count(f"(визначити {tag} (як-є decoded))") != 1:
        raise AssertionError("FS: точний протокольний тег не визначено в кодеку")
    if sum(line.startswith(f"(визначити {tag} ") for line in codec_source.splitlines()) != 1:
        raise AssertionError("FS: неоднозначне визначення протокольного тегу")
    if any(char not in ALLOWED for char in source):
        raise AssertionError("FS: джерело не повністю на українській клавіатурі")


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

    def test_full_ukrainian_source_preserves_original_sens_law(self):
        self.assertIn(
            "(000010101 (ук кодування-юнікод-8-кодувати-рядок) "
            "(укр кодування-юнікод-8-кодувати-рядок)",
            D9.read_text(encoding="utf-8"),
        )
        verify(self.source)

    def test_no_legacy_numeric_heads_or_d1_literals(self):
        code = "\n".join(line for line in self.source.splitlines()
                         if not line.lstrip().startswith(";"))
        self.assertNotRegex(code, r"\([01]{3,9}(?=\s|\))")
        self.assertNotIn("#d1:1", code)
        self.assertEqual(code.count("(визначити "), 3)
        self.assertEqual(code.count("(функція "), 3)
        self.assertIn("((атом? (як-є ()))", code)
        self.assertNotIn("(так", code)
        self.assertNotIn("((функція ", code)
        self.assertIn("(файл-обробити-декодоване", code)

    def test_host_io_boundary_and_public_ukr_names(self):
        for literal in ("(визначити читати-файл", "(визначити записати-файл",
                        "(читати-сирий-текст-файла шлях)",
                        "(записати-байти-файла шлях (кодування-юнікод-8-кодувати-рядок текст))"):
            self.assertIn(literal, re.sub(r"\s+", " ", self.source))
        executable = "\\n".join(line for line in self.source.splitlines()
                                 if not line.lstrip().startswith(";"))
        self.assertNotIn("(read-file-utf8-raw ", executable)
        self.assertNotIn("(write-file-bytes ", executable)
        verify(self.source)

    def test_negative_wrong_operation_or_d1_semantics(self):
        for changed in (
            self.source.replace("(успішно-декодовано?", "(атом?", 1),
            self.source.replace("(атом? (як-є ()))", "(атом? (як-є (())))", 1),
            self.source.replace("(визначити читати-файл", "(функція читати-файл", 1),
            self.source.replace("читати-сирий-текст-файла", "читати-файл-байти", 1),
            self.source.replace("(файл-обробити-декодоване\n", "(читати-файл\n", 1),
        ):
            with self.assertRaises(AssertionError):
                verify(changed)

    def test_negative_wrong_full_ukr_identity_or_lexical_binding(self):
        for corrupted in (
            self.source.replace("(кодування-юнікод-8-кодувати-рядок текст)",
                                "(кодування-юнікод-8-декодувати-рядок текст)", 1),
            self.source.replace("(читати-сирий-текст-файла шлях)",
                                "(читати-сирий-текст-файла текст)", 1),
        ):
            with self.assertRaises(AssertionError):
                verify(corrupted)

    def test_negative_wrong_domain_word_or_malformed_file(self):
        with self.assertRaises(AssertionError):
            verify(self.source.replace("(друге", "(1001", 1))
        with self.assertRaises(ValueError):
            parse("(визначити читати-файл (функція (шлях)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
