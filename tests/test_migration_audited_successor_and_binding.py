#!/usr/bin/env python3
"""Fail-closed migration regressions for audited D8 print and local bindings."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts/migrate-three-pass.py"
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes  # noqa: E402


COMMON = [
    "--foundation", str(ROOT / "knowledge/d1-d9-foundation.json"),
    "--domain-surfaces", str(ROOT / "crates/sens/src/domain_surface_registry_generated.rs"),
    "--semantic-generated", str(ROOT / "crates/sens/src/semantic_registry_generated.rs"),
    "--semantic-registry", str(ROOT / "crates/sens/src/semantic_registry.rs"),
    "--necessary-forms", str(ROOT / "crates/sens/src/eval/necessary_forms_generated.rs"),
    "--historical-map", str(ROOT / "contracts/core1-historical-sid-map.lisp"),
    "--legacy-coverage", str(ROOT / "knowledge/sens8-current-coverage-v1.json"),
    "--text7", str(ROOT / "crates/sens/src/text7_projection_generated.rs"),
]


def run_migrator(source: Path, out: Path):
    report = out.parent / "report.json"
    result = subprocess.run(
        [sys.executable, str(MIGRATOR), str(source), "--out", str(out),
         "--report", str(report), *COMMON],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    state = json.loads(report.read_text(encoding="utf-8"))
    return result, state


class AuditedSuccessorAndBindingTests(unittest.TestCase):
    def test_audited_d8_print_can_be_physically_migrated(self):
        with tempfile.TemporaryDirectory(prefix="sens-print0-") as td:
            root = Path(td)
            source = root / "empty-en.lisp"
            out = root / "out"
            source.write_text("(print 0)\n", encoding="utf-8")

            result, state = run_migrator(source, out)

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(state["summary"]["files_seen"], 1)
            self.assertEqual(state["summary"]["files_written"], 1)
            self.assertEqual(state["summary"]["files_blocked"], 0)
            physical = out / "empty-en.sens"
            self.assertTrue(physical.is_file())
            self.assertEqual(
                decode_bytes(physical.read_bytes()),
                ["10", "11011011", "00", "0", "01"],
            )

    def test_local_definition_shadows_global_walk_and_stays_blocked(self):
        with tempfile.TemporaryDirectory(prefix="sens-walk-") as td:
            root = Path(td)
            source = root / "recursion.lisp"
            out = root / "out"
            shutil.copyfile(ROOT / "benchmarks/recursion.lisp", source)

            result, state = run_migrator(source, out)

            self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
            self.assertEqual(state["summary"]["files_seen"], 1)
            self.assertEqual(state["summary"]["files_written"], 0)
            self.assertEqual(state["summary"]["files_blocked"], 1)
            self.assertIn("dynamic/local binding 'walk'", state["files"][0]["reason"])
            self.assertFalse((out / "recursion.sens").exists())


if __name__ == "__main__":
    unittest.main()
