#!/usr/bin/env python3
"""Actual Cargo compiler-artifact path must match executed Rust SENS host.

The tests exercise build-receipt parsing only, never invent SENS semantics.
Native Zig/C/Rust parity still uses existing H2 --run.
"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/zig-codecs/host-c/verify_h2_cross_host.py"
SPEC = importlib.util.spec_from_file_location("h2_cargo_artifact_binding", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
h2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(h2)


class H2CargoActualExecutable(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sens-h2-cargo-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.requested = "target/debug/sens"
        self.path = self.root / self.requested
        self.manifest = self.root / "crates/sens-cli/Cargo.toml"
        self.source = self.root / "crates/sens-cli/src/main.rs"
        self.artifact = {
            "reason": "compiler-artifact",
            "package_id": "path+file:///workspace#sens-cli@0.42.1",
            "manifest_path": str(self.manifest),
            "target": {"kind": ["bin"], "name": "sens",
                       "src_path": str(self.source)},
            "executable": str(self.path),
        }
        self.finish = {"reason": "build-finished", "success": True}

    def transcript(self, records=None):
        if records is None:
            records = [self.artifact, self.finish]
        return "\n".join(json.dumps(x, sort_keys=True) for x in records) + "\n"

    def check(self, records=None, requested=None):
        return h2.verify_cargo_sens_artifact(
            self.transcript(records), self.root,
            self.requested if requested is None else requested)

    def rejects(self, records, reason="H2_CARGO_ARTIFACT"):
        with self.assertRaisesRegex(h2.AuditFailure, reason):
            self.check(records)

    def test_positive_exact_artifact_and_successful_finish(self):
        proof = self.check()
        self.assertEqual(proof["executable"], str(self.path))
        self.assertEqual(proof["target"], "sens-cli/sens")

    def test_dependency_artifacts_are_ignored_not_promoted(self):
        dependency = dict(self.artifact)
        dependency["target"] = {"kind": ["lib"], "name": "sens"}
        self.assertEqual(self.check([dependency, self.artifact, self.finish])[
            "executable"], str(self.path))

    def test_spoofed_prebuilt_executable_not_reported_by_cargo(self):
        self.rejects([self.finish], "one_target_and_finish")

    def test_cargo_failure_not_promoted_by_process_exit(self):
        self.rejects([self.artifact, {"reason": "build-finished", "success": False}])

    def test_duplicate_compiler_artifact_is_not_one_executable(self):
        self.rejects([self.artifact, self.artifact, self.finish])

    def test_omitted_build_finished_is_rejected(self):
        self.rejects([self.artifact])

    def test_duplicate_build_finished_is_rejected(self):
        self.rejects([self.artifact, self.finish, self.finish])

    def test_final_record_must_be_successful_build_finished(self):
        self.rejects([self.artifact, self.finish, {"reason": "compiler-message"}])

    def test_cargo_executable_must_be_requested_host(self):
        self.artifact["executable"] = str(self.root / "fake/native-sens")
        self.rejects([self.artifact, self.finish], "expected_built_path")

    def test_rust_binary_from_another_package_rejected(self):
        self.artifact["manifest_path"] = str(self.root / "crates/other/Cargo.toml")
        self.rejects([self.artifact, self.finish], "sens-cli_manifest_and_source")

    def test_wrong_rust_entrypoint_is_rejected(self):
        self.artifact["target"]["src_path"] = str(self.root / "src/fake.rs")
        self.rejects([self.artifact, self.finish], "sens-cli_manifest_and_source")

    def test_stdout_not_a_cargo_json_object_rejected(self):
        for data in ("Cargo compiled OK\n", "null\n", ""):
            with self.subTest(data=data), self.assertRaisesRegex(
                    h2.AuditFailure, "H2_CARGO_ARTIFACT"):
                h2.verify_cargo_sens_artifact(data, self.root, self.requested)

    def test_replayed_target_receipt_cannot_override_different_requested_path(self):
        with self.assertRaisesRegex(h2.AuditFailure, "expected_built_path"):
            self.check(requested="target/release/sens")

    def test_dotdot_requested_executable_rejected(self):
        with self.assertRaisesRegex(h2.AuditFailure, "canonical_requested_path"):
            self.check(requested="target/../target/debug/sens")


if __name__ == "__main__":
    unittest.main()
