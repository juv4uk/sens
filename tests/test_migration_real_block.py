#!/usr/bin/env python3
"""Integrity guard for the real original block Lisp / physical T5 pair.

The physical file is valid transport produced by the owner-ratified Text7/T5
source migrator. Independent semantic admission remains a separate concern.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "scripts/migrate-t5-batch.py"
SOURCE = ROOT / "lib/machine/block.lisp"
PHYSICAL = ROOT / "lib/machine/block.sens"
EXPECTED_PHYSICAL_SHA256 = "b6542822c6e19716287e670ba7a47f296bec5b803479d56bed18795d99c66719"
EXPECTED_TYPED_SHA256 = "d7084d46e7e0e6946daab13b0087824db21e7097477bf4c2c09a23985426de3a"
SOURCE_GIT_BLOB = "200201b741787c4e144ad4194848acf51d7b439e"


class RealBlockQuarantineTests(unittest.TestCase):
    def test_committed_physical_artifact_is_valid_and_source_preserved(self):
        self.assertTrue(SOURCE.is_file())
        self.assertTrue(PHYSICAL.is_file())
        payload = PHYSICAL.read_bytes()
        self.assertEqual(len(payload), 343)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), EXPECTED_PHYSICAL_SHA256)
        from sens_t5_codec import decode_bytes, typed_sha256
        words = decode_bytes(payload)
        self.assertEqual(typed_sha256(words), EXPECTED_TYPED_SHA256)
        source_blob = subprocess.run(
            ["git", "hash-object", "lib/machine/block.lisp"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(source_blob, SOURCE_GIT_BLOB)

    def test_current_default_batch_blocks_unproven_original_with_exact_reason(self):
        source_before = SOURCE.read_bytes()
        with tempfile.TemporaryDirectory(prefix="sens-block-quarantine-") as td:
            temp = Path(td)
            mirror = temp / "mirror"
            report = temp / "ledger.json"
            run = subprocess.run(
                [sys.executable, str(BATCH), "lib/machine/block.lisp",
                 "--root", str(ROOT), "--out", str(mirror),
                 "--report", str(report), "--write"],
                cwd=ROOT, capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
            ledger = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(ledger["summary"]["files_seen"], 1)
            self.assertEqual(ledger["summary"]["files_admitted"], 0)
            self.assertEqual(ledger["summary"]["files_written"], 0)
            self.assertEqual(ledger["summary"]["files_blocked"], 1)
            self.assertEqual(ledger["files"][0]["path"], "lib/machine/block.lisp")
            self.assertEqual(ledger["files"][0]["status"], "blocked")
            self.assertTrue(ledger["files"][0].get("reason"))
            self.assertEqual(
                ledger["files"][0].get("source_sha256"),
                hashlib.sha256(source_before).hexdigest(),
            )
            self.assertFalse((mirror / "lib/machine/block.sens").exists())
            self.assertEqual(SOURCE.read_bytes(), source_before)

    def test_blocked_source_does_not_overwrite_existing_t5(self):
        with tempfile.TemporaryDirectory(prefix="sens-block-no-clobber-") as td:
            temp = Path(td)
            mirror = temp / "mirror"
            target = mirror / "lib/machine/block.sens"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"sentinel")
            ledger = temp / "ledger.json"
            run = subprocess.run(
                [sys.executable, str(BATCH), "lib/machine/block.lisp",
                 "--root", str(ROOT), "--out", str(mirror),
                 "--report", str(ledger), "--write"],
                cwd=ROOT, capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
            self.assertEqual(target.read_bytes(), b"sentinel")
            result = json.loads(ledger.read_text(encoding="utf-8"))
            self.assertEqual(result["summary"]["files_written"], 0)


if __name__ == "__main__":
    unittest.main()
