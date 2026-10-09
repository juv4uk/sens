#!/usr/bin/env python3
"""Research-only one-sided subsumption provenance gate, never a D10 admission."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
DOSSIER=ROOT/"knowledge/d10-symbolic-ai-one-sided-subsumption-v1.json"
INVENTORY=ROOT/"knowledge/d10-v1-semantic-inventory.json"
FOUNDATION=ROOT/"knowledge/d1-d9-foundation.json"

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def check(d,i,f):
    assert d["schema"]=="sens-d10-symbolic-one-sided-subsumption/v1"
    assert d["status"]=="RESEARCH-HOLD-OWNER-REVIEW-NO-ADMISSION"
    assert d["baseline"]["selected_at_claim"]==634
    assert d["baseline"]["inventory_blob"]=="65014431ac3e64633cd0be3630cfafc5e7a9aea3"
    assert d["baseline"]["ratified_d10"]==0
    assert d["source"]["primary"]=="https://www.swi-prolog.org/pldoc/man?predicate=subsumes_term%2F2"
    assert d["source"]["independent_oracle"]=="tests/d10_finite_subsumes_swi.pl"
    assert len(d["rows"])==1
    x=d["rows"][0]
    assert x["id"]=="D10AI-0002"
    assert x["semantic_name"]=="FINITE-TERM-SUBSUMES"
    assert x["role"]=="RESEARCH-HOLD"
    assert x["kind"]=="PURE-ONE-SIDED-TERM-INSTANCE-CHECK"
    assert x["selected"] is False
    assert x["coordinate"] is None
    assert x["ratified"] is False
    assert x["physical_t5_authorized"] is False
    assert x["surface_uk"] and x["surface_ukr"] and x["contract"]
    assert len(x["witnesses"])>=9 and len(x["falsifiers"])>=6
    assert x["core_question"] and x["source_url"]==d["source"]["primary"]
    assert len(d["anti_duplication"])>=4
    assert all(y["state"]!="SELECTED" for y in d["anti_duplication"])
    assert d["admission"]["selected_added"]==0
    assert d["admission"]["coordinate_added"]==0
    assert d["admission"]["ratified_added"]==0
    assert d["admission"]["physical_authority"] is False
    assert d["admission"]["source_only"] is True
    assert i["accounting"]["selected_semantic_candidates"]==len(i["rows"])>=634
    assert i["accounting"]["ratified_d10_residents"]==0
    assert i["accounting"]["remaining_semantic_inventory"]==1024-len(i["rows"])
    others={r["semantic_name"].upper() for r in i["rows"]}
    lower={str(v).upper() for dom in f["domains"].values() for v in dom["residents"].values()}
    assert x["semantic_name"] not in others|lower, "pre-existing selected root: stop and reconcile"
    assert "UNIFY" in lower
    assert (ROOT/"tests/d10_finite_subsumes_swi.pl").read_text(encoding="utf-8").startswith(":- initialization(main, main).")
    assert (ROOT/"tests/test_d10_finite_subsumes.py").read_text(encoding="utf-8").startswith("#!/usr/bin/env python3")
    return {"current_selected":len(i["rows"]),"new_selected":0,"ratified":0,"research_laws":1}

def adversarial(d,i,f):
    bad=[
      ("selected",lambda a:a["rows"][0].__setitem__("selected",True)),
      ("coordinate",lambda a:a["rows"][0].__setitem__("coordinate","0000000000")),
      ("ratified",lambda a:a["rows"][0].__setitem__("ratified",True)),
      ("T5",lambda a:a["rows"][0].__setitem__("physical_t5_authorized",True)),
      ("pretend UNIFY",lambda a:a["rows"][0].__setitem__("semantic_name","UNIFY")),
      ("no witnesses",lambda a:a["rows"][0].__setitem__("witnesses",[])),
      ("no falsifiers",lambda a:a["rows"][0].__setitem__("falsifiers",[])),
      ("no contract",lambda a:a["rows"][0].__setitem__("contract","")),
      ("fake source",lambda a:a["source"].__setitem__("primary","https://example.com")),
      ("premature selection",lambda a:a["admission"].__setitem__("selected_added",1))
    ]
    for label,fn in bad:
        clone=copy.deepcopy(d)
        fn(clone)
        try:check(clone,i,f)
        except AssertionError:continue
        raise AssertionError("unsafe mutation accepted: "+label)
    print("D10 AI SUBSUMPTION guard PASS 10 negative controls")

def main():
    d,i,f=map(load,(DOSSIER,INVENTORY,FOUNDATION))
    print("D10 AI SUBSUMPTION HOLD gate PASS",check(d,i,f))
    if "--self-test" in sys.argv:adversarial(d,i,f)
if __name__=="__main__":main()
