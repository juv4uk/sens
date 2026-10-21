#!/usr/bin/env python3
"""SHA можна переприв'язати після локалізації коментарів, але не даних."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from refresh_nonprogram_comment_pins import blob_sha, repin_row


class CommentPinsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sens-repin-")
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.file = self.root / "lib" / "machine" / "isa" / "adx.lisp"
        self.file.parent.mkdir(parents=True)
        original = b"; Old English comment\n(isa-catalogue-1 (extension ADX))\n"
        self.file.write_bytes(original)
        self.old = subprocess.run(
            ["git", "-C", str(self.root), "hash-object", "-w", "--stdin"],
            input=original, capture_output=True, check=True,
        ).stdout.decode().strip()
        self.row = {"path": "lib/machine/isa/adx.lisp", "git_blob_sha1": self.old}

    def tearDown(self):
        self.temp.cleanup()

    def test_comments_and_whitespace_only_are_repin_eligible(self):
        self.file.write_text("; Українська примітка\n\n(isa-catalogue-1   (extension ADX))\n")
        self.assertEqual(repin_row(self.root, self.row),
                         (self.old, blob_sha(self.file.read_bytes())))
        self.assertEqual(self.row["git_blob_sha1"], self.old)

    def test_protocol_data_changes_fail_closed(self):
        self.file.write_text("; Українська примітка\n(isa-catalogue-1 (extension AVX))\n")
        with self.assertRaisesRegex(ValueError, "ЗМІНА СЕМАНТИКИ АБО ДАНИХ"):
            repin_row(self.root, self.row)

    def test_unavailable_old_blob_is_not_automatically_replaced(self):
        self.file.write_text("; Українська примітка\n(isa-catalogue-1 (extension ADX))\n")
        self.row["git_blob_sha1"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "немає попереднього Git blob"):
            repin_row(self.root, self.row)

    def test_a_physical_companion_is_not_permitted_for_data(self):
        self.file.with_suffix(".sens").write_bytes(b"unadmitted")
        with self.assertRaisesRegex(ValueError, "має .sens"):
            repin_row(self.root, self.row)

    def test_parent_escape_is_rejected(self):
        self.row["path"] = "../escape.lisp"
        with self.assertRaisesRegex(ValueError, "небезпечний шлях"):
            repin_row(self.root, self.row)


if __name__ == "__main__":
    unittest.main()
