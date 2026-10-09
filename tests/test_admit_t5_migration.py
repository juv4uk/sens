#!/usr/bin/env python3
"""Independent proof-publisher regressions; run against real SENS migration and reader."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/admit-t5-migration.py"
spec = importlib.util.spec_from_file_location("admit_t5", SCRIPT)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)

SOURCE = "tests/fixtures/migration-multiform-cohort/two-forms.lisp"
PHYSICAL = "tests/fixtures/migration-multiform-cohort/two-forms.sens"
READER = ROOT / "target/debug/sens-trit"


def fixture_manifest() -> dict:
    source = (ROOT / SOURCE).read_bytes()
    physical = (ROOT / PHYSICAL).read_bytes()
    words = gate.decode_bytes(physical)
    return {
        "schema": gate.SCHEMA,
        "source": SOURCE,
        "source_era": "historical-legacy",
        "source_git_blob_sha1": gate.git_blob_sha(source),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "expected_physical_sha256": gate.digest(physical),
        "expected_typed_sha256": gate.typed_sha256(words),
        "oracle_commands": [
            [sys.executable, "tests/test_migration_multiform_cohort.py", "-q"],
            ["cargo", "test", "-p", "sens", "--test", "migration_multiform_cohort"],
        ],
        "oracle_witnesses": {
            "historical": {
                "path": "tests/test_migration_multiform_cohort.py",
                "git_blob_sha1": gate.git_blob_sha(
                    (ROOT / "tests/test_migration_multiform_cohort.py").read_bytes()),
            },
            "current": {
                "path": "crates/sens/tests/migration_multiform_cohort.rs",
                "git_blob_sha1": gate.git_blob_sha(
                    (ROOT / "crates/sens/tests/migration_multiform_cohort.rs").read_bytes()),
            },
        },
    }


class T5ProofPublisherTests(unittest.TestCase):
    def test_uses_current_ratified_d1_d9_authority_like_batch(self):
        foundation_path = gate.ARTIFACTS["foundation"]
        self.assertEqual(foundation_path, "knowledge/d1-d9-foundation.json")
        authority = json.loads((ROOT / foundation_path).read_text(encoding="utf-8"))
        self.assertEqual(authority["status"], "owner-ratified")
        self.assertEqual(authority["current_domains"],
                         [f"D{i}" for i in range(1, 10)])
        self.assertEqual(authority["schema"],
                         "d1-d9-foundation-ratification/v1")
        # The public preview and proof-gated publisher must not silently
        # choose different ratified semantic registries for the same file.
        batch_source = (ROOT / "scripts/migrate-t5-batch.py").read_text(encoding="utf-8")
        self.assertIn('"foundation": ROOT / "knowledge/d1-d9-foundation.json"',
                      batch_source)
        # This proof publisher takes only historical-legacy manifests;
        # the W8 era is explicit, never inherited from the migrator default.
        publisher_source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('command.extend(["--source-era", "legacy"',
                      publisher_source)

    def test_git_source_blob_is_real_git_identity(self):
        source = (ROOT / SOURCE).read_bytes()
        actual = subprocess.run(
            ["git", "hash-object", "--", SOURCE],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(gate.git_blob_sha(source), actual)

    def test_manifest_missing_oracle_or_ambiguous_era_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "m.json"
            proof = fixture_manifest()
            proof["oracle_commands"] = []
            path.write_text(json.dumps(proof))
            with self.assertRaisesRegex(gate.Blocked, "ORACLE"):
                gate.checked_manifest(path)
            proof["oracle_commands"] = [["echo", "not sufficient"]]
            proof["source_era"] = "current"
            path.write_text(json.dumps(proof))
            with self.assertRaisesRegex(gate.Blocked, "SOURCE_ERA"):
                gate.checked_manifest(path)

    def test_real_original_manifest_cannot_omit_historical_observable(self):
        proof = fixture_manifest()
        proof["source"] = "lib/machine/block.lisp"
        with tempfile.TemporaryDirectory() as directory:
            location = Path(directory) / "source.json"
            location.write_text(json.dumps(proof))
            with self.assertRaisesRegex(gate.Blocked, "OBSERVABLE_PARITY"):
                gate.checked_manifest(location)
            proof["historical_observation"] = {
                "command": [sys.executable, "-c", "print('NIL')"],
                "stdout_sha256": hashlib.sha256(b"NIL\n").hexdigest(),
            }
            location.write_text(json.dumps(proof))
            with self.assertRaisesRegex(gate.Blocked, r"\{source\}"):
                gate.checked_manifest(location)
            proof["historical_observation"]["command"].append("{source}")
            location.write_text(json.dumps(proof))
            self.assertEqual(gate.checked_manifest(location)["source"],
                             "lib/machine/block.lisp")
            proof["historical_observation"]["stdout_sha256"] = "f" * 64
            location.write_text(json.dumps(proof))
            # Hash shape alone is not evidence; actual historical output has
            # to be independently executed and matched before publication.
            self.assertEqual(gate.checked_manifest(location)["source"],
                             "lib/machine/block.lisp")

    def test_real_current_sens_eval_and_historical_observables_match_bytes(self):
        self.assertTrue(READER.is_file(), "build real sens-trit first")
        path = ROOT / "tests/fixtures/migration-quote-cohort-main/quote-legacy.sens"
        historical = [sys.executable, "-c", "print('()')", "{source}"]
        proof = {
            "source": "lib/machine/block.lisp",
            "historical_observation": {
                "command": historical,
                "stdout_sha256": hashlib.sha256(b"()\n").hexdigest(),
            },
        }
        # Synthetic historical oracle tests the COMPARE mechanism only. It is
        # not an approved source-specific oracle or an original migration.
        result = gate.verify_observable_parity(READER, path, ROOT, proof)
        self.assertEqual(result,
                         "BYTE_EXACT_HISTORICAL_VS_CURRENT_OUTPUT_REVIEW_REQUIRED")

    def test_false_old_current_parity_never_succeeds(self):
        self.assertTrue(READER.is_file(), "build real sens-trit first")
        path = ROOT / "tests/fixtures/migration-multiform-cohort/two-forms.sens"
        p = {
            "source": "lib/machine/block.lisp",
            "historical_observation": {
                "command": [sys.executable, "-c", "print('(different)')", "{source}"],
                "stdout_sha256": hashlib.sha256(b"(different)\n").hexdigest(),
            },
        }
        with self.assertRaisesRegex(gate.Blocked, "OBSERVABLE_PARITY_MISMATCH"):
            gate.verify_observable_parity(READER, path, ROOT, p)
        p["historical_observation"]["stdout_sha256"] = "0" * 64
        with self.assertRaisesRegex(gate.Blocked, "pinned source observation drift"):
            gate.verify_observable_parity(READER, path, ROOT, p)

    def test_old_oracle_failure_or_stderr_blocks_even_if_current_executes(self):
        self.assertTrue(READER.is_file(), "build real sens-trit first")
        path = ROOT / "tests/fixtures/migration-multiform-cohort/two-forms.sens"
        for script in ("import sys;sys.exit(4)",
                       "import sys;sys.stderr.write('not proven');print('NIL')"):
            proof = {
                "source": "lib/machine/block.lisp",
                "historical_observation": {
                    "command": [sys.executable, "-c", script, "{source}"],
                    "stdout_sha256": hashlib.sha256(b"NIL\n").hexdigest(),
                },
            }
            with self.subTest(script=script), self.assertRaisesRegex(
                    gate.Blocked, "OBSERVABLE_PARITY_HISTORICAL"):
                gate.verify_observable_parity(READER, path, ROOT, proof)

    def test_canary_not_misreported_as_original_source_semantic_parity(self):
        fixture = fixture_manifest()
        self.assertTrue(gate.is_fixture_canary(fixture["source"]))
        self.assertEqual(
            gate.verify_observable_parity(READER, ROOT / PHYSICAL, ROOT, fixture),
            "NOT_VERIFIED_FIXTURE_CANARY",
        )
        fixture["historical_observation"] = {
            "command": [sys.executable, "-c", "print('NIL')", "{source}"],
            "stdout_sha256": hashlib.sha256(b"NIL\n").hexdigest(),
        }
        with tempfile.TemporaryDirectory() as directory:
            location = Path(directory) / "canary.json"
            location.write_text(json.dumps(fixture))
            with self.assertRaisesRegex(gate.Blocked, "impersonate"):
                gate.checked_manifest(location)

    def test_noop_echo_or_true_cannot_claim_semantic_oracle(self):
        for junk in (
            [["echo", "PASS"], ["cargo", "test", "-p", "sens",
                                "--test", "migration_multiform_cohort"]],
            [[sys.executable, "-c", "print('OK')"],
             ["cargo", "test", "-p", "sens", "--test", "migration_multiform_cohort"]],
            [[sys.executable, "tests/test_migration_multiform_cohort.py", "-q"],
             ["true"]],
        ):
            with self.subTest(junk=junk):
                proof = fixture_manifest()
                proof["oracle_commands"] = junk
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "fake.json"
                    path.write_text(json.dumps(proof))
                    with self.assertRaisesRegex(gate.Blocked, "ORACLE"):
                        gate.checked_manifest(path)

    def test_missing_current_oracle_cannot_pass_proof(self):
        proof = fixture_manifest()
        del proof["oracle_witnesses"]["current"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "incomplete.json"
            path.write_text(json.dumps(proof))
            with self.assertRaisesRegex(gate.Blocked, "ORACLE"):
                gate.checked_manifest(path)

    def test_tampered_witness_blob_blocks_even_when_command_exits_zero(self):
        proof = fixture_manifest()
        proof["oracle_witnesses"]["historical"]["git_blob_sha1"] = "0" * 40
        with tempfile.TemporaryDirectory() as directory:
            mirror = Path(directory) / "mirror"
            with self.assertRaisesRegex(gate.Blocked, "ORACLE: historical witness changed"):
                gate.admit(ROOT, mirror, proof, READER, write=True)
            self.assertFalse(mirror.exists())

    def test_witness_path_drift_is_not_a_valid_original_oracle(self):
        proof = fixture_manifest()
        proof["oracle_witnesses"]["historical"]["path"] = "tests/test_some_other.py"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "drift.json"
            path.write_text(json.dumps(proof))
            with self.assertRaisesRegex(gate.Blocked, "ORACLE"):
                gate.checked_manifest(path)

    def test_symlink_traversal_and_non_lisp_source_block(self):
        for source in ("../escape.lisp", "/tmp/escape.lisp", "tests/test.py"):
            with self.assertRaises(gate.Blocked, msg=source):
                gate.inside_root(ROOT, source)

    def test_tampered_source_sha_blocks_before_any_output(self):
        proof = fixture_manifest()
        proof["source_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "mirror"
            with self.assertRaisesRegex(gate.Blocked, "SOURCE_PROVENANCE"):
                gate.admit(ROOT, output, proof, READER, write=True)
            self.assertFalse(output.exists())

    def test_tampered_physical_sha_blocks_before_publish(self):
        proof = fixture_manifest()
        proof["expected_physical_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "mirror"
            with self.assertRaisesRegex(gate.Blocked, "PHYSICAL"):
                gate.admit(ROOT, output, proof, READER, write=True)
            self.assertFalse((output / Path(SOURCE).with_suffix(".sens")).exists())

    def test_unapproved_oracle_is_failure_not_an_exception_to_skip(self):
        proof = fixture_manifest()
        proof["oracle_commands"] = [[sys.executable, "-c", "import sys;sys.exit(12)"]]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "mirror"
            with self.assertRaisesRegex(gate.Blocked, "ORACLE"):
                gate.admit(ROOT, output, proof, READER, write=True)
            self.assertFalse((output / Path(SOURCE).with_suffix(".sens")).exists())

    def test_real_legacy_to_physical_t5_oracle_and_no_clobber(self):
        self.assertTrue(READER.is_file(), "build the genuine sens-trit reader first")
        proof = fixture_manifest()
        with tempfile.TemporaryDirectory() as directory:
            mirror = Path(directory) / "mirror"
            expected = (ROOT / PHYSICAL).read_bytes()
            preview = gate.admit(ROOT, mirror, proof, READER, write=False)
            self.assertEqual(preview["status"], "VERIFIED_NOT_WRITTEN")
            self.assertEqual(preview["physical_bytes"], len(expected))
            self.assertEqual(preview["observable_parity"], "NOT_VERIFIED_FIXTURE_CANARY")
            self.assertFalse(preview["original_executable_parity"])
            self.assertFalse(preview["release_admitted"])
            self.assertFalse((mirror / Path(PHYSICAL)).exists())
            actual = gate.admit(ROOT, mirror, proof, READER, write=True)
            self.assertEqual(actual["status"], "WRITTEN")
            self.assertEqual(len(actual["oracle_witnesses_pinned"]), 2)
            self.assertEqual(actual["semantic_review"], "NAMED_TESTS_PASSED_OWNER_REVIEW_REQUIRED")
            self.assertEqual((mirror / PHYSICAL).read_bytes(), expected)
            self.assertEqual((ROOT / PHYSICAL).read_bytes(), expected)
            with self.assertRaisesRegex(gate.Blocked, "existing"):
                gate.admit(ROOT, mirror, proof, READER, write=True)
            self.assertEqual((mirror / PHYSICAL).read_bytes(), expected)

    def test_cli_emits_structured_block_report(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            proof = fixture_manifest()
            proof["expected_physical_sha256"] = "0" * 64
            manifest = work / "proof.json"
            manifest.write_text(json.dumps(proof))
            report = work / "result.json"
            run = subprocess.run(
                [sys.executable, str(SCRIPT), "--root", str(ROOT),
                 "--mirror", str(work / "out"), "--reader", str(READER),
                 "--manifest", str(manifest), "--report", str(report), "--write"],
                capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
            self.assertEqual(json.loads(report.read_text())["status"], "BLOCKED")
            self.assertFalse((work / "out" / PHYSICAL).exists())


if __name__ == "__main__":
    unittest.main()
