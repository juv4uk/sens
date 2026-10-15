#!/usr/bin/env python3
"""H2 H1-origin canaries. Not a mock of SENS or Zig semantic execution.

The real H2 runner still builds Zig/C and native SENS, after these checks.
"""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research" / "zig-codecs" / "host-c" / "verify_h2_cross_host.py"
SPEC = importlib.util.spec_from_file_location("sens_h2_h1_guard", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
h2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(h2)


class H2H1ExactSourceAndBinaryReceipt(unittest.TestCase):
    def setUp(self):
        self.paths = (
            h2.C_SOURCE, h2.C_ABI_HEADER, h2.C_DRIVER, h2.H1_VERIFIER, h2.ZIG_ABI,
        )
        self.sources = {path: f"{n + 1:064x}"
                        for n, path in enumerate(self.paths)}
        self.binary_sha = "b" * 64
        self.archive_sha = "c" * 64
        self.h1 = {
            "test_id": "H1_C_ZIG_ELF_DEPENDENCY_RECEIPT",
            "status": "INSPECTED_NO_RUST_MARKERS",
            "semantic_conformance_proven": False,
            "full_static_dependency_closure_proven": False,
            "binary_sha256": self.binary_sha,
            "zig_archive_sha256": self.archive_sha,
            "source_sha256": dict(self.sources),
        }

    def transcript(self):
        return [
            h2.H1_D10,
            h2.H1_VERIFIED,
            json.dumps(self.h1, sort_keys=True),
            f"C_D3_SUBSET_RECEIPT zig=0.16.0 c_binary_sha256={self.binary_sha}",
            h2.H1_READY,
        ]

    def reject(self, lines, reason="H2_H1_CHAIN"):
        with self.assertRaisesRegex(h2.AuditFailure, reason):
            h2.verify_h1_execution_receipt("\n".join(lines), self.sources)

    def test_exact_h1_rust_free_chain_reaches_h2(self):
        verified = h2.verify_h1_execution_receipt(
            "\n".join(self.transcript()), self.sources)
        self.assertEqual(verified["c_binary_sha256"], self.binary_sha)
        self.assertEqual(verified["zig_archive_sha256"], self.archive_sha)
        self.assertEqual(verified["d10_abi_physical"], "COORDINATE_ONLY")
        self.assertEqual(verified["h1_source_sha256"], self.sources)

    def test_h1_verifier_is_part_of_source_pin(self):
        self.assertIn(h2.H1_VERIFIER, h2.H2_TRACKED_INPUTS)

    def test_missing_d10_not_accepted_by_h2(self):
        self.reject(self.transcript()[1:])

    def test_duplicate_d10_not_accepted_by_h2(self):
        x = self.transcript()
        self.reject([x[0], x[0], *x[1:]])

    def test_semantic_claim_cannot_replace_d10_coordinate_evidence(self):
        x = self.transcript()
        x[0] = x[0].replace("d10_callable=NO", "d10_callable=YES")
        self.reject(x)

    def test_missing_h1_stdout_checker_rejected(self):
        x = self.transcript()
        self.reject([x[0], *x[2:]])

    def test_h1_json_missing_rejected(self):
        x = self.transcript()
        self.reject([*x[:2], *x[3:]])

    def test_replayed_h1_elf_json_rejected(self):
        x = self.transcript()
        self.reject([*x[:3], x[2], *x[3:]])

    def test_h1_claiming_full_static_closure_rejected(self):
        self.h1["full_static_dependency_closure_proven"] = True
        self.reject(self.transcript())

    def test_c_binary_digest_must_equal_inspected_elf_digest(self):
        x = self.transcript()
        x[3] = x[3].replace(self.binary_sha, "0" * 64)
        self.reject(x)

    def test_zig_archive_digest_required(self):
        self.h1["zig_archive_sha256"] = "unverified"
        self.reject(self.transcript())

    def test_c_source_digest_mismatch_rejected(self):
        self.h1["source_sha256"][h2.C_SOURCE] = "0" * 64
        self.reject(self.transcript(), "source=")

    def test_h1_verifier_digest_missing_rejected(self):
        del self.h1["source_sha256"][h2.H1_VERIFIER]
        self.reject(self.transcript(), "source=")

    def test_d10_after_elf_report_rejected(self):
        x = self.transcript()
        x[0], x[2] = x[2], x[0]
        self.reject(x)

    def test_missing_h1_final_provenance_rejected(self):
        self.reject(self.transcript()[:-1])

    def test_wrong_h1_source_authority_rejected(self):
        x = self.transcript()
        x[-1] = x[-1].replace(
            "semantic_authority=SENS", "semantic_authority=Rust")
        self.reject(x)


if __name__ == "__main__":
    unittest.main()
