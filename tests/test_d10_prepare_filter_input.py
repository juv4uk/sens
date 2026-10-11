"""Regressions for the unified D10 index -> mechanical filter adapter."""
import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import d10_prepare_filter_input as adapter
import d10_mechanical_filter as sieve


class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        folder = self.root / "knowledge/d10-filter"
        folder.mkdir(parents=True)
        self.donor = self.root / "knowledge/donor.json"
        self.donor.write_text('{\n"candidates": [{"semantic_name": "NEW-LAW"}]\n}\n')
        self.pin = sieve.git_blob(self.donor.read_bytes())
        self.inv = {"width": 10, "capacity": 1024, "rows": [
            {"stable_id": "d10.selected", "semantic_name": "OLD-LAW",
             "coordinate": "0000000000", "behavior": "old law"}]}
        self.invpath = self.root / "knowledge/v7.json"
        self.invpath.write_text(json.dumps(self.inv, indent=2))
        self.inv_sha = sieve.git_blob(self.invpath.read_bytes())
        ptr = {"canonical_current": {"path": "knowledge/v7.json",
                                     "git_blob": self.inv_sha, "selected": 1}}
        (self.root / "knowledge/d10-current-inventory.json").write_text(json.dumps(ptr))
        (self.root / "knowledge/d1-d9-foundation.json").write_text("{}")
        self.input = folder / "all-candidates.tsv"
        self.output = folder / "filter-input.tsv"
        self.row = {k: "" for k in adapter.INDEX_FIELDS}
        self.row.update(candidate_id="d10.new", semantic_name="NEW-LAW", ratified="0",
                        semantic_law_variants='["independent new law"]',
                        source_records_sha_pinned=json.dumps(
                            [f"knowledge/donor.json@{self.pin}:candidates[0]"]))
        for field in ("provisional_coordinate_claims", "donor_provenance_claims",
                      "positive_witness_claims", "falsifier_claims",
                      "historical_status_claims"):
            self.row[field] = "[]"
        self.write_index()

    def write_index(self, extra=()):
        with self.input.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=adapter.INDEX_FIELDS,
                                    delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerow(self.row)
            writer.writerows(extra)

    def read_prepared(self):
        with self.output.open(encoding="utf-8", newline="") as stream:
            return list(csv.DictReader(stream, delimiter="\t"))

    def test_pinned_source_and_lagging_canonical_overlay(self):
        counts = adapter.prepare(self.root, self.input, self.output)
        self.assertEqual(1, counts["new_selected_since_index"])
        self.assertEqual(2, counts["filter_input_rows"])
        rows = {row["candidate_id"]: row for row in self.read_prepared()}
        self.assertEqual("knowledge/donor.json:2", rows["d10.new"]["donor_provenance"])
        self.assertEqual(self.pin, rows["d10.new"]["source_pin"])
        self.assertEqual("", rows["d10.new"]["witness_verdict"])
        self.assertEqual("", rows["d10.new"]["semantic_dedup_certificate"])
        self.assertEqual("d10.selected", rows["d10.selected"]["candidate_id"])
        _, _, occupied = sieve.load_baseline(self.root)
        decision = sieve.evaluate(rows["d10.new"], self.root, self.inv_sha,
                                  sieve.git_blob((self.root / "knowledge/d1-d9-foundation.json").read_bytes()),
                                  occupied)
        self.assertEqual("EXCLUDE_NO_WITNESS", decision["reason"])

    def test_fake_source_sha_cannot_be_accepted(self):
        self.row["source_records_sha_pinned"] = json.dumps(
            ["knowledge/donor.json@" + "0"*40 + ":candidates[0]"])
        self.write_index()
        adapter.prepare(self.root, self.input, self.output)
        rows = {r["candidate_id"]: r for r in self.read_prepared()}
        self.assertEqual("", rows["d10.new"]["source_pin"])

    def test_duplicate_candidate_is_fail_closed(self):
        self.write_index([dict(self.row)])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_EMPTY"):
            adapter.prepare(self.root, self.input, self.output)

    def test_bad_canonical_pointer_is_fail_closed(self):
        self.invpath.write_text("{}")
        with self.assertRaisesRegex(ValueError, "POINTER_SHA_MISMATCH"):
            adapter.prepare(self.root, self.input, self.output)

    def test_unratified_index_only(self):
        self.row["ratified"] = "1"
        self.write_index()
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_D10_RATIFIED"):
            adapter.prepare(self.root, self.input, self.output)


if __name__ == "__main__":
    unittest.main()
