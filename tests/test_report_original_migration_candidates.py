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

    def test_pinned_historical_benchmark_stays_archive_only(self):
        rel = ("benchmarks/sens-surface/results/"
               "20260925-icount-33bfb53a/programs/empty-en.lisp")
        source = ROOT / rel
        self.assertEqual(mod.git_blob_sha(source),
                         "6e30e07f9a44391fb341f5e0ff21ba1e682b5d0f")
        row = mod.categorize({
            "path": rel, "status": "would-write",
            "bytes": 4, "physical_sha256": "a"*64,
            "typed_word_sha256": "b"*64,
            "semantic_word_count": 5, "passes": {"pass2-my-lisp": 1},
        }, ROOT)
        self.assertEqual(row["source_scope"], "ARCHIVED_BENCHMARK_NONPROGRAM")
        self.assertFalse(row["source_is_executable_proven"])
        self.assertFalse(row["independent_semantic_oracle_passed"])

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


    def test_reviewed_source_manifests_are_sha_pinned_nonexecutables(self):
        entries = mod.load_nonprogram_classification(ROOT)
        approved = {
            cohort: count for cohort, manifest, count in mod.NONPROGRAM_MANIFESTS
            if (ROOT / manifest).is_file()
        }
        self.assertEqual(len(entries), sum(approved.values()))
        self.assertEqual({
            cohort: sum(e["cohort"] == cohort for e in entries.values())
            for cohort in approved
        }, approved)
        self.assertEqual(approved.get("knowledge-record"), 14)
        self.assertTrue(all(not e["automatic_sens_companion"]
                            and not e["semantic_oracle_admitted"]
                            for e in entries.values()))
        for path in ("lib/core1.lisp", "lib/machine/block.lisp",
                     "benchmarks/arithmetic.lisp"):
            self.assertNotIn(path, entries)

    def test_data_manifest_rejects_source_drift_and_existing_physical_sens(self):
        p = self.root / "lib/machine/isa/sample.lisp"
        p.parent.mkdir(parents=True)
        p.write_text("(isa-catalogue/1)\n", encoding="utf-8")
        hash1 = mod.git_blob_sha(p)
        entry = mod._checked_nonprogram_entry(
            self.root, "lib/machine/isa/sample.lisp", hash1)
        self.assertEqual(entry["source_git_blob_sha"], hash1)
        self.assertEqual(entry["source_class"], "NONPROGRAM_DATA_REVIEWED")
        with self.assertRaisesRegex(ValueError, "drift"):
            mod._checked_nonprogram_entry(
                self.root, "lib/machine/isa/sample.lisp", "a" * 40)
        p.with_suffix(".sens").write_bytes(b"forbidden")
        with self.assertRaisesRegex(ValueError, "unproven physical pair"):
            mod._checked_nonprogram_entry(
                self.root, "lib/machine/isa/sample.lisp", hash1)

    def test_forged_executable_cannot_enter_data_isa_cohort(self):
        p = self.root / "lib/core1.lisp"
        p.parent.mkdir(parents=True)
        p.write_text("(DEFINE x (QUOTE ()))\n", encoding="utf-8")
        f = self.root / "knowledge/migration-nonprogram-isa-manifest-2026-10-08.json"
        f.parent.mkdir(parents=True)
        f.write_text(json.dumps({
            "schema": "sens-migration-nonprogram-manifest/1",
            "issue": 4460,
            "automatic_sens_companion": False,
            "entries": [{
                "path": "lib/core1.lisp",
                "git_blob_sha1": mod.git_blob_sha(p)
            }] * 25,
        }), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "mis-scoped ISA catalogue"):
            mod.load_nonprogram_classification(self.root)


    def test_exact_comment_only_loader_sources_are_data_not_executable(self):
        entries = mod.load_nonprogram_classification(ROOT)
        expected = {
            "lib/core2.lisp": "9a39a1d341dde7faf3a1899b52f78a7b1e931783",
            "lib/surface/ukr.lisp": "f5577917e72f2661cb64b277afc85122276d13c7",
        }
        for path, digest in expected.items():
            self.assertIn(path, entries)
            self.assertEqual(entries[path]["source_git_blob_sha"], digest)
            self.assertEqual(entries[path]["source_class"], "NONPROGRAM_DATA_REVIEWED")
            self.assertEqual(entries[path]["cohort"], "comment-only-loader")
            self.assertFalse(entries[path]["semantic_oracle_admitted"])
            self.assertFalse(entries[path]["automatic_sens_companion"])
            content = (ROOT / path).read_text(encoding="utf-8")
            self.assertTrue(all(
                not row.strip() or row.lstrip().startswith(";")
                for row in content.splitlines()
            ), f"comment-only loader must not have executable forms: {path}")
            self.assertFalse((ROOT / path).with_suffix(".sens").exists())

    def test_comment_only_classification_rejects_forged_executable_even_pinned(self):
        paths = ("lib/core2.lisp", "lib/surface/ukr.lisp")
        entries = []
        for path in paths:
            current = ROOT / path
            source = self.root / path
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(current.read_bytes())
            entries.append({"path": path, "git_blob_sha1": mod.git_blob_sha(source)})
        manifest = self.root / "knowledge/migration-nonprogram-comment-only-loaders-2026-10-08.json"
        manifest.parent.mkdir(parents=True)
        payload = {
            "schema": "sens-migration-nonprogram-manifest/1",
            "issue": 4460,
            "automatic_sens_companion": False,
            "entries": entries,
        }
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        self.assertEqual(len(mod.load_nonprogram_classification(self.root)), 2)
        source = self.root / paths[0]
        source.write_text(source.read_text(encoding="utf-8") + "(00001001 new-fn 00001000)\n", encoding="utf-8")
        # Adversary updates manifest SHA to match a newly injected executable.
        # The *lexical content guard*, not just the SHA pin, must still refuse.
        payload["entries"][0]["git_blob_sha1"] = mod.git_blob_sha(source)
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "executable forms"):
            mod.load_nonprogram_classification(self.root)
        payload["entries"][0]["path"] = "lib/core1.lisp"
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        p = self.root / "lib/core1.lisp"
        p.write_text("; fake empty file\n", encoding="utf-8")
        payload["entries"][0]["git_blob_sha1"] = mod.git_blob_sha(p)
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unreviewed comment-only loader path"):
            mod.load_nonprogram_classification(self.root)

    def test_ratified_domain_tables_are_data_not_executable_migration(self):
        classified = mod.load_nonprogram_classification(ROOT)
        rows = [v for v in classified.values() if v["cohort"] == "domain-table"]
        self.assertEqual(len(rows), 9)
        self.assertEqual(
            sorted(r["path"] for r in rows),
            sorted(f"lib/domains/d{i}.lisp" for i in range(1, 10)),
        )
        self.assertTrue(all(r["source_class"] == "NONPROGRAM_DATA_REVIEWED"
                            and r["semantic_oracle_admitted"] is False
                            and r["automatic_sens_companion"] is False for r in rows))
        self.assertNotIn("lib/domains/d10.lisp", classified)
        self.assertNotIn("lib/core1.lisp", classified)


if __name__ == "__main__":
    unittest.main()
