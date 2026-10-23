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

    def test_current_domain_uk_and_ukr_are_real_keyboard_glyphs(self):
        """Перевірити фактичні D1-D11, а не лише тестові підставні рядки."""
        # D11 більше не є відхиленим словником із 43 записів:
        # 256 підтверджених D10-селекторів × два суфікси = 512 D11 координат.
        # Перевірка лишається fail-closed: повнота, точна ширина, унікальність.
        expected = {width: (1 << width if width <= 10 else 512)
                    for width in range(1, 12)}
        total = 0
        for width, count in expected.items():
            path = ROOT / "lib" / "domains" / f"d{width}.lisp"
            rows = []
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not re.match(r"^\s*\([01]{1,11}\s+", line):
                    continue
                match = DOMAIN_ROW.fullmatch(line)
                self.assertIsNotNone(
                    match,
                    f"{path}:{number}: некоректний рядок проєкції",
                )
                bits, uk, ukr, san, en, lisp, sym = match.groups()
                self.assertEqual(len(bits), width)
                rows.append(bits)
                for column, token in (("ук", uk), ("укр", ukr)):
                    value = projection_value(token, f"D{width}")
                    disallowed = set(char for char in value
                                     if char.isprintable()
                                     and char not in UKRAINIAN_KEYBOARD_OUTPUTS)
                    self.assertFalse(
                        disallowed,
                        format_projection_violation(
                            str(path.relative_to(ROOT)), f"D{width}:{bits}",
                            number, column, token, value,
                        ),
                    )
            self.assertEqual(len(rows), count, f"{path}: неповна таблиця")
            self.assertEqual(len(set(rows)), count, f"{path}: повтор координати")
            total += count
        self.assertEqual(total, 2558)

    def test_live_interlisp_library_has_only_ukrainian_keyboard_symbols(self):
        """Жодної латиниці навіть у коментарях або іменах функцій."""
        path = ROOT / "lib/d11-interlisp-safe-analysis.lisp"
        source = path.read_text(encoding="utf-8")
        allowed = UKRAINIAN_KEYBOARD_OUTPUTS | {chr(9), chr(10), chr(13)}
        violations = [
            f"{i}:{ch!r} U+{ord(ch):04X}"
            for i, line in enumerate(source.splitlines(), 1)
            for ch in line if ch not in allowed
        ]
        self.assertEqual(violations, [],
                         "Латиниця або недозволена пунктуація в SENS-бібліотеці: "
                         + ", ".join(violations[:20]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
