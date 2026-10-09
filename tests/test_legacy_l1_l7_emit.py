#!/usr/bin/env python3
"""Fail-closed actual T5 staging/digest tests using canonical migration pipeline."""
from __future__ import annotations

from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
E = runpy.run_path(str(ROOT / "scripts/legacy-l1-l7-emit.py"),
                   run_name="l1_l7_emit_tests")
emit = E["emit"]


class ExactDomainEmission(unittest.TestCase):
    def test_l2_fallback_produces_staging_digest_without_publishing(self):
        result = emit("(110 (t 1))")
        self.assertEqual(result["status"], "HOLD_ORACLE", result)
        self.assertEqual(result["exact_domain"], "STAGED_IN_MEMORY")
        self.assertEqual(len(result["physical_sha256"]), 64)
        self.assertGreater(result["physical_bytes"], 0)
        self.assertEqual(result["independent_semantic_oracle"], "NOT_RUN")

    def test_digest_mismatch_blocks_release(self):
        result = emit("(110 (t 1))", "0" * 64)
        self.assertEqual(result["status"], "BLOCK", result)
        self.assertEqual(result["digest_verdict"], "MISMATCH")

    def test_digest_match_does_not_claim_semantic_proof(self):
        first = emit("(110 (t 1))")
        self.assertEqual(first["status"], "HOLD_ORACLE", first)
        result = emit("(110 (t 1))", first["physical_sha256"])
        self.assertEqual(result["status"], "DIGEST_MATCH_ONLY", result)
        self.assertEqual(result["independent_semantic_oracle"], "NOT_RUN")

    def test_l7_bad_source_does_not_emit(self):
        result = emit("(110 (t 1)")
        self.assertEqual(result["status"], "BLOCK")
        self.assertNotIn("physical_sha256", result)

    def test_unknown_d1_producer_never_emits(self):
        result = emit("(110 ((unproved x) 1))")
        self.assertEqual(result["status"], "BLOCK")
        self.assertNotIn("physical_sha256", result)


if __name__ == "__main__":
    unittest.main()
