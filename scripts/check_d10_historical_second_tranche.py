#!/usr/bin/env python3
"""Fail-closed D10 second source-backed tranche: two selected, zero ratified.

Includes bounded models, NOT evidence of actual R6RS/CL runtime execution.
"""
from __future__ import annotations
import argparse, copy, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
I=ROOT/"knowledge/d10-v1-semantic-inventory.json"
S=ROOT/"knowledge/d10-fill-v1-state.json"
P=ROOT/"knowledge/d10-historical-primary-admission-batch2-v1.json"
F=ROOT/"knowledge/d1-d9-foundation.json"
D=ROOT/"docs/architecture/ARCHIPELAGO-V1.uk.md"
NAMES=("DEPOSIT-FIELD","HASHTABLE-ENTRIES")
def read(path):return json.loads(path.read_text(encoding="utf-8"))
def gitsha(raw):
    b=raw.encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def verify(p,i,s,f,doc):
    assert p["status"]=="SELECTED-RESEARCH-UNPLACED-NOT-RATIFIED"
    assert p["base"]["original_selected"]==636
    assert p["base"]["original_ratified"]==0
    assert p["added_selected"]==len(p["rows"])==2 and p["new_selected"]==638
    assert p["coordinate_added"]==p["ratified_added"]==0
    assert [r["semantic_name"] for r in p["rows"]]==list(NAMES)
    assert len(i["rows"])==638
    assert len({r["stable_id"] for r in i["rows"]})==629
    assert len({r["semantic_name"] for r in i["rows"]})==629
    assert i["accounting"]==dict(selected_semantic_candidates=638,law_forced_coordinates=256,unplaced_selected_candidates=382,remaining_semantic_inventory=386,ratified_d10_residents=0)
    assert s["target"]["selected_semantic_candidates"]==638
    assert s["target"]["unplaced_selected_candidates"]==382
    assert s["target"]["remaining_semantic_candidates"]==386
    assert s["target"]["ratified_residents"]==0
    assert "D10 selected              638/1024" in doc
    assert "unplaced                  382" in doc
    assert "remaining                 386" in doc
    assert "ratified                    0" in doc
    assert i["sources"][-1]=="knowledge/d10-historical-primary-admission-batch2-v1.json"
    assert [r["semantic_name"] for r in i["rows"][625:627]]==["DPB","ARRAY-DISPLACEMENT"]
    assert [r["semantic_name"] for r in i["rows"][627:630]]==["SLOT-BOUNDP","SLOT-MAKUNBOUND","REMOVE-METHOD"]
    assert [r["semantic_name"] for r in i["rows"][636:]]==list(NAMES)
    old=copy.deepcopy(i)
    old["rows"]=old["rows"][:636]
    old["sources"]=old["sources"][:-1]
    old["accounting"]["selected_semantic_candidates"]=636
    old["accounting"]["unplaced_selected_candidates"]=380
    old["accounting"]["remaining_semantic_inventory"]=388
    serialized=json.dumps(old,ensure_ascii=False,indent=2)+"\n"
    assert gitsha(serialized)==p["base"]["d10_git_blob"],"636 provenance changed, not monotonic"
    lower={str(n).upper() for dm in f["domains"].values() for n in dm["residents"].values()}
    assert not lower.intersection(NAMES)
    assert sum(r["coordinate"] is not None for r in i["rows"])==256
    for r,row in zip(p["rows"],i["rows"][636:]):
        assert row["stable_id"]==r["stable_id"] and row["semantic_name"]==r["semantic_name"]
        assert row["source_class"]==r["source_class"]=="HISTORICAL-PRIMARY-TRANCHE2-20261009"
        assert row["primary_source_url"]==r["primary_url"]
        assert r["proposal_status"]=="pending-owner-ratification"
        assert r["coordinate"] is None and r["ratified_resident"] is False
        assert r["decision"]=="SELECT-D10-RESEARCH-CANDIDATE"
        assert row["status"]=="SELECTED-RESEARCH-CANDIDATE"
        assert row["coordinate"] is None and row["coordinate_basis"]=="UNPLACED"
        assert row["ratified_resident"] is False
        assert r["positive_witnesses"] and len(r["positive_witnesses"])>=2
        assert r["falsifier"] and r["surface_uk"] and r["surface_ukr"]
        assert r["language_visible"] is True and r["mechanism_only"] is False
    return True
def witnesses():
    def deposit(v,width,p,target):
        m=((1<<width)-1)<<p
        return (target & ~m) | (v & m)
    def dpb(v,width,p,target):
        m=((1<<width)-1)<<p
        return (target & ~m) | ((v<<p)&m)
    assert deposit(7,2,1,0)==6
    assert deposit(-1,4,0,0)==15
    assert deposit(10,2,1,0)==2
    assert dpb(10,2,1,0)==4 != deposit(10,2,1,0)
    cases=0
    for size in range(6):
        for pos in range(7):
            for value in range(-5,12):
                for target in (-9,-1,0,39):
                    got=deposit(value,size,pos,target)
                    for bit in range(22):
                        expected=(value>>bit&1) if pos<=bit<pos+size else (target>>bit&1)
                        assert got>>bit&1==expected
                    cases+=1
    table={"а":1,"б":2,"в":3}
    for keys in (list(table),list(reversed(table)),["б","а","в"]):
        vals=[table[k] for k in keys]
        assert len(vals)==len(keys)
        assert set(zip(keys,vals))==set(table.items())
    assert not list({}.keys())
    assert set(zip(["а","б"],[2,1]))!={("а",1),("б",2)}
    return cases
def adversarial(p,i,s,f,doc):
    def bad(mutation):
        pp,ii,ss=copy.deepcopy(p),copy.deepcopy(i),copy.deepcopy(s)
        mutation(pp,ii,ss)
        try:verify(pp,ii,ss,f,doc)
        except AssertionError:return
        raise AssertionError("unsafe mutation accepted")
    bad(lambda p,i,s:p["rows"][0].__setitem__("ratified_resident",True))
    bad(lambda p,i,s:p["rows"][0].__setitem__("coordinate","0000000000"))
    bad(lambda p,i,s:p["rows"][0].__setitem__("semantic_name","CAR"))
    bad(lambda p,i,s:p["rows"][1].__setitem__("semantic_name","GETHASH"))
    bad(lambda p,i,s:i["rows"][0].__setitem__("behavior","tampered"))
    bad(lambda p,i,s:i["rows"][636].__setitem__("coordinate","0000000000"))
    bad(lambda p,i,s:i["rows"][636].__setitem__("ratified_resident",True))
    bad(lambda p,i,s:p["rows"][0].__setitem__("primary_url","https://wrong.example"))
    bad(lambda p,i,s:s["target"].__setitem__("selected_semantic_candidates",636))
    bad(lambda p,i,s:i["rows"].pop())
    print("NEGATIVE-CONTROLS: 10/10 rejected")
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    opt=parser.parse_args()
    p,i,s,f=map(read,(P,I,S,F))
    doc=D.read_text(encoding="utf-8")
    verify(p,i,s,f,doc)
    count=witnesses()
    if opt.self_test:adversarial(p,i,s,f,doc)
    print(f"D10-BATCH2 PASS 636→638, bounded deposit cases={count}, 0 coords, 0 ratified")
if __name__=="__main__":main()
