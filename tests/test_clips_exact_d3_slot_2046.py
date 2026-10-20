"""Точковий CLIPS guard: D3 атоми, D8 рядки, 2046 точних D1–D10 адрес.

Source-level certificate complements actual Rust CLIPS importer execution.
No claim that 2046 catalog entries are executable mechanisms.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/clips-import.lisp"
BAD_GUARD = "((хибне? (атом? (перше форми-слотів))) (знайти-значення-слота-кліпс назва-слота (решта форми-слотів)))"
GOOD_GUARD = "((хибне? (атом? (перше (перше форми-слотів)))) (знайти-значення-слота-кліпс назва-слота (решта форми-слотів)))"
SKIP_ATOM = "((атом? (перше форми-слотів))  (знайти-значення-слота-кліпс назва-слота (решта форми-слотів)))"
OLD_EQUAL = "((11110111 назва-слота (перше (перше форми-слотів))) (кліпс-значення-слота (перше форми-слотів)))"
NEW_EQ = "((тотожне? назва-слота (перше (перше форми-слотів))) (кліпс-значення-слота (перше форми-слотів)))"
STRING_EQUAL = '((тотожне? (рядок-перший рядок) ":") (тотожне? (рядок-перший (рядок-решта рядок)) ":"))'


def lookup_body(source):
    start = source.index("(визначити знайти-значення-слота-кліпс")
    end = source.index("(визначити позиційні-аргументи-кліпс", start)
    return source[start:end]


def verify_source(source):
    body = lookup_body(source)
    if BAD_GUARD in body:
        raise AssertionError("небезпечний guard відсікає усі списки слотів")
    if GOOD_GUARD not in body or SKIP_ATOM not in body:
        raise AssertionError("не доведено пропуск пошкоджених записів")
    if body.index(SKIP_ATOM) > body.index(GOOD_GUARD):
        raise AssertionError("атом треба пропустити до виклику вкладеного CAR")
    if OLD_EQUAL in body:
        raise AssertionError("атомарну назву зіставлено через старий D8 EQUAL")
    if NEW_EQ not in body:
        raise AssertionError("точний D3 EQ на символах відсутній")
    if STRING_EQUAL not in source:
        raise AssertionError("канонічне порівняння двокрапок змінено без доказу")
    if source.count(STRING_EQUAL) != 1:
        raise AssertionError("канонічне порівняння двокрапок дубльоване або втрачено")
    if "11110111" in body:
        raise AssertionError("старий D8 EQUAL повернувся у викличну позицію")
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

    def test_reachable_lookup_and_atomic_eq_exact_d3(self):
        body = verify_source(self.source)
        self.assertEqual(body.count(NEW_EQ), 1)
        self.assertNotIn(BAD_GUARD, body)

    def test_current_ukrainian_d3_guard_without_fake_bit_budget(self):
        verify_source(self.source)
        self.assertIn("(атом? (перше форми-слотів))", body)
        self.assertIn("(тотожне? назва-слота", body)
        self.assertNotIn("11110111", body)
        # Довжина написання української проєкції не доводить
        # жодного скорочення фізичного T5M або нового доменного закону.

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

    def test_negative_exhaustive_old_guard_and_w8_return(self):
        verify_source(self.source)
        broken = self.source.replace(GOOD_GUARD, BAD_GUARD, 1)
        with self.assertRaisesRegex(AssertionError, "небезпечний guard"):
            verify_source(broken)
        broken = self.source.replace(NEW_EQ, OLD_EQUAL, 1)
        with self.assertRaisesRegex(AssertionError, "старий D8"):
            verify_source(broken)

    def test_negative_do_not_alias_string_equal_to_atomic_eq(self):
        verify_source(self.source)
        broken = self.source.replace(STRING_EQUAL, STRING_EQUAL.replace(
            '":"', '";"', 1), 1)
        with self.assertRaisesRegex(AssertionError, "порівняння двокрапок"):
            verify_source(broken)

    def test_negative_malformed_slot_guard_order(self):
        verify_source(self.source)
        start = self.source.index(SKIP_ATOM) + len(SKIP_ATOM)
        end = self.source.index(GOOD_GUARD, start)
        whitespace = self.source[start:end]
        broken = self.source.replace(
            SKIP_ATOM + whitespace + GOOD_GUARD,
            GOOD_GUARD + whitespace + SKIP_ATOM, 1,
        )
        self.assertNotEqual(broken, self.source)
        with self.assertRaisesRegex(AssertionError, "вкладеного CAR"):
            verify_source(broken)

    def test_negative_loss_of_malformed_atom_guard(self):
        verify_source(self.source)
        broken = self.source.replace(SKIP_ATOM, "", 1)
        with self.assertRaisesRegex(AssertionError, "пошкоджених"):
            verify_source(broken)


if __name__ == "__main__":
    unittest.main()
