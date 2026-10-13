#!/usr/bin/env python3
"""Точковий тест закону цитованих даних / драбини функцій (настанова власника 2026-10-13).

Доводить три правила:
  1. цитоване ім'я без місця в драбині функцій -> контекстний D2/W7 (D7), не блок;
  2. цитована координата драбини -> точна identity-word, не D7-написання;
  3. координата драбини в позиції аргументу -> точна identity-word;
  4. випереджувальний виклик DEFINE-імені (взаємна рекурсія) -> контекстний D7 call-head.

Негативні контролі лишаються fail-closed: невідомий head, нерозв'язаний 8-бітний SID,
незв'язане ім'я як дані.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SCRIPT = SCRIPTS / "migrate-to-sens-codes.py"
SPEC = importlib.util.spec_from_file_location("sens_migrator_quoted_law", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

from sens_source_resolver import build_resolver

FOUNDATION = ROOT / "knowledge" / "d1-d9-foundation.json"
OWNER_V2 = ROOT / "knowledge" / "d7-keyboard-v2-ratified.json"
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
HISTORICAL = ROOT / "contracts" / "core1-historical-sid-map.lisp"
DOMAIN_SURFACES = [ROOT / "lib" / "domains" / f"d{width}.lisp" for width in range(1, 10)]


def has_sublist(seq, sub):
    n = len(sub)
    return any(seq[i:i + n] == sub for i in range(len(seq) - n + 1))


class QuotedDatumLadderLaw(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data, _ = mod.load_foundation(FOUNDATION)
        cls.data = data
        code_map = mod.build_map(data, ["D3", "D4", "D5", "D6"])
        code_map = mod.augment_code_map_with_domain_surfaces(code_map, DOMAIN_SURFACES)
        code_map = mod.augment_code_map_with_registry_aliases(code_map, REGISTRY)
        cls.code_map = code_map
        cls.text7 = mod.build_text7_encoder(data, OWNER_V2)
        cls.legacy = mod.build_legacy_sid_map(REGISTRY, code_map)
        cls.registry_surfaces = mod.build_registry_surface_sid_map(REGISTRY)
        cls.resolver = build_resolver(
            historical_map=HISTORICAL,
            foundation=FOUNDATION,
            registry=REGISTRY,
            domain_surfaces=DOMAIN_SURFACES,
        )

    def binary(self, source: str):
        return mod.binary_rewrite(
            source,
            self.code_map,
            self.text7,
            self.legacy,
            self.registry_surfaces,
            self.resolver,
        )

    def framed(self, text: str):
        cells = mod.encode_text7_spelling(text, self.text7)
        seq = ["10"]
        for idx, cell in enumerate(cells):
            if idx:
                seq.append("00")
            seq.append(cell)
        seq.append("01")
        return seq

    def test_quoted_name_without_ladder_place_is_contextual_d7(self):
        converted, hits, _ = self.binary("(001 binary)\n")
        words = converted.split()
        self.assertEqual(words, ["10", "001", "00"] + self.framed("binary") + ["01"])
        self.assertEqual([h.label for h in hits], ["QUOTE"])

    def test_quoted_ladder_coordinate_keeps_exact_identity(self):
        converted, _, _ = self.binary("(001 001)\n")
        self.assertEqual(converted.split(), ["10", "001", "00", "001", "01"])

    def test_domain_coordinate_argument_keeps_exact_identity(self):
        converted, _, _ = self.binary(
            "(0011 T (0010 (VALUE) (101 VALUE 001)))\n"
        )
        words = converted.split()
        self.assertIn("101", words)
        self.assertTrue(has_sublist(words, self.framed("VALUE")), words)
        # The trailing 001 is a bare D3 coordinate right after a closed D7 frame
        # (00 <001>), never a D2/W7 spelling of the digits "001".
        bare = [
            j for j, w in enumerate(words)
            if w == "001" and j >= 2 and words[j - 1] == "00" and words[j - 2] == "01"
        ]
        self.assertTrue(bare, words)

    def test_forward_reference_call_head_is_contextual_d7(self):
        converted, _, _ = self.binary(
            "(0011 G (0010 () (F)))\n(0011 F (0010 () (G)))\n"
        )
        words = converted.split()
        f = self.framed("F")
        g = self.framed("G")
        self.assertGreaterEqual(sum(1 for i in range(len(words) - len(f) + 1) if words[i:i + len(f)] == f), 2)
        self.assertGreaterEqual(sum(1 for i in range(len(words) - len(g) + 1) if words[i:i + len(g)] == g), 2)

    def test_unknown_head_still_fails_closed(self):
        with self.assertRaisesRegex(mod.BinaryMigrationError, "unresolved executable head"):
            self.binary("(MISSING x)\n")

    def test_unresolved_legacy_sid8_still_fails_closed(self):
        with self.assertRaisesRegex(mod.BinaryMigrationError, "unresolved executable head"):
            self.binary("(11111111 x)\n")

    def test_unbound_unquoted_argument_still_fails_closed(self):
        with self.assertRaisesRegex(mod.BinaryMigrationError, "UNADMITTED_TEXT7_CONTEXT"):
            self.binary("(CONS a ())\n")


if __name__ == "__main__":
    unittest.main()
