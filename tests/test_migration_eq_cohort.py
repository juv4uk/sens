#!/usr/bin/env python3
"""#4455 exact EQ: independent historical SID8 and uppercase Lisp I -> physical T5."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-three-pass.py"
FIXTURES = ROOT / "tests" / "fixtures" / "migration-eq-cohort"
FOUNDATION = ROOT / "knowledge" / "d1-d9-foundation.json"
ARGS = {
    "foundation": FOUNDATION,
    "domain_surfaces": ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
    "semantic_generated": ROOT / "crates/sens/src/semantic_registry_generated.rs",
    "semantic_registry": ROOT / "crates/sens/src/semantic_registry.rs",
    "necessary_forms": ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
    "historical_map": ROOT / "contracts/core1-historical-sid-map.lisp",
    "text7": ROOT / "crates/sens/src/text7_projection_generated.rs",
}
WORDS = "10 101 00 000 00 000 01\n"
BYTES = bytes.fromhex("66890636b3")
CASES = {
    "eq-legacy-sid": ("(00000011 () ())\n", "pass1-sens8"),
    "eq-lisp15": ("(EQ () ())\n", "pass3-lisp15"),
}

spec = importlib.util.spec_from_file_location("migration_eq_canary", SCRIPT)
assert spec and spec.loader
migration = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = migration
spec.loader.exec_module(migration)

class EqualityMigrationCanary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = migration.load_foundation(FOUNDATION)
        cls.legacy, cls.my, cls.upper = migration.build_three_pass_maps(
            data, ARGS["domain_surfaces"], ARGS["semantic_generated"],
            ARGS["semantic_registry"], ARGS["necessary_forms"], ARGS["historical_map"]
        )
        cls.text7 = migration.build_text7(data, ARGS["text7"])
        cls.foundation = data

    def test_owner_semantics_and_historical_evidence(self):
        self.assertEqual(self.foundation["domains"]["D3"]["residents"]["101"], "EQ")
        self.assertEqual(self.foundation["domains"]["D3"]["residents"]["000"], "EMPTY")
        self.assertEqual(self.legacy["00000011"][:2], ("101", "D3"))
        self.assertEqual(self.upper["EQ"], ("101", "D3"))
        self.assertIn("(row 00000011 eq? EQ ", ARGS["historical_map"].read_text())

    def test_ambiguous_w8_head_requires_explicit_source_era(self):
        resolver = migration.Resolver(self.legacy, self.my, self.upper, source_era="auto")
        with self.assertRaises(migration.MigrationError):
            migration.migrate_file(CASES["eq-legacy-sid"][0], resolver, self.text7)

    def test_both_real_three_pass_paths_and_byte_identity(self):
        for stem, (source, pass_name) in CASES.items():
            with self.subTest(stem=stem):
                original = (FIXTURES / (stem + ".lisp")).read_text(encoding="utf-8")
                self.assertEqual(original, source)
                resolver = migration.Resolver(
                    self.legacy, self.my, self.upper,
                    source_era="legacy" if stem == "eq-legacy-sid" else "auto",
                )
                projection = migration.migrate_file(original, resolver, self.text7)
                self.assertEqual(projection, WORDS)
                self.assertEqual(resolver.counts[pass_name], 1)
                self.assertEqual(sum(resolver.counts.values()), 1)
                committed = (FIXTURES / (stem + ".sens")).read_bytes()
                self.assertEqual(committed, BYTES)
                self.assertEqual(migration.encode_projection(projection), committed)
                self.assertEqual(migration.decode_bytes(committed), WORDS.split())
                self.assertNotEqual(committed, source.encode("utf-8"))
                # Generated extensionless view is ASCII 0/1 only, never an executable.
                view = (FIXTURES / stem).read_bytes()
                self.assertEqual(view, WORDS.encode("ascii"))
                self.assertEqual(view, (" ".join(migration.decode_bytes(committed)) + "\n").encode("ascii"))
                self.assertEqual(migration.encode_projection(view.decode("ascii")), committed)

    def test_actual_cli_mirror_ledger_and_no_clobber(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest, manifest = Path(tmp) / "out", Path(tmp) / "report.json"
            command = [
                sys.executable, str(SCRIPT), str(FIXTURES), "--out", str(dest),
                *[arg for key, path in ARGS.items() for arg in
                  ("--" + key.replace("_", "-"), str(path))],
                "--report", str(manifest),
                "--source-era", "legacy",  # File cohort provenance is explicit.
            ]
            proc = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads(manifest.read_text())
            self.assertEqual(report["summary"]["files_written"], 2)
            self.assertEqual(report["summary"]["files_blocked"], 0)
            self.assertEqual({r["status"] for r in report["files"]}, {"written"})
            for stem in CASES:
                self.assertEqual((dest / (stem + ".sens")).read_bytes(), BYTES)
            again = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(again.returncode, 2, again.stdout + again.stderr)
            second = json.loads(manifest.read_text())
            self.assertEqual(second["summary"]["files_blocked"], 2)
            for stem in CASES:
                self.assertEqual((dest / (stem + ".sens")).read_bytes(), BYTES)

    def test_t5_corruption_and_unratified_source_fail_closed(self):
        with self.assertRaises(migration.SensT5Error):
            migration.decode_bytes(BYTES + b"\xf2")  # five extra terminal padding trits
        with self.assertRaises(migration.SensT5Error):
            migration.decode_bytes(bytes([243]))
        with self.assertRaises(migration.SensT5Error):
            migration.encode_projection("10 EQ 00 000 01")
        resolver = migration.Resolver(self.legacy, self.my, self.upper)
        projection = migration.migrate_file("(UNKNOWN () ())", resolver, self.text7)
        with self.assertRaises(migration.SensT5Error):
            migration.encode_projection(projection)

if __name__ == "__main__":
    unittest.main()
