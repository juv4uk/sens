"""Exact Ukrainian D3/D4 call heads and current D8 table read benchmark."""
from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "benchmark-semantic-registry-read.lisp"
ORIGINAL_BLOB = "c5b5e40403efeb8bfd22ab296d088697c3b0c39e"
# (old exact-width source head, full Ukrainian projection, exact count)
REWRITES = (
    ("(0011 ", "(визначити ", 5),  # D4:0011 DEFINE
    ("(1110 ", "(список ", 5),     # D4:1110 LIST
    ("(001 ", "(як-є ", 5),        # D3:001 QUOTE
    ("(100 ", "(перше ", 2),       # D3:100 CAR
    ("(01011010)", "(монотонний-наносекунди)", 3),  # сід8 MONO-NS → ratified D10:0011110110
    ("(110110111 ", "(читати-файл ", 1),  # повна укр-проєкція
    ("(110101001 ", "(читати-всі ", 1),  # повна укр-проєкція
    ("(11011011\n", "(друкувати\n", 1),  # повна укр-проєкція
    ("(01011 ", "(відняти ", 3),  # повна укр-проєкція
)

# Лише локальні Lisp-змінні; цитовані поля результату й рядки — незмінні.
# Зміна даних навантаження: тепер читаємо чинну таблицю Д8, не старий SID8.
# Для перевірки історичного джерела кожне редагування обертається побайтово.
SOURCE_REWRITES = (
    ("; #74 — реальне навантаження зі старої міграції Python → SENS.",
     "; #74 — реальне навантаження читання чинної ратифікованої проєкції Д8.", 1),
    ("для реєстру такий обхід", "для таблиці домену такий обхід", 1),
    ('"lib/surface/semantic-registry.lisp"', '"lib/domains/d8.lisp"', 1),
    ("eco-lisp-script-perf/read-semantic-registry",
     "eco-lisp-script-perf/read-ratified-d8-table", 1),
)

LOCAL_REWRITES = (
    ("started", "початок", 3),  # локальне ім'я, не домен
    ("registry-text", "текст-реєстру", 2),  # локальне ім'я, не домен
    ("after-read", "після-читання", 3),  # локальне ім'я, не домен
    ("registry-form", "форма-реєстру", 2),  # локальне ім'я, не домен
    ("after-parse", "після-розбору", 3),  # локальне ім'я, не домен
)


def git_blob_sha(payload: bytes) -> str:
    header = b"blob " + str(len(payload)).encode("ascii") + b"\0"
    return hashlib.sha1(header + payload).hexdigest()


def mask_comments_and_strings(source: str) -> str:
    """Preserve offsets while hiding non-executable comments and strings."""
    out = list(source)
    i = 0
    while i < len(source):
        if source[i] == ";":
            while i < len(source) and source[i] != "\n":
                out[i] = " "
                i += 1
        elif source[i] == '"':
            out[i] = " "
            i += 1
            while i < len(source):
                if ord(source[i]) == 92:
                    out[i] = " "
                    if i + 1 < len(source) and source[i + 1] != "\n":
                        out[i + 1] = " "
                    i += 2
                elif source[i] == '"':
                    out[i] = " "
                    i += 1
                    break
                else:
                    if source[i] != "\n":
                        out[i] = " "
                    i += 1
        else:
            i += 1
    return "".join(out)


def paren_depth(source: str) -> int:
    depth = 0
    for char in mask_comments_and_strings(source):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return depth
    return depth


class UkrainianRegistryReadBenchmarkTests(unittest.TestCase):
    def test_full_ukr_heads_have_exact_ratified_counts(self):
        source = SOURCE.read_text(encoding="utf-8")
        visible = mask_comments_and_strings(source)
        for old, new, count in (*REWRITES, *LOCAL_REWRITES, *SOURCE_REWRITES):
            with self.subTest(old=old):
                self.assertEqual(source.count(old), 0,
                                 "retired binary head remains in the projected source")
                self.assertEqual(visible.count(old), 0,
                                 "retired binary head remains in executable source")
                self.assertEqual(source.count(new), count)
                self.assertEqual(visible.count(new), count,
                                 "only executable full-ukr heads may be projected")
        self.assertEqual(paren_depth(source), 0)

    def test_inverse_restores_the_original_git_blob_byte_exactly(self):
        source = SOURCE.read_text(encoding="utf-8")
        restored = source
        for old, new, count in reversed((*REWRITES, *LOCAL_REWRITES, *SOURCE_REWRITES)):
            self.assertEqual(restored.count(new), count)
            restored = restored.replace(new, old)
        payload = restored.encode("utf-8")
        self.assertEqual(git_blob_sha(payload), ORIGINAL_BLOB)
        self.assertEqual(paren_depth(restored), 0)

    def test_historical_d8_d9_and_measurement_fields_restore_unchanged(self):
        source = SOURCE.read_text(encoding="utf-8")
        restored = source
        for old, new, _ in reversed((*REWRITES, *LOCAL_REWRITES, *SOURCE_REWRITES)):
            restored = restored.replace(new, old)
        for token in ("01011010", "110110111", "110101001", "11011011",
                      "01011 after-read started", "01011 after-parse after-read",
                      "01011 after-parse started"):
            self.assertIn(token, restored)
        self.assertEqual(source.count("(визначити "), 5)
        self.assertEqual(source.count("(список "), 5)
        self.assertEqual(source.count("(як-є "), 5)
        self.assertEqual(source.count("(перше "), 2)


if __name__ == "__main__":
    unittest.main()
