"""Докази точної D4→укр міграції lib/mechanism-selector.lisp.

Не виконує SENS за допомогою Python: лише перевіряє source, доменні
authority-поля та byte-exact зворотність 14 проєкцій. Фізичне виконання
належить SENS / Zig і перевіряється окремо.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/mechanism-selector.lisp"
D4 = ROOT / "lib/domains/d4.lisp"
D5 = ROOT / "lib/domains/d5.lisp"
REPLACEMENTS = (
    ("0011", "визначити", "define", "DEFINE", 8),
    ("0010", "функція", "lambda", "LAMBDA", 6),
)
LOCAL_RENAMES = (
    ("mechanism-selector-find-section", "механізм-знайти-секцію"),
    ("mechanism-selector-registry-has-sid?", "реєстр-містить-ідентичність?"),
    ("mechanism-selector-find-route", "механізм-знайти-маршрут"),
    ("mechanism-select", "вибрати-механізм"),
)
def uncommented(source: str) -> str:
    """Прибирає коментарі й рядкові payload без трактування їх як кодів."""
    lines = []
    for line in source.splitlines():
        result, quoted, escaped = [], False, False
        for ch in line:
            if quoted:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    quoted = False
                result.append(" ")
            elif ch == ";":
                break
            elif ch == '"':
                quoted = True
                result.append(" ")
            else:
                result.append(ch)
        lines.append("".join(result))
    return "\n".join(lines)


class MechanismSelectorFullUkrProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.table = D4.read_text(encoding="utf-8")
        cls.table_d5 = D5.read_text(encoding="utf-8")

    def test_ratified_peer_spellings_with_domain_width_and_identity(self):
        for bits, ukr, en, lisp, _count in REPLACEMENTS:
            matches = [
                row.strip() for row in self.table.splitlines()
                if row.lstrip().startswith(f"({bits} ")
            ]
            self.assertEqual(len(matches), 1, f"D4:{bits}: exact one row")
            row = matches[0]
            self.assertIn(f"(укр {ukr})", row)
            self.assertIn(f"(en {en})", row)
            self.assertIn(f"(LISP {lisp})", row)

    def test_active_forms_use_only_full_ukr_d4_heads(self):
        code = uncommented(self.source)
        for bits, ukr, _en, _lisp, count in REPLACEMENTS:
            self.assertEqual(code.count(f"({ukr} "), count)
            self.assertNotRegex(code, rf"\({bits}(?=\s)")
        self.assertEqual(code.count("(третє маршрут)"), 1)
        self.assertNotIn("(10011 маршрут)", code)

    def test_d5_caddr_ukr_projection_is_ratified_and_one_head_only(self):
        code = uncommented(self.source)
        self.assertEqual(code.count("(третє маршрут)"), 1)
        self.assertNotIn("(10011 маршрут)", code)
        rows = [row for row in self.table_d5.splitlines()
                if row.startswith("  (10011 ")]
        self.assertEqual(len(rows), 1)
        self.assertIn("(укр третє)", rows[0])
        self.assertIn("(en caddr)", rows[0])
        self.assertIn("(LISP CADDR)", rows[0])

    def test_local_helper_names_are_only_ukrainian(self):
        code = uncommented(self.source)
        for english, ukrainian in LOCAL_RENAMES:
            with self.subTest(helper=english):
                self.assertRegex(code, rf"\(визначити\s+{re.escape(ukrainian)}(?=\s)")
                self.assertNotRegex(code, rf"\(визначити\s+{re.escape(english)}(?=\s)")
                self.assertNotRegex(code, rf"\({re.escape(english)}(?=\s)")
        self.assertEqual(len(re.findall(r"\(визначити\s+вибрати-механізм(?=\s)", self.source)), 1)

    def test_formal_parameters_have_ukrainian_spelling(self):
        code = uncommented(self.source)
        for signature in (
            "(функція (назва секції)",
            "(функція (ідентичність рядки)",
            "(функція (ідентичність виконавець рядки)",
            "(функція (рядок)",
            "(функція (маршрут)",
            "(функція (ідентичність виконавець)",
        ):
            self.assertIn(signature, code)
        self.assertIn("(як-є rows)", code)
        self.assertIn("(третє маршрут)", code)
        self.assertNotIn("(третє route)", code)

    def test_registry_and_symbolic_sid_values_still_present(self):
        self.assertIn('"lib/surface/semantic-registry.lisp"', self.source)
        self.assertIn('"lib/function-table-mechanisms.lisp"', self.source)
        for token in ("(як-є rows)",
                      "(як-є mechanism-selected)", "(як-є sid-not-in-function-table)"):
            self.assertIn(token, self.source)
        for legacy, current in LOCAL_RENAMES:
            self.assertIn(f"(визначити {current}", self.source)
            self.assertNotIn(f"(визначити {legacy} ", self.source)
        for legacy in ("mechanism-selector-registry", "mechanism-selector-metadata",
                       "mechanism-selector-registry-rows", "mechanism-selector-routes"):
            self.assertNotIn(f"(визначити {legacy} ", self.source)

    def test_exact_d1_registry_predicate_not_old_textual_boolean(self):
        code = uncommented(self.source)
        true_d1 = "(атом? (як-є ()))"
        false_d1 = "(атом? (як-є (())))"
        self.assertIn("((атом? рядки) " + false_d1 + ")", code)
        self.assertIn(
            "((тотожне? ідентичність (перше (перше рядки))) "
            + true_d1 + ")", code,
        )
        self.assertNotRegex(code, r"(?<![\w-])(?:так|ні)(?![\w-])")
        self.assertNotIn("(як-є yes)", code)
        self.assertNotIn("(як-є no)", code)
        self.assertRegex(
            code,
            r"\(реєстр-містить-ідентичність\?\s+"
            r"ідентичність\s+рядки-реєстру-механізму\)\s+"
            + re.escape(false_d1) + r"\)",
        )

    def test_only_balanced_source_parentheses_outside_strings_and_comments(self):
        code = uncommented(self.source)
        balance = 0
        for ch in code:
            if ch == "(":
                balance += 1
            elif ch == ")":
                balance -= 1
                self.assertGreaterEqual(balance, 0, "несподівана закривальна дужка")
        self.assertEqual(balance, 0, "незавершена SENS форма")


if __name__ == "__main__":
    unittest.main(verbosity=2)
