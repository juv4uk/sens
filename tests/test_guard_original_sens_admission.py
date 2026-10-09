#!/usr/bin/env python3
"""Original-source provenance and independent proof-chain gate regressions."""
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
SCRIPT = ROOT / "scripts/guard_original_sens_admission.py"
spec = importlib.util.spec_from_file_location("original_proof_gate", SCRIPT)
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)


class ProofCarryingOriginalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sens-proof-unit-")
        self.root = Path(self.tmp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "proof@example.invalid")
        self.git("config", "user.name", "Proof Unit")
        self.reader = self.root / "sens-trit"
        self.reader.write_bytes(b"not run in unit tests")
        self.src = Path("lib/machine/real.lisp")
        self.dst = self.src.with_suffix(".sens")
        (self.root / self.src).parent.mkdir(parents=True)
        (self.root / self.src).write_bytes(b"(00000001 ())\n")
        self.commit()
        self.base = self.git("rev-parse", "HEAD")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        proc = subprocess.run(["git", *args], cwd=self.root,
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.strip()

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "test")

    def add_original_binary(self):
        (self.root / self.dst).write_bytes(b"\x12\x34\x56")
        self.commit()

    def proof(self):
        blob = self.git("hash-object", "--", self.src.as_posix())
        obj = {
            "schema": "sens-t5-proof-admission/v1",
            "source": self.src.as_posix(),
            "source_era": "historical-legacy",
            "source_git_blob_sha1": blob,
            "source_sha256": hashlib.sha256((self.root / self.src).read_bytes()).hexdigest(),
            "expected_physical_sha256": hashlib.sha256((self.root / self.dst).read_bytes()).hexdigest(),
            "expected_typed_sha256": "0" * 64,
            "expected_current_eval_stdout": "(())\n",
            "oracle_commands": [["cargo", "test", "--test", "actual_source_oracle"]],
        }
        path = self.root / gate.MANIFEST_DIR / "real.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj), encoding="utf-8")
        return path

    def safe_kind(self, _root, _source):
        return None

    def approved(self, _root, _reader, _file, _manifest, _mirror):
        return {"d2_reader": "PASS", "current_eval": "PASS", "oracle_commands_passed": 1,
                "physical_sha256": hashlib.sha256((self.root / self.dst).read_bytes()).hexdigest()}

    def test_missing_reviewed_proof_is_block_not_physical_success(self):
        self.add_original_binary()
        state = gate.inspect(self.root, self.base, self.reader, self.approved, self.safe_kind)
        self.assertEqual(state["summary"]["blocked"], 1)
        self.assertEqual(state["files"][0]["status"], "BLOCKED")
        self.assertIn("MANIFEST", state["files"][0]["reason"])

    def test_original_proof_only_after_sha_and_actual_publisher_invocation(self):
        self.add_original_binary()
        self.proof()
        invoked = []
        def witness(root, reader, file, manifest, mirror):
            invoked.append((file, manifest))
            return self.approved(root, reader, file, manifest, mirror)
        state = gate.inspect(self.root, self.base, self.reader, witness, self.safe_kind)
        self.assertEqual(state["summary"]["original_files_proof_checked"], 1)
        self.assertEqual(state["summary"]["automatic_semantic_certification"], 0)
        self.assertEqual(state["files"][0]["semantic_oracle"],
                         "NAMED_TESTS_PASSED_REVIEW_REQUIRED")
        self.assertEqual(len(invoked), 1)

    def test_same_source_path_with_mutated_old_content_blocks(self):
        (self.root / self.src).write_bytes(b"(00000100 ())\n")
        self.add_original_binary()
        self.proof()
        state = gate.inspect(self.root, self.base, self.reader, self.approved, self.safe_kind)
        self.assertEqual(state["status"], "BLOCKED")
        self.assertIn("SOURCE_CHANGED", state["files"][0]["reason"])

    def test_committed_source_change_cannot_be_hidden_by_dirty_worktree(self):
        (self.root / self.src).write_bytes(b"(00000100 ())\\n")
        self.add_original_binary()
        # Restore worktree only. The PR HEAD would still ship modified source!
        original = subprocess.run(
            ["git", "show", f"{self.base}:{self.src.as_posix()}"],
            cwd=self.root, capture_output=True, check=True,
        ).stdout
        (self.root / self.src).write_bytes(original)
        self.proof()
        state = gate.inspect(self.root, self.base, self.reader, self.approved, self.safe_kind)
        self.assertEqual(state["status"], "BLOCKED")
        self.assertIn("SOURCE_CHANGED", state["files"][0]["reason"])

    def test_dirty_physical_bytes_cannot_stand_in_for_committed_original(self):
        self.add_original_binary()
        manifest = self.proof()
        (self.root / self.dst).write_bytes(b"\x01\x23")
        document = json.loads(manifest.read_text(encoding="utf-8"))
        document["expected_physical_sha256"] = hashlib.sha256(
            (self.root / self.dst).read_bytes()
        ).hexdigest()
        manifest.write_text(json.dumps(document), encoding="utf-8")
        def must_not_attest(*args):
            self.fail("must not run oracle for uncommitted physical replacement")
        state = gate.inspect(self.root, self.base, self.reader, must_not_attest, self.safe_kind)
        self.assertEqual(state["status"], "BLOCKED")
        self.assertIn("PHYSICAL_HEAD_DRIFT", state["files"][0]["reason"])

    def test_dirty_new_cohort_binary_is_not_exempt_from_git_integrity(self):
        new = Path("tests/fixtures/new-canary/prog.lisp")
        (self.root / new).parent.mkdir(parents=True)
        (self.root / new).write_bytes(b"(001 ())\n")
        binary = self.root / new.with_suffix(".sens")
        binary.write_bytes(b"\x23")
        self.commit()
        binary.write_bytes(b"\x24")
        state = gate.inspect(self.root, self.base, self.reader, self.approved, self.safe_kind)
        self.assertEqual(state["status"], "BLOCKED")
        self.assertIn("PHYSICAL_HEAD_DRIFT", state["files"][0]["reason"])
        self.assertEqual(state["summary"]["new_cohorts_not_original_credit"], 0)

    def test_tampered_physical_digest_blocks_before_oracle(self):
        self.add_original_binary()
        manifest = self.proof()
        data = json.loads(manifest.read_text())
        data["expected_physical_sha256"] = "f" * 64
        manifest.write_text(json.dumps(data))
        def should_not_run(*args):
            self.fail("must not run publisher after physical SHA drift")
        state = gate.inspect(self.root, self.base, self.reader, should_not_run, self.safe_kind)
        self.assertIn("PHYSICAL", state["files"][0]["reason"])

    def test_missing_current_runtime_expected_output_blocks_before_publisher(self):
        self.add_original_binary()
        path = self.proof()
        obj = json.loads(path.read_text(encoding="utf-8"))
        obj.pop("expected_current_eval_stdout")
        path.write_text(json.dumps(obj), encoding="utf-8")
        def cannot_run(*args):
            self.fail("unreviewed current runtime result must never invoke publisher")
        state = gate.inspect(self.root, self.base, self.reader, cannot_run, self.safe_kind)
        self.assertEqual(state["status"], "BLOCKED")
        self.assertIn("CURRENT_EVAL", state["files"][0]["reason"])

    def test_wrong_current_runtime_result_or_skipped_execution_blocks(self):
        self.add_original_binary()
        path = self.proof()
        obj = json.loads(path.read_text(encoding="utf-8"))
        obj["expected_current_eval_stdout"] = "incorrect\n"
        path.write_text(json.dumps(obj), encoding="utf-8")
        def unexecuted(*args):
            return {"d2_reader": "PASS", "oracle_commands_passed": 3}
        state = gate.inspect(self.root, self.base, self.reader, unexecuted, self.safe_kind)
        self.assertEqual(state["status"], "BLOCKED")
        self.assertIn("CURRENT_EVAL", state["files"][0]["reason"])
        for value in ("", "not LF", "\r\n", None, 23):
            obj["expected_current_eval_stdout"] = value
            with self.subTest(value=value), self.assertRaises(gate.Blocked):
                gate.expected_current_execution(obj)

    def test_claim_of_oracle_pass_with_no_named_tests_blocks(self):
        self.add_original_binary()
        self.proof()
        def no_oracle(*args):
            return {"d2_reader": "PASS", "oracle_commands_passed": 0}
        state = gate.inspect(self.root, self.base, self.reader, no_oracle, self.safe_kind)
        self.assertEqual(state["status"], "BLOCKED")
        self.assertIn("ORACLE", state["files"][0]["reason"])

    def test_new_canary_both_source_and_target_new_not_old_credit(self):
        new = Path("tests/fixtures/new-canary/prog.lisp")
        (self.root / new).parent.mkdir(parents=True)
        (self.root / new).write_bytes(b"(001 ())\n")
        (self.root / new.with_suffix(".sens")).write_bytes(b"\x23")
        self.commit()
        state = gate.inspect(self.root, self.base, self.reader, self.approved, self.safe_kind)
        self.assertEqual(state["summary"]["new_cohorts_not_original_credit"], 1)
        self.assertEqual(state["summary"]["original_files_proof_checked"], 0)

    def test_symlink_old_source_new_binary_cannot_sneak_through(self):
        path = self.root / self.dst
        path.symlink_to(self.src.name)
        self.commit()
        with self.assertRaisesRegex(gate.Blocked, "symlink"):
            gate.inspect(self.root, self.base, self.reader, self.approved, self.safe_kind)

    def test_reviewed_archival_original_is_rejected_by_current_operator_kind(self):
        archive = Path("benchmarks/sens-surface/results/20260925-icount-33bfb53a/programs/empty-en.lisp")
        # Real installed policy, not an ad-hoc second archive list.
        with self.assertRaisesRegex(gate.Blocked, "NONPROGRAM"):
            gate.reviewed_source_kind_guard(ROOT, archive)

    def test_nonprogram_kind_blocks_even_with_oracle_claim_and_valid_digest(self):
        self.add_original_binary()
        self.proof()
        def forbidden(_root, _source):
            raise gate.Blocked("SOURCE_KIND: reviewed NONPROGRAM, not an executable")
        def should_not_run(*args):
            self.fail("kind embargo must stop publishing, even with reviewed manifest")
        state = gate.inspect(self.root, self.base, self.reader, should_not_run, forbidden)
        self.assertEqual(state["status"], "BLOCKED")
        self.assertEqual(state["summary"]["original_files_proof_checked"], 0)
        self.assertIn("NONPROGRAM", state["files"][0]["reason"])

    def test_untrusted_base_sha_blocks(self):
        self.add_original_binary()
        with self.assertRaisesRegex(gate.Blocked, "BASE"):
            gate.inspect(self.root, "HEAD;rm -rf", self.reader, self.approved, self.safe_kind)

    def test_only_unchanged_source_still_requires_one_unique_reviewed_manifest(self):
        self.add_original_binary()
        original = self.proof()
        duplicate = original.with_name("duplicate.json")
        duplicate.write_bytes(original.read_bytes())
        state = gate.inspect(self.root, self.base, self.reader, self.approved, self.safe_kind)
        self.assertEqual(state["status"], "BLOCKED")
        self.assertIn("found 2", state["files"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
