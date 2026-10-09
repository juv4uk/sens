#!/usr/bin/env python3
"""Existing Core1 C1-FOURTH -> one real physical T5 closed specialization, not a new evaluator."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/migrate-three-pass.py"
FIXTURE = ROOT / "tests/fixtures/core1-fourth-domain-canary"
SOURCE = FIXTURE / "fourth.lisp"
PHYSICAL = FIXTURE / "fourth.sens"
ARGS = {
    "foundation": ROOT / "knowledge/d1-d9-foundation.json",
    "domain_surfaces": ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
    "semantic_generated": ROOT / "crates/sens/src/semantic_registry_generated.rs",
    "semantic_registry": ROOT / "crates/sens/src/semantic_registry.rs",
    "necessary_forms": ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
    "historical_map": ROOT / "contracts/core1-historical-sid-map.lisp",
    "text7": ROOT / "crates/sens/src/text7_projection_generated.rs",
}
EXPECTED_WORDS = "10 100 00 10 011 00 10 011 00 10 011 00 10 111 00 10 001 00 000 01 00 10 111 00 10 001 00 000 01 00 10 111 00 10 001 00 000 01 00 10 111 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01 00 10 001 00 000 01 01 01 01 01 01 01 01 01\n"

EXPECTED_BYTES = bytes.fromhex("663864896489648967896389068967896389068967896389068967896789638906896389068c15a7123b2eb18c2eb3")

spec = importlib.util.spec_from_file_location("c1fourth_migration", SCRIPT)
assert spec and spec.loader
migration = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = migration
spec.loader.exec_module(migration)

class C1FourthDomainCanary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        foundation = migration.load_foundation(ARGS["foundation"])
        cls.legacy, cls.my, cls.upper = migration.build_three_pass_maps(
            foundation, ARGS["domain_surfaces"], ARGS["semantic_generated"],
            ARGS["semantic_registry"], ARGS["necessary_forms"], ARGS["historical_map"]
        )
        cls.text7 = migration.build_text7(foundation, ARGS["text7"])
        cls.foundation = foundation

    def test_existing_core1_fourth_implementation_is_source_provenance(self):
        existing = (ROOT / "lib/core1.lisp").read_text(encoding="utf-8")
        self.assertIn("(00001001 C1-FOURTH", existing)
        c1_fourth = existing.split("(00001001 C1-FOURTH", 1)[1].split("(00001001 C1-MAKE-ERROR", 1)[0]
        self.assertIn("(00000101 (00000110 (00000110 (00000110 X))))", " ".join(c1_fourth.split()))
        self.assertEqual(self.foundation["domains"]["D3"]["residents"]["100"], "CAR")
        self.assertEqual(self.foundation["domains"]["D3"]["residents"]["011"], "CDR")
        self.assertEqual(self.foundation["domains"]["D3"]["residents"]["111"], "CONS")
        self.assertEqual(self.foundation["domains"]["D3"]["residents"]["001"], "QUOTE")
        self.assertEqual(self.foundation["domains"]["D3"]["residents"]["000"], "EMPTY")
        for old, current in {"00000101": "100", "00000110": "011",
                             "00000100": "111", "00000001": "001"}.items():
            self.assertEqual(self.legacy[old][:2], (current, "D3"))
        self.assertNotIn("C1-FOURTH", SOURCE.read_text())

    def test_actual_three_pass_and_committed_real_t5(self):
        readable = SOURCE.read_text(encoding="utf-8")
        # lib/core1.lisp pins these exact-8 heads as historical Core1.
        # Do not change the global AUTO law: unknown W8 remains BLOCKED.
        resolver = migration.Resolver(self.legacy, self.my, self.upper, source_era="legacy")
        projection = migration.migrate_file(readable, resolver, self.text7)
        self.assertEqual(projection, EXPECTED_WORDS)
        self.assertEqual(resolver.counts["pass1-sens8"], 15)
        self.assertEqual(resolver.counts["passthrough-head"], 0)
        payload = PHYSICAL.read_bytes()
        self.assertEqual(payload, EXPECTED_BYTES)
        self.assertNotEqual(payload, readable.encode("utf-8"))
        self.assertEqual(migration.encode_projection(projection), payload)
        self.assertEqual(migration.decode_bytes(payload), EXPECTED_WORDS.split())
        # A same-stem extensionless file is permitted ONLY as exact ASCII view.
        # On older main commits the view may be pending; once present it must
        # reproduce the exact physical words, never masquerade as .sens.
        view = FIXTURE / "fourth"
        if view.exists() or view.is_symlink():
            self.assertTrue(view.is_file() and not view.is_symlink())
            self.assertEqual(view.read_bytes(), EXPECTED_WORDS.encode("ascii"))
            self.assertNotEqual(view.read_bytes(), payload)

    def test_real_mirror_cli_manifest_and_no_clobber(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "mirror"
            report = Path(tmp) / "manifest.json"
            cmd = [
                sys.executable, str(SCRIPT), str(FIXTURE), "--out", str(dest),
                *[item for key, path in ARGS.items() for item in
                  ("--" + key.replace("_", "-"), str(path))],
                "--report", str(report), "--source-era", "legacy"
            ]
            run = subprocess.run(cmd, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            manifest = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(manifest["summary"]["files_written"], 1)
            self.assertEqual(manifest["summary"]["files_blocked"], 0)
            self.assertEqual((dest / "fourth.sens").read_bytes(), EXPECTED_BYTES)
            again = subprocess.run(cmd, text=True, capture_output=True)
            self.assertEqual(again.returncode, 2, again.stdout + again.stderr)
            blocked = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(blocked["summary"]["files_blocked"], 1)
            self.assertEqual((dest / "fourth.sens").read_bytes(), EXPECTED_BYTES)
            self.assertTrue(SOURCE.exists())

    def test_auto_w8_remains_blocked_without_historical_source_era(self):
        readable = SOURCE.read_text(encoding="utf-8")
        auto = migration.Resolver(self.legacy, self.my, self.upper, source_era="auto")
        with self.assertRaisesRegex(migration.MigrationError, "ambiguous W8"):
            migration.migrate_file(readable, auto, self.text7)

    def test_unratified_and_corrupt_transport_stay_blocked(self):
        for invalid in (EXPECTED_BYTES + b"\xf2", bytes([243])):
            with self.assertRaises(migration.SensT5Error):
                migration.decode_bytes(invalid)
        with self.assertRaises(migration.SensT5Error):
            migration.encode_projection("10 100 00 C1-FOURTH 01")
        resolver = migration.Resolver(self.legacy, self.my, self.upper)
        with self.assertRaises(migration.MigrationError):
            migration.migrate_file("(00000101 (11110000 ()))", resolver, self.text7)

if __name__ == "__main__":
    unittest.main()
