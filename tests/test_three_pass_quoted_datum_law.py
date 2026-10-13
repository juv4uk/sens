#!/usr/bin/env python3
"""Точковий тест ратифікованого закону цитованих даних у трипрохідному міграторі.

Закон власника 2026-10-13
(docs/QUOTED-DATA-AND-STRING-ADMISSION-LAW-2026-10-13.uk.md):
цитовані дані перевіряються на місце в драбині функцій (EVAL/APPLY, D4).

- D1-предикати 0/1 у цитаті лишаються точними 1-бітними словами;
- точний координат драбини D3-D9 у цитаті лишається точною identity;
- ім'я без місця в драбині стає D2-рамкованим D7-написанням (роль
  `quoted-datum`), а не сирим текстом;
- ім'я, яке джерело зв'язує DEFINE-ом, є Text7-посиланням навіть у
  нецитованій позиції даних;
- те, що лишається без зв'язку, — точний як написано (далі це ловить
  фізична 0/1-перевірка), і жодне невідповідне слово не вигадується.

Маршрут доказу — той самий ратифікований донор Text7, що й у CLI
(`knowledge/d7-keyboard-v2-ratified.json`), а не retired SLP1 `.rs`.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-three-pass.py"

_spec = importlib.util.spec_from_file_location("three_pass_law", SCRIPT)
assert _spec and _spec.loader
mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = mod
_spec.loader.exec_module(mod)


class QuotedDatumLadderLaw(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = mod.load_foundation(ROOT / "knowledge/d1-d9-foundation.json")
        cls.legacy, cls.my, cls.upper = mod.build_three_pass_maps(
            data,
            ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry.rs",
            ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
            ROOT / "contracts/core1-historical-sid-map.lisp",
            ROOT / "knowledge/sens8-current-coverage-v1.json",
        )
        cls.text7 = mod.build_text7(data, ROOT / "knowledge/d7-keyboard-v2-ratified.json")

    def migrate(self, source):
        resolver = mod.Resolver(self.legacy, self.my, self.upper, source_era="legacy")
        return mod.migrate_file(source, resolver, self.text7), resolver

    def test_quoted_d1_predicates_keep_exact_single_bit_words(self):
        out, _ = self.migrate("'(0 1)\n")
        self.assertEqual(out, "10 001 00 10 0 00 1 01 01\n")
        self.assertNotIn("110000", out, "0 must not become a D7 glyph cell")

    def test_quoted_exact_ladder_coordinates_keep_exact_identity(self):
        out, _ = self.migrate("'(001 101)\n")
        self.assertEqual(out, "10 001 00 10 001 00 101 01 01\n")

    def test_quoted_names_use_exact_domain_identity_before_d7(self):
        # Each canonical display projection points to its exact domain address.
        cases = {
            "ні": "0",                  # D1
            "NIL": "0",                 # D1 historic surface
            "CAR": "100",               # D3
            "перше": "100",             # D3 Ukrainian surface
            "як-є": "001",              # D3 QUOTE
            "SQRT": "00001110",         # D8
            "корінь": "00001110",       # D8 Ukrainian surface
            "guard-evidence-status?": "000000000",  # D9 data identity
            "missing-capability": "0000000000",    # D10 data identity
        }
        for name, bits in cases.items():
            with self.subTest(name=name):
                out, _ = self.migrate("'" + name + "\\n")
                self.assertEqual(out, f"10 001 00 {bits} 01\\n")
                self.assertEqual(len(bits), 1 if name in ("ні", "NIL") else
                                 3 if name in ("CAR", "перше", "як-є") else
                                 8 if name in ("SQRT", "корінь") else
                                 9 if name == "guard-evidence-status?" else 10)

    def test_ambiguous_ladder_surface_blocks_instead_of_guessing_d7(self):
        # Canonical tables have MAP in both D6 and D8.
        with self.assertRaisesRegex(mod.MigrationError, "ambiguous quoted ladder"):
            self.migrate("'MAP\\n")

    def test_quote_recursively_prefers_ladder_inside_data_lists(self):
        out, _ = self.migrate("'(CAR nonresident)\\n")
        self.assertTrue(out.startswith("10 001 00 10 100 00 10 "), out)
        self.assertNotIn(" CAR ", out)

    def test_quoted_name_without_ladder_place_becomes_d2_framed_d7(self):
        out, _ = self.migrate("'(a . b)\n")
        self.assertEqual(out, "10 001 00 10 10 1100001 01 11 10 1100010 01 01 01\n")

    def test_non_quoted_global_binding_is_a_text7_reference(self):
        out, r = self.migrate("(0011 FOO (0010 (X) (FOO X)))\n")
        self.assertIn("10 1000110 00 1001111 00 1001111 01", out)
        self.assertEqual(r.counts["pass4-text7-global"], 1)
        self.assertNotIn(" FOO ", out, "a bound name must never stay raw source text")

    def test_label_name_is_framed_like_a_definite_reference(self):
        out, _ = self.migrate(
            "(0011 C1-LOOKUP-IN (00100 C1-LOOKUP-IN (0010 (NAME ENV) NAME)))\n"
        )
        self.assertNotIn(" C1-LOOKUP-IN ", out)
        self.assertIn("10 00100 00 10 ", out, "D5 LABEL head must survive exactly")

    def test_unbound_free_data_is_left_exactly_as_written(self):
        out, _ = self.migrate("(CONS x y)\n")
        self.assertEqual(out, "10 111 00 x 00 y 01\n")

    def test_quoted_unencodable_word_still_fails_closed(self):
        with self.assertRaises(mod.MigrationError):
            self.migrate("'(\U0001F642)\n")

    def test_core1_main_file_migrates_to_physical_sens(self):
        report = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "migrate-one-to-sens.py"),
             "lib/core1.lisp", "--source-era", "legacy", "--dry-run"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(report.returncode, 0, report.stderr + report.stdout)
        state = json.loads(report.stdout)
        self.assertEqual(state["status"], "would-write")
        self.assertEqual(state["output"], "lib/core1.sens")
        self.assertGreater(state["bytes"], 0)
        self.assertEqual(state["semantic_parity"], "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
