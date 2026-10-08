#!/usr/bin/env python3
"""Independent release guard for the owner-approved physical T5 .sens writer.

Keep this test separate from tests/test_sens_code_migration.py: migration PRs
must not be able to make an accidental T5 removal green by deleting its test.
No semantic-authority additions and no edits to the shared migrator.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-to-sens-codes.py"
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_projection

FOUNDATION = ROOT / "knowledge" / "d1-d7-foundation.json"
TEXT7 = ROOT / "crates" / "sens" / "src" / "text7_projection_generated.rs"
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
HISTORICAL = ROOT / "contracts" / "core1-historical-sid-map.lisp"
SURFACES = [ROOT / "lib" / "domains" / f"d{i}.lisp" for i in range(1, 7)]


class PhysicalT5MigratorContract(unittest.TestCase):
    def test_sens_mirror_is_packed_preserves_lisp_and_never_reopens_binary_input(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            source.mkdir()
            original = source / "hello.lisp"
            original.write_text("()\n", encoding="utf-8")
            # A physical .sens is never a textual .lisp input. Deliberate invalid UTF-8.
            (source / "already.sens").write_bytes(b"\xff\xfe\x00")

            destination = Path(temp) / "output"
            report = Path(temp) / "report.json"
            command = [
                sys.executable, str(SCRIPT), str(source),
                "--foundation", str(FOUNDATION),
                "--sens-mirror", str(destination),
                "--text7-projection", str(TEXT7),
                "--historical-map", str(HISTORICAL),
                "--semantic-registry", str(REGISTRY),
                "--report", str(report),
                "--domain-surfaces", *map(str, SURFACES),
            ]
            first = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True, timeout=60
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

            result_file = destination / "hello.sens"
            self.assertTrue(result_file.is_file())
            physical = result_file.read_bytes()
            self.assertEqual(physical, encode_projection("000"))
            self.assertEqual(decode_bytes(physical), ["000"])
            self.assertNotEqual(physical, b"000")
            self.assertFalse((destination / "hello").exists())
            self.assertFalse((destination / "hello.lisp").exists())
            self.assertFalse((destination / "already.sens").exists())
            self.assertEqual(original.read_text(encoding="utf-8"), "()\n")

            result = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(result["mode"], "sens-mirror")
            self.assertEqual(len(result["files"]), 1)
            self.assertEqual(result["files"][0]["status"], "sens-written")

            # Never clobber an existing binary artefact.
            second = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True, timeout=60
            )
            self.assertEqual(second.returncode, 2, second.stdout + second.stderr)
            self.assertEqual(result_file.read_bytes(), physical)


if __name__ == "__main__":
    unittest.main()
