"""Свідок opt-in міграції lib/narrate.lisp на повну SENS укр.

Той самий протокол, що й tests/test_ukr_optin_sources.py: перевіряємо форму
вихідних S-expressions і ratified identity — НЕ Python-семантику SENS.
Латинські call-heads у тілах замінено на повну укр-поверхню; історичні
латинські імена лишаються визначеними; кожна повна укр-назва має exact-value
DEFINE-аліас на історичне ім'я.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NARRATE = ROOT / "lib/narrate.lisp"
D10 = ROOT / "lib/domains/d10.lisp"

TOKEN = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();]+')

# (координата, історичне ім'я, повна укр-назва)
PEERS = (
    ("0010101110", "narrate-invalid-outcome-shape",
     "пояснити-неприпустиму-структуру-результату"),
    ("0010010110", "result-proper-list?", "результат-є-правильним-списком?"),
    ("0010101101", "narrate-proved-outcome", "пояснити-результат-із-доказом"),
)
# result-proper-list? живе в іншому модулі — тут лише як ціль аліаса.
HISTORIC = ("narrate-invalid-outcome-shape", "narrate-proved-outcome",
            "narrate-fact", "narrate-derivation", "narrate-provenance",
            "narrate-answer", "narrate-outcome")


def read_forms(source: str):
    words = [m.group() for m in TOKEN.finditer(source) if not m.group().startswith(";")]
    position = 0

    def read():
        nonlocal position
        if position == len(words):
            raise ValueError("незавершена SENS форма")
        word = words[position]
        position += 1
        if word == ")":
            raise ValueError("зайва закривальна дужка")
        if word != "(":
            return word
        items = []
        while position < len(words) and words[position] != ")":
            items.append(read())
        if position == len(words):
            raise ValueError("незакритий список")
        position += 1
        return items

    result = []
    while position < len(words):
        result.append(read())
    return result


def definitions(source: str):
    result = {}
    for form in read_forms(source):
        if not isinstance(form, list) or len(form) != 3 or form[0] not in ("0011", "визначити"):
            raise AssertionError("кожне верхнє визначення — D4:0011")
        name = form[1]
        if not isinstance(name, str) or name in result:
            raise AssertionError("дубль або неправильне ім'я DEFINE")
        result[name] = form[2]
    return result


def call_heads(expr):
    """Усі викличні голови форми (quoted data не чіпаємо)."""
    if not isinstance(expr, list) or not expr:
        return set()
    if expr[0] in ("як-є", "001"):
        return set()
    found = {expr[0]} if isinstance(expr[0], str) else call_heads(expr[0])
    for child in expr[1:]:
        found |= call_heads(child)
    return found


class NarrateUkrPeerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = NARRATE.read_text(encoding="utf-8")
        cls.defs = definitions(cls.src)
        cls.d10 = D10.read_text(encoding="utf-8")

    def test_peers_are_exact_value_aliases(self):
        for _bits, historic, full in PEERS:
            self.assertEqual(self.defs.get(full), historic,
                             f"{full}: потрібний exact-value DEFINE alias на {historic}")

    def test_historic_entrypoints_survive(self):
        for name in HISTORIC:
            self.assertIn(name, self.defs, f"історичний entrypoint {name} утрачено")

    def test_d10_rows_carry_these_exact_full_spellings(self):
        for bits, historic, full in PEERS:
            rows = [l.strip() for l in self.d10.splitlines()
                    if l.lstrip().startswith(f"({bits} ")]
            self.assertEqual(len(rows), 1, f"D10:{bits}: рівно один ratified рядок")
            self.assertIn(f"(en {historic})", rows[0])
            self.assertIn(f"(укр {full})", rows[0])

    def test_bodies_use_the_full_ukr_head(self):
        for _bits, historic, full in PEERS:
            self.assertNotIn(historic, call_heads(self.defs["narrate-outcome"]),
                             f"{historic}: латинська голова лишилась у тілі")

    def test_negative_reverting_a_peer_is_caught(self):
        broken = self.src.replace(
            "(0011 пояснити-результат-із-доказом narrate-proved-outcome)",
            "(0011 пояснити-щось-інше narrate-proved-outcome)", 1)
        self.assertNotEqual(broken, self.src)
        with self.assertRaises(AssertionError):
            for _bits, historic, full in PEERS:
                if definitions(broken).get(full) != historic:
                    raise AssertionError("exact-value DEFINE alias втрачено")

    def test_malformed_forms_rejected(self):
        with self.assertRaisesRegex(ValueError, "незакритий"):
            read_forms("(0011 неправильне (0010 ()")


if __name__ == "__main__":
    unittest.main(verbosity=2)
