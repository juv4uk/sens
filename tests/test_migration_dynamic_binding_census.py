#!/usr/bin/env python3
"""#4461: pin true dynamic blockers; redirect declarative identity fields."""
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
LEDGER = ROOT / "knowledge/migration-dynamic-binding-census-2026-10-08.json"


def git_blob_sha(content: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()


class DynamicBindingMigrationCensus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        cls.dynamic = cls.ledger["executable_dynamic"]
        cls.redirected = cls.ledger["redirected_nonprogram_identity"]

    def test_strict_artifact_provenance_and_exact_split(self):
        artifact = self.ledger["strict_artifact"]
        self.assertEqual(artifact["workflow_run"], 37810152645)
        self.assertEqual(artifact["artifact_id"], 11564951770)
        self.assertEqual(
            artifact["artifact_digest"],
            "sha256:7c972193ced938394456b901c175cd47a02348d3c21da686be9fd6537915cb5f",
        )
        self.assertEqual(artifact["report_schema"], "sens-three-pass-t5-migration/v3")
        self.assertEqual(len(self.dynamic), 4)
        self.assertEqual(len(self.redirected), 15)
        paths = [row["path"] for row in self.dynamic + self.redirected]
        self.assertEqual(len(paths), 19)
        self.assertEqual(len(paths), len(set(paths)))

    def test_four_dynamic_sources_are_real_sha_pinned_executable_bindings(self):
        for row in self.dynamic:
            with self.subTest(path=row["path"]):
                source = ROOT / row["path"]
                self.assertTrue(source.is_file())
                content = source.read_bytes()
                self.assertEqual(git_blob_sha(content), row["git_blob_sha"])
                text = content.decode("utf-8")
                symbol = row["symbol"]
                self.assertIn(f"(00001001 {symbol}", text)
                self.assertGreaterEqual(
                    text.count(f"({symbol}"),
                    1,
                    f"{row['path']} must execute/reference {symbol} after defining it",
                )
                self.assertTrue(row["action"].startswith("BLOCK_DYNAMIC_BINDING:"))
                self.assertGreaterEqual(len(row["required_evidence"]), 4)
                self.assertFalse(
                    source.with_suffix(".sens").exists(),
                    "blocked dynamic source must not have an auto-published .sens sibling",
                )

    def test_fifteen_identity_rows_are_data_not_an_identity_function(self):
        self.assertEqual(
            {row["classification"] for row in self.redirected},
            {"REDIRECT_NONPROGRAM_IDENTITY_FIELD"},
        )
        for row in self.redirected:
            with self.subTest(path=row["path"]):
                source = ROOT / row["path"]
                self.assertTrue(source.is_file())
                content = source.read_bytes()
                self.assertEqual(git_blob_sha(content), row["git_blob_sha"])
                text = content.decode("utf-8")
                self.assertIn("identity", text)
                self.assertNotIn(
                    "(00001001 identity",
                    text,
                    "redirected data row must not secretly define executable identity",
                )
                self.assertEqual(
                    row["handoff_issue"],
                    "https://github.com/juv4uk/sens/issues/4460",
                )
                self.assertTrue(row["action"].startswith("REDIRECT_NONPROGRAM:"))
                self.assertFalse(
                    source.with_suffix(".sens").exists(),
                    "declarative identity fields must not trigger automatic .sens publication",
                )

    def test_real_three_pass_migrator_keeps_dynamic_cohort_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="sens-dynamic-binding-") as td:
            folder = Path(td)
            incoming = folder / "input"
            outgoing = folder / "packed"
            incoming.mkdir()

            for row in self.dynamic:
                source = ROOT / row["path"]
                shutil.copyfile(source, incoming / source.name)

            report = folder / "report.json"
            arguments = [
                sys.executable,
                str(ROOT / "scripts/migrate-three-pass.py"),
                str(incoming),
                "--out",
                str(outgoing),
                "--foundation",
                str(ROOT / "knowledge/d1-d9-foundation.json"),
                "--domain-surfaces",
                str(ROOT / "crates/sens/src/domain_surface_registry_generated.rs"),
                "--semantic-generated",
                str(ROOT / "crates/sens/src/semantic_registry_generated.rs"),
                "--semantic-registry",
                str(ROOT / "crates/sens/src/semantic_registry.rs"),
                "--necessary-forms",
                str(ROOT / "crates/sens/src/eval/necessary_forms_generated.rs"),
                "--historical-map",
                str(ROOT / "contracts/core1-historical-sid-map.lisp"),
                "--text7",
                str(ROOT / "crates/sens/src/text7_projection_generated.rs"),
                "--report",
                str(report),
                # These four SHA-pinned fixtures are explicitly historical
                # SID8; AUTO must otherwise block before the binder evidence.
                "--source-era", "legacy",
            ]
            run = subprocess.run(
                arguments,
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(run.returncode, 2, run.stderr + "\n" + run.stdout)

            state = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(state["schema"], "sens-three-pass-t5-migration/v3")
            self.assertEqual(state["source_era"], "legacy")
            self.assertEqual(state["summary"]["files_seen"], 4)
            self.assertEqual(state["summary"]["files_written"], 0)
            self.assertEqual(state["summary"]["files_blocked"], 4)

            # The source SHA and its dynamic DEFINE/references are pinned in
            # test_four_dynamic_sources_are_real_sha_pinned_executable_bindings.
            # When a predecessor (for example a legacy SID8 successor) becomes
            # lawfully resolved, the *first* reported blocker can change. Never
            # confuse that change with approved lexical/dynamic semantics.
            expected_paths = {Path(row["path"]).name for row in self.dynamic}
            self.assertEqual(len(expected_paths), 4)
            self.assertEqual(len(state["files"]), len(expected_paths))
            observed = {}
            for row in state["files"]:
                input_name = Path(row["path"]).name
                self.assertNotIn(input_name, observed, "each original must appear exactly once")
                observed[input_name] = row
                self.assertEqual(row["status"], "blocked", row)
                self.assertIsInstance(row.get("reason"), str, row)
                self.assertTrue(row["reason"].strip(), row)
                self.assertEqual(Path(row["output"]).name, Path(input_name).with_suffix(".sens").name)
                self.assertFalse((outgoing / row["output"]).exists(), row)

            self.assertEqual(set(observed), expected_paths)
            self.assertFalse(list(folder.rglob("*.sens")),
                             "a first-blocker change MUST NEVER publish unproved .sens")


if __name__ == "__main__":
    unittest.main()
