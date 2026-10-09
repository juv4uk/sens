#!/usr/bin/env python3
"""Fail-closed D10 binary Lyndon source intake: NO selection or ratification."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"knowledge/d10-binary-lyndon-factorization-v1.json"
INVENTORY=ROOT/"knowledge/d10-v1-semantic-inventory.json"
FOUNDATION=ROOT/"knowledge/d1-d9-foundation.json"
SCHEME=ROOT/"tests/d10_binary_lyndon_factorization_chez.ss"
PYTHON=ROOT/"tests/test_d10_binary_lyndon_factorization.py"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def check(report,inventory,foundation):
    assert report["schema"]=="d10-lyndon-binary-word-donor/v1"
    assert report["status"]=="RESEARCH-HOLD-CORE-VS-LIBRARY-OWNER-REVIEW"
    assert report["baseline"]["inventory_git_blob"]=="7683f1e2bfcf67d3a45d412d3b1790b72ad623ad"
    assert report["baseline"]["selected_at_audit"]==632
    assert report["baseline"]["ratified_d10"]==0
    assert inventory["accounting"]["selected_semantic_candidates"]==len(inventory["rows"])
    assert len(inventory["rows"])>=632
    assert inventory["accounting"]["ratified_d10_residents"]==0
    assert inventory["capacity"]==1024
    assert report["admission"]["selected_delta"]==0
    assert report["admission"]["coordinates_delta"]==0
    assert report["admission"]["ratified_delta"]==0
    c=report["candidate"]
    assert c["semantic_name"]=="BINARY-LYNDON-FACTORIZATION"
    assert c["id"]=="d10.words.binary-lyndon-factorization.review.v1"
    assert c["research_only"] is True
    assert c["selected_in_canonical_d10"] is False
    assert c["coordinate"] is None and c["ratified"] is False
    assert c["physical_t5_authorized"] is False
    assert c["input"] and c["output"] and c["law"]
    assert "0<1" in c["law"] and c["owner_question"]
    assert len(c["witnesses"])>=7 and len(c["falsifiers"])>=3
    assert len(report["hold_not_root"])==4
    assert report["sources"][0]["url"]=="https://doc.sagemath.org/html/en/reference/combinat/sage/combinat/words/finite_word.html"
    other={str(s).upper() for d in foundation["domains"].values() for s in d["residents"].values()}
    now={r["semantic_name"].upper() for r in inventory["rows"]}
    assert c["semantic_name"] not in (other|now), "distinct identity already selected"
    assert "PRIMITIVE-BINARY-WORD-ROOT" in now
    assert SCHEME.read_text(encoding="utf-8").startswith("#!r6rs")
    assert PYTHON.read_text(encoding="utf-8").startswith("#!/usr/bin/env python3")
    return {"research_candidate":1,"added_selected":0,"main_selected":len(now),"ratified":0}

def adversarial(report,inventory,foundation):
    cases=[
      ("coordinate","0000000000"),
      ("ratified",True),
      ("selected_in_canonical_d10",True),
      ("physical_t5_authorized",True),
      ("semantic_name","PRIMITIVE-BINARY-WORD-ROOT"),
      ("law",""),
      ("witnesses",[]),
      ("falsifiers",[]),
      ("research_only",False),
    ]
    for field,value in cases:
        changed=copy.deepcopy(report)
        changed["candidate"][field]=value
        try: check(changed,inventory,foundation)
        except AssertionError: continue
        raise AssertionError("unsafe admission accepted: "+field)
    changed=copy.deepcopy(report)
    changed["admission"]["selected_delta"]=1
    try: check(changed,inventory,foundation)
    except AssertionError: pass
    else: raise AssertionError("selected accounting forged")
    print("D10 LYNDON source 10 negative controls PASS")

if __name__=="__main__":
    doc,inventory,foundation=map(read,(REPORT,INVENTORY,FOUNDATION))
    print("D10 LYNDON donor source PASS",check(doc,inventory,foundation))
    if "--self-test" in sys.argv: adversarial(doc,inventory,foundation)
