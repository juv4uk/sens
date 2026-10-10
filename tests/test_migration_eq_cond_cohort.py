#!/usr/bin/env python3
"""#4455: EQ/COND historical source -> exact D1/D3 -> physical T5."""
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
FIXTURES = ROOT / "tests/fixtures/migration-eq-cond-cohort"

SPEC = importlib.util.spec_from_file_location("migration_eq_cond_cohort", SCRIPT)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)

FLAGS = {
    "foundation": "knowledge/d1-d9-foundation.json",
    "domain-surfaces": "crates/sens/src/domain_surface_registry_generated.rs",
    "semantic-generated": "crates/sens/src/semantic_registry_generated.rs",
    "semantic-registry": "crates/sens/src/semantic_registry.rs",
    "necessary-forms": "crates/sens/src/eval/necessary_forms_generated.rs",
    "historical-map": "contracts/core1-historical-sid-map.lisp",
    "text7": "crates/sens/src/text7_projection_generated.rs",
}

ROWS = {
    "eq-cond-select": {
        "source": "(00000111\n  ((00000011 (00000001 1) (00000001 1))\n   (00000001 (())))\n  ((00000011 (00000001 0) (00000001 1))\n   (00000001 ())))\n",
        "projection": "10 110 00 10 10 101 00 10 001 00 1 01 00 10 001 00 1 01 01 00 10 001 00 10 000 01 01 01 00 10 10 101 00 10 001 00 0 01 00 10 001 00 1 01 01 00 10 001 00 000 01 01 01",
        "hex": "673866c215a7172dc32dd0b1410f41068c2dc440a937a8b1410f458c15a7123b2e",
    },
    "eq-cond-skip": {
        "source": "(00000111\n  ((00000011 (00000001 0) (00000001 1))\n   (00000001 (())))\n  ((00000011 (00000001 1) (00000001 1))\n   (00000001 ())))\n",
        "projection": "10 110 00 10 10 101 00 10 001 00 0 01 00 10 001 00 1 01 01 00 10 001 00 10 000 01 01 01 00 10 10 101 00 10 001 00 1 01 00 10 001 00 1 01 01 00 10 001 00 000 01 01 01",
        "hex": "673866c215a7142dc32dd0b1410f41068c2dc440a937a9b1410f458c15a7123b2e",
    },
}


class EqCondCohort(unittest.TestCase):
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

    def test_historical_heads_have_proven_current_d3_successors(self):
        for old, current in {
            "00000001": "001",  # QUOTE
            "00000011": "101",  # EQ
            "00000111": "110",  # COND
        }.items():
            with self.subTest(old=old):
                self.assertEqual(self.legacy[old][:2], (current, "D3"))

    def test_d1_atoms_are_data_not_numbers_or_d2(self):
        # Under QUOTE, exact one-bit 0/1 stay D1 atoms. This cohort deliberately
        # avoids Number/D24+ and Text7 migration questions.
        for atom in ("0", "1"):
            self.assertEqual(M.encode_atom_data(M.Atom(M.Tok("ATOM", atom, 0)), self.text7), [atom])

    def test_sources_project_to_exact_words_and_physical_t5(self):
        for stem, row in ROWS.items():
            with self.subTest(stem=stem):
                source = FIXTURES / f"{stem}.lisp"
                physical = FIXTURES / f"{stem}.sens"
                self.assertEqual(source.read_text(encoding="utf-8"), row["source"])

                resolver = M.Resolver(self.legacy, self.my, self.upper, source_era="legacy")
                projection = M.migrate_file(row["source"], resolver, self.text7).strip()
                self.assertEqual(projection, row["projection"])
                self.assertEqual(resolver.counts["pass1-sens8"], 9)

                expected = bytes.fromhex(row["hex"])
                self.assertEqual(physical.read_bytes(), expected)
                self.assertEqual(M.encode_projection(projection), expected)
                self.assertEqual(M.decode_bytes(expected), projection.split())
                self.assertEqual((FIXTURES / stem).read_text(encoding="ascii"), projection + "\n")
                self.assertEqual(
                    M.typed_sha256(M.decode_bytes(expected)),
                    M.typed_sha256(projection.split()),
                )
                self.assertNotEqual(expected, projection.encode("ascii"))

    def test_actual_three_pass_migrator_emits_same_stem_binary_only(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "out"
            report = Path(directory) / "report.json"
            cmd = [
                sys.executable,
                str(SCRIPT),
                str(FIXTURES),
                "--out",
                str(out),
                *[
                    item
                    for flag, file in FLAGS.items()
                    for item in ("--" + flag, str(ROOT / file))
                ],
                "--source-era",
                "legacy",  # Input fixtures intentionally use provenance-pinned SID8 W8 heads.
                "--report",
                str(report),
            ]
            process = subprocess.run(cmd, text=True, capture_output=True)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)

            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["summary"]["files_seen"], 2)
            self.assertEqual(data["summary"]["files_written"], 2)
            self.assertEqual(data["summary"]["files_blocked"], 0)
            self.assertEqual({row["semantic_word_count"] for row in data["files"]}, {53})
            self.assertEqual({row["bytes"] for row in data["files"]}, {33})

            for stem, row in ROWS.items():
                self.assertEqual(
                    (out / f"{stem}.sens").read_bytes(),
                    bytes.fromhex(row["hex"]),
                )
                self.assertFalse((out / stem).exists())
                self.assertFalse((out / f"{stem}.lisp").exists())
                self.assertTrue((FIXTURES / f"{stem}.lisp").is_file())

            again = subprocess.run(cmd, text=True, capture_output=True)
            self.assertEqual(again.returncode, 2)

    def test_unknown_sid_and_corrupt_transport_fail_closed(self):
        resolver = M.Resolver(self.legacy, self.my, self.upper, source_era="legacy")
        with self.assertRaises(M.MigrationError):
            M.migrate_file("(11111111 ())\n", resolver, self.text7)

        payload = (FIXTURES / "eq-cond-select.sens").read_bytes()
        with self.assertRaises(M.SensT5Error):
            M.decode_bytes(payload + bytes([242]))
        with self.assertRaises(M.SensT5Error):
            M.decode_bytes(bytes([243]))
        with self.assertRaises(M.SensT5Error):
            M.encode_projection("(00000111 ())")


if __name__ == "__main__":
    unittest.main()
