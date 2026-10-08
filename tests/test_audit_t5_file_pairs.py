#!/usr/bin/env python3
"""Read-only repo-wide T5 .lisp/.sens provenance guard regression."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_t5_file_pairs import inspect, main
from sens_t5_codec import encode_words


class AuditT5PairsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def pair(self, stem, source: str, words: list[str]):
        source_path = self.root / f"{stem}.lisp"
        binary_path = self.root / f"{stem}.sens"
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(source, encoding="utf-8")
        binary_path.write_bytes(encode_words(words))
        return source_path, binary_path

    def audit(self, strict=False):
        return inspect(self.root, include_untracked=True, strict_semantic=strict)

    def test_empty_repo_does_not_claim_migration_success(self):
        result = self.audit()
        self.assertEqual(result["status"], "NO_FILES")
        self.assertTrue(result["empty_is_not_certification"])
        self.assertEqual(result["summary"]["admitted_executable_semantics"], None)

    def test_paired_binary_projection_exact_width_is_verified(self):
        self.pair("examples/demo", "10 01\n", ["10", "01"])
        result = self.audit(strict=True)
        self.assertEqual(result["status"], "EXACT_BINARY_PAIRS")
        self.assertEqual(result["summary"]["physical_pass"], 1)
        self.assertEqual(result["summary"]["exact_binary_source_pairs"], 1)
        self.assertEqual(result["files"][0]["physical_bytes"], 1)
        self.assertEqual(result["files"][0]["physical_sha256"].__len__(), 64)

    def test_symbolic_source_requires_oracle_not_false_green(self):
        self.pair("lib/empty", "()\n", ["000"])
        result = self.audit()
        self.assertEqual(result["status"], "MECHANICAL_ONLY")
        self.assertEqual(result["summary"]["pending_oracle"], 1)
        self.assertEqual(result["files"][0]["source_status"], "PENDING_ORACLE")
        self.assertEqual(self.audit(strict=True)["status"], "BLOCKED")

    def test_same_stem_does_not_mean_same_bits(self):
        self.pair("lib/different", "0 00\n", ["000"])
        result = self.audit()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("identities differ", result["files"][0]["error"])

    def test_malformed_and_legacy_t5_are_rejected(self):
        self.pair("good", "10 01\n", ["10", "01"])
        (_, stale) = self.pair("legacy", "10 01\n", ["10", "01"])
        stale.write_bytes(bytes.fromhex("64f2"))
        self.assertEqual(self.audit()["summary"]["physical_blocked"], 1)
        self.assertIn("padding", self.audit()["files"][1]["error"])
        stale.write_bytes(b"10 01")  # ASCII is NOT the physical .sens format.
        self.assertEqual(self.audit()["status"], "BLOCKED")
        stale.write_bytes(b"\xf3")  # Impossible T5 packed byte.
        self.assertEqual(self.audit()["summary"]["physical_blocked"], 1)

    def test_missing_companion_and_symlink_are_rejected(self):
        (self.root / "orphan.sens").write_bytes(encode_words(["000"]))
        result = self.audit()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("missing same-stem", result["files"][0]["error"])
        (self.root / "orphan.sens").unlink()
        source, binary = self.pair("pair", "000\n", ["000"])
        source.unlink()
        outside = self.root / "outside.lisp"
        outside.write_text("000\n")
        source.symlink_to(outside)
        self.assertIn("symlink", self.audit()["files"][0]["error"])

    def test_collision_0_00_and_000_not_confused(self):
        self.pair("a", "0 00\n", ["0", "00"])
        self.pair("b", "000\n", ["000"])
        rows = self.audit()["files"]
        self.assertNotEqual(rows[0]["typed_word_sha256"], rows[1]["typed_word_sha256"])
        self.assertNotEqual(rows[0]["physical_sha256"], rows[1]["physical_sha256"])
        self.assertEqual(self.audit(strict=True)["status"], "EXACT_BINARY_PAIRS")

    def test_cli_generates_read_only_report_without_overwrite(self):
        self.pair("p", "10 01\n", ["10", "01"])
        report = self.root / "report.json"
        status = main([str(self.root), "--output", str(report), "--include-untracked"])
        self.assertEqual(status, 0)
        self.assertTrue(report.exists())
        self.assertEqual(list(self.root.glob("*.sens")), [self.root / "p.sens"])

    def test_separate_directories_with_same_stem_allowed(self):
        self.pair("a/lib", "000\n", ["000"])
        self.pair("b/lib", "1\n", ["1"])
        self.assertEqual(self.audit(strict=True)["summary"]["exact_binary_source_pairs"], 2)


if __name__ == "__main__":
    unittest.main()
