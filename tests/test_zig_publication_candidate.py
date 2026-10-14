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
        self.trusted_translation_sha256 = None
        self.origin = base / "pre-translation-original.lisp"
        self.origin.write_bytes(b"(historical source snapshot)")

    def write(self):
        self.receipt.write_text(json.dumps(self.data), encoding="utf-8")

    def translation_evidence(self, **changes):
        evidence_path = self.receipt.parent / "migration-attestation.json"
        evidence = {
            "schema": gate.TRANSLATION_SCHEMA,
            "origin_era": "historical",
            "origin_path": str(self.origin),
            "origin_sha256": sha(self.origin.read_bytes()),
            "post_translation_source_sha256": sha(self.source.read_bytes()),
            "candidate_physical_sha256": sha(self.candidate.read_bytes()),
        }
        evidence.update(changes)
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
        digest = sha(evidence_path.read_bytes())
        self.data["source_era"] = "translated"
        self.data["translation_receipt"] = dict(path=str(evidence_path), sha256=digest)
        self.trusted_translation_sha256 = digest
        self.write()
        return evidence_path

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
        if op == "encode":
            # Fake process executes the same I/O interface as real sens-trit;
            # it is CI glue, NEVER a replacement for SENS semantic authority.
            src = Path(command[2])
            if src.suffix != ".lisp":
                self.fail("SENS encode must receive a binary source snapshot")
            if self.mutant == "encode-error":
                return subprocess.CompletedProcess(command, 1, stdout=b"",
                                                   stderr=b"source rejected")
            if self.mutant != "encode-missing":
                projection = self.candidate.read_bytes()
                if self.mutant == "source-mismatch":
                    projection = bytes.fromhex("35")
                src.with_suffix(".sens").write_bytes(projection)
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
                           self.zig, self.sens, runner=self.runner,
                           trusted_translation_sha256=self.trusted_translation_sha256)

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
        proof = self.translation_evidence()
        self.assertEqual(self.check()["source_era"], "translated")
        self.assertEqual(self.check()["provenance_status"],
                         "EXTERNAL_PIN_AND_SOURCE_BOUND_NOT_AUTHENTICATED")
        self.trusted_translation_sha256 = None
        with self.assertRaisesRegex(gate.Rejected, "independent provenance pin"):
            self.check()
        self.trusted_translation_sha256 = sha(proof.read_bytes())
        proof.write_bytes(b"mutated")
        with self.assertRaisesRegex(gate.Rejected, "translation_receipt: digest mismatch"):
            self.check()

    def test_translation_provenance_cannot_bind_unrelated_source_or_carrier(self):
        cases = (
            ("post_translation_source_sha256", "post_translation_source"),
            ("candidate_physical_sha256", "post_translation_physical"),
            ("origin_sha256", "translation_origin"),
        )
        for field, message in cases:
            with self.subTest(field=field):
                self.translation_evidence(**{field: "0" * 64})
                with self.assertRaisesRegex(gate.Rejected, message):
                    self.check()

    def test_era_receipt_must_have_explicit_schema_and_historical_origin(self):
        for changes, expected in (
            ({"schema": "unrelated-format"}, "schema mismatch"),
            ({"origin_era": "current"}, "origin era must be explicit"),
            ({"origin_path": str(self.source)}, "distinct absolute file"),
        ):
            with self.subTest(changes=changes):
                self.translation_evidence(**changes)
                with self.assertRaisesRegex(gate.Rejected, expected):
                    self.check()

    def test_self_pinned_receipt_does_not_prove_independent_provenance(self):
        self.translation_evidence()
        self.trusted_translation_sha256 = "0" * 64
        with self.assertRaisesRegex(gate.Rejected, "independent_translation_pin"):
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

    def test_sens_source_projection_must_match_pinned_candidate(self):
        # Even when both SHA fields are correct for their own respective
        # files, mismatched source→T5 is NOT a publishable candidate.
        self.mutant = "source-mismatch"
        with self.assertRaisesRegex(gate.Rejected, "SENS source/physical mismatch"):
            self.check()

    def test_sens_source_reencoding_must_run_and_emit_a_regular_file(self):
        self.mutant = "encode-error"
        with self.assertRaisesRegex(gate.Rejected, "executor rejected"):
            self.check()
        self.mutant = "encode-missing"
        with self.assertRaisesRegex(gate.Rejected, "SENS source encode produced no"):
            self.check()

    def test_post_translation_source_must_be_exact_binary_lisp(self):
        self.source = self.source.with_suffix(".txt")
        self.source.write_bytes(b"10 001 00 000 01\n")
        self.data["source_sha256"] = sha(self.source.read_bytes())
        self.write()
        with self.assertRaisesRegex(gate.Rejected, "post-admission source"):
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

    def test_changed_admission_receipt_during_execution_is_rejected(self):
        original_runner = self.runner

        def adversarial(command, **kwargs):
            result = original_runner(command, **kwargs)
            if command[1] == "backend":
                self.receipt.write_text(self.receipt.read_text() + " ")
            return result

        with self.assertRaisesRegex(gate.Rejected, "admission receipt mutated"):
            gate.verify(self.candidate, self.source, self.receipt,
                        self.zig, self.sens, runner=adversarial)

    def test_changed_translation_evidence_during_execution_is_rejected(self):
        proof = self.translation_evidence()
        original_runner = self.runner

        def adversarial(command, **kwargs):
            result = original_runner(command, **kwargs)
            if command[1] == "backend":
                proof.write_bytes(proof.read_bytes() + b" ")
            return result

        with self.assertRaisesRegex(gate.Rejected, "translation provenance mutated"):
            gate.verify(self.candidate, self.source, self.receipt,
                        self.zig, self.sens, runner=adversarial,
                        trusted_translation_sha256=self.trusted_translation_sha256)

    def test_changed_original_during_execution_is_rejected(self):
        self.translation_evidence()
        original_runner = self.runner

        def adversarial(command, **kwargs):
            result = original_runner(command, **kwargs)
            if command[1] == "backend":
                self.origin.write_bytes(self.origin.read_bytes() + b"!")
            return result

        with self.assertRaisesRegex(gate.Rejected, "translation origin mutated"):
            gate.verify(self.candidate, self.source, self.receipt,
                        self.zig, self.sens, runner=adversarial,
                        trusted_translation_sha256=self.trusted_translation_sha256)

    def test_never_lets_unsafe_paths_pass(self):
        candidate = self.candidate
        self.candidate = candidate.with_suffix(".lisp")
        self.candidate.write_bytes(candidate.read_bytes())
        with self.assertRaisesRegex(gate.Rejected, "physical .sens"):
            self.check()


if __name__ == "__main__":
    unittest.main()
