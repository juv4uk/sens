#!/usr/bin/env python3
"""Source-only Brzozowski 1964 donor gate: no D10 selected/coordinates/ratification."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
SOURCE="knowledge/d10-brzozowski-1964-ai-donor-v1.json"

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def verify(doc,inventory,foundation):
    assert doc["schema"]=="d10-brzozowski-1964-symbolic-ai-source/v1"
    assert doc["status"]=="HOLD-COMPLETENESS-ORACLE-AND-OWNER-CORE-REVIEW"
    assert doc["baseline"]["d10_blob"]=="3db40a04c1094c9ea13b0c8d6099ef1d882cf203"
    assert doc["baseline"]["selected"]==635
    assert doc["baseline"]["ratified"]==0
    assert doc["admission"]=={
        "selected_added":0,"coordinate_added":0,"ratified_added":0,
        "actor":"source-only lane, no SENS executable code"}
    assert inventory["accounting"]["selected_semantic_candidates"]==len(inventory["rows"])
    assert inventory["accounting"]["selected_semantic_candidates"]>=635
    assert inventory["accounting"]["ratified_d10_residents"]==0
    assert inventory["capacity"]==1024
    names={r["semantic_name"].upper() for r in inventory["rows"]}
    lowers={str(v).upper() for d in foundation["domains"].values()
            for v in d["residents"].values()}
    row=doc["semantic"]
    assert row["semantic_name"]=="REGULAR-LANGUAGE-DERIVATIVE"
    assert row["semantic_name"] not in names|lowers, "Already selected: re-review name collision"
    assert row["status"]=="HOLD-RESEARCH-NO-ADMISSION"
    assert row["source_path"]==SOURCE
    assert row["coordinate"] is None and row["ratified_resident"] is False
    assert row["physical_t5_authorized"] is False
    assert row["proposal_status"]=="pending-owner-review"
    assert row["surface_uk"] and row["surface_ukr"]
    assert row["relation_class"]=="FINITE-AUTOMATA-REGULAR-LANGUAGE-LEFT-QUOTIENT"
    assert row["behavior"] and row["non_equivalence_argument"]
    assert len(row["witnesses"])>=6 and len(row["falsifiers"])>=4
    assert len(row["equations"])>=4 and len(row["applications"])>=5
    assert row["equality"]=="EXTENSIONAL-LANGUAGE-EQUALITY-NOT-RAW-TREE-EQUALITY"
    primary=[p for p in doc["historical_sources"] if p["role"]=="HISTORICAL-PRIMARY-PUBLICATION"]
    assert len(primary)==1
    assert primary[0]["year"]==1964 and primary[0]["doi"]=="10.1145/321239.321249"
    assert doc["proof_plan"]["semantic_oracle_not_sens_runtime"] is True
    assert doc["proof_plan"]["real_reference_interpreter"]=="Chez Scheme R6RS"
    return len(inventory["rows"])

def check_mutations(doc,inv,foundation):
    changed=[
       lambda d: d["semantic"].__setitem__("coordinate","0000000000"),
       lambda d: d["semantic"].__setitem__("ratified_resident",True),
       lambda d: d["semantic"].__setitem__("physical_t5_authorized",True),
       lambda d: d["semantic"].__setitem__("status","SELECTED-RESEARCH-CANDIDATE"),
       lambda d: d["semantic"].__setitem__("semantic_name","UNIFY"),
       lambda d: d["semantic"].__setitem__("behavior",""),
       lambda d: d["semantic"].__setitem__("witnesses",[]),
       lambda d: d["historical_sources"][0].__setitem__("doi","unknown"),
       lambda d: d["admission"].__setitem__("selected_added",1),
       lambda d: d["proof_plan"].__setitem__("semantic_oracle_not_sens_runtime",False),
    ]
    for i,mutate in enumerate(changed):
        bad=copy.deepcopy(doc)
        mutate(bad)
        try: verify(bad,inv,foundation)
        except AssertionError: continue
        raise AssertionError(f"unsafe source mutation accepted {i}")
    print("D10 BRZOZOWSKI source 10 negative mutation controls PASS")

def main():
    d=load(SOURCE)
    i=load("knowledge/d10-v1-semantic-inventory.json")
    f=load("knowledge/d1-d9-foundation.json")
    n=verify(d,i,f)
    if "--self-test" in sys.argv: check_mutations(d,i,f)
    print(f"D10 BRZOZOWSKI source-only PASS; current selected={n}, new selected=0, ratified=0")

if __name__=="__main__":
    main()
