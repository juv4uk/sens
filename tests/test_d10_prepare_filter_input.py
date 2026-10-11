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
        # The historical unified index was assembled as raw tab-delimited
        # fields with JSON quotes inside values, not RFC CSV quoting.
        with self.input.open("w", newline="", encoding="utf-8") as stream:
            stream.write("\t".join(adapter.INDEX_FIELDS) + "\n")
            for row in [self.row, *extra]:
                stream.write("\t".join(row[name] for name in adapter.INDEX_FIELDS) + "\n")

    def read_prepared(self):
        with self.output.open(encoding="utf-8", newline="") as stream:
            return list(csv.DictReader(stream, delimiter="\t"))

    def test_batch_name_index_matches_legacy_locators(self):
        cases = (
            (False, '{"semantic_name": "A"}\n{"semantic_name": "B"}\n'
                    '{"semantic_name": "A"}\n', ("A", "B", "MISSING")),
            (True, "semantic_name\tkind\nA\tone\nB\ttwo\n"
                   "BAD-LINE\nA\tthree\n", ("A", "B", "BAD-LINE", "MISSING")),
        )
        for is_tsv, source, names in cases:
            with self.subTest(is_tsv=is_tsv):
                indexed = adapter.index_name_lines(source, is_tsv)
                for name in names:
                    self.assertEqual(adapter.find_name_line(source, name, is_tsv),
                                     indexed.get(name.casefold()))
        many = ("semantic_name\tvalue\n" +
                "".join(f"NAME-{n}\t{n}\n" for n in range(1000)))
        index = adapter.index_name_lines(many, True)
        self.assertEqual(len(index), 1000)
        self.assertEqual(index["name-999"], 1001)

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

    def test_current_csv_quoted_json_cells_and_raw_tsv_are_semantically_equal(self):
        self.write_index()
        raw_result = adapter.prepare(self.root, self.input, self.output)
        with self.output.open(encoding="utf-8", newline="") as stream:
            raw_rows = list(csv.DictReader(stream, delimiter="\t"))
        # The producer now serializes TSV through a CSV writer. Quote escaping
        # must not turn a pinned donor into a missing/unverified source.
        with self.input.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=adapter.INDEX_FIELDS,
                                    delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerow(self.row)
        quoted_result = adapter.prepare(self.root, self.input, self.output)
        with self.output.open(encoding="utf-8", newline="") as stream:
            quoted_rows = list(csv.DictReader(stream, delimiter="\t"))
        self.assertEqual(raw_result, quoted_result)
        self.assertEqual(raw_rows, quoted_rows)
        self.assertEqual(1, quoted_result["source_file_pin_verified"])

    def test_malformed_csv_quoted_list_fails_closed(self):
        self.row["semantic_law_variants"] = '"not an array"'
        self.write_index()
        with self.assertRaisesRegex(ValueError, "INVALID_INDEX_JSON_ARRAY"):
            adapter.prepare(self.root, self.input, self.output)

    def test_rfc4180_quoted_index_keeps_json_and_unverified_witness(self):
        # New historical batches use csv.DictWriter's RFC4180 quoting.
        # JSON array quotes must survive TSV decoding unchanged, and claims
        # never imply a successfully executed witness.
        self.row["semantic_law_variants"] = json.dumps(
            ['first law with "quotes"', "independent second law"]
        )
        with self.input.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=adapter.INDEX_FIELDS,
                delimiter=chr(9), lineterminator=chr(10),
            )
            writer.writeheader()
            writer.writerow(self.row)
        counts = adapter.prepare(self.root, self.input, self.output)
        self.assertEqual(2, counts["filter_input_rows"])
        self.assertEqual(0, counts["executed_witnesses_supplied"])
        rows = {r["candidate_id"]: r for r in self.read_prepared()}
        self.assertEqual('first law with "quotes"', rows["d10.new"]["semantic_law"])
        self.assertEqual(self.pin, rows["d10.new"]["source_pin"])
        self.assertEqual("", rows["d10.new"]["witness_verdict"])

    def test_unterminated_rfc4180_field_blocks_without_output(self):
        # Do not rescue a genuinely truncated or malformed CSV field by
        # blindly stripping quotes to fabricate a JSON law.
        self.row["semantic_law_variants"] = '"[""broken""'
        self.write_index()
        with self.assertRaisesRegex(ValueError, "MALFORMED_UNIFIED_INDEX_CSV"):
            adapter.prepare(self.root, self.input, self.output)
        self.assertFalse(self.output.exists())

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

    def test_same_surface_two_distinct_candidate_ids_are_not_deduplicated(self):
        # A spelling collision is not a semantic equivalence certificate.
        other = dict(self.row)
        other["candidate_id"] = "d10.historical-namesake"
        self.write_index([other])
        counts = adapter.prepare(self.root, self.input, self.output)
        self.assertEqual(2, counts["index_rows"])
        self.assertEqual(1, counts["name_collisions_not_deduped"])
        self.assertEqual(3, counts["filter_input_rows"])  # canonical overlay
        rows = {row["candidate_id"]: row for row in self.read_prepared()}
        self.assertEqual({"d10.new", "d10.historical-namesake", "d10.selected"}, set(rows))
        self.assertEqual(rows["d10.new"]["semantic_name"], rows["d10.historical-namesake"]["semantic_name"])
        self.assertEqual("", rows["d10.historical-namesake"]["witness_verdict"])

    def test_historical_namesake_does_not_replace_canonical_stable_id(self):
        # The historical and canonical IDs both survive, with no invented
        # proof or automatic approval on the duplicate-looking name.
        self.row["semantic_name"] = "OLD-LAW"
        self.row["candidate_id"] = "d10.historical-old-law"
        self.write_index()
        counts = adapter.prepare(self.root, self.input, self.output)
        self.assertEqual(1, counts["new_selected_since_index"])
        self.assertEqual(2, counts["filter_input_rows"])
        rows = {row["candidate_id"]: row for row in self.read_prepared()}
        self.assertEqual({"d10.historical-old-law", "d10.selected"}, set(rows))
        for item in rows.values():
            self.assertEqual("", item["witness_verdict"])
            self.assertEqual("UNRATIFIED", item["ratification_state"])

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
