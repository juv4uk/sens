#!/usr/bin/env python3
import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "knowledge/migration-d2-as-data-census-2026-10-08.json"

def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

class D2AsDataCensus(unittest.TestCase):
    def test_exact_scan_cohort_remains_blocked(self):
        data = json.loads(LEDGER.read_text())
        self.assertEqual(data["schema"], "sens-d2-as-data-census/1")
        self.assertEqual(data["source_scan"]["workflow_run"], 37810152645)
        self.assertEqual(len(data["entries"]), 9)
        for entry in data["entries"]:
            self.assertEqual(entry["status"], "BLOCKED")
            self.assertIn("D2 word", entry["reason"])
            source = ROOT / entry["path"]
            self.assertTrue(source.is_file(), entry["path"])
            self.assertEqual(git_blob_sha1(source.read_bytes()), entry["git_blob_sha1"])
            self.assertFalse(
                source.with_suffix(".sens").exists(),
                f"{entry['path']}: D2-as-data blocker must not auto-publish .sens",
            )

    def test_isa_subset_routes_to_nonprogram_classification(self):
        data = json.loads(LEDGER.read_text())
        isa = [e for e in data["entries"] if e["path"].startswith("lib/machine/isa/")]
        self.assertEqual(len(isa), 4)
        self.assertTrue(all(e["route"] == "nonprogram-isa-catalogue" for e in isa))

    def test_d2_authority_file_is_not_treated_as_executable_program(self):
        data = json.loads(LEDGER.read_text())
        d2 = next(e for e in data["entries"] if e["path"] == "lib/domains/d2.lisp")
        self.assertEqual(d2["route"], "d2-authority-table-nonprogram")
        self.assertIn("executable head", d2["reason"])

if __name__ == "__main__":
    unittest.main()
