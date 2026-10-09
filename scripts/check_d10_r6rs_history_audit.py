#!/usr/bin/env python3
"""Fail-closed R6RS historical comparison. No D10 semantic admission."""
import argparse
import copy
import json
import subprocess
from pathlib import Path
from check_d10_historical_admission_batch1 import check_growth

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "knowledge/d10-r6rs-hashtable-hygiene-audit-v1.json"
LOW = ROOT / "knowledge/d1-d9-foundation.json"
HIGH = ROOT / "knowledge/d10-v1-semantic-inventory.json"

def blob(path):
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()

def check(payload, low, high, verify_pin=True):
    assert payload["status"] == "RESEARCH-ONLY-UNSELECTED-UNRATIFIED"
    assert payload["snapshot"]["ratified_d10"] == 0
    assert high["accounting"]["selected_semantic_candidates"] >= payload["snapshot"]["d10_selected"]
    check_growth(high)
    assert payload["snapshot"]["d10_capacity"] == high["capacity"] == 1024
    assert high["accounting"]["ratified_d10_residents"] == 0
    if verify_pin:
        assert blob(LOW) == payload["snapshot"]["foundation_blob"], "D1-D9 foundation changed: redo review"
        assert payload["snapshot"]["d10_inventory_blob"] == "73dd518469f972c55411e004b70b054ba8b3ec86", "historical inventory pin changed"
    lower = {str(n).upper() for d in low["domains"].values() for n in d["residents"].values()}
    high_names = {r["semantic_name"].upper() for r in high["rows"]}
    rows = payload["rows"]
    assert len(rows) == payload["accounting"]["historical_spellings_reviewed"] == 19
    assert payload["accounting"]["admitted_d10"] == payload["accounting"]["new_coordinates"] == 0
    names = [r["historical_spelling"] for r in rows]
    assert len(set(names)) == len(names), "duplicate name in research rows"
    assert len([r for r in rows if r["section"].startswith("13.")]) == 13
    assert len([r for r in rows if r["section"].startswith("12.")]) == 6
    for row in rows:
        name = row["historical_spelling"]
        assert name not in lower, f"already in D1-D9: {name}"
        if name in high_names:
            assert name == "HASHTABLE-ENTRIES", f"unreviewed R6RS promotion {name}"
            selected = next(r for r in high["rows"] if r["semantic_name"] == name)
            assert selected["source_class"] == "HISTORICAL-PRIMARY-TRANCHE2-20261009"
            assert selected["primary_source_url"] == row["primary_url"]
            assert selected["coordinate"] is None and selected["ratified_resident"] is False
            assert selected["status"] == "SELECTED-RESEARCH-CANDIDATE"
        assert row["exact_in_D1_D9"] is False
        assert row["exact_in_current_D10_selected"] is False
        assert row["overlaps_other_open_historical_audits"] is False
        assert row["status"] == "HOLD-RESEARCH-NO-ADMISSION"
        assert row["coordinate"] is None and row["ratified"] is False
        assert row["positive_witness_spec"] and row["falsifier_spec"]
        assert row["observable_law"] and row["closest_existing_semantics"]
        assert row["source"] == "R6RS Standard Libraries (2007)"
        if row["section"].startswith("12."):
            assert row["primary_url"].endswith("r6rs-lib-Z-H-13.html")
            assert row["owner_boundary"] == "D2-CONTROL-OWNER-REVIEW"
        else:
            assert row["primary_url"].endswith("r6rs-lib-Z-H-14.html")
            assert row["owner_boundary"] == "D10-CANDIDATE-OWNERSHIP-REVIEW"
    return True

def self_test(report, low, high):
    check(report, low, high)
    def rejected(mutate):
        candidate = copy.deepcopy(report)
        mutate(candidate)
        try:
            check(candidate, low, high, verify_pin=False)
        except AssertionError:
            return
        raise AssertionError("self-test failed to reject invalid research")
    rejected(lambda j: j["rows"][0].__setitem__("coordinate", "0000000000"))
    rejected(lambda j: j["rows"][0].__setitem__("ratified", True))
    rejected(lambda j: j["rows"][0].__setitem__("status", "ADMITTED"))
    rejected(lambda j: j["rows"][1].__setitem__("historical_spelling", j["rows"][0]["historical_spelling"]))
    rejected(lambda j: j["rows"][0].__setitem__("historical_spelling", "CAR"))
    rejected(lambda j: j["rows"][0].__setitem__("falsifier_spec", ""))
    rejected(lambda j: j["rows"][13].__setitem__("owner_boundary", "D10-CANDIDATE-OWNERSHIP-REVIEW"))
    print("PASS: R6RS 19 historical HOLD rows and 7 adversarial negative cases")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report, low, high = [json.loads(p.read_text(encoding="utf-8")) for p in (REPORT, LOW, HIGH)]
    if args.self_test:
        self_test(report, low, high)
    else:
        check(report, low, high)
        print("PASS: R6RS historical HOLD audit")

if __name__ == "__main__":
    main()
