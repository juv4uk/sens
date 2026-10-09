#!/usr/bin/env python3
"""#4455: real current D1/COND source -> canonical T5, no legacy truthiness."""
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
FIXTURES = ROOT / "tests/fixtures/migration-d1-cond-cohort"
READABLE = FIXTURES / "branch.lisp"
BINARY = FIXTURES / "branch.sens"
VIEW = FIXTURES / "branch"
SOURCE = "(за-умовою (ні (перше ())) (так так))\n"
WORDS = "10 110 00 10 0 00 10 100 00 000 01 01 00 10 1 00 1 01 01"
BYTES = bytes.fromhex("67386515bf123b2dc4a9b1a1")
ARGS = {
    "foundation": ROOT / "knowledge/d1-d7-foundation.json",
    "domain_surfaces": ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
    "semantic_generated": ROOT / "crates/sens/src/semantic_registry_generated.rs",
    "semantic_registry": ROOT / "crates/sens/src/semantic_registry.rs",
    "necessary_forms": ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
    "historical_map": ROOT / "contracts/core1-historical-sid-map.lisp",
    "text7": ROOT / "crates/sens/src/text7_projection_generated.rs",
}
spec = importlib.util.spec_from_file_location("migration_d1_cond_three_pass", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class D1CondPhysicalCohort(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        table = module.load_foundation(ARGS["foundation"])
        cls.legacy, cls.my, cls.upper = module.build_three_pass_maps(
            table, ARGS["domain_surfaces"], ARGS["semantic_generated"],
            ARGS["semantic_registry"], ARGS["necessary_forms"], ARGS["historical_map"]
        )
        cls.text7 = module.build_text7(table, ARGS["text7"])

    def project(self, source: str):
        resolver = module.Resolver(self.legacy, self.my, self.upper)
        result = module.migrate_file(source, resolver, self.text7)
        return result, resolver.counts

    def test_ukrainian_d1_cond_source_has_binary_same_stem(self):
        self.assertEqual(READABLE.read_text(encoding="utf-8"), SOURCE)
        projection, counts = self.project(SOURCE)
        self.assertEqual(projection, WORDS + "\n")
        self.assertEqual(counts["already-exact"], 0)
        self.assertEqual(counts["pass2-my-lisp"], 2)  # D3 Ukrainian COND and CAR
        self.assertEqual(module.load_d1_uk_surfaces(), {"ні": "0", "так": "1"})
        self.assertEqual(module.D1_UK_SURFACES["так"], "1")
        self.assertEqual(counts["pass1-sens8"], 0)
        self.assertEqual(counts["pass3-lisp15"], 0)
        self.assertEqual(BINARY.read_bytes(), BYTES)
        self.assertNotEqual(BINARY.read_bytes(), projection.encode("ascii"))
        self.assertEqual(module.encode_projection(projection), BYTES)
        self.assertEqual(module.decode_bytes(BYTES), WORDS.split())
        self.assertEqual(module.typed_sha256(WORDS.split()),
                         module.typed_sha256(module.decode_bytes(BYTES)))
        self.assertEqual(len(BYTES), 12)
        self.assertEqual(VIEW.read_bytes(), (WORDS + "\n").encode("ascii"))
        self.assertEqual(module.decode_bytes(BINARY.read_bytes()), VIEW.read_text(encoding="ascii").split())
        self.assertEqual(module.encode_projection(VIEW.read_text(encoding="ascii")), BINARY.read_bytes())

    def test_existing_three_pass_cli_proves_safe_physical_output(self):
        with tempfile.TemporaryDirectory(prefix="sens-d1-cond-") as directory:
            root = Path(directory)
            out = root / "output"
            report = root / "report.json"
            command = [
                sys.executable, str(SCRIPT), str(FIXTURES), "--out", str(out),
                *[item for key, value in ARGS.items()
                  for item in ("--" + key.replace("_", "-"), str(value))],
                "--report", str(report),
            ]
            run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=90)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            self.assertEqual((out / "branch.sens").read_bytes(), BYTES)
            self.assertFalse((out / "branch.lisp").exists())
            self.assertFalse((out / "branch").exists())
            record = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(record["schema"], "sens-three-pass-t5-migration/v3")
            self.assertEqual(record["summary"]["files_seen"], 1)
            self.assertEqual(record["summary"]["files_written"], 1)
            self.assertEqual(record["summary"]["files_blocked"], 0)
            entry = record["files"][0]
            self.assertEqual(entry["path"], "branch.lisp")
            self.assertEqual(entry["output"], "branch.sens")
            self.assertEqual(entry["semantic_word_count"], len(WORDS.split()))
            self.assertEqual(entry["bytes"], len(BYTES))
            self.assertEqual(entry["typed_word_sha256"], module.typed_sha256(WORDS.split()))
            self.assertEqual(READABLE.read_text(encoding="utf-8"), SOURCE)
            retry = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=90)
            self.assertEqual(retry.returncode, 2)
            self.assertEqual((out / "branch.sens").read_bytes(), BYTES)

    def test_legacy_truthiness_and_bad_transport_not_silently_admitted(self):
        # D2:10 in data position cannot become predicate control.
        with self.assertRaises(module.MigrationError):
            self.project("(110 (10 1))\n")
        for malformed in (BYTES + bytes([242]), bytes([243])):
            with self.subTest(malformed=malformed.hex()):
                with self.assertRaises(module.SensT5Error):
                    module.decode_bytes(malformed)
        with self.assertRaises(module.SensT5Error):
            module.encode_projection("10 110 00 historical-truth 01")


if __name__ == "__main__":
    unittest.main()
