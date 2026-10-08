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

    def audit(self, strict=False, require=None):
        return inspect(self.root, include_untracked=True, strict_semantic=strict,
                       require_view_for=require)

    def test_exact_spaced_view_triple_is_mechanically_reversible(self):
        self.pair("uk/branch", "(за-умовою (ні (перше ())) (так так))\n",
                  ["10", "110", "00", "10", "0", "00", "10", "100",
                   "00", "000", "01", "01", "00", "10", "1", "00", "1", "01", "01"])
        binary = self.root / "uk/branch.sens"
        self.assertEqual(binary.read_bytes().hex(), "67386515bf123b2dc4a9b1a1")
        (self.root / "uk/branch").write_bytes(
            b"10 110 00 10 0 00 10 100 00 000 01 01 00 10 1 00 1 01 01\n"
        )
        report = self.audit(require=["uk/branch.sens"])
        self.assertEqual(report["summary"]["required_spaced_views"], 1)
        self.assertEqual(report["summary"]["spaced_view_pass"], 1)
        self.assertEqual(report["summary"]["spaced_view_blocked"], 0)
        self.assertEqual(report["summary"]["physical_pass"], 1)
        self.assertEqual(report["files"][0]["view_status"], "PASS")
        self.assertEqual(report["files"][0]["view_typed_word_sha256"],
                         report["files"][0]["typed_word_sha256"])
        self.assertEqual(len(report["files"][0]["view_sha256"]), 64)
        self.assertEqual(report["files"][0]["source_status"], "PENDING_ORACLE")
        self.assertEqual(report["status"], "MECHANICAL_ONLY")

    def test_invalid_spaced_view_blocks_without_faking_t5_failure(self):
        self.pair("p", "(українська)\n", ["0", "00", "000"])
        good = b"0 00 000\n"
        view = self.root / "p"
        for bad in (
            None, b"", b"0 00 000", b"0 00 000\r\n",
            b"0  00 000\n", b" 0 00 000\n", b"0 00 000 \n",
            b"0\t00 000\n", b"0 00 000\n\n", b"0 00 000\n ",
            b"0 0 000\n", b"0 00 00\n", b"0 00 001\n",
            b"0 00 0002\n", b"D1:0 00 000\n",
            b"(0 00 000)\n", b"0 00 000# comment\n",
            b"\xd0° 00 000\n",
        ):
            with self.subTest(bad=bad):
                if bad is None:
                    view.unlink(missing_ok=True)
                else:
                    view.write_bytes(bad)
                result = self.audit(require=["p.sens"])
                self.assertEqual(result["status"], "BLOCKED")
                self.assertEqual(result["summary"]["physical_pass"], 1)
                self.assertEqual(result["summary"]["physical_blocked"], 0)
                self.assertEqual(result["summary"]["spaced_view_blocked"], 1)
                self.assertEqual(result["files"][0]["view_status"], "BLOCKED")
                self.assertIn("view", result["files"][0]["view_error"])
        view.write_bytes(good)
        self.assertEqual(self.audit(require=["p.sens"])["summary"]["spaced_view_pass"], 1)

    def test_view_scope_requires_real_selected_file_and_rejects_unsafe_paths(self):
        self.pair("safe", "(ні)\n", ["10", "0", "01"])
        (self.root / "safe").write_bytes(b"10 0 01\n")
        for scope in (["missing.sens"], ["safe.sens", "safe.sens"],
                      ["../safe.sens"], ["/safe.sens"], ["safe"],
                      ["./safe.sens"], ["sub//safe.sens"],
                      ["sub\\safe.sens"]):
            with self.subTest(scope=scope), self.assertRaises(ValueError):
                self.audit(require=scope)
        # No implicit 'all .sens' admission or view requirement.
        report = self.audit()
        self.assertEqual(report["summary"]["required_spaced_views"], 0)
        self.assertEqual(report["files"][0]["view_status"], "NOT_REQUIRED")

    def test_same_stem_view_symlink_does_not_escape_source_tree(self):
        self.pair("dir/check", "(ні)\n", ["10", "0", "01"])
        outside = self.root / "other"
        outside.write_bytes(b"10 0 01\n")
        (self.root / "dir/check").symlink_to(outside)
        report = self.audit(require=["dir/check.sens"])
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["summary"]["physical_pass"], 1)
        self.assertEqual(report["summary"]["spaced_view_blocked"], 1)
        self.assertIn("symlink", report["files"][0]["view_error"])

    def test_triple_view_scope_cli_fails_closed_on_missing_view(self):
        self.pair("required", "(ні)\n", ["10", "0", "01"])
        self.assertEqual(main([str(self.root), "--include-untracked",
                               "--require-view-for", "required.sens"]), 2)
        (self.root / "required").write_bytes(b"10 0 01\n")
        self.assertEqual(main([str(self.root), "--include-untracked",
                               "--require-view-for", "required.sens"]), 0)

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
