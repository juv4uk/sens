#!/usr/bin/env python3
"""Historical Core1 resolver: exact SHA, real canonical no-write frontier."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "scripts/audit_core1_original_candidate.py"
spec = importlib.util.spec_from_file_location("core1_original_frontier", P)
assert spec and spec.loader
frontier = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = frontier
spec.loader.exec_module(frontier)


class Core1OriginalFrontierTests(unittest.TestCase):
    def test_existing_real_historical_source_is_exact_git_blob(self):
        self.assertEqual(frontier.git_source_sha(ROOT), frontier.SOURCE_GIT_BLOB)
        self.assertEqual((ROOT / frontier.SOURCE).stat().st_size, 638)
        self.assertFalse((ROOT / frontier.SOURCE.with_suffix(".sens")).exists())

    def test_first_blocker_is_reproducible_without_publishing_any_sens(self):
        source = ROOT / frontier.SOURCE
        old = source.read_bytes()
        result = frontier.audit(ROOT)
        self.assertEqual(result["status"], "RESEARCH_FRONTIER_NOT_SEMANTIC_ADMISSION")
        self.assertEqual(result["historical_original_git_blob_sha1"], frontier.SOURCE_GIT_BLOB)
        self.assertEqual(result["historical_oracle"]["expected_observations"], 11)
        self.assertFalse(result["historical_oracle"]["replayed_here"])
        self.assertEqual([p["source_era"] for p in result["canonical_no_write_probes"]],
                         ["auto", "legacy"])
        for row in result["canonical_no_write_probes"]:
            self.assertIn(row["classification"],
                          ("BLOCKED_WITH_REASON", "MECHANICAL_ONLY_NOT_ADMITTED"))
            self.assertEqual(row["published_physical_bytes"], 0)
            self.assertFalse(row["historical_executable_admitted"])
            if row["classification"] == "BLOCKED_WITH_REASON":
                self.assertTrue(row["first_blocker"])
        self.assertEqual(result["new_historically_certified_executables"], 0)
        self.assertEqual(result["new_physical_sens_files"], 0)
        self.assertEqual(result["d10_residents_added"], 0)
        self.assertEqual(source.read_bytes(), old)
        self.assertFalse(source.with_suffix(".sens").exists())

    def test_modified_historical_source_cannot_be_silently_accepted(self):
        with tempfile.TemporaryDirectory(prefix="core1-original-mutation-") as td:
            temp = Path(td)
            target = temp / frontier.SOURCE
            target.parent.mkdir(parents=True)
            target.write_bytes((ROOT / frontier.SOURCE).read_bytes() + b"\n; forged\n")
            with self.assertRaisesRegex(frontier.FrontierBlocked, "PROVENANCE"):
                frontier.audit(temp)

    def test_existing_physical_partner_must_not_be_overwritten_or_counted(self):
        with tempfile.TemporaryDirectory(prefix="core1-original-pair-") as td:
            temp = Path(td)
            source = temp / frontier.SOURCE
            source.parent.mkdir(parents=True)
            source.write_bytes((ROOT / frontier.SOURCE).read_bytes())
            source.with_suffix(".sens").write_bytes(b"not trusted physical bytes")
            with self.assertRaisesRegex(frontier.FrontierBlocked, "already exists"):
                frontier.audit(temp)
            self.assertEqual(source.with_suffix(".sens").read_bytes(),
                             b"not trusted physical bytes")

    def test_no_local_hidden_semantic_slot_published(self):
        receipt = frontier.audit(ROOT)
        self.assertTrue(receipt["d10_is_not_a_transport_workaround"])
        self.assertEqual(receipt["current_physical_11_observables"], "NOT_VERIFIED")
        self.assertIn("11/11", receipt["next_admission_requires"])


if __name__ == "__main__":
    unittest.main()
