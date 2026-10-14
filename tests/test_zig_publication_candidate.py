"""CI_GLUE_NO_SEMANTICS: positive/negative proof of prepublication boundaries."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "verify_zig_publication_candidate.py"
spec = importlib.util.spec_from_file_location("zig_pub_gate", MODULE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def sha(value):
    return hashlib.sha256(value).hexdigest()


class PublicationCandidateTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="zig-corridor-pub-")
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.candidate = base / "quote.sens"
        self.candidate.write_bytes(bytes.fromhex("638906a1"))
        self.source = base / "quote.lisp"
        self.source.write_bytes(b"10 001 00 000 01\n")
        self.zig = base / "zig-transporter"
        self.zig.write_bytes(b"pinned zig bytes")
        self.sens = base / "sens-trit"
        self.sens.write_bytes(b"pinned native SENS binary")
        self.receipt = base / "receipt.json"
        self.native_stdout = b"000\n"
        self.data = dict(
            schema=gate.SCHEMA, source_era="current",
            source_sha256=sha(self.source.read_bytes()),
            physical_sha256=sha(self.candidate.read_bytes()),
            zig_executor_sha256=sha(self.zig.read_bytes()),
            sens_executor_sha256=sha(self.sens.read_bytes()),
            expected_native_stdout_sha256=sha(self.native_stdout),
        )
        self.write()
        self.mutant = None

    def write(self):
        self.receipt.write_text(json.dumps(self.data), encoding="utf-8")

    def runner(self, command, **kwargs):
        self.assertEqual(kwargs.get("check"), False)
        op = command[1]
        if op == "backend":
            out = b"transport=zig abi=2 semantic_authority=SENS\n"
            if self.mutant == "backend":
                out = b"transport=rust semantic_authority=SENS\n"
            return subprocess.CompletedProcess(command, 0, stdout=out, stderr=b"")
        if op == "t5-roundtrip":
            body = self.candidate.read_bytes()
            if self.mutant == "replay":
                body = body[:-1]
            Path(command[3]).write_bytes(body)
            return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")
        if op == "eval":
            if self.mutant == "native-error":
                return subprocess.CompletedProcess(command, 1, stdout=b"", stderr=b"rejected")
            out = self.native_stdout
            if self.mutant == "native-mismatch":
                out = b"001\n"
            return subprocess.CompletedProcess(command, 0, stdout=out, stderr=b"")
        self.fail(f"unexpected command {command!r}")

    def check(self):
        return gate.verify(self.candidate, self.source, self.receipt,
                           self.zig, self.sens, runner=self.runner)

    def test_exact_source_zig_replay_and_native_sens_receipt(self):
        verdict = self.check()
        self.assertEqual(verdict["status"], "CANDIDATE_VERIFIED_NOT_PUBLISHED")
        self.assertEqual(verdict["semantic_authority"],
                         "SENS_EXECUTED_NOT_RATIFIED_BY_THIS_SCRIPT")

    def test_no_implicit_era_even_if_physical_bytes_identical(self):
        for invalid in (None, "auto", "legacy", "unknown"):
            with self.subTest(invalid=invalid):
                self.data["source_era"] = invalid
                self.write()
                with self.assertRaisesRegex(gate.Rejected, "era must be explicit"):
                    self.check()

    def test_translation_requires_distinct_pinned_provenance(self):
        self.data["source_era"] = "translated"
        self.write()
        with self.assertRaisesRegex(gate.Rejected, "separate provenance"):
            self.check()
        proof = self.receipt.parent / "migration-attestation.json"
        proof.write_bytes(b'{"origin":"historical","witness":"source hash pinned"}')
        self.data["translation_receipt"] = dict(
            path=str(proof), sha256=sha(proof.read_bytes())
        )
        self.write()
        self.assertEqual(self.check()["source_era"], "translated")
        proof.write_bytes(b"mutated")
        with self.assertRaisesRegex(gate.Rejected, "translation_receipt: digest mismatch"):
            self.check()

    def test_physical_and_source_sha_mismatches_fail_closed(self):
        for key in ("source_sha256", "physical_sha256", "zig_executor_sha256",
                    "sens_executor_sha256", "expected_native_stdout_sha256"):
            with self.subTest(key=key):
                original = self.data[key]
                self.data[key] = "0" * 64
                self.write()
                with self.assertRaises(gate.Rejected):
                    self.check()
                self.data[key] = original
                self.write()

    def test_zig_must_replay_exact_bytes_before_native_execution(self):
        self.mutant = "replay"
        with self.assertRaisesRegex(gate.Rejected, "Zig byte replay mismatch"):
            self.check()

    def test_backend_must_claim_zig_and_sens_separately(self):
        self.mutant = "backend"
        with self.assertRaisesRegex(gate.Rejected, "Zig mechanical backend"):
            self.check()

    def test_native_result_must_be_real_and_match_pinned_digest(self):
        for mutant in ("native-error", "native-mismatch"):
            with self.subTest(mutant=mutant):
                self.mutant = mutant
                with self.assertRaises(gate.Rejected):
                    self.check()

    def test_never_lets_unsafe_paths_pass(self):
        candidate = self.candidate
        self.candidate = candidate.with_suffix(".lisp")
        self.candidate.write_bytes(candidate.read_bytes())
        with self.assertRaisesRegex(gate.Rejected, "physical .sens"):
            self.check()


if __name__ == "__main__":
    unittest.main()
