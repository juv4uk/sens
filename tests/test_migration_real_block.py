#!/usr/bin/env python3
"""Real original Lisp -> physical T5 migration through the canonical entrypoint."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "scripts/migrate.py"
SOURCE = ROOT / "lib/machine/block.lisp"
PHYSICAL = ROOT / "lib/machine/block.sens"
READER = ROOT / "target/debug/sens-trit"
SOURCE_GIT_BLOB = "200201b741787c4e144ad4194848acf51d7b439e"
PHYSICAL_GIT_BLOB = "2ebc8401fef2bd585231e0f3b410c933712cd140"


class RealBlockMigrationTests(unittest.TestCase):
    def test_front_door_preview_reproduces_real_physical_file(self):
        self.assertEqual(
            subprocess.run(
                ["git", "hash-object", "--", str(SOURCE.relative_to(ROOT))],
                cwd=ROOT, capture_output=True, text=True, check=True,
            ).stdout.strip(),
            SOURCE_GIT_BLOB,
        )
        self.assertEqual(
            subprocess.run(
                ["git", "hash-object", "--", str(PHYSICAL.relative_to(ROOT))],
                cwd=ROOT, capture_output=True, text=True, check=True,
            ).stdout.strip(),
            PHYSICAL_GIT_BLOB,
        )
        original = SOURCE.read_bytes()
        expected = PHYSICAL.read_bytes()
        with tempfile.TemporaryDirectory(prefix="sens-real-block-") as td:
            temp = Path(td)
            mirror = temp / "mirror"
            report = temp / "report.json"
            proc = subprocess.run(
                [sys.executable, str(ENTRYPOINT), "preview",
                 str(SOURCE.relative_to(ROOT)), "--mirror", str(mirror),
                 "--report", str(report)],
                cwd=ROOT, capture_output=True, text=True, timeout=120,
            )
            # Preview must reproduce the candidate but publish nothing.
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            state = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(state["summary"]["files_seen"], 1)
            self.assertEqual(state["summary"]["files_admitted"], 1)
            self.assertEqual(state["summary"]["files_written"], 0)
            self.assertEqual(state["summary"]["files_would_write"], 1)
            self.assertEqual(state["files"][0]["status"], "would-write")
            self.assertFalse(mirror.exists())
            self.assertEqual(SOURCE.read_bytes(), original)

    def test_batch_driver_physical_write_matches_committed_artifact_and_reader(self):
        with tempfile.TemporaryDirectory(prefix="sens-real-block-write-") as td:
            temp = Path(td)
            mirror = temp / "mirror"
            report = temp / "report.json"
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts/migrate-t5-batch.py"),
                 str(SOURCE.relative_to(ROOT)), "--root", str(ROOT),
                 "--out", str(mirror), "--report", str(report), "--write"],
                cwd=ROOT, capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            generated = mirror / "lib/machine/block.sens"
            self.assertEqual(generated.read_bytes(), PHYSICAL.read_bytes())
            self.assertEqual(
                hashlib.sha256(generated.read_bytes()).hexdigest(),
                hashlib.sha256(PHYSICAL.read_bytes()).hexdigest(),
            )
            reader = subprocess.run(
                [str(READER), "open", str(generated)],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(reader.returncode, 0, reader.stdout + reader.stderr)

    def test_no_clobber_is_enforced_by_canonical_batch_driver(self):
        with tempfile.TemporaryDirectory(prefix="sens-real-block-clobber-") as td:
            temp = Path(td)
            mirror = temp / "mirror"
            target = mirror / "lib/machine/block.sens"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"sentinel")
            report = temp / "report.json"
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts/migrate-t5-batch.py"),
                 str(SOURCE.relative_to(ROOT)), "--root", str(ROOT),
                 "--out", str(mirror), "--report", str(report), "--write"],
                cwd=ROOT, capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertEqual(target.read_bytes(), b"sentinel")


if __name__ == "__main__":
    unittest.main()
