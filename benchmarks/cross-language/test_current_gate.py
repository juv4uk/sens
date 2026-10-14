#!/usr/bin/env python3
"""Fail-closed guard for the historical cross-language benchmark lane."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "benchmarks" / "cross-language" / "bench.json"


class CurrentCrossLanguageGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_current_canonical_replay_is_explicitly_blocked(self) -> None:
        self.assertEqual(
            self.data["status"],
            "BLOCKED-CURRENT-CANONICAL-REPLAY-NOT-IMPLEMENTED",
        )
        command = self.data["reproduce"]
        self.assertIn("SENS_BENCHMARK_STATUS=BLOCKED", command)
        self.assertIn("exit 2", command)

    def test_historical_fasl_is_provenance_not_current_performance_evidence(self) -> None:
        claim = self.data["claim"]
        self.assertIn("Historical Function8/FASL results remain provenance only", claim)
        self.assertIn("independent correctness oracle", claim)
        self.assertIn("semantic parity", claim)
        command = self.data["reproduce"]
        self.assertNotIn("--historical-function8-fasl", command)
        self.assertNotIn("guix time-machine", command)

    def test_required_gate_has_a_manifest_witness(self) -> None:
        self.assertIn("test_current_gate.py", self.data["witness"])

    def test_current_status_doc_is_witnessed(self) -> None:
        self.assertIn("CURRENT-STATUS-2026-10-14.uk.md", self.data["witness"])
        status_doc = (
            ROOT / "benchmarks" / "cross-language" / "CURRENT-STATUS-2026-10-14.uk.md"
        )
        self.assertTrue(status_doc.is_file(), "status map missing")
        body = status_doc.read_text(encoding="utf-8")
        self.assertIn("BLOCKED", body)
        self.assertIn("Zig", body)
        self.assertIn("CPython", body)
        self.assertIn("переносяться", body)

    def test_claim_separates_transport_from_language_ranking(self) -> None:
        claim = self.data["claim"]
        self.assertIn("must not be relabeled", claim)
        self.assertTrue(
            "Zig" in claim and "transport" in claim.lower(),
            "claim must mention Zig transport vs language ranking",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
