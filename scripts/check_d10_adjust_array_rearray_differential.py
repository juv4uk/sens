#!/usr/bin/env python3
"""Fail-closed provenance and neighbor gate for ADJUST-ARRAY differential review.

This is a source/metadata gate, not a claim that SBCL is the historical MacLisp
runtime or that ADJUST-ARRAY already deserves a separate D10 identity.
"""
from __future__ import annotations
import argparse
import copy
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "knowledge/d10-adjust-array-rearray-differential-v1.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"

class GateFailure(Exception):
    pass

def need(condition, message):
    if not condition:
        raise GateFailure(message)

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def verify(ledger, foundation, inventory, pin=True):
    need(ledger.get("schema") == "d10-adjust-array-rearray-differential/v1", "wrong schema")
    need(ledger.get("status") == "RESEARCH-HOLD-DIFFERENTIAL-REVIEW", "unexpected status")
    if pin:
        blob = subprocess.check_output(
            ["git", "hash-object", str(FOUNDATION)], cwd=ROOT, text=True
        ).strip()
        need(blob == ledger["snapshot"]["foundation_blob"], "ratified D1-D9 foundation changed; redo dedup")
    need(inventory["schema"] == "d10-v1-semantic-inventory/v1", "wrong D10 inventory schema")
    need(inventory["capacity"] == 1024, "D10 capacity mismatch")
    rows = {str(r["semantic_name"]).upper(): r for r in inventory["rows"]}
    need("ADJUST-ARRAY" not in rows, "ADJUST-ARRAY is already selected; refresh review instead of duplicating")
    for name in ("MAKE-ARRAY", "REARRAY"):
        need(name in rows, f"expected current D10 neighbor {name} is absent; redo review")
    lower = {
        str(name).upper()
        for domain in foundation["domains"].values()
        for name in domain.get("residents", {}).values()
    }
    need("COPY-ARRAY" in lower, "ratified D8 COPY-ARRAY neighbor not found")
    need("ADJUST-ARRAY" not in lower, "unexpected exact D1-D9 duplicate; redo behavior review")
    candidate = ledger["candidate"]
    need(candidate["semantic_name"] == "ADJUST-ARRAY", "candidate identity changed")
    need(candidate["status"] == "HOLD-DIFFERENTIAL-REVIEW", "candidate was promoted without owner review")
    need(candidate["selected_d10"] is False, "HOLD candidate cannot be selected")
    need(candidate["coordinate"] is None, "HOLD candidate cannot receive a coordinate")
    need(candidate["ratified"] is False, "HOLD candidate cannot be ratified")
    need(candidate["physical_t5_authorized"] is False, "research review cannot authorize physical T5")
    need(len(candidate["positive_laws"]) >= 4, "too few executable laws")
    need(len(candidate["falsifiers"]) >= 4, "too few falsifiers")
    sources = {s["kind"]: s for s in ledger["sources"]}
    need("primary-standard" in sources and "primary-historical" in sources, "primary sources missing")
    need("REARRAY" in ledger["neighbors"][1]["name"], "historical REARRAY attack missing")
    return {"status": ledger["status"], "candidate": candidate["semantic_name"],
            "selected_added": 0, "coordinates_added": 0, "ratified_added": 0,
            "current_selected_count": inventory["accounting"]["selected_semantic_candidates"]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    ledger, foundation, inventory = read(LEDGER), read(FOUNDATION), read(INVENTORY)
    result = verify(ledger, foundation, inventory)
    if args.self_test:
        bad = copy.deepcopy(ledger)
        bad["candidate"]["coordinate"] = "0000000000"
        try:
            verify(bad, foundation, inventory, pin=False)
        except GateFailure:
            pass
        else:
            raise SystemExit("negative self-test failed to reject coordinate")
        bad = copy.deepcopy(ledger)
        bad["candidate"]["selected_d10"] = True
        try:
            verify(bad, foundation, inventory, pin=False)
        except GateFailure:
            pass
        else:
            raise SystemExit("negative self-test failed to reject silent promotion")
    print("D10-ADJUST-ARRAY-DIFFERENTIAL: PASS", json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
