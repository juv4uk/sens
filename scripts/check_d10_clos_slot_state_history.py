#!/usr/bin/env python3
"""Fail-closed historical CLOS slot-state intake; never assigns bit coordinates."""
import copy
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "knowledge/d10-clos-slot-state-historical-review-v1.json"
F = ROOT / "knowledge/d1-d9-foundation.json"
I = ROOT / "knowledge/d10-v1-semantic-inventory.json"
ALLOWED = {"REVIEW-SEMANTIC-CANDIDATE", "HOLD-D2-EFFECT-HOOK", "HOLD-D2-ENVIRONMENT", "HOLD-DERIVED-PROJECTION"}
def verify(p,f,i):
    assert p["schema"] == "sens-d10-clos-slot-state-history-review/v1"
    assert p["status"] == "RESEARCH-UNRATIFIED-NOT-IN-SELECTED-INVENTORY"
    assert p["baseline"]["selected_d10"] == 625
    assert i["accounting"]["selected_semantic_candidates"] == len(i["rows"])
    assert len(i["rows"]) >= 625
    assert i["accounting"]["ratified_d10_residents"] == 0
    lower={str(v).upper() for d in f["domains"].values() for v in d["residents"].values()}
    selected={r["semantic_name"].upper() for r in i["rows"]}
    names=[r["historical_name"].upper() for r in p["rows"]]
    assert len(names) == len(set(names)) == 8
    assert not set(names).intersection(lower|selected), "Historical proposal collides with current admitted/selected domain"
    assert sum(r["triage"] == "REVIEW-SEMANTIC-CANDIDATE" for r in p["rows"]) == 4
    for r in p["rows"]:
        assert r["triage"] in ALLOWED
        assert r["coordinate"] is None
        assert r["selected_in_d10"] is False and r["ratified"] is False and r["physical_t5_authorized"] is False
        for field in ("surface_uk", "surface_ukr", "observable_law", "positive_witness", "falsifier", "conceptual_neighbors", "ownership_question"):
            assert isinstance(r.get(field),str) and r[field].strip(),field
        assert r["primary_url"].startswith("https://")
        assert r["owner_review"] == "PENDING"
    return {"status":"PASS","historical_rows":len(names),"d10_selected_live":len(i["rows"]),"ratified_added":0,"coordinates_added":0}
def selftest(p,f,i):
    verify(p,f,i)
    for modify in ({"coordinate":"0000000000"},{"selected_in_d10":True},{"ratified":True},{"physical_t5_authorized":True},{"falsifier":""},{"historical_name":"DEFCLASS"},{"triage":"RATIFIED"}):
        x=copy.deepcopy(p);x["rows"][0].update(modify)
        try:verify(x,f,i)
        except AssertionError:continue
        raise AssertionError("mutation not rejected: "+str(modify))
    x=copy.deepcopy(p);x["rows"][1]["historical_name"]=x["rows"][0]["historical_name"]
    try:verify(x,f,i)
    except AssertionError:pass
    else:raise AssertionError("duplicate not rejected")
    return 8
if __name__ == "__main__":
    p=json.loads(P.read_text());f=json.loads(F.read_text());i=json.loads(I.read_text())
    a=verify(p,f,i);print(json.dumps(a,sort_keys=True))
    if "--self-test" in sys.argv:print("negative_tests",selftest(p,f,i),"PASS")
