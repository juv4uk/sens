#!/usr/bin/env python3
"""Verify real Git ancestry, clean candidate and content-equivalent replay."""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_branch_merges as audit


class BranchCensusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_cwd = Path.cwd()
        os.chdir(self.tmp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "merge-test@example.com")
        self.git("config", "user.name", "Merge Census Test")
        Path("a.txt").write_text("zero\n")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        base = self.git("rev-parse", "HEAD").strip()
        self.git("branch", "-M", "main")
        self.git("branch", "research/new", base)
        self.git("branch", "research/equivalent", base)
        Path("a.txt").write_text("one\n")
        self.git("commit", "-qam", "main change")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.git("checkout", "-q", "research/new")
        Path("b.txt").write_text("new\n")
        self.git("add", ".")
        self.git("commit", "-qm", "new branch only")
        self.git("update-ref", "refs/remotes/origin/research/new", "HEAD")
        self.git("checkout", "-q", "research/equivalent")
        Path("a.txt").write_text("one\n")
        self.git("commit", "-qam", "independent same content")
        self.git("update-ref", "refs/remotes/origin/research/equivalent", "HEAD")
        self.git("checkout", "-q", "main")

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.tmp.cleanup()

    @staticmethod
    def git(*args):
        return subprocess.check_output(["git", *args], text=True)

    def test_research_mergeable_and_replayed(self):
        now = datetime.now(timezone.utc)
        new = audit.classify("origin/main", "origin/research/new", now, 300)
        same = audit.classify("origin/main", "origin/research/equivalent", now, 300)
        self.assertTrue(new["recent_72h"])
        self.assertTrue(new["research"])
        self.assertEqual(new["status"], "MERGEABLE_NEEDS_CI")
        self.assertEqual(new["unique_content_paths"], 1)
        self.assertEqual(same["status"], "CONTENT_EQUIVALENT")
        self.assertEqual(same["unique_content_paths"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
