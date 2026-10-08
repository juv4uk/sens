#!/usr/bin/env python3
"""A blocked source disappearing is not proof that a SENS program was migrated."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/diff_original_migration_snapshots.py"
spec = importlib.util.spec_from_file_location("sens_migration_snapshot_delta", SOURCE)
assert spec and spec.loader
delta = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = delta
spec.loader.exec_module(delta)

SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40


def row(path: str, sha: str = SHA_A, status: str = "BLOCKED",
        scope: str = "UNCLASSIFIED_NEEDS_SOURCE_PROOF",
        reason: str = "legacy-unmapped function") -> dict:
    r = {
        "path": path, "source_git_blob_sha": sha, "status": status,
        "source_scope": scope, "source_is_executable_proven": False,
        "independent_semantic_oracle_passed": False,
        "same_stem_sens_already_exists": False,
    }
    if status == "BLOCKED":
        r["reason"] = reason
    else:
        r["destination"] = path[:-5] + ".sens"
    return r


def report(*rows: dict, paired: tuple[str, ...] = ()) -> dict:
    blocked = [x for x in rows if x["status"] == "BLOCKED"]
    cand = [x for x in rows if x["status"] == "CANDIDATE_NOT_ADMITTED"]
    return {
        "schema": "sens-original-three-pass-eligibility/v1",
        "source_era": "auto",
        "mode": "read-only canonical migrator dry-run",
        "summary": {
            "original_unpaired_sources_scanned": len(rows),
            "blocked": len(blocked),
            "mechanical_candidates": len(cand),
            "already_paired_sources_excluded": len(paired),
            "physical_outputs_created": 0,
            "original_unpaired_executables_migrated_by_this_tool": 0,
        },
        "blocked_sources": blocked, "mechanical_candidates": cand,
        "already_paired_sources_excluded": list(paired),
    }


class MigrationDiffTests(unittest.TestCase):
    def test_same_input_no_fictitious_success(self):
        x = report(row("lib/core.lisp"))
        d = delta.compare(x, x)
        self.assertEqual(d["summary"]["change_events"], 0)
        self.assertEqual(d["summary"]["semantically_admitted_by_this_tool"], 0)
        self.assertEqual(d["summary"]["unchanged_unpaired_sources"], 1)

    def test_first_blocker_change_not_program_migration(self):
        a = report(row("lib/core.lisp", reason="legacy W8 ambiguity"))
        b = report(row("lib/core.lisp", reason="unbound dynamic local"))
        d = delta.compare(a, b)
        self.assertEqual(d["changes"][0]["kind"], "FIRST_BLOCKER_CHANGED_NOT_MIGRATED")
        self.assertEqual(d["summary"]["new_pairs_pending_proof"], 0)

    def test_candidate_is_not_oracle(self):
        a = report(row("lib/core.lisp"))
        b = report(row("lib/core.lisp", status="CANDIDATE_NOT_ADMITTED"))
        d = delta.compare(a, b)
        self.assertEqual(d["changes"][0]["kind"], "MECHANICAL_CANDIDATE_NOT_ORACLE_ADMITTED")
        self.assertEqual(d["summary"]["semantically_admitted_by_this_tool"], 0)

    def test_reverse_transition_is_not_progress(self):
        a = report(row("lib/core.lisp", status="CANDIDATE_NOT_ADMITTED"))
        b = report(row("lib/core.lisp"))
        self.assertEqual(delta.compare(a, b)["changes"][0]["kind"],
                         "MECHANICAL_CANDIDATE_REGRESSED_TO_BLOCKED")

    def test_new_pair_excluded_but_must_be_oracle_proven_elsewhere(self):
        a = report(row("lib/core.lisp", SHA_A), paired=("old/already.lisp",))
        b = report(paired=("old/already.lisp", "lib/core.lisp"))
        d = delta.compare(a, b)
        self.assertEqual(d["summary"]["new_pairs_pending_proof"], 1)
        self.assertEqual(d["changes"][0]["kind"],
                         "NEW_PAIR_REQUIRES_ORACLE_AND_SOURCE_RECHECK")
        self.assertEqual(d["summary"]["semantically_admitted_by_this_tool"], 0)

    def test_unpaired_disappearance_cannot_reduce_denominator(self):
        with self.assertRaisesRegex(delta.SnapshotError, "vanished"):
            delta.compare(report(row("lib/real.lisp")), report())

    def test_existing_pair_must_not_disappear(self):
        with self.assertRaisesRegex(delta.SnapshotError, "pair disappeared"):
            delta.compare(report(paired=("fixtures/x.lisp",)), report())

    def test_sha_drift_requires_review_not_credit(self):
        a = report(row("lib/core.lisp", SHA_A, reason="legacy W8"))
        b = report(row("lib/core.lisp", SHA_B, reason="unmapped function"))
        d = delta.compare(a, b)
        self.assertEqual(len(d["changes"]), 1)
        self.assertEqual(d["changes"][0]["kind"], "SOURCE_BYTES_CHANGED_REVIEW_REQUIRED")

    def test_nonprogram_classification_not_new_executable(self):
        a = report(row("knowledge/schema.lisp"))
        b = report(row("knowledge/schema.lisp", scope="NONPROGRAM_DATA_REVIEWED"))
        d = delta.compare(a, b)
        self.assertEqual(d["changes"][0]["kind"],
                         "NEW_NONPROGRAM_CLASSIFICATION_NOT_MIGRATION")
        self.assertEqual(d["summary"]["new_pairs_pending_proof"], 0)

    def test_new_source_does_not_count_as_migration(self):
        d = delta.compare(report(), report(row("lib/new.lisp", SHA_C)))
        self.assertEqual(d["changes"][0]["kind"], "NEW_SOURCE_NEEDS_ADMISSION")
        self.assertEqual(d["summary"]["new_sources_not_credit"], 1)

    def test_bad_schema_count_duplicates_and_symlinks_are_rejected(self):
        a = report(row("lib/core.lisp"))
        for key, value in [("schema", "other"), ("mode", "write"),
                           ("source_era", "legacy")]:
            changed = json.loads(json.dumps(a))
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(delta.SnapshotError):
                delta.compare(a, changed)
        changed = json.loads(json.dumps(a))
        changed["blocked_sources"].append(row("lib/core.lisp"))
        changed["summary"]["blocked"] += 1
        changed["summary"]["original_unpaired_sources_scanned"] += 1
        with self.assertRaisesRegex(delta.SnapshotError, "duplicate"):
            delta.compare(a, changed)
        for illegal in ("../data.lisp", "/tmp/a.lisp", "a//x.lisp", "a\\x.lisp"):
            with self.subTest(path=illegal), self.assertRaises(delta.SnapshotError):
                delta.compare(report(row(illegal)), report())

    def test_falsified_source_authority_and_counts_are_rejected(self):
        good = report(row("lib/core.lisp"))
        falsified = report(row("lib/core.lisp"))
        falsified["blocked_sources"][0]["independent_semantic_oracle_passed"] = True
        with self.assertRaisesRegex(delta.SnapshotError, "misrepresented"):
            delta.compare(good, falsified)
        other = report(row("lib/core.lisp"))
        other["summary"]["blocked"] = 0
        with self.assertRaisesRegex(delta.SnapshotError, "count mismatch"):
            delta.compare(good, other)

    def test_cli_output_new_only_no_overwrite_deterministic(self):
        a = report(row("lib/core.lisp", SHA_A))
        b = report(row("lib/core.lisp", SHA_A, reason="unbound"))
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            before, after, out = (folder / name for name in ("before.json", "after.json", "delta.json"))
            before.write_text(json.dumps(a), encoding="utf-8")
            after.write_text(json.dumps(b), encoding="utf-8")
            args = [sys.executable, str(SOURCE), "--before", str(before),
                    "--after", str(after), "--out", str(out)]
            proc = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(out.read_text())["schema"], delta.SCHEMA)
            proc2 = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(proc2.returncode, 2)
            self.assertIn("output exists", proc2.stderr)
            self.assertEqual(json.loads(before.read_text()), a)


if __name__ == "__main__":
    unittest.main()
