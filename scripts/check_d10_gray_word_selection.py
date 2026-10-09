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
PRE="7683f1e2bfcf67d3a45d412d3b1790b72ad623ad"
POST="65014431ac3e64633cd0be3630cfafc5e7a9aea3"
DONOR="0cf23c95660aa7ae199e6f683bc76f14eabbf958"
NAMES=("GRAY-ENCODE-WORD","GRAY-DECODE-WORD")
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def blob(x):
    raw=(json.dumps(x,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def verify(inv,src,his,state,low,ledger,doc):
    """Prove the immutable 632→634 Gray checkpoint within a GROWING D10."""
    assert src["checks"]["d10_preselection_sha"]=="34efd273000e3de8510441764cb59acbb5ab284b"
    assert src["checks"]["d10_selected_preselection"]==631
    assert src["status"]=="SOURCE-PINNED-RESEARCH-SELECTED-UNRATIFIED"

    rows=inv["rows"]
    count=len(rows)
    assert 634<=count<=1024, "historic Gray checkpoint must remain in the append-only inventory"
    assert inv["accounting"]["selected_semantic_candidates"]==count
    assert inv["accounting"]["law_forced_coordinates"]==256
    assert inv["accounting"]["unplaced_selected_candidates"]==count-256
    assert inv["accounting"]["remaining_semantic_inventory"]==1024-count
    assert inv["accounting"]["ratified_d10_residents"]==0
    assert state["target"]["selected_semantic_candidates"]==count
    assert state["target"]["unplaced_selected_candidates"]==count-256
    assert state["target"]["remaining_semantic_candidates"]==1024-count
    assert state["target"]["ratified_residents"]==0
    assert f"D10 selected              {count}/1024" in doc
    assert f"unplaced                  {count-256}" in doc
    assert f"remaining                 {1024-count}" in doc

    # The original Gray selected row identities must remain in their fixed
    # historical coordinates IN THE INVENTORY; they are not assigned D10
    # binary coordinates yet. Later selected rows may appear AFTER them.
    grayrows=rows[632:634]
    assert [r["semantic_name"] for r in grayrows]==list(NAMES)
    gray_source="knowledge/d10-gray-reflected-binary-research-v1.json"
    assert inv["sources"].count(gray_source)==1
    source_index=inv["sources"].index(gray_source)
    original=copy.deepcopy(inv)
    original["rows"]=original["rows"][:634]
    original["sources"]=original["sources"][:source_index+1]
    original["accounting"]["selected_semantic_candidates"]=634
    original["accounting"]["unplaced_selected_candidates"]=378
    original["accounting"]["remaining_semantic_inventory"]=390
    assert blob(original)==POST, "original 634 selected prefix was modified or reordered"

    prior=copy.deepcopy(original)
    prior["rows"]=prior["rows"][:-2]
    prior["sources"]=prior["sources"][:-1]
    prior["accounting"]["selected_semantic_candidates"]=632
    prior["accounting"]["unplaced_selected_candidates"]=376
    prior["accounting"]["remaining_semantic_inventory"]=392
    assert blob(prior)==PRE, "original 632 prefix must remain immutable"

    records=[t for t in his["transitions"]
             if t.get("id")=="d10.hobby.gray.reflected-word.after-primitive-root.20261009"]
    assert len(records)==1, "Gray historical transition must be unique"
    transition=records[0]
    assert transition["previous_inventory_blob_sha"]==PRE
    assert transition["resulting_inventory_blob_sha"]==POST
    assert transition["delta_selected"]==2
    assert transition["previous_selected"]==632
    assert transition["resulting_selected"]==634
    assert transition["coordinates_added"]==transition["ratified_added"]==0
    assert transition["added_stable_ids"]==[r["stable_id"] for r in grayrows]

    lower={str(n).upper() for v in low["domains"].values()
           for n in v["residents"].values()}
    ledgerrows=list(csv.DictReader(io.StringIO(ledger),delimiter="\t"))
    for idx,(r,s) in enumerate(zip(grayrows,src["rows"])):
        assert r["stable_id"]==s["stable_id"]
        assert r["semantic_name"]==s["semantic_name"]
        assert r["status"]=="SELECTED-RESEARCH-CANDIDATE"
        assert r["source_class"]=="HISTORICAL-REFLECTED-BINARY-GRAY-1953"
        assert r["coordinate"] is None and r["coordinate_basis"]=="UNPLACED"
        assert r["ratified_resident"] is False
        assert r["surface_uk"]==s["surface_uk"] and r["surface_ukr"]==s["surface_ukr"]
        assert r["semantic_name"] not in lower
        assert r["positive_witnesses"] and r["falsifiers"]
        assert s["positive_witnesses"] and s["falsifiers"]
        assert r["positive_witnesses"] == s["positive_witnesses"]
        assert r["falsifiers"] == s["falsifiers"]
        assert r["source_path"]==str(SRC.relative_to(ROOT))
        # Row identity, NOT position: unrelated ledger proposals can append.
        matching=[ent for ent in ledgerrows
                  if ent["semantic_name"]==r["semantic_name"]]
        assert len(matching)==1, "missing/duplicate Gray historical proposal"
        l=matching[0]
        assert l["proposal_id"]=="D10P-"+str(9+idx).zfill(4)
        assert l["ratified"]=="0" and l["status"]=="pending-review"
        assert l["dedup_check"]==f"D1-D9@09d1d71c39d1484dfd005a5068dbb18b76f0f0d4=NO-MATCH;D10@{PRE}=NO-MATCH"
        assert f"juv4uk/sens@{DONOR}:" in l["donor_provenance"]

    assert len({r["semantic_name"] for r in rows})==count
    assert len({r["stable_id"] for r in rows})==count
    return True

def models():
    def encode(w,n):
        assert isinstance(w,int) and w>=0 and 0<=n<1<<w
        return n^(n>>1)
    def decode(w,g):
        assert isinstance(w,int) and w>=0 and 0<=g<1<<w
        rank=0
        prefix=0
        for i in range(w-1,-1,-1):
            prefix ^= (g>>i)&1
            rank |= prefix << i
        return rank
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
    reject(lambda a,b,c,d:a["rows"][633].__setitem__("coordinate","1111111111"))
    reject(lambda a,b,c,d:a["rows"][633].__setitem__("ratified_resident",True))
    reject(lambda a,b,c,d:a["rows"][0].__setitem__("behavior","changed"))
    reject(lambda a,b,c,d:a["sources"].remove("knowledge/d10-gray-reflected-binary-research-v1.json"))
    reject(lambda a,b,c,d:a["rows"][633].__setitem__("semantic_name","CAR"))
    reject(lambda a,b,c,d:next(t for t in c["transitions"] if t.get("id")=="d10.hobby.gray.reflected-word.after-primitive-root.20261009").__setitem__("previous_inventory_blob_sha","0"*40))
    reject(lambda a,b,c,d:b["rows"][-1].__setitem__("positive_witnesses",[]))
    reject(lambda a,b,c,d:d["target"].__setitem__("selected_semantic_candidates",631))
    # Two properties must hold simultaneously:
    # unrelated new proposal rows are permitted; Gray donor evidence cannot drift.
    ledger_lines=led.rstrip("\n").split("\n")
    donor=next(csv.DictReader(io.StringIO(led),delimiter="\t"))
    donor["proposal_id"]="D10P-9999"
    donor["surface_uk"]="додатковий-донор"
    donor["surface_ukr"]="окрема-дослідницька-пропозиція"
    donor["semantic_name"]="UNRELATED-FUTURE-DONOR"
    donor["blocked_source"]="NOT-A-MIGRATION-BLOCK"
    donor["ratified"]="0"
    out=io.StringIO()
    writer=csv.DictWriter(out,fieldnames=list(donor),delimiter="\t",lineterminator="\n")
    writer.writerow(donor)
    verify(inv,src,his,state,low,led+out.getvalue(),doc)
    # But deleting or altering the immutable Gray proposal must still fail.
    changed=copy.deepcopy(ledger_lines)
    for i,line in enumerate(changed):
        if "\tGRAY-ENCODE-WORD\t" in line:
            changed[i]=line.replace("\tGRAY-ENCODE-WORD\t","\tNOT-GRAY\t")
            break
    else:
        raise AssertionError("missing Gray proposal in test")
    try:
        verify(inv,src,his,state,low,"\n".join(changed)+"\n",doc)
    except AssertionError:
        pass
    else:
        raise AssertionError("Gray proposal rename escaped guard")
    print("APPEND-PATH positive extension + Gray mutation rejection PASS")
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
    print("D10-GRAY PASS 632→634, 2047 exact round-trips, cyclic one-bit adjacency, 0 coordinates, 0 ratified")
if __name__=="__main__":main()
