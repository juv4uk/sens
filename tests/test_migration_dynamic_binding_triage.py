#!/usr/bin/env python3
"""#4461: pin real local-binding benchmarks and enforce fail-closed T5 migration.

Read-only census. A BLOCKED source is not an admitted physical .sens program.
"""
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
LEDGER = ROOT / "knowledge/migration-dynamic-binding-triage-2026-10-08.json"


def git_blob_sha(content: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()


class DynamicBindingT5Gate(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        cls.cohort = cls.ledger["files"]

    def test_pinned_sources_and_no_new_semantic_authority(self):
        self.assertEqual(self.ledger["schema"], "sens-migration-dynamic-binding-triage/v1")
        self.assertEqual(self.ledger["status"], "BLOCKED_UNPROVEN_BINDING")
        paths = [row["path"] for row in self.cohort]
        self.assertEqual(
            paths,
            [
                "benchmarks/arithmetic.lisp",
                "benchmarks/closures.lisp",
                "benchmarks/recursion.lisp",
            ],
        )
        for row in self.cohort:
            with self.subTest(source=row["path"]):
                raw = (ROOT / row["path"]).read_bytes()
                self.assertEqual(git_blob_sha(raw), row["git_blob_sha"])
                self.assertGreaterEqual(len(row["blocks"]), 2)
                self.assertGreaterEqual(len(row["required_evidence"]), 3)

    def test_evidence_is_present_not_merely_a_filename(self):
        for row in self.cohort:
            with self.subTest(source=row["path"]):
                lines = (ROOT / row["path"]).read_text(encoding="utf-8").splitlines()
                self.assertGreaterEqual(len(lines), max(row["proof_lines"].values()))
                self.assertTrue(all(lines[n - 1].strip() for n in row["proof_lines"].values()))
                for fragment in row["exact_fragments"]:
                    self.assertIn(fragment, "\n".join(lines))
                # Historical function names, bound vars and numeric values
                # are evidence, NOT successor semantic IDs.
                self.assertTrue(any("binding" in claim or "binder" in claim
                                    or "closure" in claim for claim in row["blocks"]))

    def test_provenance_guard_detects_mutation(self):
        for row in self.cohort:
            raw = (ROOT / row["path"]).read_bytes()
            self.assertNotEqual(git_blob_sha(raw + b"; tampered\n"), row["git_blob_sha"])

    def test_real_three_pass_migrator_must_block_all(self):
        with tempfile.TemporaryDirectory(prefix="sens-dynamic-4461-") as temp:
            folder = Path(temp)
            incoming = folder / "input"
            outgoing = folder / "packed"
            incoming.mkdir()
            for row in self.cohort:
                source = ROOT / row["path"]
                shutil.copyfile(source, incoming / source.name)

            report = folder / "report.json"
            cmd = [
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
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=90)
            self.assertEqual(proc.returncode, 2, proc.stdout + "\n" + proc.stderr)
            state = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(state["schema"], "sens-three-pass-t5-migration/v3")
            self.assertEqual(state["summary"]["files_seen"], 3)
            self.assertEqual(state["summary"]["files_written"], 0)
            self.assertEqual(state["summary"]["files_blocked"], 3)
            self.assertEqual(len(state["files"]), 3)
            for entry in state["files"]:
                self.assertEqual(entry["status"], "blocked", entry)
                self.assertTrue(entry.get("reason"), entry)
                self.assertEqual(Path(entry["output"]).suffix, ".sens")
                self.assertFalse((outgoing / entry["output"]).exists())
            self.assertFalse(list(folder.rglob("*.sens")))
            for row in self.cohort:
                snapshot = incoming / Path(row["path"]).name
                self.assertEqual(git_blob_sha(snapshot.read_bytes()), row["git_blob_sha"])


if __name__ == "__main__":
    unittest.main()
