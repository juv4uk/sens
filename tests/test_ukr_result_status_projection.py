"""Статичні інваріанти source-міграції result-status; не Python-SENS evaluator."""
from __future__ import annotations
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "lib/result-status.lisp").read_text(encoding="utf-8")
D1 = {"0": "ні", "1": "так"}
NATIVE = {
    3: {"001": "як-є", "010": "атом?", "011": "решта",
        "100": "перше", "101": "тотожне?", "110": "за-умовою"},
    4: {"0010": "функція", "0011": "визначити",
        "0100": "хибне?", "0111": "решта-решти",
        "1001": "друге", "1110": "список"},
    6: {"001001": "нехай-послідовно"},
}
D9_PROVEN = {
    "000000100": "результат-позначений?",
    "000000111": "створити-спірний",
    "000001101": "створити-некоректний",
    "000010000": "міркувати-спостерігати",
    "000011101": "результат-ціль?",
    "000100111": "створити-заблокований",
    "000111010": "результат-заперечений-ціль?",
    "000111101": "створити-доведений",
    "000111110": "результат-протилежний-ціль",
    "110101100": "символ?",
}
D9_CALL_SURFACES = {
    "101001110": "міркувати",
    "101010010": "модуль-відомий?",
    "110000011": "модуль-клаузи-зараз",
}


def source_code(source):
    # Ignore comments and quoted strings; preserve executable parentheses.
    return re.sub(r';[^\n]*|"(?:\\.|[^"\\])*"', "", source)


class ResultStatusProjectionTests(unittest.TestCase):
    def test_exact_peers_in_ratified_domain_tables(self):
        tables = {d: (ROOT / f"lib/domains/d{d}.lisp").read_text(encoding="utf-8")
                  for d in (*NATIVE, 9)}
        for bits, name in D1.items():
            self.assertIn(f"({bits} (ук {name}) (укр {name})",
                          (ROOT / "lib/domains/d1.lisp").read_text(encoding="utf-8"))
        for d, peers in {**NATIVE, 9: {**D9_PROVEN, **D9_CALL_SURFACES}}.items():
            for bits, ukr in peers.items():
                with self.subTest(domain=d, bits=bits):
                    self.assertRegex(tables[d], re.compile(
                        r"^\s*\(" + bits + r"\s+\(ук [^()]+\) \(укр "
                        + re.escape(ukr) + r"\)", re.MULTILINE))

    def test_d9_names_have_concrete_source_closure(self):
        core = (ROOT / "lib/core4.lisp").read_text(encoding="utf-8")
        for name in D9_PROVEN.values():
            with self.subTest(name=name):
                if name == "міркувати-спостерігати":
                    self.assertRegex(SOURCE,
                                     r"\(визначити\s+міркувати-спостерігати\s+\(функція")
                else:
                    self.assertRegex(core, r"\((?:0011|визначити) "
                                     + re.escape(name) + r"[\s()]")

    def test_no_unqualified_d1_or_migrated_numeric_heads(self):
        code = source_code(SOURCE)
        heads = set(re.findall(r"\(\s*([01]+)(?=[\s()])", code))
        native = {bits for entries in NATIVE.values() for bits in entries}
        # Historical numeric call-head spellings are not a condition of
        # correct Ukrainian Lisp: only code-position heads count.
        self.assertFalse(heads, f"legacy numeric executable heads: {sorted(heads)}")
        self.assertFalse(heads & (native | set(D9_PROVEN) | set(D9_CALL_SURFACES)))
        self.assertNotRegex(code, r"(?<![\w:#])[01](?![01\w])")
        self.assertIn("так", code)
        self.assertIn("ні", code)

    def test_d9_surfaces_are_exact_ukr_without_claiming_callability(self):
        code = source_code(SOURCE)
        # Source identity is checkable here; a D9 resident alone does not
        # demonstrate a native callable mechanism.
        for bits, ukr in D9_CALL_SURFACES.items():
            with self.subTest(bits=bits, ukr=ukr):
                self.assertRegex(code, r"\(\s*" + re.escape(ukr) + r"(?=[\s()])")
                self.assertNotRegex(code, r"\(\s*" + bits + r"(?=[\s()])")
        self.assertNotIn("D7", SOURCE.splitlines()[0])

    def test_only_needed_legacy_entrypoints_and_protocol_tags_remain(self):
        code = source_code(SOURCE)
        for name in ("make-proved", "make-unknown", "make-partial",
                     "make-blocked", "make-disputed", "make-invalid",
                     "result-status", "result-payload", "reason-observe",
                     "reason-in-observe"):
            self.assertIn("(визначити " + name + "\n", code)
        for obsolete in ("result-goal?", "result-negated-goal?",
                         "result-opposite-goal"):
            self.assertNotIn("(визначити " + obsolete + " ", code)
        for current in ("результат-ціль?", "результат-заперечений-ціль?",
                        "результат-протилежний-ціль"):
            self.assertIn("(визначити " + current + "\n", code)
        for tag in ("proved", "unknown", "partial", "blocked",
                    "disputed", "invalid", "not?", "invalid-goal"):
            self.assertIn("(як-є " + tag + ")", code)

    def test_balanced_source_and_no_host_evaluator(self):
        code = source_code(SOURCE)
        balance = 0
        for char in code:
            balance += (char == "(") - (char == ")")
            self.assertGreaterEqual(balance, 0)
        self.assertEqual(balance, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
