"""Докази точної D4→укр міграції lib/mechanism-selector.lisp.

Не виконує SENS за допомогою Python: лише перевіряє source, доменні
authority-поля та byte-exact зворотність 14 проєкцій. Фізичне виконання
належить SENS / Zig і перевіряється окремо.
"""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/mechanism-selector.lisp"
D4 = ROOT / "lib/domains/d4.lisp"
D5 = ROOT / "lib/domains/d5.lisp"
# Git blob оригіналу перед переходом на укр: НЕ semantic або wire identity.
ORIGINAL_SOURCE_BLOB = "6a766d43132d44151803c1f473fdc4d7da26457f"
REPLACEMENTS = (
    ("0011", "визначити", "define", "DEFINE", 12),
    ("0010", "функція", "lambda", "LAMBDA", 6),
)
LOCAL_RENAMES = (
    ("mechanism-selector-find-section", "механізм-знайти-секцію"),
    ("mechanism-selector-registry-has-sid?", "реєстр-містить-ідентичність?"),
    ("mechanism-selector-find-route", "механізм-знайти-маршрут"),
    ("mechanism-select", "вибрати-механізм"),
)
COMPATIBILITY_ALIAS_BLOCK = "\n\n; Сумісні англомовні назви залишаються псевдонімами тих самих Lisp-значень.\n(визначити mechanism-selector-find-section механізм-знайти-секцію)\n(визначити mechanism-selector-registry-has-sid? реєстр-містить-ідентичність?)\n(визначити mechanism-selector-find-route механізм-знайти-маршрут)\n(визначити mechanism-select вибрати-механізм)\n"


def restore_local_helper_names(source: str) -> str:
    if not source.endswith(COMPATIBILITY_ALIAS_BLOCK):
        raise AssertionError("compatibility aliases drifted or are missing")
    source = source[:-len(COMPATIBILITY_ALIAS_BLOCK)]
    for english, ukrainian in LOCAL_RENAMES:
        source = source.replace(ukrainian, english)
    return source


def restore_previous_projection(source: str) -> str:
    source = restore_local_helper_names(source)
    for bits, ukr, _en, _lisp, _count in REPLACEMENTS:
        source = source.replace(f"({ukr} ", f"({bits} ")
    source = source.replace("(третє route)", "(10011 route)")
    return source



def git_blob(source: bytes) -> str:
    header = f"blob {len(source)}\0".encode("ascii")
    return hashlib.sha1(header + source).hexdigest()


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
        self.assertEqual(code.count("(третє route)"), 1)
        self.assertNotIn("(10011 route)", code)

    def test_d5_caddr_ukr_projection_is_ratified_and_one_head_only(self):
        code = uncommented(self.source)
        self.assertEqual(code.count("(третє route)"), 1)
        self.assertNotIn("(10011 route)", code)
        rows = [row for row in self.table_d5.splitlines()
                if row.startswith("  (10011 ")]
        self.assertEqual(len(rows), 1)
        self.assertIn("(укр третє)", rows[0])
        self.assertIn("(en caddr)", rows[0])
        self.assertIn("(LISP CADDR)", rows[0])

    def test_local_helper_names_are_ukrainian_active_heads_and_english_value_aliases(self):
        code = uncommented(self.source)
        for english, ukrainian in LOCAL_RENAMES:
            with self.subTest(helper=english):
                self.assertRegex(code, rf"\(визначити\s+{re.escape(ukrainian)}(?=\s)")
                self.assertIn(f"(визначити {english} {ukrainian})", self.source)
                self.assertNotRegex(code, rf"\({re.escape(english)}(?=\s)")
        self.assertEqual(len(re.findall(r"\(визначити\s+вибрати-механізм(?=\s)", self.source)), 1)

    def test_original_source_recoverable_byte_for_byte(self):
        reverted = restore_previous_projection(self.source)
        self.assertEqual(git_blob(reverted.encode("utf-8")), ORIGINAL_SOURCE_BLOB,
                         "змінено дані, коментарі, структуру або нецільові голови")

    def test_wrong_d5_peer_fails_historical_source_inverse(self):
        wrong = self.source.replace("(третє route)", "(друге route)", 1)
        self.assertNotEqual(wrong, self.source)
        inverse = restore_previous_projection(wrong)
        self.assertNotEqual(git_blob(inverse.encode("utf-8")),
                            ORIGINAL_SOURCE_BLOB)

    def test_registry_and_symbolic_sid_values_still_present(self):
        self.assertIn('"lib/surface/semantic-registry.lisp"', self.source)
        self.assertIn('"lib/function-table-mechanisms.lisp"', self.source)
        for token in ("(як-є rows)", "(як-є no)", "(як-є yes)",
                      "(як-є mechanism-selected)", "(як-є sid-not-in-function-table)"):
            self.assertIn(token, self.source)
        for name in ("mechanism-selector-find-section",
                     "mechanism-selector-registry-has-sid?",
                     "mechanism-selector-find-route",
                     "mechanism-select"):
            self.assertIn(f"(визначити {name}", self.source)

    def test_malformed_mutation_is_detected_instead_of_masked(self):
        reverted = restore_previous_projection(self.source)
        tampered = reverted.replace("(як-є rows)", "(як-є other-rows)", 1)
        self.assertNotEqual(git_blob(tampered.encode("utf-8")),
                            ORIGINAL_SOURCE_BLOB)

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
