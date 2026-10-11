"""D10 lossless provenance restoration and negative regression checks."""
import csv
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from d10_restore_source_occurrences import SOURCE_COLUMNS, expand, validate


def source_row(cid, name, references):
    values = {k: "" for k in SOURCE_COLUMNS}
    values.update(candidate_id=cid, semantic_name=name,
                  source_record_count=str(len(references)),
                  source_records_sha_pinned=json.dumps(references),
                  ratified="0")
    return values


def document(rows):
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=SOURCE_COLUMNS, delimiter="\t",
                            lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return text.getvalue()


class Restoration(unittest.TestCase):
    SHA = "a" * 40

    def test_name_collision_preserves_identities_and_occurrences(self):
        ref = f"knowledge/a.json@{self.SHA}:rows[2]"
        contents = document([
            source_row("one", "SAME", [ref, ref]),
            source_row("two", "SAME", [ref]),
        ])
        expanded, count, files = expand(contents)
        lines = list(csv.DictReader(io.StringIO(expanded), delimiter="\t"))
        self.assertEqual(len(lines), 3)
        self.assertEqual([r["candidate_id"] for r in lines], ["one", "one", "two"])
        self.assertEqual([r["source_ordinal"] for r in lines], ["1", "2", "1"])
        self.assertEqual(count["candidate_identities"], 2)
        self.assertEqual(count["semantic_name_spellings"], 1)
        self.assertEqual(count["distinct_reference_strings"], 1)
        self.assertEqual(files["knowledge/a.json"], 3)

    def test_rejects_unpinned_sources(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_REF_NOT_SHA_PINNED"):
            expand(document([source_row("x", "X", ["knowledge/a.json:1"])]))

    def test_rejects_duplicate_identity(self):
        ref = f"knowledge/a.json@{self.SHA}:1"
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_EMPTY_CANDIDATE_ID"):
            expand(document([source_row("x", "X", [ref]), source_row("x", "X", [ref])]))

    def test_rejects_inconsistent_count(self):
        row = source_row("x", "X", [])
        row["source_record_count"] = "3"
        with self.assertRaisesRegex(ValueError, "SOURCE_RECORD_COUNT_LOSS"):
            expand(document([row]))

    def test_rejects_ratification(self):
        row = source_row("x", "X", [])
        row["ratified"] = "1"
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_RATIFICATION_CLAIM"):
            expand(document([row]))

    def test_checked_repository_snapshot(self):
        counts = validate(Path(__file__).resolve().parents[1],
                          Path(__file__).resolve().parents[1] /
                          "knowledge/d10-filter/source-occurrence-manifest.json")
        self.assertGreaterEqual(counts["pinned_source_occurrences"], 3000)


if __name__ == "__main__":
    unittest.main()
