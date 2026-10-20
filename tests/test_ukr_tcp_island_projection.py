"""Read-only negative/positive witnesses for the ratified Ukrainian TCP/Island cut.

This checks source AST identity and domain surfaces only, not SENS call admission
or Zig/T5M transport. The frozen fingerprints are from the pre-change source AST.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();]+')
LOCAL_HELPERS = {"вибрати-механізм": "mechanism-select"}
PEERS = {
    "функція": (4, "0010"), "як-є": (3, "001"), "атом?": (3, "010"),
    "решта": (3, "011"), "перше": (3, "100"),
    "тотожне?": (3, "101"), "за-умовою": (3, "110"),
    "сполучити": (3, "111"), "друге": (4, "1001"),
    "список": (4, "1110"), "рядок-додати": (9, "110011110"),
    "четверте": (6, "100111"),
}
# Frozen pre-migration AST, NOT a сід8 byte/width authority.
BASELINE = {
  "lib/tcp.lisp": {
    "fingerprint": "9566f4cd27d15f90",
    "count": 5,
    "forms": 7
  },
  "lib/island-lowering.lisp": {
    "fingerprint": "dcc87879d0c95fa0",
    "count": 50,
    "forms": 3
  }
}


def parse(source: str):
    words = [item.group() for item in TOKEN.finditer(source)
             if not item.group().startswith(";")]
    index = 0

    def read():
        nonlocal index
        if index >= len(words):
            raise ValueError("незавершена Lisp форма")
        word = words[index]
        index += 1
        if word == ")":
            raise ValueError("зайва закривальна дужка")
        if word != "(":
            return word
        values = []
        while index < len(words) and words[index] != ")":
            values.append(read())
        if index >= len(words):
            raise ValueError("немає закривальної дужки")
        index += 1
        return values

    forms = []
    while index < len(words):
        forms.append(read())
    return forms


def current_to_exact(node):
    """Only call heads. No decoding quoted data or changing literal values."""
    if not isinstance(node, list) or not node:
        return node
    first = node[0]
    if isinstance(first, str):
        first = LOCAL_HELPERS.get(first, PEERS.get(first, (None, first))[1])
    else:
        first = current_to_exact(first)
    if first == "001":  # ratified D3 QUOTE owns data
        return [first] + node[1:]
    return [first] + [current_to_exact(child) for child in node[1:]]


def signature(forms):
    # Same FNV-1a convention as the original-domain AST regressions;
    # hash character codepoints, never physical T5M bytes.
    data = json.dumps(forms, ensure_ascii=False, separators=(",", ":"))
    h = 0xCBF29CE484222325
    for char in data:
        h = ((h ^ ord(char)) * 0x100000001B3) & ((1 << 64) - 1)
    return f"{h:016x}"


def heads(node):
    if not isinstance(node, list) or not node:
        return []
    first = node[0]
    result = [first] if isinstance(first, str) else heads(first)
    if first in ("001", "як-є"):
        return result
    for child in node[1:]:
        result.extend(heads(child))
    return result


def validate(path: str, source: str):
    forms = parse(source)
    if len(forms) != BASELINE[path]["forms"]:
        raise AssertionError("змінилася кількість форм")
    if signature([current_to_exact(node) for node in forms]) != BASELINE[path]["fingerprint"]:
        raise AssertionError("порушено початковий точний AST закон, арність або цитату")
    called = [name for node in forms for name in heads(node)]
    translated = [x for x in called if x in PEERS]
    if len(translated) != BASELINE[path]["count"]:
        raise AssertionError("не всі викличні голови на українській поверхні")
    leftovers = [name for name in called
                 if re.fullmatch(r"[01]{3,10}", name) and name not in
                 ("0010", "0011", "100111")]
    if leftovers:
        raise AssertionError(f"невиправдані сирі голови: {leftovers}")
    return forms


class UkrainianTcpIslandTests(unittest.TestCase):
    def test_ratified_domain_bits_and_both_ukrainian_peers(self):
        for spelling, (width, bits) in PEERS.items():
            with self.subTest(surface=spelling, domain=width, bits=bits):
                rows = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
                line = next((s for s in rows.splitlines() if s.startswith(f"  ({bits} ")), None)
                self.assertIsNotNone(line)
                if spelling == "четверте":
                    # D6 compact ук=пррр; full укр=четверте is distinct.
                    self.assertIn("(ук пррр)", line)
                else:
                    self.assertIn(f"(ук {spelling})", line)
                self.assertIn(f"(укр {spelling})", line)

    def test_exact_unchanged_ast_and_all_projection_callsites(self):
        for path in BASELINE:
            with self.subTest(path=path):
                validate(path, (ROOT / path).read_text(encoding="utf-8"))

    def test_quote_data_and_host_tcp_string_stay_data(self):
        data = (ROOT / "lib/tcp.lisp").read_text(encoding="utf-8")
        self.assertIn('"0.0.0.0"', data)
        self.assertIn("#d1:1", data)
        validate("lib/tcp.lisp", data)
        island = (ROOT / "lib/island-lowering.lisp").read_text(encoding="utf-8")
        self.assertIn("(четверте selection)", island)  # exact D6:100111 CADDDR
        self.assertNotIn("(100111 selection)", island)
        self.assertIn("(вибрати-механізм sid executor)", island)
        self.assertNotIn("(mechanism-select sid executor)", island)
        self.assertIn("(рядок-додати", island)
        self.assertEqual(island.count("((функція ("), 4)
        self.assertEqual(island.count("(0010 ("), 3)
        validate("lib/island-lowering.lisp", island)

    def test_negative_wrong_current_operation_or_domain(self):
        path = "lib/island-lowering.lisp"
        original = (ROOT / path).read_text(encoding="utf-8")
        for changed in [
            original.replace("(рядок-додати", "(сполучити", 1),
            original.replace("((функція (selection)", "((сполучити (selection)", 1),
            original.replace("(тотожне?", "(сполучити", 1),
            original.replace("(рядок-додати", "(00000101", 1),
            original.replace("(четверте selection)", "(третє selection)", 1),
        ]:
            with self.assertRaises(AssertionError):
                validate(path, changed)

    def test_negative_quote_and_d1_fallback_mutants(self):
        path = "lib/tcp.lisp"
        original = (ROOT / path).read_text(encoding="utf-8")
        for changed in [
            original.replace("(як-є decoded)", "(як-є rejected)", 1),
            original.replace("#d1:1", "#d1:0", 1),
            original.replace('"0.0.0.0"', '"127.0.0.1"', 1),
        ]:
            with self.assertRaises(AssertionError):
                validate(path, changed)

    def test_negative_malformed_source_rejected(self):
        for value in ("(", ")", "(за-умовою (тотожне?"):
            with self.assertRaises(ValueError):
                parse(value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
