"""Точковий свідок Core1: бітність, дубль і відмова від змішування доменів.

Це перевірка вихідного коду, НЕ доказ паритету C1-EVAL або фізичного T5.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
START = "(0011 C1-ADMITTED-SID-VALUEP"
END = "(0011 C1-PRIMITIVE-IDENTITY"
ENTRY = re.compile(r"\(\(101 VALUE ([01]+)\) T\)")
EXPECTED = {
    3: {"001", "010", "011", "100", "101", "110", "111"},
    4: {"0010", "0011", "0100", "1110"},
    5: {"01010", "01011"},
}
DOMAIN_COUNTS = {1: 2, 2: 4, 3: 8, 4: 16, 5: 32,
                 6: 64, 7: 126, 8: 256, 9: 512, 10: 1024}
D7_RESERVED = {"0100001", "0101010"}


def core1_admission_source():
    source = (ROOT / "lib/core1.lisp").read_text(encoding="utf-8")
    if source.count(START) != 1 or source.count(END) != 1:
        raise AssertionError("Не знайдено одну чинну секцію Core1")
    return source.split(START, 1)[1].split(END, 1)[0]


def admitted_words(section):
    return ENTRY.findall(section)


def valid_admission(section):
    words = admitted_words(section)
    if len(words) != len(set(words)):
        return False
    grouped = {}
    for word in words:
        grouped.setdefault(len(word), set()).add(word)
    return grouped == EXPECTED


def domain_words(width):
    source = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
    return re.findall(r"(?m)^  \(([01]+)\s", source)


class Core1ExactDomainAdmission(unittest.TestCase):
    def test_approved_words_and_distinct_widths(self):
        section = core1_admission_source()
        self.assertTrue(valid_admission(section))
        self.assertNotIn("0", admitted_words(section))  # D1:NO != D3
        self.assertNotIn("000", admitted_words(section))  # D3:EMPTY != call
        self.assertEqual(sum(map(len, admitted_words(section))), 47)

    def test_admitted_words_exist_at_their_exact_width(self):
        for width, expected in EXPECTED.items():
            with self.subTest(domain=width):
                self.assertLessEqual(expected, set(domain_words(width)))

    def test_all_ratified_table_coordinate_widths(self):
        for width, count in DOMAIN_COUNTS.items():
            with self.subTest(domain=width):
                words = domain_words(width)
                self.assertEqual(len(words), count)
                self.assertEqual(len(set(words)), count)
                self.assertTrue(all(len(word) == width for word in words))
                self.assertEqual(words, sorted(words))
                if width != 7:
                    self.assertEqual(
                        words, [format(i, f"0{width}b") for i in range(count)]
                    )
                else:
                    all_words = {format(i, "07b") for i in range(128)}
                    self.assertEqual(all_words - set(words), D7_RESERVED)

    def test_negative_duplicate_d4_coordinate(self):
        section = core1_admission_source()
        modified = section.replace(
            "((101 VALUE 0011) T)",
            "((101 VALUE 0011) T)\n      ((101 VALUE 0011) T)",
            1,
        )
        self.assertNotEqual(modified, section)
        self.assertFalse(valid_admission(modified))

    def test_negative_truncated_d5_becomes_d4(self):
        section = core1_admission_source()
        modified = section.replace(
            "((101 VALUE 01010) T)", "((101 VALUE 1010) T)", 1
        )
        self.assertNotEqual(modified, section)
        self.assertFalse(valid_admission(modified))

    def test_negative_legacy_w8_collision(self):
        section = core1_admission_source()
        modified = section.replace(
            "((101 VALUE 0011) T)",
            "((101 VALUE 0011) T)\n      ((101 VALUE 11011011) T)",
            1,
        )
        self.assertNotEqual(modified, section)
        self.assertFalse(valid_admission(modified))
        self.assertIn("11011011", domain_words(8))


if __name__ == "__main__":
    unittest.main()
