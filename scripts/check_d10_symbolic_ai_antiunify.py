#!/usr/bin/env python3
"""Fail closed on unreviewed D10 symbolic-AI donor promotion; no admission here."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"knowledge/d10-symbolic-ai-antiunify-research-v1.json"
D10=ROOT/"knowledge/d10-v1-semantic-inventory.json"
LOWER=ROOT/"knowledge/d1-d9-foundation.json"

def read(p): return json.loads(p.read_text(encoding="utf-8"))

def validate(report,inventory,lower):
    assert report["schema"]=="sens-d10-symbolic-ai-antiunification/v1"
    assert report["status"]=="RESEARCH-OWNER-REVIEW-NOT-SELECTED"
    assert report["baseline"]["main_inventory_git_blob"]=="65014431ac3e64633cd0be3630cfafc5e7a9aea3"
    assert report["baseline"]["main_selected_at_claim"]==634
    assert report["baseline"]["foundation_git_blob"]=="09d1d71c39d1484dfd005a5068dbb18b76f0f0d4"
    assert report["baseline"]["ratified_d10"]==0
    assert report["donor"]["url"]=="https://www.swi-prolog.org/pldoc/man?section=terms"
    assert report["donor"]["implementation_executable"]=="tests/d10_antiunify_swi.pl"
    assert report["donor"]["counterpart"]=="tests/test_d10_antiunify_finite.py"
    assert len(report["rows"])==1
    law=report["rows"][0]
    assert law["proposal_key"]=="D10AI-0001"
    assert law["semantic_name"]=="FINITE-TERM-ANTI-UNIFY"
    assert law["kind"]=="PURE-FINITE-FIRST-ORDER-SYMBOLIC-LAW"
    assert law["selected_in_d10"] is False
    assert law["coordinate"] is None
    assert law["ratified_resident"] is False
    assert law["physical_t5_authorized"] is False
    assert law["surface_uk"] and law["surface_ukr"] and law["law"]
    assert len(law["witnesses"])>=6
    assert len(law["falsifiers"])>=5
    assert len(law["neighbors"])>=4 and "UNIFY" in " ".join(law["neighbors"])
    assert law["owner_question"] and law["dedup"]
    assert len(report["related_holds"])>=4
    assert all(z["status"]!="SELECTED" for z in report["related_holds"])
    assert report["admission"]["selected_added"]==0
    assert report["admission"]["coordinates_added"]==0
    assert report["admission"]["ratified_added"]==0
    assert report["admission"]["canonical_inventory_changed"] is False
    assert report["admission"]["python_model_is_sens_runtime"] is False
    assert len(inventory["rows"])==inventory["accounting"]["selected_semantic_candidates"]
    assert len(inventory["rows"])>=634
    assert inventory["accounting"]["ratified_d10_residents"]==0
    assert inventory["accounting"]["remaining_semantic_inventory"]==1024-len(inventory["rows"])
    names={row["semantic_name"].upper() for row in inventory["rows"]}
    lows={str(x).upper() for d in lower["domains"].values() for x in d["residents"].values()}
    assert law["semantic_name"] not in names|lows,"already selected elsewhere: re-review"
    assert "UNIFY" in lows
    assert (ROOT/"tests/d10_antiunify_swi.pl").read_text(encoding="utf-8").startswith(":- use_module(library(terms)).")
    assert (ROOT/"tests/test_d10_antiunify_finite.py").read_text(encoding="utf-8").startswith("#!/usr/bin/env python3")
    return {"current_selected":len(inventory["rows"]),"root_research_laws":1,"newly_selected":0,"ratified":0}

def adversarial(report,inventory,lower):
    mutants=[
      ("forged selection",lambda r:r["rows"][0].__setitem__("selected_in_d10",True)),
      ("forged coordinate",lambda r:r["rows"][0].__setitem__("coordinate","0000000000")),
      ("forged ratification",lambda r:r["rows"][0].__setitem__("ratified_resident",True)),
      ("physical binary authority",lambda r:r["rows"][0].__setitem__("physical_t5_authorized",True)),
      ("name becomes lower-domain UNIFY",lambda r:r["rows"][0].__setitem__("semantic_name","UNIFY")),
      ("erase law",lambda r:r["rows"][0].__setitem__("law","")),
      ("erase counterexamples",lambda r:r["rows"][0].__setitem__("falsifiers",[])),
      ("false SWI source",lambda r:r["donor"].__setitem__("url","https://example.com")),
      ("admit without gate",lambda r:r["admission"].__setitem__("selected_added",1)),
      ("inconsistent ratification baseline",lambda r:r["baseline"].__setitem__("ratified_d10",1))
    ]
    for label,mutate in mutants:
        r=copy.deepcopy(report)
        mutate(r)
        try:validate(r,inventory,lower)
        except AssertionError:continue
        raise AssertionError("accepted adversarial mutation: "+label)
    print("D10 SYMBOLIC-AI source gate 10 adversarial mutations PASS")

def main():
    report,inv,lower=map(read,(REPORT,D10,LOWER))
    print("D10 SYMBOLIC-AI source gate PASS",validate(report,inv,lower))
    if "--self-test" in sys.argv:adversarial(report,inv,lower)
if __name__=="__main__":main()
