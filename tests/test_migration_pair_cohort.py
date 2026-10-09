#!/usr/bin/env python3
"""#4455: трипрохідне переведення CAR/CDR/CONS із фізичним T5."""
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
FIXTURES = ROOT / "tests/fixtures/migration-pair-cohort"
SPEC = importlib.util.spec_from_file_location("migration_pair_cohort", SCRIPT)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)

FLAGS = {
    "foundation": "knowledge/d1-d7-foundation.json",
    "domain-surfaces": "crates/sens/src/domain_surface_registry_generated.rs",
    "semantic-generated": "crates/sens/src/semantic_registry_generated.rs",
    "semantic-registry": "crates/sens/src/semantic_registry.rs",
    "necessary-forms": "crates/sens/src/eval/necessary_forms_generated.rs",
    "historical-map": "contracts/core1-historical-sid-map.lisp",
    "text7": "crates/sens/src/text7_projection_generated.rs",
}
# Авторитет бітів — таблиці/мапи SENS; ці значення є контролями регресії.
ROWS = {
    "car-head": {
        "source": "(00000101 (00000100 (00000001 ()) (00000001 (()))))\n",
        "projection": "10 100 00 10 111 00 10 001 00 000 01 00 10 001 00 10 000 01 01 01 01",
        "hex": "66386789638906896389633b2eb3",
        "head": "100",
    },
    "cdr-tail": {
        "source": "(00000110 (00000100 (00000001 ()) (00000001 (()))))\n",
        "projection": "10 011 00 10 111 00 10 001 00 000 01 00 10 001 00 10 000 01 01 01 01",
        "hex": "64896789638906896389633b2eb3",
        "head": "011",
    },
}


class PairCohort(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        foundation = M.load_foundation(ROOT / FLAGS["foundation"])
        cls.legacy, cls.my, cls.upper = M.build_three_pass_maps(
            foundation,
            ROOT / FLAGS["domain-surfaces"],
            ROOT / FLAGS["semantic-generated"],
            ROOT / FLAGS["semantic-registry"],
            ROOT / FLAGS["necessary-forms"],
            ROOT / FLAGS["historical-map"],
        )
        cls.text7 = M.build_text7(foundation, ROOT / FLAGS["text7"])

    def test_historical_code_roles_are_proven_by_existing_resolver(self):
        for old, current in {
            "00000001": "001",  # QUOTE
            "00000100": "111",  # CONS
            "00000101": "100",  # CAR
            "00000110": "011",  # CDR
        }.items():
            with self.subTest(old=old):
                self.assertEqual(self.legacy[old][:2], (current, "D3"))

    def test_source_to_physical_t5_roundtrip_for_both_selectors(self):
        for stem, row in ROWS.items():
            with self.subTest(stem=stem):
                source_path = FIXTURES / (stem + ".lisp")
                target = FIXTURES / (stem + ".sens")
                self.assertEqual(source_path.read_text(encoding="utf-8"), row["source"])
                resolver = M.Resolver(self.legacy, self.my, self.upper)
                projection = M.migrate_file(row["source"], resolver, self.text7).strip()
                self.assertEqual(projection, row["projection"])
                self.assertEqual(projection.split()[1], row["head"])
                self.assertEqual(resolver.counts["pass1-sens8"], 4)
                expected = bytes.fromhex(row["hex"])
                self.assertEqual(target.read_bytes(), expected)
                self.assertEqual(M.encode_projection(projection), expected)
                self.assertEqual(M.decode_bytes(expected), projection.split())
                self.assertEqual(M.typed_sha256(M.decode_bytes(expected)),
                                 M.typed_sha256(projection.split()))
                self.assertNotEqual(expected, projection.encode("ascii"))

    def test_actual_three_pass_command_uses_same_stem_and_preserves_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "out"
            report = Path(directory) / "report.json"
            cmd = [
                sys.executable, str(SCRIPT), str(FIXTURES),
                "--out", str(out),
                *[s for flag, file in FLAGS.items() for s in ("--" + flag, str(ROOT / file))],
                "--report", str(report),
            ]
            process = subprocess.run(cmd, text=True, capture_output=True)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["summary"]["files_seen"], 2)
            self.assertEqual(data["summary"]["files_written"], 2)
            self.assertEqual(data["summary"]["files_blocked"], 0)
            for stem, row in ROWS.items():
                self.assertEqual((out / (stem + ".sens")).read_bytes(),
                                 bytes.fromhex(row["hex"]))
                self.assertFalse((out / stem).exists())
                self.assertTrue((FIXTURES / (stem + ".lisp")).is_file())
            self.assertEqual({r["semantic_word_count"] for r in data["files"]}, {21})
            self.assertEqual({r["bytes"] for r in data["files"]}, {14})
            # Повторно — тільки BLOCK, ніколи не перезаписувати.
            again = subprocess.run(cmd, text=True, capture_output=True)
            self.assertEqual(again.returncode, 2)
            for stem, row in ROWS.items():
                self.assertEqual((out / (stem + ".sens")).read_bytes(),
                                 bytes.fromhex(row["hex"]))

    def test_invalid_wire_or_unproven_function_is_blocked(self):
        payload = (FIXTURES / "car-head.sens").read_bytes()
        for corrupted in ([243], list(payload) + [242]):
            with self.subTest(corrupted=corrupted):
                with self.assertRaises(M.SensT5Error):
                    M.decode_bytes(bytes(corrupted))
        resolver = M.Resolver(self.legacy, self.my, self.upper)
        with self.assertRaises(M.MigrationError):
            M.migrate_file("(11111111 ())\n", resolver, self.text7)
        with self.assertRaises(M.SensT5Error):
            M.encode_projection("10 111 00 text 01")


if __name__ == "__main__":
    unittest.main()
