"""Перевірка колонок проєкцій D1–D11 у таблицях .lisp-файлів."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
D7_ESCAPE = re.compile(r"\\x([0-9a-fA-F]{2})\Z")
TOKEN = r'(\(\)|"(?:\\.|[^"\\])*"|[^()\s]+)'
DOMAIN_ROW = re.compile(
    r'^\s*\(([01]{1,11})\s+'
    + rf'\(ук\s+{TOKEN}\)\s+'
    + rf'\(укр\s+{TOKEN}\)\s+'
    + rf'\(san\s+{TOKEN}\)\s+'
    + rf'\(en\s+{TOKEN}\)\s+'
    + rf'\(LISP\s+{TOKEN}\)\s+'
    + rf'\(sym\s+{TOKEN}\)\)\s*$'
)

# Видимі виходи Microsoft Ukrainian (Enhanced), включно з AltGr.
# Джерело: https://learn.microsoft.com/en-us/globalization/keyboards/kbdur1
UKRAINIAN_KEYBOARD_OUTPUTS = set(
    "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
    "0123456789"
    "'\\-=./!\"№;%:?*()_+,₴ "
)


def read_selected_projection_tokens() -> list[tuple[str, int, str, str, str]]:
    """Зчитати значення проєкцій ук, укр і sym із таблиць D1–D11."""
    rows: list[tuple[str, int, str, str, str]] = []
    for width in range(1, 12):
        path = ROOT / "lib" / "domains" / f"d{width}.lisp"
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = DOMAIN_ROW.match(line)
            if match:
                bits, uk, ukr, _san, _en, _lisp, sym = match.groups()
                rows.append((f"D{width}:{bits}", line_number, uk, ukr, sym))
    return rows


def projection_value(token: str, domain: str) -> str:
    """Розгорнути Lisp-рядок і D7-нотацію керівного символу."""
    if token == "()":
        return ""
    if token.startswith('"'):
        json_safe = "".join(
            f"\\u{ord(char):04x}" if ord(char) < 0x20 else char for char in token
        )
        value = json.loads(json_safe)
    else:
        value = token
    if domain == "D7":
        escaped = D7_ESCAPE.fullmatch(value)
        if escaped:
            return chr(int(escaped.group(1), 16))
    return value


def format_projection_violation(
    path: str,
    coordinate: str,
    line_number: int,
    projection: str,
    token: str,
    value: str,
) -> str:
    """Показати точну клітинку таблиці та кожний видимий недозволений символ."""
    disallowed = sorted(
        {char for char in value if char.isprintable()} - UKRAINIAN_KEYBOARD_OUTPUTS,
        key=ord,
    )
    rendered = ", ".join(f"U+{ord(char):04X} {char!r}" for char in disallowed)
    return (
        f"{path}:{line_number}: {coordinate} projection={projection}; "
        f"token={token!r}; value={value!r}; поза розкладкою: {rendered}; "
        "виправ лише цю клітинку проєкції, не ключ та не інші колонки"
    )


def collect_projection_violations(
    rows: list[tuple[str, int, str, str, str]],
) -> list[str]:
    """Повернути всі порушення, не обрізаючи список до кількох прикладів."""
    findings: list[str] = []
    for coordinate, line_number, uk, ukr, sym in rows:
        domain = coordinate.split(":", 1)[0]
        path = f"lib/domains/d{int(domain[1:])}.lisp"
        for projection, token in (("ук", uk), ("укр", ukr), ("sym", sym)):
            value = projection_value(token, domain)
            disallowed = {
                char
                for char in value
                if char.isprintable() and char not in UKRAINIAN_KEYBOARD_OUTPUTS
            }
            if disallowed:
                findings.append(
                    format_projection_violation(
                        path, coordinate, line_number, projection, token, value
                    )
                )
    return findings


class UkrainianDomainProjectionRulesTests(unittest.TestCase):
    def test_diagnostic_names_exact_cell_and_each_forbidden_character(self):
        finding = format_projection_violation(
            "lib/domains/d5.lisp",
            "D5:11010",
            35,
            "sym",
            '"x<"',
            "x<",
        )

        self.assertIn("lib/domains/d5.lisp:35", finding)
        self.assertIn("D5:11010", finding)
        self.assertIn("projection=sym", finding)
        self.assertIn('token=\'"x<"\'', finding)
        self.assertIn("U+003C '<'", finding)
        self.assertIn("U+0078 'x'", finding)
        self.assertIn("виправ лише цю клітинку проєкції", finding)

    def test_diagnostic_lists_every_invalid_projection_cell(self):
        rows = [
            (f"D5:{key:05b}", key, "x", "x", "x")
            for key in range(1, 8)
        ]

        findings = collect_projection_violations(rows)

        self.assertEqual(len(findings), 21)
        self.assertIn("D5:00001", findings[0])
        self.assertIn("D5:00111", findings[-1])

    def test_d1_through_d11_uk_ukr_and_sym_use_only_ukrainian_keyboard_characters(self):
        rows = read_selected_projection_tokens()
        self.assertTrue(rows, "не знайдено проєкцій ук, укр і sym у D1–D11")

        found_domains = {coordinate.split(":", 1)[0] for coordinate, *_ in rows}
        self.assertEqual(
            found_domains,
            {f"D{width}" for width in range(1, 12)},
            "сканер має охопити кожен файл доменів D1–D11",
        )

        findings = collect_projection_violations(rows)
        if findings:
            self.fail(
                "Порушення в таблицях D1–D11: розширення .lisp означає "
                "українську проєкцію укр (тут також перевіряються клітинки ук і sym); "
                ".sens означає двійкове представлення й цим тестом не перевіряється. "
                "Кожен рядок указує точну клітинку для виправлення:\n"
                + "\n".join(findings)
            )



    def test_d11_ratified_projection_authority_matches_table_without_admitting_calls(self):
        authority = json.loads(
            (ROOT / "knowledge/d11-testing-vocabulary-ratified.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(authority["schema"], "sens.d11.testing/v1")
        self.assertEqual(authority["status"], "owner-ratified")
        self.assertEqual(authority["width"], 11)
        self.assertEqual(authority["occupancy"], 43)
        self.assertEqual(
            authority["semantic_scope"],
            "Testing vocabulary for binary SENS semantic tests; not callable Core",
        )

        # D11's current table supplies human projections only. Its 11-bit
        # identities remain test data and do not become callable Core heads.
        table = {}
        for line in (ROOT / "lib/domains/d11.lisp").read_text(
            encoding="utf-8"
        ).splitlines():
            match = DOMAIN_ROW.match(line)
            if not match:
                continue
            bits, uk, ukr, _san, _en, _lisp, sym = match.groups()
            if len(bits) == 11:
                self.assertNotIn(bits, table)
                table[bits] = (
                    projection_value(uk, "D11"),
                    projection_value(ukr, "D11"),
                    projection_value(sym, "D11"),
                )

        rows = authority["table"]
        self.assertEqual(len(rows), 43)
        self.assertEqual(len({row["bits"] for row in rows}), 43)
        self.assertEqual({row["bits"] for row in rows}, set(table))

        for row in rows:
            with self.subTest(bits=row["bits"]):
                self.assertRegex(row["bits"], r"^[01]{11}$")
                self.assertNotIn("ukр", row,
                                 "JSON key must use ASCII 'ukr', not Cyrillic р")
                self.assertTrue({"uk", "ukr", "sym"}.issubset(row))
                self.assertEqual(
                    (row["uk"], row["ukr"], row["sym"]),
                    table[row["bits"]],
                    "D11 projection must match the existing table without changing identity",
                )

        full_labels = {row["ukr"] for row in rows}
        self.assertEqual(len(full_labels), 43,
                         "D11 full Ukrainian peer labels must be unique")
        self.assertTrue(
            all(row["uk"] != row["ukr"] for row in rows),
            "укр is the full projection; ук remains the compact projection",
        )
if __name__ == "__main__":
    unittest.main(verbosity=2)
