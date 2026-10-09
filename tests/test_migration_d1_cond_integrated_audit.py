#!/usr/bin/env python3
"""Physical T5 pair-audit + independent executable oracle handoff (#4455).

The repo-wide pair auditor intentionally does NOT declare a symbolic .lisp
source semantically migrated. Its PENDING_ORACLE result must be paired with
the dedicated D1/COND Python conversion and current Rust evaluator witness.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/migration-d1-cond-cohort"
sys.path.insert(0, str(ROOT / "scripts"))
from audit_t5_file_pairs import inspect
from sens_t5_codec import decode_bytes, typed_sha256


class ExecutableD1CondPairAudit(unittest.TestCase):
    def test_canonical_same_stem_binary_is_not_false_semantic_certification(self):
        record = inspect(FIXTURES, include_untracked=True, strict_semantic=False)
        self.assertEqual(record["schema"], "sens-t5-file-pair-audit/v1")
        self.assertEqual(record["status"], "MECHANICAL_ONLY")
        self.assertEqual(record["summary"]["sens_files"], 1)
        self.assertEqual(record["summary"]["physical_pass"], 1)
        self.assertEqual(record["summary"]["physical_blocked"], 0)
        self.assertEqual(record["summary"]["pending_oracle"], 1)
        self.assertIsNone(record["summary"]["admitted_executable_semantics"])
        [row] = record["files"]
        self.assertEqual(row["sens"], "branch.sens")
        self.assertEqual(row["source"], "branch.lisp")
        self.assertEqual(row["source_status"], "PENDING_ORACLE")
        self.assertEqual(row["physical_status"], "PASS")
        binary = (FIXTURES / "branch.sens").read_bytes()
        words = decode_bytes(binary)
        self.assertEqual(row["physical_bytes"], len(binary))
        self.assertEqual(row["physical_sha256"], hashlib.sha256(binary).hexdigest())
        self.assertEqual(row["typed_word_sha256"], typed_sha256(words))
        self.assertEqual(row["source_sha256"], hashlib.sha256(
            (FIXTURES / "branch.lisp").read_bytes()
        ).hexdigest())

    def test_strict_audit_rejects_implied_lisp_to_sens_semantics(self):
        record = inspect(FIXTURES, include_untracked=True, strict_semantic=True)
        self.assertEqual(record["status"], "BLOCKED")
        self.assertEqual(record["summary"]["physical_blocked"], 0)
        self.assertEqual(record["summary"]["pending_oracle"], 1)
        # Real source->physical three-pass / current Rust semantic execution
        # is asserted by tests/test_migration_d1_cond_cohort.py and
        # crates/sens/tests/migration_d1_cond_cohort.rs, never this audit alone.


if __name__ == "__main__":
    unittest.main()
