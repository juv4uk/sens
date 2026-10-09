#!/usr/bin/env python3
"""CLOS history research-only gate: proposals never mint D10 residents."""
from __future__ import annotations
import copy
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
A = "knowledge/d10-clos-instance-lifecycle-residual-v1.json"
I = "knowledge/d10-v1-semantic-inventory.json"
F = "knowledge/d1-d9-foundation.json"
def demand(ok, msg):
    if not ok: raise ValueError(msg)

def check(a, inv, foundation):
    rows = a["rows"]
    demand(len(rows) == 8 and a["status"] == "RESEARCH-NOT-SELECTED-NOT-RATIFIED", "review status/row count")
    demand(len(inv["rows"]) == inv["accounting"]["selected_semantic_candidates"], "inventory invariant")
    demand(inv["accounting"]["ratified_d10_residents"] == 0, "ratification unexpected")
    lower = {str(n).upper() for d in foundation["domains"].values() for n in d["residents"].values()}
    existing = {r["semantic_name"].upper() for r in inv["rows"]}
    names = [r["historical_name"].upper() for r in rows]
    demand(len(set(names)) == 8, "duplicate historical name")
    demand(not set(names).intersection(lower | existing), "already assigned current D1-D10 name")
    for r in rows:
        demand(r["source_url"].startswith("https://") and r["source_type"], "missing primary-source URL")
        demand(bool(r["observable_law"]) and bool(r["positive_witness"]) and bool(r["falsifier"]), "missing falsifiable law")
        demand(r["surface_uk"] and r["surface_ukr"], "Ukrainian surface required")
        demand(r["triage_status"].startswith(("HOLD-", "REVIEW-")), "invalid triage")
        demand(r["coordinate"] is None and r["selected_in_d10"] is False and r["ratified"] is False and r["physical_t5_authorized"] is False, "false admission")
    demand(sum(r["triage_status"].startswith("REVIEW-") for r in rows)==2, "review count drift")
    return {"proposed":8,"review":2,"hold":6,"selected_added":0,"ratified":0}

def self_test(a, inv, foundation):
    check(a,inv,foundation)
    for field,value in [("coordinate","0000000000"),("selected_in_d10",True),("ratified",True),("physical_t5_authorized",True),("falsifier",""),("historical_name","CAR"),("triage_status","RATIFIED")]:
        z=copy.deepcopy(a);z["rows"][0][field]=value
        try:check(z,inv,foundation)
        except ValueError:continue
        raise ValueError("mutation accepted: "+field)
    print("SELF-TEST PASS 7 mutation guards")

def main():
    a=json.loads((R/A).read_text(encoding="utf-8"))
    i=json.loads((R/I).read_text(encoding="utf-8"))
    f=json.loads((R/F).read_text(encoding="utf-8"))
    print("D10-CLOS-LIFECYCLE PASS",json.dumps(check(a,i,f),sort_keys=True))
    self_test(a,i,f)
if __name__=="__main__":main()
