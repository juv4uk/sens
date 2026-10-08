#!/usr/bin/env python3
"""Regression for read-only old source T5 migratability census."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import json
import subprocess
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/report_original_migration_candidates.py"
spec = importlib.util.spec_from_file_location("original_candidate_report", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OriginalCandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_pin_real_git_blob_sha_not_plain_sha1(self):
        sample = self.root / "old.lisp"
        sample.write_bytes(b"hello\n")
        self.assertEqual(mod.git_blob_sha(sample),
                         "ce013625030ba8dba906f756967f9e9ca394464a")

    def test_mechanical_candidate_not_semantically_admitted(self):
        source = self.root / "old.lisp"
        source.write_text("(001 ())\n", encoding="utf-8")
        row = mod.categorize({
            "path":"old.lisp", "status":"would-write",
            "bytes":4, "physical_sha256":"a"*64,
            "typed_word_sha256":"b"*64, "semantic_word_count":5,
            "passes":{"already-exact":1},
        },self.root)
        self.assertEqual(row["status"], "CANDIDATE_NOT_ADMITTED")
        self.assertEqual(row["destination"], "old.sens")
        self.assertFalse(row["same_stem_sens_already_exists"])
        self.assertFalse(row["source_is_executable_proven"])
        self.assertFalse(row["independent_semantic_oracle_passed"])
        self.assertEqual(row["proposed_bytes"], 4)

    def test_already_paired_cannot_count_as_old_unpaired(self):
        self.root.joinpath("old.lisp").write_text("(001 ())\n", encoding="utf-8")
        self.root.joinpath("old.sens").write_bytes(b"not relevant to classification")
        row = mod.categorize({
            "path":"old.lisp", "status":"would-write",
            "bytes":4, "physical_sha256":"a"*64,
            "typed_word_sha256":"b"*64, "semantic_word_count":5,
            "passes":{},
        }, self.root)
        self.assertTrue(row["same_stem_sens_already_exists"])

    def test_blocked_lisp_stays_blocked(self):
        self.root.joinpath("unknown.lisp").write_text("(unknown ())\n", encoding="utf-8")
        row = mod.categorize({
            "path":"unknown.lisp","status":"blocked",
            "reason":"legacy-unmapped current function",
        }, self.root)
        self.assertEqual(row["status"], "BLOCKED")
        self.assertIn("legacy-unmapped",row["reason"])

    def test_paths_and_missing_or_symlink_sources_fail_closed(self):
        for path in ["../escape.lisp", "/tmp/escape.lisp", "test.sens"]:
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    mod.categorize({"path":path,"status":"blocked"}, self.root)
        with self.assertRaises(ValueError):
            mod.categorize({"path":"missing.lisp","status":"blocked"},self.root)
        link = self.root / "link.lisp"
        link.symlink_to(self.root / "missing.lisp")
        with self.assertRaises(ValueError):
            mod.categorize({"path":"link.lisp","status":"blocked"},self.root)


    def test_current_d1_d9_unpaired_source_era_is_default(self):
        self.assertIn("knowledge/d1-d9-foundation.json", mod.ARGS)
        self.assertNotIn("knowledge/d1-d7-foundation.json", mod.ARGS)

    def test_real_original_report_excludes_paired_before_counting(self):
        (self.root / "new-old.lisp").write_text("(unknown ())\\n", encoding="utf-8")
        (self.root / "paired.lisp").write_text("()\\n", encoding="utf-8")
        (self.root / "paired.sens").write_bytes(b"\\x00")
        report = {
            "mode": "dry-run",
            "summary": {
                "files_seen": 1,
                "files_written": 0,
                "files_would_write": 0,
                "files_blocked": 1,
                "files_skipped_paired": 1,
            },
            "skipped_paired_paths": ["paired.lisp"],
            "files": [{
                "path": "new-old.lisp", "status": "blocked",
                "reason": "unratified historical unknown",
            }],
        }
        def fake_run(command, **kwargs):
            self.assertIn("--unpaired-only", command)
            self.assertEqual(command[command.index("--source-era")+1], "auto")
            self.assertIn("knowledge/d1-d9-foundation.json", command)
            Path(command[command.index("--report")+1]).write_text(json.dumps(report))
            return subprocess.CompletedProcess(command, 2, "", "")
        with patch.object(mod.subprocess, "run", side_effect=fake_run):
            result = mod.build_report(self.root)
        summary = result["summary"]
        self.assertEqual(summary["scanned"], 1)
        self.assertEqual(summary["blocked"], 1)
        self.assertEqual(summary["already_paired_sources_excluded"], 1)
        self.assertEqual(result["already_paired_sources_excluded"], ["paired.lisp"])
        self.assertEqual(summary["mechanical_candidates"], 0)
        self.assertEqual(result["source_era"], "auto")
        self.assertEqual(summary["original_unpaired_executables_migrated_by_this_tool"], 0)

    def test_false_pair_in_unpaired_ledger_fails_closed(self):
        (self.root / "paired.lisp").write_text("()\\n")
        (self.root / "paired.sens").write_bytes(b"\\x01")
        report = {
            "mode": "dry-run",
            "summary": {
                "files_seen": 1, "files_written": 0,
                "files_would_write": 1, "files_blocked": 0,
                "files_skipped_paired": 0,
            },
            "skipped_paired_paths": [],
            "files": [{
                "path": "paired.lisp", "status": "would-write",
                "bytes": 1, "physical_sha256": "a"*64,
                "typed_word_sha256": "b"*64, "semantic_word_count": 1,
                "passes": {},
            }],
        }
        def fake_run(command, **kwargs):
            Path(command[command.index("--report")+1]).write_text(json.dumps(report))
            return subprocess.CompletedProcess(command, 0, "", "")
        with patch.object(mod.subprocess, "run", side_effect=fake_run):
            with self.assertRaisesRegex(RuntimeError, "already paired"):
                mod.build_report(self.root)


    def test_first_blocker_families_do_not_claim_semantic_admission(self):
        samples = {
            "ambiguous 8-bit head 00001001": "w8-provenance",
            "legacy-unmapped my-lisp function 'print'": "host-effect",
            "legacy-unmapped my-lisp function 'foo'": "unmapped-function",
            "word 2 is not a ratified data domain": "d2-or-domain-data",
            "unbound lexical variable x": "lexical-binding",
            "unratified numeric literal": "numeric-law",
            "text7 symbol not admitted": "text-or-quote",
            "no proof of unknown symbol": "other-unproved",
        }
        for reason, family in samples.items():
            with self.subTest(reason=reason):
                self.assertEqual(mod.blocker_family(reason), family)
                self.assertTrue(mod.BLOCKER_ACTIONS[family])

    def test_exhaustive_sha_pinned_cohorts_are_disjoint_and_stable(self):
        def row(name, reason, sha):
            return {
                "path": name, "source_git_blob_sha": sha,
                "status": "BLOCKED", "same_stem_sens_already_exists": False,
                "reason": reason,
                "source_is_executable_proven": False,
                "independent_semantic_oracle_passed": False,
            }
        sources = [
            row("z.lisp", "ambiguous 8-bit head 00001001", "a"*40),
            row("a.lisp", "word 2 invalid", "b"*40),
            row("b.lisp", "ambiguous 8-bit head 00001011", "c"*40),
        ]
        cohorts = mod.blocker_cohorts(sources)
        self.assertEqual([c["family"] for c in cohorts],
                         ["w8-provenance", "d2-or-domain-data"])
        self.assertEqual([c["count"] for c in cohorts], [2, 1])
        self.assertEqual(
            [x["path"] for x in cohorts[0]["original_sources"]],
            ["b.lisp", "z.lisp"]
        )
        self.assertEqual(
            cohorts[0]["original_sources"][1]["source_git_blob_sha"], "a"*40
        )
        self.assertTrue(all(c["status"] == "BLOCKED_NOT_ORACLE_ADMITTED"
                            for c in cohorts))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            mod.blocker_cohorts(sources + sources[:1])
        with self.assertRaisesRegex(ValueError, "not an unpaired"):
            mod.blocker_cohorts([{**sources[0],
                                  "same_stem_sens_already_exists": True}])

    def test_full_old_original_blocker_rows_retained_not_only_first_20(self):
        for i in range(25):
            (self.root / f"item{i}.lisp").write_text("(unknown)\\n")
        rows = [{"path": f"item{i}.lisp", "status": "blocked",
                 "reason": "ambiguous 8-bit head 00001001" if i%2 else "word 2"}
                for i in range(25)]
        report = {
            "mode": "dry-run",
            "summary": {
                "files_seen": 25, "files_written": 0,
                "files_would_write": 0, "files_blocked": 25,
                "files_skipped_paired": 0,
            },
            "skipped_paired_paths": [],
            "files": rows,
        }
        def fake_run(command, **kwargs):
            Path(command[command.index("--report")+1]).write_text(json.dumps(report))
            return subprocess.CompletedProcess(command, 2, "", "")
        with patch.object(mod.subprocess, "run", side_effect=fake_run):
            result = mod.build_report(self.root)
        self.assertEqual(len(result["blocked_sources"]), 25)
        self.assertEqual(len(result["unpaired_blocker_sample"]), 20)
        self.assertEqual(sum(c["count"] for c in result["blocker_cohorts"]), 25)
        self.assertEqual(result["summary"]["blocker_family_counts"],
                         {"d2-or-domain-data": 13, "w8-provenance": 12})
        self.assertEqual(result["summary"]["mechanical_candidates"], 0)
        self.assertTrue(all(len(x["source_git_blob_sha"]) == 40
                            for x in result["blocked_sources"]))



    def test_exact_w8_and_nonbit_word_cohorts_keep_every_source_sha(self):
        sources = []
        cases = [
            ("a.lisp", "ambiguous W8 executable head 00001001: choose source era", "w8-provenance", "00001001"),
            ("b.lisp", "ambiguous W8 executable head 00001001: choose source era", "w8-provenance", "00001001"),
            ("c.lisp", "ambiguous W8 executable head 00001011: choose source era", "w8-provenance", "00001011"),
            ("d.lisp", "word 2: requires exact D1-D9 binary word", "d2-or-domain-data", "word2"),
            ("e.lisp", "word 3: requires exact D1-D9 binary word", "d2-or-domain-data", "word3"),
        ]
        for path, reason, _, _ in cases:
            sources.append({
                "path": path, "source_git_blob_sha": "a"*40,
                "same_stem_sens_already_exists": False,
                "status": "BLOCKED", "reason": reason,
            })
        out = mod.blocker_coordinate_cohorts(sources)
        self.assertEqual(sum(x["count"] for x in out), len(sources))
        self.assertEqual(out[0]["family"], "w8-provenance")
        self.assertEqual(out[0]["coordinate"], "00001001")
        self.assertEqual(out[0]["count"], 2)
        self.assertEqual(out[0]["owner_issue"], "#4459")
        self.assertEqual(len({x["path"] for g in out for x in g["original_sources"]}), 5)
        self.assertEqual({g["coordinate"] for g in out if g["family"]=="w8-provenance"},
                         {"00001001", "00001011"})
        self.assertTrue(all(g["status"]=="FIRST_BLOCK_ONLY_NOT_SEMANTICALLY_ADMITTED" for g in out))

    def test_exact_coordinate_split_never_relabels_originals_as_certified(self):
        a = {"path":"old.lisp","source_git_blob_sha":"f"*40,
             "same_stem_sens_already_exists":False,"status":"BLOCKED",
             "reason":"legacy-unmapped SID8/Sens8 00100010 no resident"}
        self.assertEqual(mod.blocker_coordinate_cohorts([a])[0]["coordinate"],"00100010")
        with self.assertRaisesRegex(ValueError,"duplicate"):
            mod.blocker_coordinate_cohorts([a,a])
        with self.assertRaisesRegex(ValueError,"exact Git blob"):
            mod.blocker_coordinate_cohorts([{**a,"source_git_blob_sha":"0"*39}])
        with self.assertRaisesRegex(ValueError,"unpaired BLOCK"):
            mod.blocker_coordinate_cohorts([{**a,"status":"CANDIDATE_NOT_ADMITTED"}])
        self.assertEqual(mod.blocker_coordinate_cohorts([]), [])

    def test_reviewed_isa_catalogues_are_data_not_executable_candidates(self):
        # Real manifest and REAL tracked sources: no synthetic pairs credited.
        rows = mod.load_nonprogram_classification(ROOT)
        isa = [x for x in rows.values() if x["cohort"] == "isa"]
        self.assertEqual(len(isa), 25)
        self.assertTrue(all(x["source_class"] == "NONPROGRAM_DATA_REVIEWED"
                            for x in isa))
        self.assertTrue(all(not x["automatic_sens_companion"] for x in isa))
        self.assertNotIn("lib/core1.lisp", rows)
        self.assertNotIn("lib/machine/block.lisp", rows)
        self.assertNotIn("benchmarks/arithmetic.lisp", rows)

    def test_reviewed_nonprogram_blob_drift_and_forged_pair_fail_closed(self):
        source = self.root / "item.lisp"
        source.write_text("(isa-catalogue/1)\n", encoding="utf-8")
        sha = mod.git_blob_sha(source)
        row = mod._checked_nonprogram_entry(self.root, "item.lisp", sha)
        self.assertEqual(row["source_git_blob_sha"], sha)
        self.assertFalse(row["semantic_oracle_admitted"])
        with self.assertRaisesRegex(ValueError, "drift"):
            mod._checked_nonprogram_entry(self.root, "item.lisp", "a" * 40)
        source.with_suffix(".sens").write_bytes(b"invalid")
        with self.assertRaisesRegex(ValueError, "unproven physical pair"):
            mod._checked_nonprogram_entry(self.root, "item.lisp", sha)

    def test_nonprogram_loader_never_accepts_arbitrary_executable_claim(self):
        src = self.root / "lib/core1.lisp"
        src.parent.mkdir(parents=True)
        src.write_text("(DEFINE x (QUOTE ()))\n", encoding="utf-8")
        folder = self.root / "knowledge"
        folder.mkdir()
        manifest = folder / "migration-nonprogram-isa-manifest-2026-10-08.json"
        manifest.write_text(json.dumps({
            "schema": "sens-migration-nonprogram-manifest/1",
            "automatic_sens_companion": False,
            "issue": 4460,
            "entries": [{"path": "lib/core1.lisp",
                         "git_blob_sha1": mod.git_blob_sha(src)}] * 25,
        }), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "mis-scoped ISA catalogue"):
            mod.load_nonprogram_classification(self.root)


    def test_priority_queue_excludes_reviewed_data_but_retains_raw_census(self):
        for name in ("record.lisp", "program.lisp"):
            (self.root / name).write_text("(unknown)\n", encoding="utf-8")
        raw = {
            "mode": "dry-run",
            "summary": {
                "files_seen": 2, "files_written": 0,
                "files_would_write": 0, "files_blocked": 2,
                "files_skipped_paired": 0,
            },
            "skipped_paired_paths": [],
            "files": [
                {"path": "record.lisp", "status": "blocked", "reason": "word 2"},
                {"path": "program.lisp", "status": "blocked",
                 "reason": "ambiguous 8-bit head 00001001"},
            ],
        }
        verified_data = {
            "record.lisp": {
                "path": "record.lisp",
                "source_class": "NONPROGRAM_DATA_REVIEWED",
                "cohort": "schema",
                "source_git_blob_sha": mod.git_blob_sha(self.root / "record.lisp"),
                "automatic_sens_companion": False,
                "semantic_oracle_admitted": False,
            }
        }
        def fake_run(command, **kwargs):
            Path(command[command.index("--report") + 1]).write_text(
                json.dumps(raw), encoding="utf-8"
            )
            return subprocess.CompletedProcess(command, 2, "", "")
        with patch.object(mod.subprocess, "run", side_effect=fake_run), \
             patch.object(mod, "load_nonprogram_classification",
                          return_value=verified_data):
            result = mod.build_report(self.root)
        summary = result["summary"]
        self.assertEqual(summary["scanned"], 2)
        self.assertEqual(summary["blocked"], 2)
        self.assertEqual(summary["classified_nonprogram"], 1)
        self.assertEqual(summary["blocked_excluding_classified_nonprogram"], 1)
        self.assertEqual(summary["mechanical_candidates"], 0)
        self.assertEqual(summary["physical_outputs_created"], 0)
        self.assertEqual(result["priority_blocker_sample"][0]["path"], "program.lisp")
        self.assertEqual(result["nonprogram_classification"][0]["path"], "record.lisp")
        self.assertEqual(result["blocked_sources"][0]["path"], "program.lisp")


if __name__ == "__main__":
    unittest.main()
