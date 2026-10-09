#!/usr/bin/env python3
"""Historical reflected Gray-word research selection -- exact source and bijection.

This verifies semantic mathematical witnesses and machine-readable selected
inventory; it does not ratify a D10 coordinate or prove full SENS parity.
"""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INV=ROOT/"knowledge/d10-v1-semantic-inventory.json"
HIS=ROOT/"knowledge/d10-selection-transition-history.json"
DOC=ROOT/"docs/architecture/ARCHIPELAGO-V1.uk.md"
STATE=ROOT/"knowledge/d10-fill-v1-state.json"
SRC=ROOT/"knowledge/d10-gray-reflected-binary-research-v1.json"
LOW=ROOT/"knowledge/d1-d9-foundation.json"
LED=ROOT/"knowledge/d10-proposal-ledger.tsv"
PRE="34efd273000e3de8510441764cb59acbb5ab284b"
POST="2ef73a8fb2d1e5aa1e0133c725a2d712286a4ecf"
DONOR="0cf23c95660aa7ae199e6f683bc76f14eabbf958"
NAMES=("GRAY-ENCODE-WORD","GRAY-DECODE-WORD")
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def blob(x):
    raw=(json.dumps(x,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def verify(inv,src,his,state,low,ledger,doc):
    assert src["checks"]["d10_preselection_sha"]==PRE
    assert src["checks"]["d10_selected_preselection"]==631
    assert src["status"]=="SOURCE-PINNED-RESEARCH-SELECTED-UNRATIFIED"
    assert blob(inv)==POST
    assert len(inv["rows"])==inv["accounting"]["selected_semantic_candidates"]==633
    assert inv["accounting"]["law_forced_coordinates"]==256
    assert inv["accounting"]["unplaced_selected_candidates"]==377
    assert inv["accounting"]["remaining_semantic_inventory"]==391
    assert inv["accounting"]["ratified_d10_residents"]==0
    assert state["target"]["selected_semantic_candidates"]==633
    assert state["target"]["unplaced_selected_candidates"]==377
    assert state["target"]["remaining_semantic_candidates"]==391
    assert state["target"]["ratified_residents"]==0
    assert "D10 selected              633/1024" in doc
    assert "unplaced                  377" in doc
    assert "remaining                 391" in doc
    assert [r["semantic_name"] for r in inv["rows"][-2:]]==list(NAMES)
    assert inv["sources"][-1]=="knowledge/d10-gray-reflected-binary-research-v1.json"
    original=copy.deepcopy(inv)
    original["rows"]=original["rows"][:-2]
    original["sources"]=original["sources"][:-1]
    original["accounting"]["selected_semantic_candidates"]=631
    original["accounting"]["unplaced_selected_candidates"]=375
    original["accounting"]["remaining_semantic_inventory"]=393
    assert blob(original)==PRE, "old 631 rows changed, not append-only"
    records=his["transitions"]
    assert records[-1]["id"]=="d10.hobby.gray.reflected-word.20261009"
    assert records[-1]["previous_inventory_blob_sha"]==PRE
    assert records[-1]["resulting_inventory_blob_sha"]==POST
    assert records[-1]["delta_selected"]==2
    assert records[-1]["coordinates_added"]==records[-1]["ratified_added"]==0
    assert records[-1]["added_stable_ids"]==[r["stable_id"] for r in inv["rows"][-2:]]
    lower={str(n).upper() for v in low["domains"].values() for n in v["residents"].values()}
    ledgerrows=list(csv.DictReader(io.StringIO(ledger),delimiter="\t"))
    for idx,(r,s) in enumerate(zip(inv["rows"][-2:],src["rows"])):
        assert r["stable_id"]==s["stable_id"]
        assert r["semantic_name"]==s["semantic_name"]
        assert r["status"]=="SELECTED-RESEARCH-CANDIDATE"
        assert r["source_class"]=="HISTORICAL-REFLECTED-BINARY-GRAY-1953"
        assert r["coordinate"] is None and r["coordinate_basis"]=="UNPLACED"
        assert r["ratified_resident"] is False
        assert r["surface_uk"]==s["surface_uk"] and r["surface_ukr"]==s["surface_ukr"]
        assert r["semantic_name"] not in lower
        assert r["positive_witnesses"] and r["falsifiers"]
        assert r["source_path"]==str(SRC.relative_to(ROOT))
        l=ledgerrows[-2+idx]
        assert l["proposal_id"]=="D10P-"+str(7+idx).zfill(4)
        assert l["semantic_name"]==r["semantic_name"]
        assert l["ratified"]=="0" and l["status"]=="pending-review"
        assert l["dedup_check"]==f"D1-D9@09d1d71c39d1484dfd005a5068dbb18b76f0f0d4=NO-MATCH;D10@{PRE}=NO-MATCH"
        assert f"juv4uk/sens@{DONOR}:" in l["donor_provenance"]
    assert len({r["semantic_name"] for r in inv["rows"]})==633
    assert len({r["stable_id"] for r in inv["rows"]})==633
    return True

def models():
    def encode(w,n):
        assert isinstance(w,int) and w>=0 and 0<=n<1<<w
        return n^(n>>1)
    def decode(w,g):
        assert isinstance(w,int) and w>=0 and 0<=g<1<<w
        r=0
        for i in range(w-1,-1,-1):
            r ^= (g>>i)&1
            if i:r <<= 1
        return r
    assert encode(4,7)==4 and encode(4,11)==14
    assert decode(4,4)==7 and decode(4,14)==11
    assert encode(0,0)==decode(0,0)==0
    total=0
    for w in range(11):
        n=1<<w
        encoded=[encode(w,i) for i in range(n)]
        assert set(encoded)==set(range(n))
        for i,g in enumerate(encoded):
            assert decode(w,g)==i
            assert encode(w,decode(w,g))==g
            if w>=1:
                assert (g^encoded[(i+1)%n]).bit_count()==1
            total+=1
    return total

def adversarial(inv,src,his,state,low,led,doc):
    def reject(mut):
        x,y,z,w=copy.deepcopy(inv),copy.deepcopy(src),copy.deepcopy(his),copy.deepcopy(state)
        mut(x,y,z,w)
        try:verify(x,y,z,w,low,led,doc)
        except AssertionError:return
        raise AssertionError("mutation accepted")
    reject(lambda a,b,c,d:a["rows"][-1].__setitem__("coordinate","1111111111"))
    reject(lambda a,b,c,d:a["rows"][-1].__setitem__("ratified_resident",True))
    reject(lambda a,b,c,d:a["rows"][0].__setitem__("behavior","changed"))
    reject(lambda a,b,c,d:a["sources"].pop())
    reject(lambda a,b,c,d:a["rows"][-1].__setitem__("semantic_name","CAR"))
    reject(lambda a,b,c,d:c["transitions"][-1].__setitem__("previous_inventory_blob_sha","0"*40))
    reject(lambda a,b,c,d:b["rows"][-1].__setitem__("positive_witnesses",[]))
    reject(lambda a,b,c,d:d["target"].__setitem__("selected_semantic_candidates",631))
    print("NEGATIVE-CONTROLS 8/8 rejected")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    objects=[read(p) for p in (INV,SRC,HIS,STATE,LOW)]
    verify(*objects,LED.read_text(encoding="utf-8"),DOC.read_text(encoding="utf-8"))
    total=models()
    if args.self_test:adversarial(*objects,LED.read_text(encoding="utf-8"),DOC.read_text(encoding="utf-8"))
    if args.self_test:
        excerpt=subprocess.check_output(["git","show",DONOR+":knowledge/d10-gray-reflected-binary-research-v1.json"],cwd=ROOT,text=True).splitlines()
        assert '"semantic_name": "GRAY-ENCODE-WORD"' in excerpt[35]
        assert '"semantic_name": "GRAY-DECODE-WORD"' in excerpt[57]
    print("D10-GRAY PASS 631→633, 2047 exact round-trips, cyclic one-bit adjacency, 0 coordinates, 0 ratified")
if __name__=="__main__":main()
