"""Точковий CLIPS guard: D3 атоми, D8 рядки, 2046 точних D1–D10 адрес.

Source-level certificate complements actual Rust CLIPS importer execution.
No claim that 2046 catalog entries are executable mechanisms.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/clips-import.lisp"
BAD_GUARD = "((0100 (010 (100 slot-forms))) (clips-lookup-slot-value slot-name (011 slot-forms)))"
GOOD_GUARD = "((0100 (010 (100 (100 slot-forms)))) (clips-lookup-slot-value slot-name (011 slot-forms)))"
SKIP_ATOM = "((010 (100 slot-forms))  (clips-lookup-slot-value slot-name (011 slot-forms)))"
OLD_EQUAL = "((11110111 slot-name (100 (100 slot-forms))) (clips-slot-value-of (100 slot-forms)))"
NEW_EQ = "((101 slot-name (100 (100 slot-forms))) (clips-slot-value-of (100 slot-forms)))"
STRING_EQUAL = '(11110111 (110101011 (11101110 symbol)) (110101011 "?_"))'


def lookup_body(source):
    start = source.index("(0011 clips-lookup-slot-value")
    end = source.index("(0011 clips-positional-args", start)
    return source[start:end]


def verify_source(source):
    body = lookup_body(source)
    if BAD_GUARD in body:
        raise AssertionError("небезпечний guard відсікає усі списки слотів")
    if GOOD_GUARD not in body or SKIP_ATOM not in body:
        raise AssertionError("не доведено пропуск пошкоджених записів")
    if OLD_EQUAL in body:
        raise AssertionError("атомарну назву зіставлено через старий D8 EQUAL")
    if NEW_EQ not in body:
        raise AssertionError("точний D3 EQ на символах відсутній")
    if STRING_EQUAL not in source:
        raise AssertionError("рядковий D8 EQUAL змінили без доказу")
    if source.count("(11110111 ") != 1:
        raise AssertionError("кількість рядкових D8 EQUAL має лишитися один")
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

    def test_ophead_budget_only_not_fake_physical_compression(self):
        verify_source(self.source)
        self.assertEqual(len("100"), 3)      # Added CAR (D3)
        self.assertEqual(len("11110111"), 8) # Removed one D8 EQUAL
        self.assertEqual(len("101"), 3)      # Added D3 EQ
        self.assertEqual(3 + 3 - 8, -2)       # Net call-head bits

    def test_exhaustive_2046_exact_width_domain_addresses(self):
        cells = validate_all_cells(domain_keys())
        self.assertEqual(len(set(cells)), 2046)
        self.assertEqual(len({int(bits, 2) for _, bits in cells}), 1024)
        self.assertEqual([sum(w == i for w, _ in cells) for i in range(1, 11)],
                         [1 << i for i in range(1, 11)])

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
            "11110111", "101", 1), 1)
        with self.assertRaisesRegex(AssertionError, "рядковий D8"):
            verify_source(broken)

    def test_negative_loss_of_malformed_atom_guard(self):
        verify_source(self.source)
        broken = self.source.replace(SKIP_ATOM, "", 1)
        with self.assertRaisesRegex(AssertionError, "пошкоджених"):
            verify_source(broken)


if __name__ == "__main__":
    unittest.main()
