#!/usr/bin/env python3
"""Canonical third-view inventory tests; never infer Ukrainian semantic authority."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_t5_triplets.py"
spec = importlib.util.spec_from_file_location("audit_t5_triplets_under_test", SCRIPT)
assert spec and spec.loader
import sys
sys.path.insert(0, str(ROOT / "scripts"))
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
from sens_t5_codec import encode_words


class T5TripletInventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sens-triplet-audit-")
        self.root = Path(self.tmp.name)
        self.stem = self.root / "cohort" / "demo"
        self.stem.parent.mkdir(parents=True)
        self.source = self.stem.with_suffix(".lisp")
        self.physical = self.stem.with_suffix(".sens")
        self.view = self.stem
        self.words = ["10", "001", "00", "10", "000", "01"]
        self.source.write_text("(за-умовою (ні ()))\n", encoding="utf-8")
        self.physical.write_bytes(encode_words(self.words))

    def tearDown(self):
        self.tmp.cleanup()

    def audit(self):
        return mod.inspect(self.root, include_untracked=True)

    def test_complete_physical_view_never_claims_uk_oracle(self):
        self.view.write_bytes(mod.expected_ascii_view(self.words))
        audit = self.audit()
        self.assertEqual(audit["status"], "ALL_PHYSICAL_VIEWS_MATCH_PENDING_UK_ORACLE")
        self.assertEqual(audit["summary"]["tracked_physical_pairs"], 1)
        self.assertEqual(audit["summary"]["views_verified"], 1)
        self.assertEqual(audit["summary"]["views_missing"], 0)
        self.assertEqual(audit["summary"]["uk_semantic_oracles_certified_by_this_audit"], 0)
        self.assertEqual(audit["summary"]["original_executables_migrated_by_this_audit"], 0)
        row = audit["files"][0]
        self.assertEqual(row["stem"], "cohort/demo")
        self.assertEqual(row["view_status"], "VIEW_PASS")
        self.assertEqual(row["view_sha256"], row["expected_view_sha256"])
        self.assertFalse(row["executable_semantics_admitted"])
        self.assertEqual(row["uk_projection_status"], "ORACLE_NOT_VERIFIED")

    def test_missing_extensionless_is_incomplete_not_fake_pass(self):
        result = self.audit()
        self.assertEqual(result["status"], "PARTIAL_TRIPLES")
        self.assertEqual(result["summary"]["views_missing"], 1)
        self.assertEqual(result["files"][0]["view_status"], "MISSING_VIEW")
        self.assertEqual(mod.main([str(self.root), "--include-untracked",
                                   "--require-all-views"]), 2)

    def test_one_space_one_lf_exact_byte_contract(self):
        canonical = mod.expected_ascii_view(self.words)
        self.assertTrue(canonical.endswith(b"\n"))
        self.assertNotIn(b"2", canonical)
        self.assertEqual(canonical.count(b" "), len(self.words) - 1)
        self.view.write_bytes(canonical)
        self.assertEqual(self.audit()["summary"]["views_verified"], 1)
        corruptions = [
            canonical[:-1], canonical + b"\n", canonical.replace(b" ", b"  ", 1),
            canonical[:-1] + b" \n", canonical.replace(b" ", b"\t", 1),
            canonical.replace(b" ", b"2", 1), canonical.replace(b"\n", b"\r\n"),
            canonical.replace(b"1", b"\xd1\x96", 1), b"header: " + canonical,
        ]
        for raw in corruptions:
            with self.subTest(raw=raw[:25]):
                self.view.write_bytes(raw)
                audit = self.audit()
                self.assertEqual(audit["status"], "BLOCKED")
                self.assertEqual(audit["summary"]["views_invalid"], 1)

    def test_valid_but_stale_view_from_different_program_blocks(self):
        self.view.write_bytes(mod.expected_ascii_view(["10", "001", "01"]))
        self.assertEqual(self.audit()["files"][0]["view_status"], "INVALID_VIEW")

    def test_corrupt_physical_never_passes_from_good_view(self):
        self.view.write_bytes(mod.expected_ascii_view(self.words))
        self.physical.write_bytes(b"\xf3")
        result = self.audit()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["summary"]["physical_pairs_blocked"], 1)
        self.assertEqual(result["files"][0]["view_status"], "BLOCKED_PHYSICAL")

    def test_missing_source_blocks_physical_pair(self):
        self.view.write_bytes(mod.expected_ascii_view(self.words))
        self.source.unlink()
        result = self.audit()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["summary"]["physical_pairs_blocked"], 1)

    def test_extensionless_symlink_is_not_trusted(self):
        target = self.root / "danger.txt"
        target.write_bytes(mod.expected_ascii_view(self.words))
        self.view.symlink_to(target)
        self.assertEqual(self.audit()["files"][0]["view_status"], "INVALID_VIEW")
        self.assertEqual(target.read_bytes(), mod.expected_ascii_view(self.words))

    def test_existing_view_is_never_overwritten(self):
        self.view.write_bytes(b"sentinel")
        self.assertEqual(self.audit()["status"], "BLOCKED")
        self.assertEqual(self.view.read_bytes(), b"sentinel")
        self.assertTrue(self.physical.is_file())
        self.assertTrue(self.source.is_file())

    def test_cli_cannot_write_into_source_or_overwrite_report(self):
        self.view.write_bytes(mod.expected_ascii_view(self.words))
        self.assertEqual(mod.main([str(self.root), "--include-untracked",
                                   "--output", str(self.root / "report.json")]), 2)
        self.assertFalse((self.root / "report.json").exists())
        with tempfile.TemporaryDirectory(prefix="sens-triplet-report-") as external:
            dest = Path(external) / "audit.json"
            argv = [str(self.root), "--include-untracked", "--output", str(dest)]
            self.assertEqual(mod.main(argv), 0)
            data = json.loads(dest.read_text(encoding="utf-8"))
            self.assertEqual(data["summary"]["views_verified"], 1)
            before = dest.read_bytes()
            self.assertEqual(mod.main(argv), 2)
            self.assertEqual(dest.read_bytes(), before)

    def test_empty_corpus_cannot_pass_release(self):
        self.physical.unlink()
        data = self.audit()
        self.assertEqual(data["status"], "NO_PAIRS")
        self.assertEqual(mod.main([str(self.root), "--include-untracked",
                                   "--require-all-views"]), 2)

    def test_real_existing_ukrainian_cond_triple_is_one_mechanical_witness(self):
        stem = ROOT / "tests/fixtures/migration-d1-cond-cohort/branch"
        if not all(p.is_file() for p in (stem, stem.with_suffix(".lisp"),
                                          stem.with_suffix(".sens"))):
            self.fail("real Ukrainian COND triple is missing from checked-in corpus")
        physical = stem.with_suffix(".sens").read_bytes()
        words = mod.decode_bytes(physical)
        self.assertEqual(stem.read_bytes(), mod.expected_ascii_view(words))
        self.assertEqual(mod.encode_words(words), physical)
        self.assertTrue(stem.with_suffix(".lisp").read_text(encoding="utf-8").startswith("("))


if __name__ == "__main__":
    unittest.main()
