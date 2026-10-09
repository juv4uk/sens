#!/usr/bin/env python3
"""Fail-closed historical donor review; never promote a D10 resident."""
from __future__ import annotations
import argparse
import copy
import json
import subprocess
from pathlib import Path
from d10_historical_snapshot_compat import historic_view, pinned_inventory_git_blob

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "knowledge/d10-historical-primary-manual-reconciliation-20261009.json"
LOW = ROOT / "knowledge/d1-d9-foundation.json"
HIGH = ROOT / "knowledge/d10-v1-semantic-inventory.json"
OVERFLOW = ROOT / "knowledge/d9-overflow-review-v1.json"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def blob(path):
    if path == HIGH:
        return pinned_inventory_git_blob(path)
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()

def check(r, low, high, ov, pin=True):
    high = historic_view(high, r["snapshot"]["d10_git_blob"])
    assert r["status"] == "RESEARCH-ONLY-NO-RESIDENTS"
    assert r["accounting"]["auto_selected_d10"] == 0
    assert r["accounting"]["auto_ratified"] == 0
    assert r["accounting"]["auto_coordinates"] == 0
    assert high["accounting"]["ratified_d10_residents"] == r["snapshot"]["d10_ratified"] == 0
    assert high["accounting"]["selected_semantic_candidates"] == r["snapshot"]["d10_selected"]
    assert high["capacity"] == 1024
    if pin:
        assert blob(LOW) == r["snapshot"]["lower_git_blob"], "D1–D9 changed: rerun semantics"
        assert blob(HIGH) == r["snapshot"]["d10_git_blob"], "D10 changed: rerun dedup"
    lower = {str(s).upper(): domain + ":" + bits for domain, v in low["domains"].items() for bits,s in v["residents"].items()}
    sel = {x["semantic_name"].upper() for x in high["rows"]}
    historic = r["historical_ledger_2344"]
    assert historic["count"] == r["accounting"]["history_2344_rows"] == 19
    assert len(historic["rows"]) == 19
    for entry in historic["rows"]:
        assert entry["lower_current"] == lower.get(entry["historical_name"].upper())
    assert sum(x["lower_current"] is not None for x in historic["rows"]) == 17
    assert historic["already_lower_exact"] == 17
    assert any(x["name"] == "TRANSFORMER" and x["existing"] == "D8 TRANSFORMER/HART-MACRO" for x in historic["explicit_semantic_neighbor_exceptions"])
    remains = sorted(z["semantic_name"] for z in ov["rows"] if z["semantic_name"].upper() not in lower and z["semantic_name"].upper() not in sel)
    assert sorted(r["d9_overflow_leftover_exact_names"]) == remains
    assert len(remains) == r["accounting"]["history_d8_overflow_unrepresented"] == 6
    for name in r["already_selected_d10_do_not_readd"]:
        assert name in sel, f"no longer in D10: {name}"
    props = r["proposals"]
    assert len(props) == r["accounting"]["proposals"] == 13
    assert len({z["historical_name"] for z in props}) == 13
    assert sum(z["primary_name_attested"] is True for z in props) == r["accounting"]["primary_name_attested"] == 8
    assert sum(z["primary_name_attested"] is False for z in props) == r["accounting"]["unverified_historical_labels"] == 5
    for z in props:
        assert z["historical_name"].upper() not in lower
        assert z["historical_name"].upper() not in sel
        assert z["coordinate"] is None and z["selected_d10"] is False and z["ratified"] is False
        assert z["exact_in_lower"] is False and z["exact_in_d10_selected"] is False
        assert z["triage"].startswith(("HOLD-", "D10-PROPOSAL-REVIEW"))
        assert z["source_url"].startswith("https://")
        assert z["evidence_grade"] == ("PRIMARY-MANUAL-SPEC-READ" if z["primary_name_attested"] else "OLD-BRANCH-LEAD-NEEDS-PRIMARY-MANUAL")
        if not z["primary_name_attested"]:
            assert z["triage"].startswith("HOLD-"), "Unverified names may not be selected"
            assert "UNVERIFIED" in z["source_section"].upper() or "Unverified" in z["source_section"]
        assert z["source_section"] and z["observable_claim"] and z["positive_witness_spec"] and z["falsifier_spec"]
        assert z["nearby_existing"] and z["proposed_owner"]
        if z["triage"].startswith("HOLD-D2"):
            assert z["proposed_owner"] == "D2-EXCLUSIVE-CONTROL"
    return True

def test(r,lo,hi,ov):
    check(r,lo,hi,ov,True)
    def rejected(mut):
        x=copy.deepcopy(r)
        mut(x)
        try: check(x,lo,hi,ov,False)
        except AssertionError: return
        raise AssertionError("INVALID case passed the guard")
    rejected(lambda x: x["proposals"][0].__setitem__("coordinate","0000000000"))
    rejected(lambda x: x["proposals"][0].__setitem__("ratified",True))
    rejected(lambda x: x["proposals"][0].__setitem__("selected_d10",True))
    rejected(lambda x: x["proposals"][0].__setitem__("historical_name","CAR"))
    rejected(lambda x: x["proposals"][0].__setitem__("historical_name","REARRAY"))
    rejected(lambda x: x["proposals"][0].__setitem__("positive_witness_spec",""))
    rejected(lambda x: x["proposals"][0].__setitem__("falsifier_spec",""))
    rejected(lambda x: x["proposals"][0].__setitem__("triage","ADMITTED"))
    rejected(lambda x: x["d9_overflow_leftover_exact_names"].pop())
    rejected(lambda x: x["historical_ledger_2344"]["rows"][0].__setitem__("lower_current","D10:0000000000"))
    rejected(lambda x: x["proposals"][-1].__setitem__("triage","D10-PROPOSAL-REVIEW"))
    rejected(lambda x: x["proposals"][-1].__setitem__("primary_name_attested",True))
    print("PASS: 13 historical HOLD/proposal rows, 19 legacy crosschecks, six overflow holds, 12 adverse cases")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    r,lo,hi,ov=(read(p) for p in (P,LOW,HIGH,OVERFLOW))
    if args.self_test: test(r,lo,hi,ov)
    else:
        check(r,lo,hi,ov)
        print("PASS: historical donor reconciliation")
if __name__ == "__main__":
    main()
