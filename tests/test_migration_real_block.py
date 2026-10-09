#!/usr/bin/env python3
"""P0 guard: a transport-valid source pair is NOT a proven executable SENS program.

The previously checked-in 343-byte block.sens failed the real Rust D2 reader
and was not reproducible by the canonical three-pass source migrator. Keep the
unchanged original .lisp and fail closed until source+oracle admission exists.
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
NOT_ADMITTED = ROOT / "lib/machine/block.sens"
SOURCE_GIT_BLOB = "200201b741787c4e144ad4194848acf51d7b439e"


class RealBlockQuarantineTests(unittest.TestCase):
    def test_preserve_original_and_do_not_claim_invalid_physical_program(self):
        self.assertTrue(SOURCE.is_file())
        self.assertFalse(NOT_ADMITTED.exists(), "invalid-D2 binary must not be published")
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

    def test_canonical_preview_reports_block_reason_and_keeps_original_untouched(self):
        """#4556: the public front door must expose BLOCK, not only exit 2.

        This protects every future original-source lane: mechanical T5 output
        does NOT certify executable semantics or allow source overwrites.
        """
        front = ROOT / "scripts/migrate.py"
        original = SOURCE.read_bytes()
        with tempfile.TemporaryDirectory(prefix="sens-block-frontdoor-") as td:
            temp = Path(td)
            mirror = temp / "mirror"
            report = temp / "preview.json"
            run = subprocess.run(
                [sys.executable, str(front), "preview",
                 "lib/machine/block.lisp", "--mirror", str(mirror),
                 "--report", str(report)],
                cwd=ROOT, capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
            self.assertTrue(report.is_file(), run.stdout + run.stderr)
            ledger = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(ledger["summary"]["files_seen"], 1)
            self.assertEqual(ledger["summary"]["files_admitted"], 0)
            self.assertEqual(ledger["summary"]["files_written"], 0)
            self.assertEqual(ledger["summary"]["files_blocked"], 1)
            row, = ledger["files"]
            self.assertEqual(row["path"], "lib/machine/block.lisp")
            self.assertEqual(row["status"], "blocked")
            self.assertEqual(row["source_era"], "auto")
            self.assertTrue(row["reason"])
            # The reason cannot be hidden behind a generic exit code.
            self.assertIn("BLOCKED lib/machine/block.lisp:", run.stderr)
            normalized = row["reason"][:100].replace("\\n", " ").replace("\\r", " ")
            self.assertIn(normalized, run.stderr)
            self.assertEqual(
                row["source_sha256"], hashlib.sha256(original).hexdigest()
            )
            self.assertFalse((mirror / "lib/machine/block.sens").exists())
            self.assertFalse(NOT_ADMITTED.exists())
            self.assertEqual(SOURCE.read_bytes(), original)

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
