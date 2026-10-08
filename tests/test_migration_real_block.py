#!/usr/bin/env python3
"""Regression: original machine-block cannot yet become a current D2 T5 program.

The previously committed 343-byte T5 transport blob was rejected by the
actual Rust sens-trit D2 parser. The canonical migrator also rejected its
original tracked .lisp. Never claim source migration solely from valid bytes.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE_REL = "lib/machine/block.lisp"
PHYSICAL_REL = "lib/machine/block.sens"
SOURCE = ROOT / SOURCE_REL
PHYSICAL = ROOT / PHYSICAL_REL
SOURCE_GIT_BLOB = "200201b741787c4e144ad4194848acf51d7b439e"


def original_source_blob() -> str:
    proc = subprocess.run(
        ["git", "hash-object", "--", SOURCE_REL],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    return proc.stdout.strip()


class RealBlockMigrationTests(unittest.TestCase):
    def test_preserve_original_source_and_quarantine_invalid_physical_t5(self):
        self.assertEqual(original_source_blob(), SOURCE_GIT_BLOB)
        self.assertTrue(SOURCE.is_file())
        self.assertFalse(
            PHYSICAL.exists(),
            "unadmitted 343-byte block.sens must not appear as a valid program",
        )

    def test_main_migration_preview_rejects_unproved_machine_block_head(self):
        before = SOURCE.read_bytes()
        with tempfile.TemporaryDirectory(prefix="sens-original-block-preview-") as td:
            temp = Path(td)
            mirror = temp / "mirror"
            report = temp / "report.json"
            cmd = [
                sys.executable, str(ROOT / "scripts/migrate.py"), "preview",
                SOURCE_REL, "--mirror", str(mirror), "--report", str(report),
            ]
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True,
                                  text=True, timeout=120, check=False)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertTrue(report.is_file(), proc.stdout + proc.stderr)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["summary"]["files_seen"], 1)
            self.assertEqual(data["summary"]["files_admitted"], 0)
            self.assertEqual(data["summary"]["files_blocked"], 1)
            self.assertEqual(data["summary"]["files_written"], 0)
            row = data["files"][0]
            self.assertEqual(row["status"], "blocked")
            self.assertEqual(row["path"], SOURCE_REL)
            self.assertTrue(row.get("reason"), data)
            self.assertFalse(mirror.exists())
        self.assertEqual(SOURCE.read_bytes(), before)
        self.assertEqual(original_source_blob(), SOURCE_GIT_BLOB)

    def test_batch_write_fails_closed_before_creating_physical_t5(self):
        before = SOURCE.read_bytes()
        with tempfile.TemporaryDirectory(prefix="sens-original-block-blocked-") as td:
            mirror = Path(td) / "mirror"
            report = Path(td) / "report.json"
            cmd = [
                sys.executable, str(ROOT / "scripts/migrate-t5-batch.py"),
                SOURCE_REL, "--root", str(ROOT), "--out", str(mirror),
                "--report", str(report), "--write", "--source-era", "auto",
            ]
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True,
                                  text=True, timeout=120, check=False)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["summary"]["files_seen"], 1)
            self.assertEqual(data["summary"]["files_admitted"], 0)
            self.assertEqual(data["summary"]["files_blocked"], 1)
            self.assertEqual(data["summary"]["files_written"], 0)
            self.assertEqual(data["files"][0]["status"], "blocked")
            self.assertTrue(data["files"][0].get("reason"))
            self.assertFalse((mirror / PHYSICAL_REL).exists())
        self.assertEqual(SOURCE.read_bytes(), before)

    def test_existing_external_candidate_is_never_overwritten(self):
        with tempfile.TemporaryDirectory(prefix="sens-original-block-clobber-") as td:
            mirror = Path(td) / "mirror"
            target = mirror / PHYSICAL_REL
            target.parent.mkdir(parents=True)
            target.write_bytes(b"sentinel")
            report = Path(td) / "report.json"
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts/migrate-t5-batch.py"),
                 SOURCE_REL, "--root", str(ROOT), "--out", str(mirror),
                 "--report", str(report), "--write", "--source-era", "auto"],
                cwd=ROOT, capture_output=True, text=True, timeout=120,
                check=False,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertEqual(target.read_bytes(), b"sentinel")
            self.assertEqual(original_source_blob(), SOURCE_GIT_BLOB)


if __name__ == "__main__":
    unittest.main()
