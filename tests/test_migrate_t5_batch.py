#!/usr/bin/env python3
"""End-to-end safe batch regression using existing REAL Core1 executable .lisp."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

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

    def call(self, *paths, write=False, out=None):
        return subprocess.run([
            sys.executable, str(DRIVER), *paths, "--root", str(self.root),
            "--out", str(out or self.out), "--report", str(self.report),
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

    def test_mixed_selection_reports_real_blocks_and_preserves_admitted(self):
        p = self.call("lib", write=True)
        self.assertEqual(p.returncode, 2, p.stderr + p.stdout)
        doc = json.loads(self.report.read_text())
        self.assertEqual(doc["summary"]["files_seen"], 2)
        self.assertEqual(doc["summary"]["files_written"], 1)
        self.assertEqual(doc["summary"]["files_blocked"], 1)
        self.assertEqual(doc["files"][1]["status"], "blocked")
        self.assertFalse((self.out / "lib/unknown.sens").exists())

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
