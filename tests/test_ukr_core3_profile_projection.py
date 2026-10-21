"""Full Ukrainian projection for the pinned Core3 profile source checker."""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/check-core3-profile-contract.lisp"
PROJECTIONS = (
    ("0011", "визначити", 3),
    ("0010", "функція", 2),
    ("110", "за-умовою", 7),
    ("0100", "хибне?", 1),
    ("010", "атом?", 8),
    ("101", "тотожне?", 6),
    ("100", "перше", 1),
    ("001", "як-є", 32),
)
RAW_HEADS = re.compile(re.escape("(") + r"(?:001000|0011|0010|0100|010|101|100|110|001)(?=\s)")


def mask_comments_and_strings(source: str) -> str:
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


def inverse_projection(source: str) -> str:
    visible = mask_comments_and_strings(source)
    if RAW_HEADS.search(visible):
        raise AssertionError("old binary D3/D4 call-head remains in source")
    for bits, name, count in PROJECTIONS:
        pattern = re.compile(re.escape("(") + re.escape(name) + r"(?=\s)")
        if len(pattern.findall(source)) != count:
            raise AssertionError(f"unexpected full-ukr count for {name}")
        if len(pattern.findall(visible)) != count:
            raise AssertionError(f"{name} appeared outside executable source")
        source = pattern.sub("(" + bits, source)
    return source


class Core3ProfileUkrProjection(unittest.TestCase):
    def test_all_exact_call_heads_are_full_ukr_and_width_preserving(self):
        source = SOURCE.read_text(encoding="utf-8")
        visible = mask_comments_and_strings(source)
        self.assertIsNone(RAW_HEADS.search(visible))
        for bits, name, count in PROJECTIONS:
            with self.subTest(bits=bits):
                self.assertEqual(source.count("(" + name), count)
                self.assertEqual(visible.count("(" + name), count)
        self.assertNotIn('(завантажити-файл "', visible,
                         "D7 file paths must be quoted symbols before text I/O")
        self.assertEqual(visible.count("(символ-у-текст (як-є lib/"), 4)
        self.assertEqual(visible.count("(нехай "), 1,
                         "D6 LET must use its full ratified Ukrainian surface")

    def test_inverse_preserves_semantic_shape_and_quote_data(self):
        source = SOURCE.read_text(encoding="utf-8")
        restored = inverse_projection(source)
        self.assertIn("(нехай ((вибір-механізму (ядро3-маршрут ідентичність-плюса виконавець)))", restored)
        self.assertNotIn("(001000 ", restored)
        self.assertIn("(001 yes)", restored)


if __name__ == "__main__":
    unittest.main()
