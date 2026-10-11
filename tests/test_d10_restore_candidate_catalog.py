"""Lossless historical 1495-name D10 source-catalog merge regressions."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import d10_restore_candidate_catalog as merge
from d10_mechanical_filter import git_blob


class CatalogRestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        k = self.root / "knowledge"
        k.mkdir()
        self.old = k / "old.tsv"
        self.current = k / "current.tsv"
        self.output = k / "union.tsv"
        inv = {"width": 10, "capacity": 1024, "rows": [
            {"stable_id": "d10.canonical", "semantic_name": "ALPHA",
             "coordinate": "0000000010", "ratified_resident": False}]}
        invraw = (json.dumps(inv) + "\n").encode()
        (k / "v7.json").write_bytes(invraw)
        (k / "d10-current-inventory.json").write_text(json.dumps(
            {"canonical_current": {"path": "knowledge/v7.json",
                                   "git_blob": git_blob(invraw), "selected": 1}}))
        self.old_rows = [self.make("ALPHA", "d10.alpha"), self.make("BETA", "d10.name.2"),
                         self.make("GAMMA", "d10.name.3")]
        self.current_rows = [self.make("ALPHA", "d10.name.1"),
                             self.make("DELTA", "d10.name.2")]
        self.write(self.old, self.old_rows)
        self.write(self.current, self.current_rows)
        self.original = merge.HISTORICAL_BLOB
        merge.HISTORICAL_BLOB = git_blob(self.old.read_bytes())
        self.addCleanup(lambda: setattr(merge, "HISTORICAL_BLOB", self.original))

    def make(self, name, ident):
        row = {k: "" for k in merge.INDEX_FIELDS}
        row.update(candidate_id=ident, semantic_name=name, source_record_count="1",
                   current_d10_selected="NOT_SELECTED", canonical_coordinate="NONE",
                   ratified="0")
        for field in merge.ARRAY_FIELDS:
            row[field] = json.dumps([name + "-" + field])
        return row

    def write(self, path, records):
        with path.open("w", encoding="utf-8") as fh:
            fh.write("\t".join(merge.INDEX_FIELDS) + "\n")
            for row in records:
                fh.write("\t".join(row[k] for k in merge.INDEX_FIELDS) + "\n")

    def test_union_preserves_all_names_and_original_source_ids(self):
        report = merge.merge_catalog(self.root, self.old, self.current, self.output)
        self.assertEqual(3, report["source_historical_names"])
        self.assertEqual(2, report["source_latest_names"])
        self.assertEqual(2, report["restored_old_only_names"])
        self.assertEqual(4, report["full_union_names"])
        result = merge.literal_tsv(self.output)
        self.assertEqual({"alpha", "beta", "gamma", "delta"}, set(result))
        self.assertEqual("d10.canonical", result["alpha"]["candidate_id"])
        self.assertEqual("0000000010", result["alpha"]["canonical_coordinate"])
        self.assertNotEqual(result["beta"]["candidate_id"], result["delta"]["candidate_id"])
        self.assertIn("HISTORIC_SOURCE_ID:d10.name.2",
                      json.loads(result["beta"]["historical_status_claims"]))
        self.assertIn("RESTORED_FROM_1495_NAME_FROZEN_INTAKE",
                      json.loads(result["beta"]["historical_status_claims"]))
        self.assertEqual("0", result["beta"]["ratified"])

    def test_new_catalog_rfc_tsv_quoting_is_accepted(self):
        with self.current.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=merge.INDEX_FIELDS,
                                    delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(self.current_rows)
        report = merge.merge_catalog(self.root, self.old, self.current, self.output)
        self.assertEqual(4, report["full_union_names"])
        self.assertEqual(2, report["restored_old_only_names"])

    def test_historical_blob_tampering_fails(self):
        self.old.write_text(self.old.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "HISTORICAL_CATALOG_BLOB_CHANGED"):
            merge.merge_catalog(self.root, self.old, self.current, self.output)

    def test_unexpected_ratified_flag_fails(self):
        self.current_rows[0]["ratified"] = "1"
        self.write(self.current, self.current_rows)
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_RATIFICATION"):
            merge.merge_catalog(self.root, self.old, self.current, self.output)

    def test_malformed_historical_array_fails(self):
        self.current_rows[1]["semantic_law_variants"] = "unparsed"
        self.write(self.current, self.current_rows)
        with self.assertRaisesRegex(ValueError, "INVALID_JSON_LIST"):
            merge.merge_catalog(self.root, self.old, self.current, self.output)


if __name__ == "__main__":
    unittest.main()
