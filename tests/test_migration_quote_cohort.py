#!/usr/bin/env python3
"""Міграція одного наявного історичного виклику QUOTE через всі три проєкції."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SCRIPT = SCRIPTS / "migrate-three-pass.py"
FIXTURES = ROOT / "tests" / "fixtures" / "migration-quote-cohort"
LEGACY_SOURCE = FIXTURES / "quote-legacy.lisp"
PHYSICAL = FIXTURES / "quote-legacy.sens"
EXPECTED = "10 001 00 000 01\n"
COHORT = (
    ("quote-legacy.lisp", "quote-legacy.sens", "(00000001 ())\n", "pass1-sens8"),
    ("quote-mylisp.lisp", "quote-mylisp.sens", "(quote ())\n", "pass2-my-lisp"),
    ("quote-lisp15.lisp", "quote-lisp15.sens", "(QUOTE ())\n", "pass3-lisp15"),
)

spec = importlib.util.spec_from_file_location("migration_quote_three_pass", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

ARGS = {
    "foundation": ROOT / "knowledge/d1-d7-foundation.json",
    "domain_surfaces": ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
    "semantic_generated": ROOT / "crates/sens/src/semantic_registry_generated.rs",
    "semantic_registry": ROOT / "crates/sens/src/semantic_registry.rs",
    "necessary_forms": ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
    "historical_map": ROOT / "contracts/core1-historical-sid-map.lisp",
    "text7": ROOT / "crates/sens/src/text7_projection_generated.rs",
}


class QuoteCohort(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        table = module.load_foundation(ARGS["foundation"])
        cls.legacy, cls.my, cls.upper = module.build_three_pass_maps(
            table, ARGS["domain_surfaces"], ARGS["semantic_generated"],
            ARGS["semantic_registry"], ARGS["necessary_forms"], ARGS["historical_map"]
        )
        cls.text7 = module.build_text7(table, ARGS["text7"])

    def project(self, source):
        resolver = module.Resolver(self.legacy, self.my, self.upper)
        result = module.migrate_file(source, resolver, self.text7)
        return result, resolver.counts

    def test_pinned_historical_quote_is_d3_not_atom(self):
        # Историчне 00000001 = QUOTE; 00000010 = ATOM.
        mapped = self.legacy["00000001"]
        self.assertEqual(mapped[:2], ("001", "D3"))
        self.assertNotEqual(self.legacy["00000010"][:2], mapped[:2])

    def test_one_real_lisp_source_has_one_physical_same_stem_companion(self):
        self.assertEqual(LEGACY_SOURCE.read_text(encoding="utf-8"), "(00000001 ())\n")
        projection, counts = self.project(LEGACY_SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(projection, EXPECTED)
        self.assertEqual(counts["pass1-sens8"], 1)
        payload = PHYSICAL.read_bytes()
        self.assertEqual(payload, b"\x63\x89\x06\xa1")
        self.assertNotEqual(payload, projection.encode("ascii"))
        self.assertEqual(module.encode_projection(projection), payload)
        self.assertEqual(module.decode_bytes(payload), EXPECTED.split())
        self.assertEqual(module.typed_sha256(module.decode_bytes(payload)),
                         module.typed_sha256(EXPECTED.split()))

    def test_three_historical_source_spellings_project_identically(self):
        for _, _, source, phase in COHORT:
            with self.subTest(source=source):
                projection, counts = self.project(source)
                self.assertEqual(projection, EXPECTED)
                self.assertEqual(counts[phase], 1)
                self.assertEqual(module.encode_projection(projection), PHYSICAL.read_bytes())

    def test_three_real_sources_have_physical_same_stem_companions(self):
        for source_name, binary_name, source_text, phase in COHORT:
            with self.subTest(source_name=source_name):
                source = FIXTURES / source_name
                physical = FIXTURES / binary_name
                self.assertEqual(source.read_text(encoding="utf-8"), source_text)
                projection, counts = self.project(source_text)
                self.assertEqual(projection, EXPECTED)
                self.assertEqual(counts[phase], 1)
                self.assertEqual(physical.read_bytes(), bytes.fromhex("638906a1"))
                self.assertEqual(module.encode_projection(projection), physical.read_bytes())
                self.assertEqual(module.decode_bytes(physical.read_bytes()), EXPECTED.split())

    def test_actual_migrator_creates_physical_artifact_and_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out = root / "output"
            report = root / "report.json"
            command = [
                sys.executable, str(SCRIPT), str(FIXTURES), "--out", str(out),
                *[item for key, path in ARGS.items() for item in ("--" + key.replace("_", "-"), str(path))],
                "--report", str(report),
            ]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            emitted = out / "quote-legacy.sens"
            self.assertEqual(emitted.read_bytes(), PHYSICAL.read_bytes())
            self.assertFalse((out / "quote-legacy").exists())
            self.assertFalse((out / "quote-legacy.lisp").exists())
            rows = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(rows["summary"]["files_seen"], 3)
            self.assertEqual(rows["summary"]["files_written"], 3)
            self.assertEqual(rows["summary"]["files_blocked"], 0)
            self.assertEqual({row["path"] for row in rows["files"]}, {name for name, _, _, _ in COHORT})
            self.assertTrue(all(row["semantic_word_count"] == 5 for row in rows["files"]))
            self.assertTrue(all(row["bytes"] == 4 for row in rows["files"]))
            self.assertTrue(LEGACY_SOURCE.is_file(), "historical source preserved")
            # На повторному запуску не можна перезаписати готовий файл.
            again = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(again.returncode, 2)
            self.assertEqual(emitted.read_bytes(), PHYSICAL.read_bytes())

    def test_corrupt_transport_never_becomes_an_executable_program(self):
        with self.assertRaises(module.SensT5Error):
            module.decode_bytes(PHYSICAL.read_bytes() + b"\xf2")
        with self.assertRaises(module.SensT5Error):
            module.decode_bytes(bytes([243]))
        with self.assertRaises(module.SensT5Error):
            module.encode_projection("10 001 00 text 01")


if __name__ == "__main__":
    unittest.main()
