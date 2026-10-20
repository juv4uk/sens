"""Статичні інваріанти українського CLIPS-читача й точних адрес D1–D10.

Це не виконавець SENS: поведінку засвідчують SENS/Rust integration tests.
Історичні W8-опкоди та латинські псевдоніми не є чинним джерелом істини.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/clips-import.lisp"
SKIP_ATOM = "((атом? (перше форми-слотів))"
CHECK_ATOMIC_NAME = "((хибне? (атом? (перше (перше форми-слотів))))"
EQ_ATOMS = "((тотожне? назва-слота (перше (перше форми-слотів)))"
BAD_GUARD = "((хибне? (атом? (перше форми-слотів)))"
BAD_EQUAL = "((рівне? назва-слота (перше (перше форми-слотів)))"


def lookup_body(source):
    start = source.index("(визначити знайти-значення-слота-кліпс")
    end = source.index("(визначити позиційні-аргументи-кліпс", start)
    return source[start:end]


def verify_source(source):
    body = lookup_body(source)
    if BAD_GUARD in body:
        raise AssertionError("старий guard відсікає коректні списки слотів")
    if SKIP_ATOM not in body or CHECK_ATOMIC_NAME not in body:
        raise AssertionError("пропуск пошкодженого слота не доведено")
    if EQ_ATOMS not in body or BAD_EQUAL in body:
        raise AssertionError("тотожність атомарних назв має використовувати D3 EQ")
    if not (body.index(SKIP_ATOM) < body.index(CHECK_ATOMIC_NAME) < body.index(EQ_ATOMS)):
        raise AssertionError("небезпечний порядок перевірок вкладених пар")
    if "(визначити clips-" in source:
        raise AssertionError("латинську викличну поверхню CLIPS повернуто")
    return body


def domain_keys(root=ROOT):
    cells = []
    for width in range(1, 11):
        data = (root / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
        bits = re.findall(r"(?m)^  \(([01]+)\s", data)
        cells.extend((width, value) for value in bits)
    return cells


def validate_all_cells(cells):
    # Domain identity = (width, payload), never just int(payload, 2).
    if len(cells) != 2046:
        raise AssertionError("неповний реєстр D1–D10")
    if len(set(cells)) != 2046:
        raise AssertionError("колізія доменної координати")
    offset = 0
    for width in range(1, 11):
        values = cells[offset:offset + (1 << width)]
        expected = [(width, f"{number:0{width}b}") for number in range(1 << width)]
        if values != expected:
            raise AssertionError(f"D{width}: порядок, кількість або бітність")
        offset += 1 << width
    return cells


class ClipsSlotD3Exact2046(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_ukrainian_lookup_safe_structure(self):
        body = verify_source(self.source)
        self.assertEqual(body.count(EQ_ATOMS), 1)
        self.assertEqual(body.count(SKIP_ATOM), 1)
        self.assertNotIn("((11110111 ", body)

    def test_no_english_define_aliases(self):
        self.assertNotRegex(self.source, r"(?m)^\(визначити clips[-а-я]")
        self.assertIn("(визначити кліпс-імпорт", self.source)
        self.assertIn("(визначити кліпс-імпорт-файл", self.source)

    def test_exhaustive_2046_exact_width_domain_addresses(self):
        cells = validate_all_cells(domain_keys())
        self.assertEqual(len(set(cells)), 2046)
        self.assertEqual(len({int(bits, 2) for _, bits in cells}), 1024)
        self.assertEqual([sum(w == i for w, _ in cells) for i in range(1, 11)],
                         [1 << i for i in range(1, 11)])

    def test_all_2046_functions_have_six_ordered_projections(self):
        # Test actual catalog *records*, not only numeric keys:
        # Ukrainian short, Ukrainian full, Sanskrit, English, LISP, symbols.
        labels = ["(ук ", "(укр ", "(san ", "(en ", "(LISP ", "(sym "]
        total = 0
        for width in range(1, 11):
            data = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
            rows = re.findall(r"(?m)^  \(([01]+) (.*)$", data)
            self.assertEqual(len(rows), 1 << width)
            for bits, rest in rows:
                with self.subTest(domain=f"D{width}", code=bits):
                    positions = [rest.find(label) for label in labels]
                    self.assertTrue(all(p >= 0 for p in positions))
                    self.assertEqual(positions, sorted(positions))
                    total += 1
        self.assertEqual(total, 2046)

    def test_negative_w10_truncated_to_w9(self):
        cells = validate_all_cells(domain_keys())
        modified = list(cells)
        pos = modified.index((10, "1111111111"))
        modified[pos] = (9, "111111111")
        with self.assertRaisesRegex(AssertionError, "колізія"):
            validate_all_cells(modified)

    def test_negative_duplicate_w7_key_and_swapped_order(self):
        cells = validate_all_cells(domain_keys())
        modified = list(cells)
        pos = modified.index((7, "0000001"))
        modified[pos] = (7, "0000010")
        with self.assertRaisesRegex(AssertionError, "колізія"):
            validate_all_cells(modified)
        modified = list(cells)
        i, j = modified.index((10, "0000000001")), modified.index((10, "0000000010"))
        modified[i], modified[j] = modified[j], modified[i]
        with self.assertRaisesRegex(AssertionError, "D10"):
            validate_all_cells(modified)

    def test_negative_old_guard_does_not_return(self):
        verify_source(self.source)
        broken = self.source.replace(SKIP_ATOM, BAD_GUARD, 1)
        with self.assertRaisesRegex(AssertionError, "старий guard"):
            verify_source(broken)

    def test_negative_name_compared_by_non_d3_equality(self):
        verify_source(self.source)
        broken = self.source.replace(EQ_ATOMS, BAD_EQUAL, 1)
        with self.assertRaisesRegex(AssertionError, "D3 EQ"):
            verify_source(broken)

    def test_negative_missing_malformed_name_guard(self):
        verify_source(self.source)
        broken = self.source.replace(CHECK_ATOMIC_NAME, "", 1)
        with self.assertRaisesRegex(AssertionError, "пошкодженого слота"):
            verify_source(broken)

    def test_negative_reordered_malformed_guards(self):
        verify_source(self.source)
        body = lookup_body(self.source)
        mutated = body.replace(SKIP_ATOM, "@SWAP@", 1).replace(CHECK_ATOMIC_NAME, SKIP_ATOM, 1).replace("@SWAP@", CHECK_ATOMIC_NAME, 1)
        broken = self.source.replace(body, mutated, 1)
        with self.assertRaisesRegex(AssertionError, "порядок"):
            verify_source(broken)


if __name__ == "__main__":
    unittest.main()
