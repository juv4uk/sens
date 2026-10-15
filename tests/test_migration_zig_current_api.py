#!/usr/bin/env python3
"""One true current three-pass API path into Zig-only T5 publication.

Dry-run keeps source and output untouched; this is not SENS semantic admission.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "scripts/migrate-t5-batch.py"
INPUT = Path("tests/fixtures/migration-d1-cond-cohort/branch.lisp")


class CurrentThreePassZigCorridorTest(unittest.TestCase):
    def call(self, output: Path, report: Path, *options: str):
        return subprocess.run([
            sys.executable, str(DRIVER), INPUT.as_posix(),
            "--root", str(ROOT), "--out", str(output),
            "--report", str(report), *options,
        ], cwd=ROOT, text=True, capture_output=True, timeout=45, check=False)

    def test_real_ukrainian_source_uses_current_two_map_resolver_in_dry_run(self):
        original = (ROOT / INPUT).read_bytes()
        with tempfile.TemporaryDirectory(prefix="sens-current-zig-api-") as name:
            base = Path(name)
            output = base / "mirror"
            report = base / "receipt.json"
            result = self.call(output, report)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(receipt["summary"]["files_admitted"], 1)
            self.assertEqual(receipt["summary"]["files_blocked"], 0)
            self.assertEqual(receipt["files"][0]["status"], "would-write")
            self.assertEqual(receipt["authority"]["source_era"], "auto")
            self.assertIn("SID8 retired", receipt["authority"]["w8_policy"])
            self.assertFalse(output.exists(), "dry-run cannot publish .sens or view")
        self.assertEqual((ROOT / INPUT).read_bytes(), original)

    def test_retired_sid8_source_era_rejected_before_publication(self):
        with tempfile.TemporaryDirectory(prefix="sens-no-retired-era-") as name:
            base = Path(name)
            output = base / "mirror"
            result = self.call(output, base / "receipt.json", "--source-era", "legacy")
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertIn("RETIRED_SID8_SOURCE_ERA", result.stderr)
            self.assertFalse(output.exists())

    def test_write_without_zig_is_rejected_before_creating_any_carrier(self):
        with tempfile.TemporaryDirectory(prefix="sens-no-zig-bypass-") as name:
            base = Path(name)
            output = base / "mirror"
            result = self.call(output, base / "receipt.json", "--write")
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertIn("--write requires --zig-codec", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
