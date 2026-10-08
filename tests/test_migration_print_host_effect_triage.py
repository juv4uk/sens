#!/usr/bin/env python3
"""Pinned, non-overlapping #4458 host-I/O blockers; never fake ready .sens."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "knowledge/migration-print-host-effect-triage-2026-10-08.json"


def git_blob_sha(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()


class HostEffectMigrationGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        cls.cohort = cls.ledger["files"]

    def test_three_distinct_sha_pinned_real_sources(self):
        self.assertEqual(self.ledger["status"], "BLOCKED_HOST_EFFECT")
        self.assertEqual(len(self.cohort), 3)
        paths = [row["path"] for row in self.cohort]
        self.assertEqual(len(paths), len(set(paths)))
        for row in self.cohort:
            with self.subTest(path=row["path"]):
                source = ROOT / row["path"]
                self.assertTrue(source.is_file())
                self.assertEqual(git_blob_sha(source.read_bytes()), row["git_blob_sha"])
                self.assertTrue(row["action"].startswith("BLOCK:"))
                self.assertGreaterEqual(len(row["required_evidence"]), 3)

    def test_proven_nontrivial_io_and_binders(self):
        for row in self.cohort:
            with self.subTest(path=row["path"]):
                lines = (ROOT / row["path"]).read_text(encoding="utf-8").splitlines()
                at = row["line_numbers"]
                # Historical 01001000/01001011: NOT current domain identities.
                self.assertIn("(01001000 ", lines[at["output_call"] - 1])
                self.assertIn("(01001011 ", lines[at["host_read"] - 1])
                self.assertIn("(00001001 ", lines[at["local_binding"] - 1])
                self.assertGreaterEqual(len(lines), max(at.values()))

    def test_real_three_pass_cli_must_block_not_publish(self):
        with tempfile.TemporaryDirectory(prefix="sens-print-host-") as td:
            folder = Path(td)
            incoming = folder / "input"
            outgoing = folder / "packed"
            incoming.mkdir()
            for row in self.cohort:
                source = ROOT / row["path"]
                shutil.copyfile(source, incoming / source.name)
            report = folder / "report.json"
            arguments = [
                sys.executable, str(ROOT / "scripts/migrate-three-pass.py"),
                str(incoming), "--out", str(outgoing),
                "--foundation", str(ROOT / "knowledge/d1-d7-foundation.json"),
                "--domain-surfaces", str(ROOT / "crates/sens/src/domain_surface_registry_generated.rs"),
                "--semantic-generated", str(ROOT / "crates/sens/src/semantic_registry_generated.rs"),
                "--semantic-registry", str(ROOT / "crates/sens/src/semantic_registry.rs"),
                "--necessary-forms", str(ROOT / "crates/sens/src/eval/necessary_forms_generated.rs"),
                "--historical-map", str(ROOT / "contracts/core1-historical-sid-map.lisp"),
                "--text7", str(ROOT / "crates/sens/src/text7_projection_generated.rs"),
                "--report", str(report),
            ]
            run = subprocess.run(arguments, cwd=ROOT, capture_output=True, text=True, timeout=90)
            self.assertEqual(run.returncode, 2, run.stderr + "\n" + run.stdout)
            state = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(state["schema"], "sens-three-pass-t5-migration/v3")
            self.assertEqual(state["summary"]["files_seen"], 3)
            self.assertEqual(state["summary"]["files_written"], 0)
            self.assertEqual(state["summary"]["files_blocked"], 3)
            for row in state["files"]:
                self.assertEqual(row["status"], "blocked", row)
                self.assertTrue(row.get("reason"), row)
                self.assertEqual(Path(row["output"]).suffix, ".sens")
                self.assertFalse((outgoing / row["output"]).exists())
            self.assertFalse(list(folder.rglob("*.sens")))
            for row in self.cohort:
                self.assertEqual(
                    git_blob_sha((incoming / Path(row["path"]).name).read_bytes()),
                    row["git_blob_sha"],
                )


if __name__ == "__main__":
    unittest.main()
