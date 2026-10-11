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
                             self.make("DELTA", "d10.name.4")]
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

    def test_find_name_line_matches_only_canonical_json_property(self):
        canonical = (
            '{\n'
            '  "rows": [\n'
            '    {\n'
            '      "semantic_name": "ALPHA",\n'
            '      "provenance": "BETA",\n'
            '      "note": "ALPHA appears in this ordinary string"\n'
            '    },\n'
            '    {\n'
            '      "semantic_name": "BETA"\n'
            '    }\n'
            '  ]\n'
            '}\n'
        )
        self.assertEqual(4, merge.find_name_line(canonical, "ALPHA", True))
        self.assertEqual(8, merge.find_name_line(canonical, "BETA", True))
        self.assertIsNone(merge.find_name_line(canonical, "ALPH", True))
        self.assertEqual(4, merge.find_name_line(canonical, "alpha", False))

    def test_find_name_line_fails_closed_on_duplicate_canonical_rows(self):
        canonical = (
            '{\n'
            '  "semantic_name": "ALPHA",\n'
            '  "semantic_name": "ALPHA"\n'
            '}\n'
        )
        with self.assertRaisesRegex(ValueError, "AMBIGUOUS_CANONICAL_SEMANTIC_NAME"):
            merge.find_name_line(canonical, "ALPHA", True)

    def test_union_preserves_all_names_and_original_source_ids(self):
        report = merge.merge_catalog(self.root, self.old, self.current, self.output)
        self.assertEqual(3, report["source_historical_ids"])
        self.assertEqual(2, report["source_latest_ids"])
        self.assertEqual(0, report["source_id_overlap"])
        self.assertEqual(3, report["restored_prior_only_ids"])
        self.assertEqual(5, report["source_union_candidate_ids"])
        self.assertEqual(1, report["canonical_overlay_ids_added"])
        self.assertEqual(6, report["full_union_ids"])
        self.assertEqual(4, report["full_union_names"])
        self.assertEqual(1, report["colliding_spelling_groups_not_deduped"])
        result = merge.literal_tsv(self.output)
        self.assertEqual({
            "d10.alpha", "d10.name.1", "d10.name.2", "d10.name.3",
            "d10.name.4", "d10.canonical"
        }, set(result))
        self.assertEqual("ALPHA", result["d10.alpha"]["semantic_name"])
        self.assertEqual("ALPHA", result["d10.name.1"]["semantic_name"])
        self.assertEqual("ALPHA", result["d10.canonical"]["semantic_name"])
        self.assertEqual("0000000010", result["d10.canonical"]["canonical_coordinate"])
        self.assertEqual("d10.alpha", result["d10.alpha"]["candidate_id"])
        self.assertEqual("d10.name.1", result["d10.name.1"]["candidate_id"])
        self.assertIn("HISTORIC_SOURCE_ID:d10.name.2",
                      json.loads(result["d10.name.2"]["historical_status_claims"]))
        self.assertIn("RESTORED_FROM_1495_NAME_FROZEN_INTAKE",
                      json.loads(result["d10.name.2"]["historical_status_claims"]))
        self.assertEqual("0", result["d10.name.2"]["ratified"])

    def test_historical_and_current_same_name_distinct_ids_survive(self):
        report = merge.merge_catalog(self.root, self.old, self.current, self.output)
        self.assertEqual(4, report["full_union_names"])
        rows = merge.literal_tsv(self.output)
        self.assertEqual({"d10.alpha", "d10.name.1", "d10.canonical"},
                         {ident for ident, row in rows.items()
                          if row["semantic_name"] == "ALPHA"})
        self.assertEqual(0, report["new_ratifications"])
        self.assertEqual(0, report["new_allocations"])

    def test_same_candidate_id_with_conflicting_name_blocks(self):
        self.current_rows[1]["candidate_id"] = "d10.name.2"
        self.write(self.current, self.current_rows)
        with self.assertRaisesRegex(ValueError, "HISTORICAL_ID_NAME_CONFLICT"):
            merge.merge_catalog(self.root, self.old, self.current, self.output)
        self.assertFalse(self.output.exists())

    def test_duplicate_candidate_id_in_one_source_blocks(self):
        self.current_rows[1]["candidate_id"] = self.current_rows[0]["candidate_id"]
        self.write(self.current, self.current_rows)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_EMPTY_SOURCE_IDENTITY"):
            merge.merge_catalog(self.root, self.old, self.current, self.output)
        self.assertFalse(self.output.exists())

    def test_new_catalog_rfc_tsv_quoting_is_accepted(self):
        with self.current.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=merge.INDEX_FIELDS,
                                    delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(self.current_rows)
        report = merge.merge_catalog(self.root, self.old, self.current, self.output)
        self.assertEqual(4, report["full_union_names"])
        self.assertEqual(2, report["restored_old_only_names"])
        self.assertEqual(6, report["full_union_ids"])

    def test_duplicate_source_name_preserves_independent_candidate_ids(self):
        # Same spelling is not a semantic equivalence certificate. Retain both
        # source claims under their distinct immutable IDs, never merge by name.
        duplicate = self.make("DELTA", "d10.name.5")
        duplicate["semantic_law_variants"] = json.dumps(["independent law claim"])
        duplicate["donor_provenance_claims"] = json.dumps(["second donor source"])
        duplicate["source_records_sha_pinned"] = json.dumps(["second-source@" + "a" * 40])
        self.write(self.current, self.current_rows + [duplicate])

        report = merge.merge_catalog(self.root, self.old, self.current, self.output)
        self.assertEqual(3, report["source_latest_ids"])
        self.assertEqual(7, report["full_union_ids"])
        result = merge.literal_tsv(self.output)
        self.assertEqual({"d10.name.4", "d10.name.5"},
                         {ident for ident, row in result.items()
                          if row["semantic_name"] == "DELTA"})
        original, extra = result["d10.name.4"], result["d10.name.5"]
        self.assertEqual("1", original["source_record_count"])
        self.assertEqual("1", extra["source_record_count"])
        self.assertEqual("0", extra["ratified"])
        self.assertEqual("NONE", extra["canonical_coordinate"])
        self.assertIn("independent law claim", json.loads(extra["semantic_law_variants"]))
        self.assertIn("second donor source", json.loads(extra["donor_provenance_claims"]))
        self.assertIn("second-source@" + "a" * 40,
                      json.loads(extra["source_records_sha_pinned"]))
        self.assertIn("HISTORIC_SOURCE_ID:d10.name.2",
                      json.loads(result["d10.name.2"]["historical_status_claims"]))

    def test_repeated_name_with_same_candidate_id_still_fails(self):
        duplicate = dict(self.current_rows[1])
        self.write(self.current, self.current_rows + [duplicate])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_EMPTY_SOURCE_IDENTITY"):
            merge.merge_catalog(self.root, self.old, self.current, self.output)

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
