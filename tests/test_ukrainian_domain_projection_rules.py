"""Перевірка символів української проєкції D1–D11."""
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


class UkrainianDomainProjectionRulesTests(unittest.TestCase):
    def test_d1_through_d11_uk_ukr_and_sym_use_only_ukrainian_keyboard_characters(self):
        rows = read_selected_projection_tokens()
        self.assertTrue(rows, "не знайдено проєкцій ук, укр і sym у D1–D11")

        found_domains = {coordinate.split(":", 1)[0] for coordinate, *_ in rows}
        self.assertEqual(
            found_domains,
            {f"D{width}" for width in range(1, 12)},
            "сканер має охопити кожен файл доменів D1–D11",
        )

        findings_by_domain: dict[str, list[str]] = {}
        for coordinate, line_number, uk, ukr, sym in rows:
            domain = coordinate.split(":", 1)[0]
            for projection, token in (("ук", uk), ("укр", ukr), ("sym", sym)):
                value = projection_value(token, domain)
                disallowed = sorted(
                    {char for char in value if char.isprintable()} - UKRAINIAN_KEYBOARD_OUTPUTS
                )
                if disallowed:
                    rendered = " ".join(f"U+{ord(char):04X} {char!r}" for char in disallowed)
                    findings_by_domain.setdefault(domain, []).append(
                        f"{coordinate} line={line_number} {projection}={value!r}; "
                        f"поза розкладкою: {rendered}"
                    )

        if findings_by_domain:
            diagnostics = []
            for domain, findings in sorted(
                findings_by_domain.items(), key=lambda item: int(item[0][1:])
            ):
                examples = "\n  ".join(findings[:5])
                remainder = len(findings) - min(len(findings), 5)
                suffix = f"\n  … ще {remainder} рядків" if remainder else ""
                diagnostics.append(f"{domain}: {len(findings)} рядків\n  {examples}{suffix}")
            self.fail(
                "символи поза українською клавіатурою в ук/укр/sym:\n"
                + "\n".join(diagnostics)
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
