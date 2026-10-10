#!/usr/bin/env python3
"""#4455 bounded historical CAR/CDR/CONS migration canary."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-three-pass.py"
FIXTURES = ROOT / "tests" / "fixtures" / "migration-pair-cohort"
ARGS = {
    "foundation": ROOT / "knowledge/d1-d7-foundation.json",
    "domain_surfaces": ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
    "semantic_generated": ROOT / "crates/sens/src/semantic_registry_generated.rs",
    "semantic_registry": ROOT / "crates/sens/src/semantic_registry.rs",
    "necessary_forms": ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
    "historical_map": ROOT / "contracts/core1-historical-sid-map.lisp",
    "text7": ROOT / "crates/sens/src/text7_projection_generated.rs",
}

spec = importlib.util.spec_from_file_location("migration_pair", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

CASES = {
    "pair-car-cdr": {
        "source": "(00000101 (00000110 (00000001 (() ()))))\n",
        "words": "10 100 00 10 011 00 10 001 00 10 000 00 000 01 01 01 01\n",
        "t5": bytes.fromhex("6638648963896338068c2e"),
    },
    "pair-cons": {
        "source": "(00000100 (00000001 ()) (00000001 ()))\n",
        "words": "10 111 00 10 001 00 000 01 00 10 001 00 000 01 01\n",
        "t5": bytes.fromhex("6789638906896389068c"),
    },
}


class PairCohort(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        table = module.load_foundation(ARGS["foundation"])
        cls.legacy, cls.my, cls.upper = module.build_three_pass_maps(
            table,
            ARGS["domain_surfaces"],
            ARGS["semantic_generated"],
            ARGS["semantic_registry"],
            ARGS["necessary_forms"],
            ARGS["historical_map"],
        )
        cls.text7 = module.build_text7(table, ARGS["text7"])

    def project(self, source: str):
        resolver = module.Resolver(self.legacy, self.my, self.upper, source_era="legacy")
        return module.migrate_file(source, resolver, self.text7), resolver.counts

    def test_pinned_legacy_car_cdr_cons_successors_are_proven(self):
        self.assertEqual(self.legacy["00000100"][:2], ("111", "D3"))
        self.assertEqual(self.legacy["00000101"][:2], ("100", "D3"))
        self.assertEqual(self.legacy["00000110"][:2], ("011", "D3"))
        self.assertEqual(self.legacy["00000001"][:2], ("001", "D3"))

    def test_actual_three_pass_projection_and_physical_bytes(self):
        for stem, case in CASES.items():
            with self.subTest(stem=stem):
                source = (FIXTURES / f"{stem}.lisp").read_text(encoding="utf-8")
                projection, counts = self.project(source)
                self.assertEqual(projection, case["words"])
                self.assertEqual((FIXTURES / stem).read_text(encoding="ascii"), case["words"])
                self.assertEqual((FIXTURES / f"{stem}.sens").read_bytes(), case["t5"])
                self.assertEqual(counts["pass1-sens8"], 3)
                with tempfile.TemporaryDirectory() as directory:
                    out = Path(directory) / "out"
                    report = Path(directory) / "report.json"
                    command = [
                        sys.executable, str(SCRIPT), str(FIXTURES), "--out", str(out),
                        *[item for key, path in ARGS.items() for item in ("--" + key.replace("_", "-"), str(path))],
                        "--source-era", "legacy",  # Explicit historical W8 provenance.
                        "--report", str(report),
                    ]
                    result = subprocess.run(command, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                    emitted = out / f"{stem}.sens"
                    self.assertEqual(emitted.read_bytes(), case["t5"])
                    self.assertEqual(module.decode_bytes(case["t5"]), case["words"].split())

    def test_ambiguous_historical_w8_does_not_migrate_in_auto_mode(self):
        resolver = module.Resolver(self.legacy, self.my, self.upper, source_era="auto")
        with self.assertRaises(module.MigrationError):
            module.migrate_file(CASES["pair-cons"]["source"], resolver, self.text7)

    def test_existing_lisp_provenance_is_preserved_and_corruption_fails_closed(self):
        for stem, case in CASES.items():
            with self.subTest(stem=stem):
                self.assertTrue((FIXTURES / f"{stem}.lisp").is_file())
                with self.assertRaises(module.SensT5Error):
                    module.decode_bytes(case["t5"] + b"\xf2")
                with self.assertRaises(module.SensT5Error):
                    module.encode_projection(" ".join(["x", *case["words"].split()[1:]]))


if __name__ == "__main__":
    unittest.main()
