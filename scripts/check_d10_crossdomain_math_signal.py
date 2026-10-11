#!/usr/bin/env python3
"""Research-only D10 math intake: never admit raw hobby ideas as core opcodes."""
import copy
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
def get(p):
    return json.loads((R/p).read_text(encoding="utf-8"))
def check(doc, inv, foundation):
    assert doc["schema"] == "sens-d10-crossdomain-math-source-intake/v1"
    assert doc["status"] == "RESEARCH-HOLD-CORE-VS-LIBRARY-OWNER-REVIEW"
    assert len(doc["candidates"]) == 2
    assert inv["accounting"]["selected_semantic_candidates"] == len(inv["rows"])
    assert inv["accounting"]["selected_semantic_candidates"] >= 630
    assert inv["accounting"]["ratified_d10_residents"] == 0
    assert doc["admission"] == {"selected_added":0,"coordinates_added":0,"ratified_added":0,"oracle_source":"tests/test_d10_crossdomain_math_laws.py","owner_gate":"#4013, #4463; exclusive canonical selection writer required; derivability and donor admissibility remain OPEN"}
    low = {str(v).upper() for d in foundation["domains"].values() for v in d["residents"].values()}
    high = {x["semantic_name"].upper(): x for x in inv["rows"]}
    proof = get("knowledge/d10-existing-math-signal-selected-20261011.json") if (
        {"FINITE-CONVOLUTION", "PHASE-UNWRAP"} & set(high)) else None
    assert {x["semantic_name"] for x in doc["candidates"]} == {"FINITE-CONVOLUTION","PHASE-UNWRAP"}
    if proof is not None:
        assert proof["status"] == "SELECTED-RESEARCH-BATCH-NO-RATIFICATION"
        assert proof["source_d10_preselection"].endswith("@7d8745cb6f183cf0c015812359a6c0f87c4c2ffb")
        assert "be9a340b28123d81b4203ccfbe3d1b20e707bbae" in {
            p["blob"] for p in proof["premises"]}
    for x in doc["candidates"]:
        assert x["semantic_name"] not in low
        live = high.get(x["semantic_name"])
        if live is not None:
            # A source-era HOLD stays immutable; only an independently appended
            # source-pinned selection may change the *current* canonical inventory.
            assert proof is not None
            witness = [p for p in proof["selected"] if p["semantic_name"] == x["semantic_name"]]
            assert len(witness) == 1 and witness[0]["law"] == x["law"]
            assert live["stable_id"] == witness[0]["stable_id"]
            assert live["behavior"] == witness[0]["law"]
            assert live["status"] == "SELECTED-RESEARCH-CANDIDATE"
            assert live.get("coordinate") is None and live.get("ratified_resident") is False
            assert "knowledge/d10-existing-math-signal-selected-20261011.json" in live["provenance"]
        assert x["role"] == "RESEARCH-UNSELECTED"
        assert x["selection"] is False and x["coordinate"] is None and x["ratified"] is False
        assert x["physical_t5_authorized"] is False
        assert x["proposed_owner"] == "CORE-MATH-LIBRARY-REVIEW"
        assert x["law"] and x["core_question"] and len(x["witnesses"]) >= 3
        assert len(x["falsifiers"]) >= 2 and x["reference"].startswith("https://numpy.org/")
    donors=doc["owned_repo_donors"]
    assert len(donors) == 4
    assert {r["repo"] for r in donors} == {"juv4uk/spanda","juv4uk/radio-log","juv4uk/my-lisp-panini"}
    for r in donors:
        assert len(r["blob"]) == 40 and all(c in "0123456789abcdef" for c in r["blob"])
        assert r["url"].startswith("https://github.com/"+r["repo"]+"/blob/")
        assert r["file"] and r["relevance"] and r["disposition"]
    assert len(doc["rejected_as_core"]) >= 7
    return True

def main():
    d,i,f = map(get, ["knowledge/d10-crossdomain-math-signal-research-v1.json","knowledge/d10-v1-semantic-inventory.json","knowledge/d1-d9-foundation.json"])
    check(d,i,f)
    for key,value in [("selection",True),("coordinate","0000000000"),("ratified",True),("law",""),("semantic_name","GCD")]:
        b=copy.deepcopy(d)
        b["candidates"][0][key]=value
        try: check(b,i,f)
        except AssertionError: continue
        raise AssertionError("negative control accepted: "+key)
    print("D10 CROSSDOMAIN MATH SOURCE PASS: 2 historical HOLD donors, current selections separately source-pinned, 5 negative controls")

if __name__ == "__main__":
    main()
