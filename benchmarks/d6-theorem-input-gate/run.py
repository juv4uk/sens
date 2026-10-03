#!/usr/bin/env python3
"""Neutral D6 theorem-input stability gate for #2711.

This script does not search D6 coordinates and does not implement the
independent attacks owned by #2702.  It treats the merged theorem-first
witnesses as black boxes and checks only that the current input surface still
matches the frozen manifest.

If a semantic premise changes, the correct result is REOPEN, not a guessed
placement.
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("manifest.json")


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def run_witness(relative_path: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(ROOT / relative_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def current_snapshot(manifest: dict) -> dict:
    witnesses = []
    for item in manifest["witnesses"]:
        code, output = run_witness(item["path"])
        witnesses.append(
            {
                "path": item["path"],
                "exit_code": code,
                "expected_result_seen": item["expected_result"] in output,
                "output": output,
            }
        )

    placement_path = ROOT / manifest["placement"]["path"]
    placement = json.loads(placement_path.read_text(encoding="utf-8"))
    candidates = [
        {
            "operation": row["operation"],
            "coordinate": row["candidate_coordinate"],
        }
        for row in placement["rows"]
        if row.get("candidate_coordinate")
    ]
    setq = next(row for row in placement["rows"] if row["operation"] == manifest["placement"]["setq_operation"])

    return {
        "witnesses": witnesses,
        "candidate_coordinates": candidates,
        "setq_state": {
            "placement_kind": setq["placement_kind"],
            "exact_domain": setq["exact_domain"],
            "coordinate": setq["coordinate"],
            "candidate_coordinate": setq.get("candidate_coordinate"),
        },
    }


def evaluate(snapshot: dict, manifest: dict) -> list[str]:
    reasons: list[str] = []

    expected_by_path = {
        row["path"]: row["expected_result"]
        for row in manifest["witnesses"]
    }
    for row in snapshot["witnesses"]:
        if row["exit_code"] != 0:
            reasons.append(f"witness-failed:{row['path']}")
        if not row["expected_result_seen"]:
            reasons.append(f"witness-result-changed:{row['path']}")
        if row["path"] not in expected_by_path:
            reasons.append(f"unexpected-witness:{row['path']}")

    allowed_states = manifest["placement"]["allowed_states"]
    matching_states = [
        state["state"]
        for state in allowed_states
        if all(snapshot["setq_state"].get(key) == value for key, value in state.items() if key != "state")
    ]
    if len(matching_states) != 1:
        reasons.append("setq-owner-transition-outside-allowed-states")

    expected_candidates = (
        [{"operation": "SETQ", "coordinate": "D6:001111 (OD-001 owner-ready only)"}]
        if matching_states == ["PRE-OWNER-READY"]
        else []
    )
    if snapshot["candidate_coordinates"] != expected_candidates:
        reasons.append("historical-placement-candidate-set-changed")

    return reasons


def self_test(snapshot: dict, manifest: dict) -> None:
    assert evaluate(snapshot, manifest) == [], "current snapshot must be stable"

    changed = copy.deepcopy(snapshot)
    changed["candidate_coordinates"].append(
        {"operation": "SYNTHETIC", "coordinate": "D6:111111"}
    )
    reasons = evaluate(changed, manifest)
    assert "historical-placement-candidate-set-changed" in reasons

    changed = copy.deepcopy(snapshot)
    changed["setq_state"]["coordinate"] = "001110"
    changed["setq_state"]["candidate_coordinate"] = None
    reasons = evaluate(changed, manifest)
    assert "setq-owner-transition-outside-allowed-states" in reasons

    changed = copy.deepcopy(snapshot)
    changed["witnesses"][0]["expected_result_seen"] = False
    reasons = evaluate(changed, manifest)
    assert any(reason.startswith("witness-result-changed:") for reason in reasons)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest()
    snapshot = current_snapshot(manifest)
    reasons = evaluate(snapshot, manifest)

    if args.self_test:
        self_test(snapshot, manifest)
        print("D6-THEOREM-INPUT-SELF-TEST=PASS")

    if reasons:
        print("D6-ANALYSIS-REOPEN-REQUIRED")
        for reason in reasons:
            print(f"reason={reason}")
        return 1

    print("D6-INPUTS-STABLE")
    print("d5-child-witness=#2704")
    print("d4-product-witness=#2708")
    print(f"historical-candidate-count={len(snapshot['candidate_coordinates'])}")
    print("owner-isolated-coordinate=SETQ:D6:001111")
    print("owner-transition=PRE-OWNER-READY|POST-OWNER-RATIFIED")
    print("independent-falsifier=#2702")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
