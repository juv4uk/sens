"""D1-D10 are machine words; only explicit D12+ math can display decimal."""
import pathlib
import importlib.util
import subprocess
import sys
import tempfile
from unittest.mock import patch
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from domain_tables import (  # noqa: E402
    human_number, is_number_width, machine_word, number_domains, number_word,
)

DOMAIN_GATE_SPEC = importlib.util.spec_from_file_location(
    "check_domain_tables", ROOT / "scripts/check-domain-tables.py"
)
assert DOMAIN_GATE_SPEC and DOMAIN_GATE_SPEC.loader
DOMAIN_GATE = importlib.util.module_from_spec(DOMAIN_GATE_SPEC)
DOMAIN_GATE_SPEC.loader.exec_module(DOMAIN_GATE)


class BinaryProjection(unittest.TestCase):
    def test_machine_word_is_binary_of_exact_width(self):
        self.assertEqual(machine_word(5, 3), "101")
        self.assertEqual(machine_word(0, 4), "0000")
        self.assertEqual(machine_word(255, 8), "11111111")

    def test_only_qualified_d12_plus_can_display_decimal(self):
        for width in (12, 24, 48, 96, 192):
            for number in (0, 1, 2, 7, 31, 127, 255):
                bits = number_word(number, width)
                self.assertEqual(human_number(bits, domain_width=width), number)

    def test_signed_d12_boundaries_use_twos_complement(self):
        self.assertEqual(number_word(-1, 12), "1" * 12)
        self.assertEqual(human_number("1" * 12, domain_width=12), -1)
        self.assertEqual(human_number(number_word(-2048, 12), domain_width=12), -2048)
        self.assertEqual(human_number(number_word(2047, 12), domain_width=12), 2047)
        with self.assertRaises(ValueError):
            number_word(2048, 12)
        with self.assertRaises(ValueError):
            number_word(-2049, 12)

    def test_signed_d24_boundaries_use_twos_complement(self):
        self.assertEqual(number_word(-1, 24), "1" * 24)
        self.assertEqual(human_number("1" * 24, domain_width=24), -1)
        minimum = -(1 << 23)
        maximum = (1 << 23) - 1
        self.assertEqual(human_number(number_word(minimum, 24), domain_width=24), minimum)
        self.assertEqual(human_number(number_word(maximum, 24), domain_width=24), maximum)
        with self.assertRaises(ValueError):
            number_word(1 << 23, 24)
        with self.assertRaises(ValueError):
            number_word(-(1 << 23) - 1, 24)

    def test_d1_d10_are_not_decimal_operands(self):
        for width, bits in ((1, "1"), (2, "01"), (3, "101"),
                            (7, "0110001"), (8, "10101000"),
                            (9, "100000001"), (10, "1000000001")):
            with self.assertRaises(ValueError):
                human_number(bits, domain_width=width)
        with self.assertRaises(TypeError):
            human_number("0" * 23 + "1")

    def test_d24_d48_have_distinct_exact_width(self):
        self.assertEqual(human_number(number_word(5, 24), domain_width=24), 5)
        self.assertEqual(human_number(number_word(5, 48), domain_width=48), 5)
        with self.assertRaises(ValueError):
            human_number(number_word(5, 24), domain_width=48)

    def test_machine_word_fails_closed(self):
        for number, width in ((-1, 4), (8, 3), (256, 8)):
            with self.assertRaises(ValueError):
                machine_word(number, width)

    def test_human_number_rejects_non_binary(self):
        for word in ("", "012", "10a", "0b1", "101"):
            with self.assertRaises(ValueError):
                human_number(word, domain_width=24)
        for width in (1, 7, 10, 25):
            with self.assertRaises(ValueError):
                human_number("0" * 24, domain_width=width)


class NumericDomains(unittest.TestCase):
    def test_numbers_live_in_the_owner_ratified_ladder(self):
        self.assertEqual(
            number_domains(),
            (("D12", 12), ("D24", 24), ("D48", 48), ("D96", 96), ("D192", 192)),
        )

    def test_duplicate_numeric_first_domain_is_rejected(self):
        source = (ROOT / "contracts/numeric-domains-ratification.lisp").read_text(encoding="utf-8")
        field = "(first-domain . D12)"
        self.assertEqual(source.count(field), 1)

        class MutantContract:
            def __init__(self, content):
                self.content = content

            def read_text(self, encoding="utf-8"):
                return self.content

        for duplicate in ("D12", "D13"):
            with self.subTest(duplicate=duplicate):
                mutated = source.replace(
                    field, field + "\n  (first-domain . " + duplicate + ")", 1
                )
                with self.assertRaisesRegex(ValueError, "first-domain"):
                    number_domains(MutantContract(mutated))

    def test_only_the_d12_ladder_widths_are_numeric(self):
        for width in (12, 24, 48, 96, 192, 384):
            self.assertTrue(is_number_width(width))
        for width in (1, 7, 10, 13, 23, 25, 100):
            self.assertFalse(is_number_width(width))

    def test_number_word_requires_an_explicit_numeric_domain(self):
        self.assertEqual(number_word(5, 24), "0" * 21 + "101")
        with self.assertRaises(ValueError):
            number_word(5, 7)

    def test_domain_table_gate_uses_current_d7_rows_not_the_archived_keyboard_map(self):
        rows = DOMAIN_GATE.validate_d7()
        self.assertEqual(len(rows), 128)
        # D7 v2 is a keyboard/data domain, not the retired Devanagari
        # syllabary: control W7:0000000 has no printable projection.
        self.assertEqual(
            (rows[0].bits, rows[0].ukr, rows[0].san, rows[0].en, rows[0].lisp),
            ("0000000", None, None, None, None),
        )
        # Printable cells use current IAST/ASCII keyboard positions.
        self.assertEqual(
            (rows[65].bits, rows[65].ukr, rows[65].san, rows[65].en, rows[65].lisp),
            ("1000001", "Ф", "o", "A", None),
        )
        self.assertEqual(
            [row.bits for row in rows],
            [f"{number:07b}" for number in range(128)],
        )
        self.assertTrue(all(row.lisp is None for row in rows))

    def test_current_d7_gate_rejects_retired_keyboard_glyph_and_preserves_real_source(self):
        # Mutate only a temporary human-view table. A historical v1 glyph
        # must not replace owner-ratified v2 at W7:0000000.
        original = (ROOT / "lib/domains/d7.lisp").read_text(encoding="utf-8")
        old = "(0000000 (ук ()) (укр ()) (san ()) (en ())"
        retired = "(0000000 (ук ()) (укр ()) (san क) (en k)"
        self.assertEqual(original.count(old), 1)
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "d7.lisp"
            path.write_text(original.replace(old, retired, 1), encoding="utf-8")
            with patch.object(DOMAIN_GATE, "D7_TABLE", path):
                with self.assertRaisesRegex(SystemExit, "D7:0000000.*glyph"):
                    DOMAIN_GATE.validate_d7()
        # Normal authority remains usable after the negative fixture.
        self.assertEqual(len(DOMAIN_GATE.validate_d7()), 128)

    def test_full_domain_gate_accepts_current_ukrainian_selector_names(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check-domain-tables.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("DOMAIN-TABLES: PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
