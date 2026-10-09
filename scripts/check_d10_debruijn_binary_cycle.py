#!/usr/bin/env python3
"""Fail-closed D10 research-only donor gate. Does NOT select or ratify a resident."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DONOR=ROOT/"knowledge/d10-debruijn-binary-cycle-research-v1.json"
INVENTORY=ROOT/"knowledge/d10-v1-semantic-inventory.json"
FOUNDATION=ROOT/"knowledge/d1-d9-foundation.json"
PY_ORACLE=ROOT/"tests/test_d10_debruijn_binary_cycle.py"
R6RS_ORACLE=ROOT/"tests/d10_debruijn_binary_cycle_chez.ss"

def read(file):
    return json.loads(file.read_text(encoding="utf-8"))

def check(d, inventory, foundation):
    assert d["schema"]=="d10-debruijn-binary-cycle-source-research/v1"
    assert d["status"]=="HOLD-OWNER-CORE-VS-LIBRARY-REVIEW-NOT-SELECTED"
    assert d["baseline"]["d10_selected"]==634
    assert d["baseline"]["d10_ratified"]==0
    assert d["baseline"]["d10_inventory_git_blob"]=="65014431ac3e64633cd0be3630cfafc5e7a9aea3"
    assert inventory["accounting"]["selected_semantic_candidates"]==len(inventory["rows"])
    assert len(inventory["rows"])>=634
    assert inventory["accounting"]["ratified_d10_residents"]==0
    assert inventory["accounting"]["remaining_semantic_inventory"]==1024-len(inventory["rows"])
    assert d["admission"]["new_selected"]==0
    assert d["admission"]["new_coordinates"]==d["admission"]["new_ratified"]==0
    assert d["validation"]["not_sens_runtime"] is True
    assert d["validation"]["oracle_status"]=="PENDING-CI"
    c=d["candidate"]
    assert c["id"]=="D10-DB-RESEARCH-001"
    assert c["semantic_name"]=="DE-BRUIJN-BINARY-CYCLE?"
    assert c["arity"]==2
    assert c["source_semantics"]=="SOURCE-PROVED-HOLD"
    assert c["selected_in_d10"] is False
    assert c["coordinate"] is None and c["ratified"] is False
    assert c["physical_t5_authorized"] is False
    assert c["language_control_owner"]=="D2-ONLY"
    assert c["owner_decision"]=="OPEN-RESEARCH"
    assert c["surface_uk"] and c["surface_ukr"] and c["law"]
    assert len(c["witnesses"])>=10 and len(c["falsifiers"])>=4
    assert len(c["neighbors"])>=5 and len(c["use_cases"])>=5
    assert any(x["word"]=="00010111" and x["n"]==3 and x["value"]==1 for x in c["witnesses"])
    assert any(x["word"]=="000101110" and x["n"]==3 and x["value"]==0 for x in c["witnesses"])
    assert len(d["source"])==2
    assert d["source"][0]["url"]=="https://doc.sagemath.org/html/en/reference/combinat/sage/combinat/debruijn_sequence.html"
    assert d["source"][1]["url"]=="https://debruijnsequence.org/db/home"
    selected={x["semantic_name"].upper() for x in inventory["rows"]}
    lower={str(s).upper() for domain in foundation["domains"].values()
            for s in domain["residents"].values()}
    assert c["semantic_name"] not in (selected | lower), "A real resident now exists: review before proceeding"
    assert PY_ORACLE.exists() and R6RS_ORACLE.exists()
    return {"research":1,"added":0,"main_selected":len(selected),"ratified":0}

def bad_mutation_proofs(d,i,f):
    variants=[
       ("false selection",lambda x: x["candidate"].__setitem__("selected_in_d10",True)),
       ("false coordinate",lambda x: x["candidate"].__setitem__("coordinate","0000000000")),
       ("false ratification",lambda x: x["candidate"].__setitem__("ratified",True)),
       ("false runtime",lambda x: x["candidate"].__setitem__("physical_t5_authorized",True)),
       ("empty law",lambda x: x["candidate"].__setitem__("law","")),
       ("lost witnesses",lambda x: x["candidate"].__setitem__("witnesses",[])),
       ("lost falsifiers",lambda x: x["candidate"].__setitem__("falsifiers",[])),
       ("forged source",lambda x: x["source"][0].__setitem__("url","https://example.org")),
       ("selected counter",lambda x: x["admission"].__setitem__("new_selected",1)),
       ("rebranded opcode",lambda x: x["candidate"].__setitem__("semantic_name","GRAY-DECODE-WORD")),
       ("no core review",lambda x: x["candidate"].__setitem__("owner_decision","RATIFIED"))
    ]
    for name,fn in variants:
        change=copy.deepcopy(d);fn(change)
        try:check(change,i,f)
        except AssertionError:continue
        raise AssertionError("unsafe change accepted: "+name)
    print("D10 DE BRUIJN adversarial negative controls PASS:",len(variants))

def main():
    dossier,inventory,foundation=map(read,(DONOR,INVENTORY,FOUNDATION))
    print("D10 DE BRUIJN donor gate PASS",check(dossier,inventory,foundation))
    if "--self-test" in sys.argv:
        bad_mutation_proofs(dossier,inventory,foundation)

if __name__=="__main__":
    main()
