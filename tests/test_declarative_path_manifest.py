#!/usr/bin/env python3
"""Fail closed when a research DATA shortlist mislabels executable originals.

#4460 is a source-classification observation, NOT executable admission.
Authoritative DATA exclusions live in knowledge/migration-nonprogram-*.json.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "docs/research/declarative-path-manifest.json"
AUTHORITIES = (
    "migration-nonprogram-domain-tables-2026-10-08.json",
    "migration-nonprogram-comment-only-loaders-2026-10-08.json",
    "migration-nonprogram-isa-manifest-2026-10-08.json",
    "migration-nonprogram-schema-manifest-2026-10-08.json",
    "migration-nonprogram-evidence-manifest-2026-10-08.json",
    "migration-nonprogram-expr-records-2026-10-08.json",
    "migration-nonprogram-knowledge-records-2026-10-08.json",
)
EXECUTABLE = {
    "lib/quantity.lisp": 42,
    "lib/reason.lisp": 37,
    "lib/si.lisp": 29,
    "lib/translation.lisp": 31,
}


def checked_source(row: dict) -> tuple[bytes, str]:
    name = row["path"]
    assert isinstance(name, str) and name and "\\" not in name
    rel = PurePosixPath(name)
    assert not rel.is_absolute() and rel.suffix == ".lisp"
    assert ".." not in rel.parts and rel.as_posix() == name
    path = ROOT.joinpath(*rel.parts)
    assert path.is_file() and not path.is_symlink()
    assert not path.with_suffix(".sens").exists(), name
    raw = path.read_bytes()
    assert len(raw) == row["bytes"], name
    assert hashlib.sha256(raw).hexdigest() == row["sha256"], name
    code_lines = [line.strip() for line in raw.decode("utf-8").splitlines()
                  if line.strip() and not line.lstrip().startswith(";")]
    assert code_lines, name
    return raw, code_lines[0]


def authority_paths() -> set[str]:
    paths: set[str] = set()
    for name in AUTHORITIES:
        item = json.loads((ROOT / "knowledge" / name).read_text(encoding="utf-8"))
        assert item["schema"] == "sens-migration-nonprogram-manifest/1"
        assert item["automatic_sens_companion"] is False
        for entry in item["entries"]:
            assert entry["path"] not in paths, entry["path"]
            paths.add(entry["path"])
    assert len(paths) == 92
    return paths


class DeclarativeResearchTruthTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(RESEARCH.read_text(encoding="utf-8"))
        self.assertEqual(self.doc["schema"], "sens-declarative-path-manifest/v1")
        self.rows = self.doc["files"]
        self.excluded = self.doc["excluded_executable"]

    def test_declarative_data_not_confused_with_executable_definitions(self):
        self.assertEqual(len(self.rows), 35)
        self.assertEqual(self.doc["counts"]["files"], 35)
        self.assertEqual(sum(self.doc["counts"]["by_head"].values()), 35)
        paths = set()
        for row in self.rows:
            with self.subTest(path=row["path"]):
                self.assertNotIn(row["path"], paths)
                paths.add(row["path"])
                raw, first = checked_source(row)
                self.assertEqual(first.split(maxsplit=1)[0], "(" + row["head"])
                # No top-level binary executable head may hide behind a name/N
                # embedded deeper in source DATA.
                self.assertIsNone(re.search(
                    rb"(?m)^\([01]{3,9}(?=\s|\))", raw), row["path"]
                )
        self.assertTrue(paths.isdisjoint(EXECUTABLE))
        self.assertEqual(self.doc["counts"]["excluded_executable_modules"], 4)

    def test_four_real_executable_modules_are_never_dropped_from_work_queue(self):
        rows = {entry["path"]: entry for entry in self.excluded}
        self.assertEqual(set(rows), set(EXECUTABLE))
        self.assertEqual(sum(EXECUTABLE.values()), 139)
        self.assertEqual(self.doc["counts"]["excluded_top_level_define_forms"], 139)
        for name, expected in EXECUTABLE.items():
            with self.subTest(path=name):
                row = rows[name]
                self.assertEqual(row["classification"], "EXECUTABLE_NOT_NONPROGRAM")
                raw, first = checked_source(row)
                self.assertRegex(first, r"^\(000010(?:01|11)\b")
                actual = len(re.findall(
                    rb"(?m)^\(000010(?:01|11)(?=\s|\))", raw))
                self.assertEqual(actual, expected)
                self.assertEqual(row["top_level_define_count"], expected)

    def test_39_does_not_equal_39_new_nonprogram_classifications(self):
        approved = authority_paths()
        claimed = {row["path"] for row in self.rows}
        self.assertEqual(len(claimed & approved), 27)
        self.assertEqual(len(claimed - approved), 8)
        self.assertEqual(self.doc["counts"]["already_reviewed_existing"], 27)
        self.assertEqual(
            self.doc["counts"]["new_declarative_candidates_not_yet_authority"], 8
        )
        # Excluded executable originals are NOT previously approved DATA.
        self.assertTrue(set(EXECUTABLE).isdisjoint(approved))
        self.assertIn("RESEARCH_DATA_CANDIDATE_ONLY", self.doc["decision"])
        self.assertIn("NEVER", self.doc["research_warning"])

    def test_original_active_machine_block_remains_outside_data_shortlist(self):
        original = "lib/machine/block.lisp"
        listed = {row["path"] for row in self.rows + self.excluded}
        self.assertNotIn(original, listed)
        self.assertNotIn(original, authority_paths())
        self.assertFalse((ROOT / "lib/machine/block.sens").exists())


if __name__ == "__main__":
    unittest.main()
