"""Lossless D10 research triage, NOT a semantic verifier."""
import csv
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from d10_restore_source_occurrences import SOURCE_COLUMNS
from d10_sort_review_queue import category, make_queue, parse_source, render, validate


def row(name, cid, *, law=(), donor=(), pos=(), neg=(),
        selected="NOT_SELECTED", coordinate="NONE"):
    record = {k: "" for k in SOURCE_COLUMNS}
    record.update(
        candidate_id=cid, semantic_name=name,
        source_record_count="1", canonical_coordinate=coordinate,
        current_d10_selected=selected, ratified="0",
        semantic_law_variants=json.dumps(list(law)),
        donor_provenance_claims=json.dumps(list(donor)),
        positive_witness_claims=json.dumps(list(pos)),
        falsifier_claims=json.dumps(list(neg)),
        source_records_sha_pinned=json.dumps(
            ["knowledge/source.json@" + "a" * 40 + ":rows[0]"]),
    )
    return record


class TriageRegression(unittest.TestCase):
    def test_ready_for_replay_is_not_admission(self):
        rows = [row("FUNC", "a", law=["law"], donor=["donor"],
                    pos=["case"], neg=["falsifier"])]
        q = make_queue(parse_source(self._source(rows)))
        self.assertEqual(q[0]["review_tier"], "P0_REPLAY_BOTH_WITNESSES")
        self.assertEqual(q[0]["witness_status"], "NOT_ATTESTED_NO_F2_PASS")
        self.assertEqual(q[0]["semantic_distinctness_status"], "UNPROVEN_NO_F3_PASS")
        self.assertEqual(q[0]["canonical_coordinate"], "NONE")

    def test_name_collision_is_not_dedup(self):
        rows = [
            row("SAME", "one", law=["law-1"]),
            row("SAME", "two", law=["different-law"]),
        ]
        q = make_queue(parse_source(self._source(rows)))
        self.assertEqual(len(q), 2)
        self.assertEqual({x["candidate_id"] for x in q}, {"one", "two"})
        self.assertEqual({x["same_spelling_records"] for x in q}, {"2"})

    def test_archive_selected_is_not_duplicated(self):
        rows = [
            row("SAME", "selected-identity", law=["observed"],
                selected="RESEARCH_SELECTED_UNRATIFIED", coordinate="0000000001"),
            row("SAME", "provisional-identity", law=["other"]),
        ]
        q = make_queue(parse_source(self._source(rows)))
        other = next(x for x in q if x["candidate_id"] == "provisional-identity")
        self.assertEqual(other["same_spelling_as_other_selected"], "YES")
        self.assertEqual(other["canonical_selection"], "NOT_SELECTED")
        self.assertEqual(other["canonical_coordinate"], "NONE")
        self.assertTrue(any(x["review_tier"] == "ARCHIVE_ALREADY_RESEARCH_SELECTED"
                            for x in q))

    def test_full_check_committed_snapshot(self):
        root = Path(__file__).resolve().parents[1]
        result = validate(root,
                          root / "knowledge/d10-filter/review-triage-manifest.json")
        self.assertEqual(result["total"], 1809)
        self.assertEqual(result["archive_rows"], 7396)

    def test_bad_coordinate_fails(self):
        rows = [row("X", "new", coordinate="0000000001")]
        with self.assertRaisesRegex(ValueError, "NONSELECTED_HAS_CANONICAL_COORDINATE"):
            make_queue(parse_source(self._source(rows)))

    def test_duplicate_id_fails(self):
        rows = [row("X", "same"), row("Y", "same")]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_EMPTY_CANDIDATE_ID"):
            parse_source(self._source(rows))

    @staticmethod
    def _source(rows):
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=SOURCE_COLUMNS, delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()


if __name__ == "__main__":
    unittest.main()
