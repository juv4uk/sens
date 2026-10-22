"""Регресійні обмеження живої української SENS-поверхні.

Історичний Git-blob/offset inverse більше не накладається на чинну
реалізацію після змін її AST. Справжній паритет ADD/SUB/MUL з донорськими
формами, фізичними байтами й декодером перевіряється нативними тестами
crates/sens/tests/machine_effect_{add,d5_arithmetic}_projection.rs.
Тут лише статичні заборони для виконуваного українського джерела.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_ROW = re.compile(r"^\s*\(([01]+)\s+\(ук\s+[^()]*\)\s+\(укр\s+([^\s()]+)\)")
OLD_MACHINE_LITERAL = re.compile(r"#(?:d\d+:[01]+|b[01]+)")
RAW_BINARY_CALL = re.compile(r"\(\s*[01]{3,11}(?=\s|\))")


def exact_authority() -> dict[tuple[int, str], str]:
    index = {}
    for d in (1, 3, 4, 5, 6, 8):
        source = (ROOT / "lib" / "domains" / f"d{d}.lisp").read_text(encoding="utf-8")
        for line in source.splitlines():
            row = DOMAIN_ROW.match(line)
            if row is not None and len(row[1]) == d:
                index[(d, row[1])] = row[2]
    return index


def mask_comments_and_strings(source: str) -> str:
    return re.sub(r'"(?:\\.|[^"\\])*"|;[^\n]*',
                  lambda match: " " * len(match[0]), source)


class MachineUkrMigrationTests(unittest.TestCase):
    def test_structural_d8_equal_remains_distinct_from_atomic_d3_eq(self):
        authority = exact_authority()
        self.assertEqual(authority[(8, "11110111")], "однакові?")
        self.assertEqual(authority[(3, "101")], "тотожне?")
        self.assertNotEqual(authority[(8, "11110111")], authority[(3, "101")])
        core4 = (ROOT / "lib/core4.lisp").read_text(encoding="utf-8")
        self.assertIn("(визначити однакові?\n  (функція", core4)
        self.assertIn("(визначити equal? однакові?)", core4)
        self.assertNotIn("(визначити однакові? equal?)", core4)

    def test_native_parity_keeps_exact_fifth_field_and_structural_comparison(self):
        parity = (ROOT / "lib/machine/dispatch/native-first-parity.lisp").read_text(
            encoding="utf-8"
        )
        self.assertIn("(визначити нативний-паритет-пятичленний?", parity)
        self.assertIn("(перше (решта (решта (решта (решта рядок))))))", parity)
        self.assertNotIn("(п'ятий рядок)", parity)
        self.assertIn("(однакові? результат-обчислювача очікуване)", parity)
        self.assertIn("(однакові? результат-машини очікуваний-результат-машини)", parity)
        self.assertNotIn("(визначити native-first-parity-", parity)

    def test_ukrainian_machine_projection_preserves_instructions_and_rejection(self):
        source = (ROOT / "lib/machine/projection/x86-64.lisp").read_text(
            encoding="utf-8"
        )
        self.assertIn("(визначити проєктувати-машинний-ефект-на-х86", source)
        self.assertIn("(визначити закодувати-машинний-ефект-на-х86", source)
        self.assertIn("(визначити проєктувати-двійковий-ефект-на-х86", source)
        self.assertNotIn("(визначити x86-project-machine-effect", source)
        self.assertNotIn("(визначити x86-encode-machine-effect", source)
        self.assertIn("(як-є x86-projection-rejected)", source)
        self.assertIn("(нехай", source)
        self.assertNotRegex(mask_comments_and_strings(source), OLD_MACHINE_LITERAL)
        self.assertNotRegex(mask_comments_and_strings(source), RAW_BINARY_CALL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
