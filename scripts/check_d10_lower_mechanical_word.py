#!/usr/bin/env python3
"""D10 mechanical word: доказ джерела й HOLD, не дозвіл на вибір координати."""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
def read(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))

def verify(report, inv, foundation):
    assert report["schema"] == "d10-binary-mechanical-word-research/v1"
    assert report["status"] == "RESEARCH-OWNER-REVIEW-NOT-SELECTED"
    assert report["baseline"]["canonical_d10_selected"] == 630
    assert report["baseline"]["d10_ratified"] == 0
    assert report["baseline"]["canonical_d10_git_blob"] == "a55f307c27f17091795d75ebfcd7d051547d80bc"
    assert report["owner_claim"]["issue"] == "#4013"
    assert len(report["candidates"]) == 1
    c=report["candidates"][0]
    assert c["proposal_key"] == "D10M-001"
    assert c["semantic_name"] == "LOWER-MECHANICAL-WORD"
    assert c["status"] == "SOURCE-PROVED-OWNER-REVIEW"
    assert c["selected_in_canonical_d10"] is False
    assert c["coordinate"] is None and c["ratified"] is False
    assert c["physical_t5_authorized"] is False
    assert c["surface_uk"] and c["surface_ukr"] and c["law"]
    assert c["arity"] == 3 and len(c["witnesses"]) >= 7
    assert len(c["invariants"]) >= 4 and len(c["falsifiers"]) >= 3
    assert len(c["hold_related"]) >= 3 and c["independent_root_challenge"]
    assert report["admission"]["d10_count_delta"] == 0
    assert report["admission"]["coordinate_delta"] == 0
    assert report["admission"]["ratified_delta"] == 0
    assert inv["accounting"]["selected_semantic_candidates"] == len(inv["rows"])
    assert inv["accounting"]["selected_semantic_candidates"] >= 630
    assert inv["accounting"]["law_forced_coordinates"] == 256
    assert inv["accounting"]["ratified_d10_residents"] == 0
    assert inv["accounting"]["remaining_semantic_inventory"] == 1024-len(inv["rows"])
    high={x["semantic_name"].upper() for x in inv["rows"]}
    low={str(s).upper() for d in foundation["domains"].values() for s in d["residents"].values()}
    assert c["semantic_name"] not in (high|low), "exact name already selected; re-review dedup"
    official = [x for x in report["source"] if x["kind"] == "REFERENCE-CONTRACT"]
    assert len(official) == 1
    assert official[0]["url"] == "https://passagemath.org/docs/10.8/html/en/reference/combinat/sage/combinat/words/word_generators.html"
    for x in report["source"]:
        assert x["claim"]
        if "repository" in x:
            assert len(x["git_blob_sha"]) == 40
            assert x["repository"].startswith("juv4uk/")
    return {"research_candidates":1,"selected_added":0,"ratified_added":0,
            "live_selected":len(inv["rows"])}

def main():
    r=read("knowledge/d10-lower-mechanical-word-research-v1.json")
    i=read("knowledge/d10-v1-semantic-inventory.json")
    f=read("knowledge/d1-d9-foundation.json")
    print("D10 MECHANICAL SOURCE GATE PASS",verify(r,i,f))
    mutants=[
      ("coordinate","0000000000"),("ratified",True),("selected_in_canonical_d10",True),
      ("physical_t5_authorized",True),("semantic_name","MODULO"),("law",""),
      ("falsifiers",[]),("status","RATIFIED")
    ]
    if "--self-test" in sys.argv:
        for name,value in mutants:
            changed=copy.deepcopy(r)
            changed["candidates"][0][name]=value
            try: verify(changed,i,f)
            except AssertionError: continue
            raise AssertionError("unsafe mutant accepted: "+name)
        print("D10 MECHANICAL SOURCE negative controls PASS",len(mutants))

if __name__=="__main__":
    main()
