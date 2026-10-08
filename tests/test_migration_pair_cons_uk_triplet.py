#!/usr/bin/env python3
"""Existing pair-cons: exact Ukrainian source / unchanged T5 / extensionless view."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "tests/fixtures/migration-pair-cohort-main"
SOURCE = "(сполучити (як-є ()) (як-є ()))\n"
HISTORICAL = "(00000100 (00000001 ()) (00000001 ()))\n"
VISIBLE = "10 111 00 10 001 00 000 01 00 10 001 00 000 01 01\n"
MIGRATOR = ROOT / "scripts/migrate-three-pass.py"
VIEWER = ROOT / "scripts/sens_spaced_view.py"
spec = importlib.util.spec_from_file_location("pair_cons_three_pass", MIGRATOR)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
AUTHORITY = {
    "foundation": ROOT / "knowledge/d1-d9-foundation.json",
    "domain_surfaces": ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
    "semantic_generated": ROOT / "crates/sens/src/semantic_registry_generated.rs",
    "semantic_registry": ROOT / "crates/sens/src/semantic_registry.rs",
    "necessary_forms": ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
    "historical_map": ROOT / "contracts/core1-historical-sid-map.lisp",
    "text7": ROOT / "crates/sens/src/text7_projection_generated.rs",
}


class UkrainianPairConsTriple(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        foundation = mod.load_foundation(AUTHORITY["foundation"])
        cls.assert_residents = foundation["domains"]["D3"]["residents"]
        cls.legacy, cls.my, cls.upper = mod.build_three_pass_maps(
            foundation, AUTHORITY["domain_surfaces"], AUTHORITY["semantic_generated"],
            AUTHORITY["semantic_registry"], AUTHORITY["necessary_forms"],
            AUTHORITY["historical_map"],
        )
        cls.text7 = mod.build_text7(foundation, AUTHORITY["text7"])

    def test_uk_source_to_same_t5_and_view_without_new_domain_identity(self):
        self.assertEqual(self.assert_residents["111"], "CONS")
        self.assertEqual(self.assert_residents["001"], "QUOTE")
        self.assertEqual(self.assert_residents["000"], "EMPTY")
        self.assertEqual((HERE / "pair-cons.lisp").read_text(encoding="utf-8"), SOURCE)
        resolver = mod.Resolver(self.legacy, self.my, self.upper, source_era="auto")
        projection = mod.migrate_file(SOURCE, resolver, self.text7)
        self.assertEqual(projection, VISIBLE)
        self.assertEqual(resolver.counts["pass2-my-lisp"], 3)
        physical = (HERE / "pair-cons.sens").read_bytes()
        self.assertEqual(mod.encode_projection(projection), physical)
        self.assertEqual(mod.decode_bytes(physical), VISIBLE.split())
        self.assertEqual((HERE / "pair-cons").read_bytes(), VISIBLE.encode("ascii"))
        self.assertNotEqual(physical, SOURCE.encode("utf-8"))
        self.assertEqual(VISIBLE.count("\n"), 1)

    def test_legacy_eight_bit_requires_explicit_source_era(self):
        with self.assertRaises((mod.MigrationError, mod.SensT5Error)):
            auto = mod.Resolver(self.legacy, self.my, self.upper, source_era="auto")
            mod.encode_projection(mod.migrate_file(HISTORICAL, auto, self.text7))
        legacy = mod.Resolver(self.legacy, self.my, self.upper, source_era="legacy")
        projection = mod.migrate_file(HISTORICAL, legacy, self.text7)
        self.assertEqual(projection, VISIBLE)
        self.assertEqual(mod.encode_projection(projection), (HERE / "pair-cons.sens").read_bytes())

    def test_existing_view_verification_and_external_no_clobber(self):
        command = [sys.executable, str(VIEWER), "--root", str(ROOT),
                   "--sens", "tests/fixtures/migration-pair-cohort-main/pair-cons.sens"]
        verified = subprocess.run(command + ["--verify"], cwd=ROOT, text=True,
                                  capture_output=True, timeout=45)
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        with tempfile.TemporaryDirectory(prefix="sens-pair-cons-view-") as td:
            first = subprocess.run(command + ["--stage", td], cwd=ROOT,
                                   text=True, capture_output=True, timeout=45)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            dest = Path(td) / "tests/fixtures/migration-pair-cohort-main/pair-cons"
            self.assertEqual(dest.read_bytes(), VISIBLE.encode("ascii"))
            repeated = subprocess.run(command + ["--stage", td], cwd=ROOT,
                                      text=True, capture_output=True, timeout=45)
            self.assertEqual(repeated.returncode, 2, repeated.stdout + repeated.stderr)
            self.assertEqual(dest.read_bytes(), VISIBLE.encode("ascii"))

    def test_corrupt_t5_and_text_as_function_are_rejected(self):
        with self.assertRaises(mod.SensT5Error):
            mod.decode_bytes((HERE / "pair-cons.sens").read_bytes() + b"\xf2")
        with self.assertRaises(mod.SensT5Error):
            mod.encode_projection("10 сполучити 00 000 01")
        self.assertNotEqual(VISIBLE.encode("ascii"),
                            VISIBLE.replace(" 01 00", " 01  00").encode("ascii"))


if __name__ == "__main__":
    unittest.main()
