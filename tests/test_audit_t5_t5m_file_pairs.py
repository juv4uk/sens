#!/usr/bin/env python3
"""Read-only repo-wide T5 .lisp/.sens provenance guard regression."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_t5_t5m_file_pairs import inspect, main, require_changed_views, split_nul_delimited_paths
from sens_t5_t5m_codec import encode_words, encode_t5m_projection


class AuditT5PairsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_git_z_path_parser_splits_actual_nul_delimiters(self):
        self.assertEqual(split_nul_delimited_paths(b""), [])
        self.assertEqual(
            split_nul_delimited_paths(b"examples/a.sens" + bytes([0]) + b"nested/b.sens" + bytes([0])),
            ["examples/a.sens", "nested/b.sens"],
        )

    def test_git_z_path_parser_fails_closed_on_malformed_framing(self):
        with self.assertRaisesRegex(ValueError, "NUL"):
            split_nul_delimited_paths(b"examples/a.sens")
        with self.assertRaisesRegex(ValueError, "NUL"):
            split_nul_delimited_paths(b"examples/a.sens" + bytes([0, 0]))

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

    def test_untracked_inventory_does_not_cross_into_nested_worktree(self):
        self.pair("main/програма", "()\n", ["000"])
        self.pair(".worktrees/інша-гілка/старий-знімок", "()\n", ["000"])
        result = self.audit()
        self.assertEqual(len(result["files"]), 1)
        self.assertEqual(result["files"][0]["source"], "main/програма.lisp")

    def test_superseded_contest_candidates_are_outside_active_audit(self):
        self.pair("benchmarks/contest-uk/winner", "10 01\n", ["10", "01"])
        self.pair("benchmarks/contest-uk/superseded/older", "10 01\n", ["10", "01"])
        report = self.audit()
        self.assertEqual(report["summary"]["sens_files"], 1)
        self.assertEqual(report["summary"]["lisp_files"], 1)
        self.assertEqual(report["files"][0]["source"],
                         "benchmarks/contest-uk/winner.lisp")

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

    def test_new_t5m_pair_and_view_use_exact_words_without_false_semantic_credit(self):
        # Reuse a real canonical Ukrainian Lisp/T5 witness, repacked as T5M.
        fixture = ROOT / "tests/fixtures/migration-d1-cond-cohort"
        source = (fixture / "branch.lisp").read_text(encoding="utf-8")
        canonical = (fixture / "branch").read_text(encoding="ascii")
        words = canonical.rstrip("\n").split(" ")
        _, binary = self.pair("lib/current", source, words)
        binary.write_bytes(encode_t5m_projection(canonical))
        binary.with_suffix("").write_text(canonical, encoding="ascii")
        row = self.audit()["files"][0]
        self.assertEqual(row["physical_status"], "PASS")
        self.assertEqual(row["physical_codec"], "t5m")
        self.assertEqual(row["view_status"], "PASS")
        self.assertEqual(row["source_status"], "PENDING_ORACLE")

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
        _, current = self.pair("src/first", "10 01\n", ["10", "01"])
        current.write_bytes(encode_t5m_projection("10 01\n"))
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

    def test_identical_t5_and_t5m_wire_is_current_canonical_t5m(self):
        # Both codecs emit the same exact physical bytes for this stream.
        # Byte identity cannot establish historical origin; do not invent
        # a legacy classification when canonical T5M accepts those bytes.
        words = ["10", "01"]
        self.assertEqual(encode_words(words), encode_t5m_projection("10 01\n"))
        self.pair("lib/shared-wire", "10 01\n", words)
        (self.root / "lib/shared-wire").write_text("10 01\n", encoding="ascii")
        report = self.audit()
        self.assertEqual(report["files"][0]["physical_codec"], "t5m")
        self.assertEqual(report["files"][0]["view_status"], "PASS")
        self.assertEqual(report["status"], "EXACT_BINARY_PAIRS")
        require_changed_views(report, ["lib/shared-wire.sens"])

        # A genuinely identified legacy row remains unfit for NEW physical
        # artifacts. This negative guard is an explicit report-state witness,
        # not an invented claim about identical wire bytes.
        report["files"][0]["physical_codec"] = "t5"
        with self.assertRaisesRegex(ValueError, "canonical T5M"):
            require_changed_views(report, ["lib/shared-wire.sens"])

    def test_source_census_exposes_lisp_without_sens_and_release_gate_blocks(self):
        self.pair("lib/paired", "10 01\n", ["10", "01"])
        (self.root / "lib/unpaired.lisp").write_text(
            "(визначити відсутній так)\n", encoding="utf-8"
        )
        inventory = self.audit(strict=True)
        self.assertEqual(inventory["status"], "EXACT_BINARY_PAIRS")
        self.assertEqual(inventory["summary"]["lisp_files"], 2)
        self.assertEqual(inventory["summary"]["lisp_with_sens"], 1)
        self.assertEqual(inventory["summary"]["lisp_without_sens"], 1)
        self.assertEqual(inventory["lisp_without_sens"], ["lib/unpaired.lisp"])
        gated = inspect(self.root, include_untracked=True,
                        strict_semantic=True, require_complete_sources=True)
        self.assertEqual(gated["status"], "BLOCKED")
        self.assertEqual(main([str(self.root), "--include-untracked",
                               "--require-complete-sources"]), 2)
        self.assertEqual(main([str(self.root), "--include-untracked",
                               "--require-complete-sources", "--inventory-only"]), 0)

    def test_no_sens_files_does_not_hide_unpaired_lisp(self):
        (self.root / "only.lisp").write_text(
            "(визначити річ так)\n", encoding="utf-8"
        )
        inventory = self.audit()
        self.assertEqual(inventory["status"], "NO_FILES")
        self.assertEqual(inventory["summary"]["lisp_without_sens"], 1)
        self.assertEqual(inventory["lisp_without_sens"], ["only.lisp"])
        strict = inspect(self.root, include_untracked=True,
                         require_complete_sources=True)
        self.assertEqual(strict["status"], "BLOCKED")
        self.assertTrue(strict["empty_is_not_certification"])

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
