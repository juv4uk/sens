#!/usr/bin/env python3
"""Реальні Git-репозиторії перевіряють delta, не лише синтетичні списки."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from guard_t5_triplet_delta import inspect, main
from sens_t5_codec import encode_words

WORDS = ["10", "000", "01"]
PHYSICAL = encode_words(WORDS)
VIEW = (" ".join(WORDS) + "\n").encode("ascii")


class IncrementalTripletGate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sens-git-triplet-")
        self.root = Path(self.temp.name)
        self.cmd("init", "-q")
        self.cmd("config", "user.email", "ci@sens.invalid")
        self.cmd("config", "user.name", "SENS Test")
        # Ancient valid physical pair has NO view. This admitted baseline debt
        # must never stop unrelated PRs, and must not count as release GREEN.
        (self.root / "old.lisp").write_text("(старий)\n", encoding="utf-8")
        (self.root / "old.sens").write_bytes(PHYSICAL)
        self.commit("old baseline")
        self.base = self.cmd("rev-parse", "HEAD").strip()

    def tearDown(self):
        self.temp.cleanup()

    def cmd(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args],
                                capture_output=True, text=True, check=True)
        return result.stdout

    def commit(self, message="test"):
        self.cmd("add", "-A")
        self.cmd("commit", "-qm", message)

    def new_pair(self, *, sens="new.sens", with_view=True):
        stem = self.root / sens[:-5]
        stem.parent.mkdir(parents=True, exist_ok=True)
        stem.with_suffix(".lisp").write_text("(так)\n", encoding="utf-8")
        stem.with_suffix(".sens").write_bytes(PHYSICAL)
        if with_view:
            stem.write_bytes(VIEW)
        self.commit("new pair")
        return stem

    def scan(self):
        return inspect(self.root, base=self.base)

    def test_unrelated_change_does_not_turn_ancient_missing_view_red(self):
        (self.root / "README.md").write_text("не змінює SENS\n", encoding="utf-8")
        self.commit("docs")
        result = self.scan()
        self.assertEqual(result["status"], "DELTA_PHYSICAL_VIEW_ONLY_UK_PENDING")
        self.assertEqual(result["summary"]["changed_pairs"], 0)
        self.assertEqual(result["summary"]["historical_missing_views_remain_release_debt"], 1)
        self.assertEqual(result["summary"]["release_admitted"], 0)

    def test_new_physical_without_view_is_rejected(self):
        self.new_pair(with_view=False)
        row = self.scan()["files"][0]
        self.assertEqual(row["status"], "BLOCKED")
        self.assertEqual(row["view_status"], "MISSING_VIEW")
        self.assertEqual(self.scan()["summary"]["changed_blocked"], 1)

    def test_new_complete_triplet_passes_transport_but_not_uk_oracle(self):
        self.new_pair(with_view=True)
        result = self.scan()
        self.assertEqual(result["status"], "DELTA_PHYSICAL_VIEW_ONLY_UK_PENDING")
        self.assertEqual(result["summary"]["changed_verified_transport"], 1)
        self.assertEqual(result["summary"]["historical_missing_views_remain_release_debt"], 1)
        self.assertEqual(result["summary"]["uk_oracle_verified"], 0)
        self.assertEqual(result["summary"]["original_executable_migrations_certified"], 0)
        self.assertEqual(result["files"][0]["uk_oracle"], "NOT_VERIFIED")
        self.assertEqual(result["files"][0]["view_sha256"],
                         result["files"][0]["view_sha256"])

    def test_existing_binary_modified_without_matching_view_is_rejected(self):
        old = self.root / "old"
        old.write_bytes(VIEW)
        self.commit("initially add old view")
        self.base = self.cmd("rev-parse", "HEAD").strip()
        (self.root / "old.sens").write_bytes(encode_words(["10", "001", "01"]))
        self.commit("binary changes only")
        result = self.scan()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["files"][0]["view_status"], "VIEW_MISMATCH")

    def test_view_modified_without_binary_change_is_rejected(self):
        old = self.root / "old"
        old.write_bytes(VIEW)
        self.commit("backfill baseline view")
        self.base = self.cmd("rev-parse", "HEAD").strip()
        old.write_bytes(b"10 000 01 \n")
        self.commit("stale view")
        result = self.scan()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["changed_paths"][0]["kind"], "view")

    def test_deleted_view_is_detected_without_changes_to_binary(self):
        old = self.root / "old"
        old.write_bytes(VIEW)
        self.commit("good view")
        self.base = self.cmd("rev-parse", "HEAD").strip()
        old.unlink()
        self.commit("remove view")
        result = self.scan()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["files"][0]["view_status"], "MISSING_VIEW")

    def test_deleted_physical_program_not_mistaken_for_no_change(self):
        (self.root / "old.sens").unlink()
        self.commit("delete physical")
        result = self.scan()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("deleted", result["files"][0]["reason"])

    def test_changed_physical_symlink_view_is_blocked(self):
        self.new_pair(with_view=True)
        view = self.root / "new"
        target = self.root / "view-target"
        target.write_bytes(VIEW)
        view.unlink()
        view.symlink_to(target)
        self.commit("replace view with symlink")
        self.assertEqual(self.scan()["status"], "BLOCKED")

    def test_existing_view_typechange_to_symlink_never_bypasses_delta(self):
        old = self.root / "old"
        old.write_bytes(VIEW)
        self.commit("regular baseline view")
        self.base = self.cmd("rev-parse", "HEAD").strip()
        original = self.root / "other-view"
        original.write_bytes(VIEW)
        old.unlink()
        old.symlink_to(original)
        self.commit("T status replaces tracked regular view by a symlink")
        result = self.scan()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["files"][0]["view_status"], "UNSAFE_LINK")
        self.assertTrue(any(row["change"] == "T" for row in result["changed_paths"]))

    def test_nested_pair_uses_relative_same_stem(self):
        self.new_pair(sens="lib/диво.sens", with_view=True)
        result = self.scan()
        self.assertEqual(result["status"], "DELTA_PHYSICAL_VIEW_ONLY_UK_PENDING")
        self.assertEqual(result["files"][0]["sens"], "lib/диво.sens")

    def test_no_base_or_unsafe_ref_never_succeeds(self):
        for sha in ("main", "0" * 40, "../abc", "a" * 38):
            with self.subTest(sha=sha), self.assertRaises(ValueError):
                inspect(self.root, base=sha)

    def test_cli_succeeds_with_strict_delta_and_never_writes(self):
        self.new_pair(with_view=True)
        before = (self.root / "new.sens").read_bytes()
        self.assertEqual(main(["--root", str(self.root),
                               "--base-sha", self.base]), 0)
        self.assertEqual((self.root / "new.sens").read_bytes(), before)

    def test_real_main_python_source_is_reused_not_reimplemented(self):
        source = (ROOT / "scripts" / "guard_t5_triplet_delta.py").read_text(encoding="utf-8")
        self.assertIn("from report_t5_triplet_inventory import inspect", source)
        self.assertNotIn("def encode_words", source)


if __name__ == "__main__":
    unittest.main()
