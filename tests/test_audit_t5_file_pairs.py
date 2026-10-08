#!/usr/bin/env python3
"""Read-only repo-wide T5 .lisp/.sens provenance guard regression."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_t5_file_pairs import inspect, main, require_changed_views
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

    def test_canonical_extensionless_view_passes_but_not_semantic_oracle(self):
        self.pair("ok/branch", "(за-умовою (ні (перше ())) (так так))\n",
                  ["10", "110", "00", "10", "0", "01"])
        view = self.root / "ok/branch"
        view.write_bytes(b"10 110 00 10 0 01\n")
        report = inspect(self.root, include_untracked=True, require_spaced_view=True)
        self.assertEqual(report["status"], "MECHANICAL_ONLY")
        self.assertEqual(report["summary"]["spaced_view_pass"], 1)
        self.assertEqual(report["summary"]["spaced_view_blocked"], 0)
        self.assertEqual(report["summary"]["spaced_view_missing"], 0)
        self.assertEqual(report["files"][0]["view_status"], "PASS")
        self.assertEqual(len(report["files"][0]["view_sha256"]), 64)
        self.assertEqual(report["files"][0]["source_status"], "PENDING_ORACLE")
        self.assertIsNone(report["summary"]["admitted_executable_semantics"])

    def test_present_but_forged_or_noncanonical_view_always_blocks(self):
        self.pair("branch", "(за-умовою (ні (перше ())) (так так))\n",
                  ["10", "110", "00", "1", "01"])
        view = self.root / "branch"
        canonical = b"10 110 00 1 01\n"
        variants = (
            canonical.replace(b" ", b"  ", 1),
            canonical.replace(b" ", b"\t", 1),
            canonical.replace(b" ", b"2", 1),
            canonical.replace(b"110", b"111", 1),
            canonical.replace(b"10", b"010", 1),
            canonical.rstrip(b"\n"),
            canonical + b"\n",
            canonical.replace(b"\n", b"\r\n"),
            b"(110 (1 1))\n",
            b"\xef\xbb\xbf" + canonical,
        )
        for data in variants:
            with self.subTest(view=data):
                view.write_bytes(data)
                report = self.audit()
                self.assertEqual(report["status"], "BLOCKED")
                self.assertEqual(report["summary"]["physical_blocked"], 0)
                self.assertEqual(report["summary"]["spaced_view_blocked"], 1)
                self.assertEqual(report["files"][0]["view_status"], "BLOCKED")
                self.assertIn("canonical T5", report["files"][0]["view_reason"])
        view.write_bytes(canonical)
        self.assertEqual(self.audit()["summary"]["spaced_view_pass"], 1)

    def test_legacy_pair_can_remain_view_pending_but_strict_scoped_gate_blocks(self):
        self.pair("legacy", "10 01\n", ["10", "01"])
        nonstrict = self.audit(strict=True)
        self.assertEqual(nonstrict["status"], "EXACT_BINARY_PAIRS")
        self.assertEqual(nonstrict["summary"]["spaced_view_missing"], 1)
        self.assertEqual(nonstrict["files"][0]["view_status"], "MISSING_NOT_CERTIFIED")
        strict = inspect(self.root, include_untracked=True, require_spaced_view=True)
        self.assertEqual(strict["status"], "BLOCKED")
        self.assertEqual(strict["summary"]["physical_blocked"], 0)
        self.assertEqual(strict["summary"]["spaced_view_missing"], 1)
        self.assertEqual(strict["summary"]["spaced_view_pass"], 0)
        self.assertEqual(main([str(self.root), "--include-untracked",
                               "--require-spaced-view"]), 2)
        (self.root / "legacy").write_bytes(b"10 01\n")
        self.assertEqual(main([str(self.root), "--include-untracked",
                               "--require-spaced-view"]), 0)

    def test_extensionless_symlink_cannot_pass_same_stem_validation(self):
        self.pair("test", "10 01\n", ["10", "01"])
        outside = self.root / "spaced-view"
        outside.write_text("10 01\n", encoding="ascii")
        (self.root / "test").symlink_to(outside)
        result = self.audit()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["summary"]["physical_pass"], 1)
        self.assertEqual(result["summary"]["spaced_view_blocked"], 1)
        self.assertIn("symlink", result["files"][0]["view_reason"])

    def test_repository_d1_uk_cond_fixture_is_real_triple_not_english_or_binary_lisp(self):
        cohort = ROOT / "tests/fixtures/migration-d1-cond-cohort"
        report = inspect(cohort, include_untracked=True, require_spaced_view=True)
        self.assertEqual(report["summary"]["sens_files"], 1)
        self.assertEqual(report["summary"]["spaced_view_pass"], 1)
        self.assertEqual(report["summary"]["physical_pass"], 1)
        self.assertEqual(report["summary"]["pending_oracle"], 1)
        self.assertEqual(report["status"], "MECHANICAL_ONLY")
        self.assertEqual(
            (cohort / "branch.lisp").read_text(encoding="utf-8"),
            "(за-умовою (ні (перше ())) (так так))\n",
        )
        self.assertTrue((cohort / "branch").read_bytes().endswith(b"\n"))

    def test_changed_new_physical_requires_proven_extensionless_view(self):
        self.pair("src/first", "10 01\n", ["10", "01"])
        self.pair("src/second", "10 01\n", ["10", "01"])
        src = "src/first.sens"
        report = self.audit()
        with self.assertRaisesRegex(ValueError, "same-stem canonical"):
            require_changed_views(report, [src])
        (self.root / "src/first").write_bytes(b"10 01\n")
        report = self.audit()
        require_changed_views(report, [src])  # original second pair is grandfathered
        with self.assertRaisesRegex(ValueError, "same-stem canonical"):
            require_changed_views(report, ["src/second.sens"])
        with self.assertRaisesRegex(ValueError, "not included"):
            require_changed_views(report, ["src/missing.sens"])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            require_changed_views(report, [src, src])
        with self.assertRaisesRegex(ValueError, "unsafe changed"):
            require_changed_views(report, ["../src/first.sens"])
        with self.assertRaisesRegex(ValueError, "invalid changed"):
            require_changed_views(report, ["/src/first.sens"])
        with self.assertRaisesRegex(ValueError, "invalid changed"):
            require_changed_views(report, ["src/first.lisp"])
        report["files"][0]["physical_status"] = "BLOCKED"
        with self.assertRaisesRegex(ValueError, "same-stem canonical"):
            require_changed_views(report, [src])
        with self.assertRaisesRegex(ValueError, "unknown T5 report"):
            require_changed_views({"schema": "unsupported"}, [src])

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
