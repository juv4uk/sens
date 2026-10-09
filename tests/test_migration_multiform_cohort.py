#!/usr/bin/env python3
"""#4455: two historical programs in one real packed same-stem T5 file."""
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
COHORT = ROOT / "tests/fixtures/migration-multiform-cohort"
SOURCE = COHORT / "two-forms.lisp"
PHYSICAL = COHORT / "two-forms.sens"
SOURCE_TEXT = "(00000001 ())\n(00000100 (00000001 ()) (00000001 ()))\n"
WORDS = "10 001 00 000 01 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01"
BYTES = bytes.fromhex("63 89 06 89 67 89 63 89 06 89 63 89 06 8c")

ARGS = {
    "foundation": ROOT / "knowledge/d1-d7-foundation.json",
    "domain_surfaces": ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
    "semantic_generated": ROOT / "crates/sens/src/semantic_registry_generated.rs",
    "semantic_registry": ROOT / "crates/sens/src/semantic_registry.rs",
    "necessary_forms": ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
    "historical_map": ROOT / "contracts/core1-historical-sid-map.lisp",
    "text7": ROOT / "crates/sens/src/text7_projection_generated.rs",
}
spec = importlib.util.spec_from_file_location("multiform_migrator", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class PhysicalMultiformMigration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        foundation = module.load_foundation(ARGS["foundation"])
        cls.legacy, cls.my, cls.upper = module.build_three_pass_maps(
            foundation, ARGS["domain_surfaces"], ARGS["semantic_generated"],
            ARGS["semantic_registry"], ARGS["necessary_forms"], ARGS["historical_map"],
        )
        cls.text7 = module.build_text7(foundation, ARGS["text7"])

    def test_actual_three_pass_produces_one_two_program_t5_file(self):
        self.assertEqual(SOURCE.read_text(encoding="utf-8"), SOURCE_TEXT)
        self.assertEqual(self.legacy["00000001"][:2], ("001", "D3"))
        self.assertEqual(self.legacy["00000100"][:2], ("111", "D3"))
        resolver = module.Resolver(self.legacy, self.my, self.upper, source_era="legacy")
        projection = module.migrate_file(SOURCE_TEXT, resolver, self.text7)
        self.assertEqual(projection, WORDS + "\n")
        self.assertEqual(resolver.counts["pass1-sens8"], 4)
        self.assertEqual(projection.split()[5], "00", "D2 inter-form separator")
        self.assertEqual(PHYSICAL.read_bytes(), BYTES)
        self.assertEqual(module.encode_projection(projection), PHYSICAL.read_bytes())
        self.assertEqual(module.decode_bytes(BYTES), WORDS.split())
        self.assertEqual(
            module.typed_sha256(module.decode_bytes(BYTES)),
            module.typed_sha256(WORDS.split()),
        )

    def test_real_cli_preserves_source_and_does_not_publish_extensionless(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            target = work / "out"
            report = work / "report.json"
            command = [
                sys.executable, str(SCRIPT), str(COHORT), "--out", str(target),
                *[item for key, value in ARGS.items()
                  for item in ("--" + key.replace("_", "-"), str(value))],
                "--report", str(report),
                # This exact fixture predates D8 and preserves old SID8 heads.
                "--source-era", "legacy",
            ]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            self.assertEqual((target / "two-forms.sens").read_bytes(), BYTES)
            self.assertFalse((target / "two-forms").exists())
            self.assertFalse((target / "two-forms.lisp").exists())
            self.assertEqual(SOURCE.read_text(encoding="utf-8"), SOURCE_TEXT)
            record = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(record["source_era"], "legacy")
            self.assertEqual(record["summary"]["files_seen"], 1)
            self.assertEqual(record["summary"]["files_written"], 1)
            self.assertEqual(record["summary"]["files_blocked"], 0)
            self.assertEqual(record["files"][0]["semantic_word_count"], 21)
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2, second.stderr + second.stdout)
            self.assertEqual((target / "two-forms.sens").read_bytes(), BYTES)

    def test_corrupt_transport_and_unproven_head_fail_closed(self):
        with self.assertRaises(module.SensT5Error):
            module.decode_bytes(BYTES + bytes([242]))
        with self.assertRaises(module.SensT5Error):
            module.decode_bytes(bytes([243]))
        resolver = module.Resolver(self.legacy, self.my, self.upper, source_era="legacy")
        with self.assertRaises(module.MigrationError):
            module.migrate_file("(11111111 ())", resolver, self.text7)


if __name__ == "__main__":
    unittest.main()
