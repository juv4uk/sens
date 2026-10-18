"""Свідок opt-in міграції lib-модулів на повну SENS укр-поверхню.

Дані-driven: для кожного мігрованого модуля перевіряємо, що кожна повна
укр-назва з таблиці драбини визначена як exact-value DEFINE-аліас на своє
історичне (en) ім'я, і що історичне ім'я лишається визначеним. Форму
S-expressions — не Python-семантику SENS.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = r'(\(\)|"(?:\\.|[^"\\])*"|[^()\s]+)'
ROW = re.compile(r'^\s*\(([01]{1,11})\s+\(ук\s+' + TOKEN + r'\)\s+\(укр\s+' + TOKEN +
                 r'\)\s+\(san\s+' + TOKEN + r'\)\s+\(en\s+' + TOKEN +
                 r'\)\s+\(LISP\s+' + TOKEN + r'\)\s+\(sym\s+' + TOKEN + r'\)\)\s*$')
DEF = re.compile(r'\((?:0011|визначити)\s+([^\s()]+)\s')

MIGRATED = ("lib/time.lisp", "lib/reason.lisp", "lib/utf8.lisp",
            "lib/meta-eval-mutual.lisp", "lib/knowledge.lisp", "lib/narrate.lisp")


def load_rows():
    rows = {}
    for w in range(1, 12):
        p = ROOT / f"lib/domains/d{w}.lisp"
        if p.is_file():
            for line in p.read_text(encoding="utf-8").splitlines():
                m = ROW.match(line)
                if m:
                    rows.setdefault(f"D{w}:{m.group(1)}", (m.group(2), m.group(3), m.group(5)))
    return rows


ROWS = load_rows()


MARKER = "; opt-in повна укр-поверхня"


def definitions(src: str):
    return {m.group(1) for m in DEF.finditer(src)}


def optin_pairs(src: str):
    """Лише аліаси з доданого інструментом opt-in-блоку."""
    if MARKER not in src:
        return []
    block = src.split(MARKER, 1)[1]
    return [(m.group(1), m.group(2))
            for m in re.finditer(r'\(визначити\s+([^\s()]+)\s+([^\s()]+)\)', block)]


class LibUkrPeerTests(unittest.TestCase):
    def test_every_migrated_full_ukr_name_is_an_exact_value_alias(self):
        checked = 0
        for rel in MIGRATED:
            src = (ROOT / rel).read_text(encoding="utf-8")
            defs = definitions(src)
            for ukr, en in optin_pairs(src):
                checked += 1
                self.assertIn(en, defs,
                              f"{rel}: аліас {ukr}->{en} без історичного імені {en}")
            # жодного дубля
            names = [x.group(1) for x in DEF.finditer(src)]
            self.assertEqual(len(names), len(set(names)), f"{rel}: дубль визначення")
        self.assertGreater(checked, 20, "мало перевірених peer-аліасів")

    def test_migrated_names_are_ratified_identities(self):
        for rel in MIGRATED:
            src = (ROOT / rel).read_text(encoding="utf-8")
            for ukr, en in optin_pairs(src):
                hit = [k for k, (_uk, u, e) in ROWS.items() if u == ukr and e == en]
                self.assertTrue(hit, f"{rel}: {ukr}/{en} не є ratified identity парою")

    def test_numeric_heads_gone_from_the_alias_block(self):
        for rel in MIGRATED:
            src = (ROOT / rel).read_text(encoding="utf-8")
            for line in src.splitlines():
                if line.startswith("(визначити") and re.search(r"[а-яїієґ]", line):
                    self.assertNotRegex(line, r"^\(0011\b",
                                        f"{rel}: новий аліас мусить вживати визначити")


if __name__ == "__main__":
    unittest.main(verbosity=2)
