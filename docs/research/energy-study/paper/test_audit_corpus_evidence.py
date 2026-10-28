"""Synthetic positive/negative evidence mutations; never physical measurements."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from audit_corpus_evidence import InvalidRaw, audit, strict_json

SHA = "a" * 40
OUT = "42"
DIGEST = hashlib.sha256(OUT.encode()).hexdigest()


def fixture():
    pairs = []
    for p in range(8):
        for k in range(4):
            pairs.append({
                "process_id": f"p{p}", "session_id": f"session-{p // 2}",
                "session_started_utc": "2026-10-28T12:00:00Z" if p < 4 else "2026-10-29T12:00:00Z",
                "order": "AB" if k % 2 == 0 else "BA",
                "baseline_ns": 101_000, "candidate_ns": 102_000,
                "baseline_output": OUT, "candidate_output": OUT,
                "energy_not_measured": True,
            })
    return {"schema": "sens-energy-study-raw/v1", "tasks": {
        "T01-symbolic-recursion": {
            "schema": "sens-paired-physical/v1", "metric": "wall_time_ns",
            "provenance": {"git_sha": SHA},
            "parity": {"passed": True, "mode": "external_run",
                       "oracle_id": "parity_check.py --run command",
                       "input_sha256": "b" * 64,
                       "reference_output_sha256": DIGEST},
            "pairs": pairs,
        }
    }}


class EvidenceTests(unittest.TestCase):
    def check_block(self, mutation, code):
        document = fixture()
        mutation(document["tasks"]["T01-symbolic-recursion"])
        self.assertIn(code, audit(document, SHA)["tasks"]["T01-symbolic-recursion"]["blockers"])

    def test_metadata_complete_is_structure_only_not_a_win(self):
        result = audit(fixture(), SHA)
        self.assertEqual(result["status"], "STRUCTURE_ONLY")
        self.assertEqual(result["scientific_conclusion"], "NONE")
        self.assertEqual(result["physical_energy"], "NOT_VERIFIED")
        self.assertEqual(result["independent_reproduction"], "NOT_REPRODUCED")

    def test_actual_t01_style_missing_sha_blocks(self):
        self.check_block(lambda t: t["provenance"].update(git_sha="not-a-git-checkout"),
                         "SOURCE_SHA_UNPINNED_OR_MISMATCHED")

    def test_selftest_does_not_certify_measured_outputs(self):
        self.check_block(lambda t: t["parity"].update(oracle_id="parity_check.py --selftest"),
                         "PARITY_SELFTEST_IS_NOT_MEASURED_OUTPUT_PROOF")

    def test_missing_run_outputs_blocks(self):
        self.check_block(lambda t: t["pairs"][0].pop("candidate_output"), "MEASURED_OUTPUTS_MISSING")

    def test_wrong_output_is_rejected(self):
        self.check_block(lambda t: t["pairs"][0].update(candidate_output="41"),
                         "MEASURED_OUTPUT_PARITY_MISMATCH")

    def test_only_one_session_blocks(self):
        self.check_block(lambda t: [p.update(session_id="session-0") for p in t["pairs"]],
                         "INSUFFICIENT_INDEPENDENT_SESSION_EVIDENCE")

    def test_short_pair_count_blocks(self):
        self.check_block(lambda t: t["pairs"].__delitem__(slice(-4, None)),
                         "INSUFFICIENT_PROCESS_BLOCKS")

    def test_unbalanced_order_blocks(self):
        self.check_block(lambda t: t["pairs"][0].update(order="BA"),
                         "UNBALANCED_PROCESS_PAIRS")

    def test_zero_time_blocks(self):
        self.check_block(lambda t: t["pairs"][0].update(baseline_ns=0), "WALL_TIME_INVALID")

    def test_huge_wall_time_fails_closed(self):
        self.check_block(lambda t: t["pairs"][0].update(baseline_ns=10**400), "WALL_TIME_INVALID")

    def test_process_id_reused_between_sessions_blocks(self):
        self.check_block(lambda t: t["pairs"][0].update(session_id="session-1"),
                         "PROCESS_REUSED_ACROSS_SESSIONS")

    def test_energy_without_meter_blocks(self):
        self.check_block(lambda t: t["pairs"][0].update(energy_uj=123), "ENERGY_SCOPE_UNVERIFIED")

    def test_inadequate_metadata_and_input_blocks(self):
        self.check_block(lambda t: t["parity"].pop("input_sha256"), "MEASURED_INPUT_NOT_PINNED")

    def test_missing_session_timestamp_blocks(self):
        self.check_block(lambda t: t["pairs"][0].pop("session_started_utc"), "SESSION_TIMESTAMP_MISSING")

    def test_json_duplicate_fields_fail_closed(self):
        with self.assertRaisesRegex(InvalidRaw, "duplicate JSON"):
            strict_json('{"tasks":{"a":1,"a":2}}')

    def test_cli_must_return_failure_for_real_style_missing_proof(self):
        doc = fixture()
        task = doc["tasks"]["T01-symbolic-recursion"]
        task["provenance"]["git_sha"] = "not-a-git-checkout"
        task["parity"]["oracle_id"] = "parity_check.py --selftest"
        for p in task["pairs"]:
            p.pop("baseline_output")
            p.pop("candidate_output")
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / "raw.json"
            file.write_text(json.dumps(doc), encoding="utf-8")
            script = Path(__file__).with_name("audit_corpus_evidence.py")
            proc = subprocess.run([sys.executable, str(script), str(file), "--source-sha", SHA],
                                  capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 2, proc.stderr)
            report = json.loads(proc.stdout)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertIn("MEASURED_OUTPUTS_MISSING", report["tasks"]["T01-symbolic-recursion"]["blockers"])


if __name__ == "__main__":
    unittest.main()
