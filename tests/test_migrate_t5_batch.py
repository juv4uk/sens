#!/usr/bin/env python3
"""End-to-end safe batch regression using existing REAL Core1 executable .lisp."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
DRIVER = REPO / "scripts/migrate-t5-batch.py"
PROVEN = REPO / "tests/fixtures/core1-third-domain-canary/third"

class RealBatchTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "repo"
        self.root.mkdir()
        (self.root / "lib").mkdir()
        self.out = self.base / "mirror"
        self.report = self.base / "report.json"
        shutil.copy2(PROVEN.with_suffix(".lisp"), self.root / "lib/third.lisp")
        (self.root / "lib/unknown.lisp").write_text("(UNKNOWN ())\n", encoding="utf-8")

    def call(self, *paths, write=False, out=None, era="legacy"):
        return subprocess.run([
            sys.executable, str(DRIVER), *paths, "--root", str(self.root),
            "--out", str(out or self.out), "--report", str(self.report),
            *(["--source-era", era] if era else []),
            *(["--write"] if write else []),
        ], text=True, capture_output=True)

    def test_real_existing_core1_converts_to_exact_physical_t5(self):
        before = (self.root / "lib/third.lisp").read_bytes()
        expected = PROVEN.with_suffix(".sens").read_bytes()
        dry = self.call("lib/third.lisp")
        self.assertEqual(dry.returncode, 0, dry.stderr + dry.stdout)
        self.assertFalse(self.out.exists())
        result = json.loads(self.report.read_text())
        self.assertEqual(result["summary"]["files_would_write"], 1)
        self.assertEqual(result["files"][0]["status"], "would-write")
        self.assertEqual(result["files"][0]["physical_bytes"], len(expected))
        live = self.call("lib/third.lisp", write=True)
        self.assertEqual(live.returncode, 0, live.stderr + live.stdout)
        self.assertEqual((self.out / "lib/third.sens").read_bytes(), expected)
        self.assertEqual((self.root / "lib/third.lisp").read_bytes(), before)
        self.assertFalse((self.out / "lib/third").exists())
        rerun = self.call("lib/third.lisp", write=True)
        self.assertEqual(rerun.returncode, 2)
        self.assertEqual((self.out / "lib/third.sens").read_bytes(), expected)

    def test_auto_blocks_ambiguous_historical_w8_without_writing(self):
        # The real previously admitted C1-THIRD source uses historical
        # exact-eight heads; unqualified W8 is NOT proof of a modern D8 call.
        p = self.call("lib/third.lisp", write=True, era=None)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        doc = json.loads(self.report.read_text())
        self.assertEqual(doc["authority"]["source_era"], "auto")
        self.assertEqual(doc["summary"]["files_written"], 0)
        self.assertIn("ambiguous W8", doc["files"][0]["reason"])
        self.assertFalse((self.out / "lib/third.sens").exists())

    def test_explicit_legacy_is_recorded_and_cannot_be_inferred(self):
        p = self.call("lib/third.lisp", write=True, era="legacy")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        doc = json.loads(self.report.read_text())
        self.assertEqual(doc["authority"]["source_era"], "legacy")
        self.assertEqual(doc["files"][0]["source_era"], "legacy")
        self.assertEqual(doc["files"][0]["passes"]["pass1-sens8"], 16)
        self.assertEqual((self.out / "lib/third.sens").read_bytes(),
                         PROVEN.with_suffix(".sens").read_bytes())

    def test_current_d8_head_stays_exact_and_legacy_is_not_guessed(self):
        src = self.root / "lib/current.lisp"
        src.write_text("(10000000 ())\n", encoding="utf-8")
        p = self.call("lib/current.lisp", era="auto")
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertIn("ambiguous W8", json.loads(self.report.read_text())
                      ["files"][0]["reason"])
        p = self.call("lib/current.lisp", era="current", write=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        data = json.loads(self.report.read_text())
        self.assertEqual(data["files"][0]["passes"]["already-exact"], 1)
        self.assertEqual(data["files"][0]["passes"]["pass1-sens8"], 0)
        self.assertEqual(data["authority"]["source_era"], "current")
        self.assertTrue((self.out / "lib/current.sens").is_file())

    def test_mixed_selection_reports_real_blocks_and_preserves_admitted(self):
        p = self.call("lib", write=True)
        self.assertEqual(p.returncode, 2, p.stderr + p.stdout)
        doc = json.loads(self.report.read_text())
        self.assertEqual(doc["summary"]["files_seen"], 2)
        self.assertEqual(doc["summary"]["files_written"], 0)
        self.assertEqual(doc["summary"]["files_would_write"], 1)
        self.assertEqual(doc["summary"]["files_blocked"], 1)
        self.assertEqual(doc["files"][0]["status"], "would-write")
        self.assertEqual(doc["files"][1]["status"], "blocked")
        self.assertFalse((self.out / "lib/third.sens").exists())
        self.assertFalse((self.out / "lib/unknown.sens").exists())

    def test_two_proven_sources_publish_as_one_transaction(self):
        branch = REPO / "tests/fixtures/migration-d1-cond-cohort/branch.lisp"
        shutil.copy2(branch, self.root / "lib/branch.lisp")
        p = self.call("lib/third.lisp", "lib/branch.lisp", write=True)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        doc = json.loads(self.report.read_text())
        self.assertEqual(doc["summary"]["files_written"], 2)
        self.assertEqual(doc["summary"]["files_blocked"], 0)
        self.assertEqual(
            (self.out / "lib/third.sens").read_bytes(),
            PROVEN.with_suffix(".sens").read_bytes()
        )
        self.assertEqual(
            (self.out / "lib/branch.sens").read_bytes(),
            branch.with_suffix(".sens").read_bytes()
        )

    def test_existing_target_in_group_blocks_every_other_write(self):
        # A pre-existing destination is never overwritten, AND no other
        # candidate in the cohort may be published if this one BLOCKS.
        branch = REPO / "tests/fixtures/migration-d1-cond-cohort/branch.lisp"
        shutil.copy2(branch, self.root / "lib/branch.lisp")
        (self.out / "lib").mkdir(parents=True)
        (self.out / "lib/branch.sens").write_bytes(b"sentinel")
        p = self.call("lib/third.lisp", "lib/branch.lisp", write=True)
        self.assertEqual(p.returncode, 2, p.stderr + p.stdout)
        d = json.loads(self.report.read_text())
        self.assertEqual(d["summary"]["files_written"], 0)
        self.assertEqual(d["summary"]["files_would_write"], 1)
        self.assertEqual(d["summary"]["files_blocked"], 1)
        self.assertEqual((self.out / "lib/branch.sens").read_bytes(), b"sentinel")
        self.assertFalse((self.out / "lib/third.sens").exists())

    def test_mid_transaction_writer_failure_rolls_back_created_binary(self):
        branch = REPO / "tests/fixtures/migration-d1-cond-cohort/branch.lisp"
        shutil.copy2(branch, self.root / "lib/branch.lisp")
        spec = importlib.util.spec_from_file_location(
            "sens_atomic_batch_test_impl", DRIVER)
        assert spec is not None and spec.loader is not None
        batch = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(batch)
        original_writer = batch.mig.write_atomic_no_clobber
        calls = []

        def intermittent_writer(target, payload):
            calls.append(target)
            if len(calls) == 2:
                raise OSError("test injected second-write failure")
            original_writer(target, payload)

        args = argparse.Namespace(
            paths=["lib/branch.lisp", "lib/third.lisp"], root=self.root,
            out=self.out, report=self.report, source_era="legacy", write=True,
        )
        with patch.object(batch.mig, "write_atomic_no_clobber",
                          side_effect=intermittent_writer):
            outcome = batch.run(args)
        self.assertEqual(len(calls), 2)
        self.assertEqual(outcome["summary"]["files_written"], 0)
        self.assertEqual(outcome["summary"]["files_blocked"], 1)
        self.assertEqual(outcome["summary"]["files_would_write"], 1)
        self.assertIn("atomic batch aborted",
                      str([e.get("reason", "") for e in outcome["files"]]))
        self.assertFalse((self.out / "lib/branch.sens").exists())
        self.assertFalse((self.out / "lib/third.sens").exists())
        self.assertEqual((self.root / "lib/branch.lisp").read_bytes(),
                         branch.read_bytes())

    def test_symlinks_traversal_bad_suffix_and_absent_sources_are_rejected(self):
        (self.root / "lib/link.lisp").symlink_to(self.root / "lib/third.lisp")
        for value in ("lib/link.lisp", "../external.lisp",
                      "/etc/passwd", "lib/third.sens", "no-such-file.lisp"):
            with self.subTest(value=value):
                p = self.call(value, write=True)
                self.assertEqual(p.returncode, 2, p.stderr + p.stdout)
                self.assertEqual(json.loads(self.report.read_text())
                                 ["summary"]["files_written"], 0)
        self.assertFalse((self.out / "lib/link.sens").exists())

    def test_refuse_outputs_inside_source_root(self):
        result = self.call("lib/third.lisp", write=True, out=self.root / "out")
        self.assertEqual(result.returncode, 3)
        self.assertFalse((self.root / "out").exists())

    def test_duplicate_paths_are_processed_once(self):
        result = self.call("lib/third.lisp", "lib/third.lisp", write=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(self.report.read_text())
                         ["summary"]["files_written"], 1)

if __name__ == "__main__":
    unittest.main()
