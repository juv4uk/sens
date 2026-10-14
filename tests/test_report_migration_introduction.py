#!/usr/bin/env python3
"""Five synthetic Git-history witnesses for the read-only pickaxe reporter."""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "report_migration_introduction.py"
spec = importlib.util.spec_from_file_location("migration_pickaxe", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HistoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git_cmd("init", "-q")
        self.git_cmd("config", "user.name", "SENS fixture")
        self.git_cmd("config", "user.email", "fixture@example.invalid")
        (self.root / "lib").mkdir()
        self.path = self.root / "lib" / "one.lisp"

    def git_cmd(self, *args):
        return subprocess.check_output(
            ["git", "-C", str(self.root), *args], text=True).strip()

    def commit(self, text):
        self.path.write_text(text, encoding="utf-8")
        self.git_cmd("add", "-A")
        self.git_cmd("commit", "-qm", "fixture")
        return self.git_cmd("rev-parse", "HEAD")

    def test_first_addition_and_removal_are_distinct_events(self):
        first = self.commit("(0010 before)\n")
        added = self.commit("(0010 before)\n(111 marker)\n")
        removed = self.commit("(0010 before)\n")
        report = module.inspect(self.root, "lib/one.lisp", "(111 marker)")
        self.assertEqual(first, self.git_cmd("rev-parse", "HEAD~2"))
        self.assertEqual(2, report["event_count"])
        self.assertEqual(added, report["first_observed_delta"]["sha"])
        self.assertEqual([added, removed], [e["sha"] for e in report["events"]])
        self.assertEqual("READ_ONLY_PROVENANCE_NOT_SEMANTIC_AUTHORITY", report["role"])

    def test_follow_records_origin_before_rename(self):
        introduced = self.commit("(111 marker)\n")
        self.git_cmd("mv", "lib/one.lisp", "lib/renamed.lisp")
        self.git_cmd("commit", "-qm", "rename")
        report = module.inspect(self.root, "lib/renamed.lisp", "(111 marker)")
        self.assertEqual(introduced, report["first_observed_delta"]["sha"])
        self.assertEqual(1, report["event_count"])

    def test_no_match_does_not_infer_ratification(self):
        self.commit("(0010 bootstrap)\n")
        report = module.inspect(self.root, "lib/one.lisp", "D8 pre-ratification")
        self.assertIsNone(report["first_observed_delta"])
        self.assertEqual(0, report["event_count"])

    def test_symlink_and_bad_paths_fail_closed(self):
        self.commit("(0010 original)\n")
        (self.root / "lib" / "link.lisp").symlink_to("one.lisp")
        self.git_cmd("add", "-A")
        self.git_cmd("commit", "-qm", "symlink")
        for path in ("lib/link.lisp", "../outside.lisp", "/tmp/path",
                     "lib//one.lisp"):
            with self.subTest(path=path):
                with self.assertRaises(module.HistoryError):
                    module.inspect(self.root, path, "(0010")

    def test_limit_keeps_full_count(self):
        self.commit("(0010 before)\n")
        self.commit("(111 marker)\n")
        self.commit("(0010 before)\n")
        report = module.inspect(self.root, "lib/one.lisp", "marker", limit=1)
        self.assertEqual(2, report["event_count"])
        self.assertTrue(report["truncated"])
        self.assertEqual(1, len(report["events"]))


if __name__ == "__main__":
    unittest.main()
