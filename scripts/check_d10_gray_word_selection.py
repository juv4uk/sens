#!/usr/bin/env python3
"""Historical Gray-word proof on an immutable inventory snapshot plus later append-only growth."""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import io
import json
import subprocess
import sys
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
GRAY_EVENT="d10.hobby.gray.reflected-word.after-primitive-root.20261009"
NAMES=("GRAY-ENCODE-WORD","GRAY-DECODE-WORD")
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def blob(x):
    raw=(json.dumps(x,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def rewind_to_snapshot(live,history,target_sha):
    """Reverse only explicit, hash-linked append events after a historical snapshot."""
    work=copy.deepcopy(live)
    if blob(work)==target_sha:return work
    records=history.get("transitions",[])
    seen=set()
    while blob(work)!=target_sha:
        current=blob(work)
        assert current not in seen, "cycle in transition history"
        seen.add(current)
        matches=[r for r in records if r.get("resulting_inventory_blob_sha")==current]
        assert len(matches)==1, "live inventory changed without a unique append event"
        event=matches[0]
        n=event.get("delta_selected")
        ids=event.get("added_stable_ids",[])
        srcs=event.get("appended_sources",[])
        assert isinstance(n,int) and n>0 and n==len(ids), "bad append event size"
        assert work["accounting"]["selected_semantic_candidates"]==event["resulting_selected"]==len(work["rows"]), "selected count/event mismatch"
        assert event["previous_selected"]+n==event["resulting_selected"], "bad transition count arithmetic"
        assert event["coordinates_added"]==0 and event["ratified_added"]==0, "historical transition minted authority"
        tail=work["rows"][-n:]
        assert [r["stable_id"] for r in tail]==ids, "non-append row change after snapshot"
        for row in tail:
            assert row.get("status")=="SELECTED-RESEARCH-CANDIDATE", "post-snapshot row not research-only"
            assert row.get("coordinate") is None and row.get("coordinate_basis")=="UNPLACED", "post-snapshot coordinate assigned"
            assert row.get("ratified_resident") is False, "post-snapshot row ratified"
        if srcs:
            assert work["sources"][-len(srcs):]==srcs, "source tail is not append-only"
            del work["sources"][-len(srcs):]
        del work["rows"][-n:]
        work["accounting"]["selected_semantic_candidates"]=event["previous_selected"]
        work["accounting"]["unplaced_selected_candidates"]=event["previous_selected"]-256
        work["accounting"]["remaining_semantic_inventory"]=1024-event["previous_selected"]
        work["accounting"]["ratified_d10_residents"]=0
        assert blob(work)==event["previous_inventory_blob_sha"], "previous snapshot SHA mismatch after rewind"
    return work

def expected_crosswalk():
    return {
      "()":{"historical_code":"000","current_d3_code":"000","current_name":"()"},
      "QUOTE":{"historical_code":"001","current_d3_code":"001","current_name":"QUOTE"},
      "ATOM":{"historical_code":"010","current_d3_code":"010","current_name":"ATOM"},
      "EQ":{"historical_code":"011","current_d3_code":"101","current_name":"EQ"},
      "CONS":{"historical_code":"100","current_d3_code":"111","current_name":"CONS"},
      "CAR":{"historical_code":"101","current_d3_code":"100","current_name":"CAR"},
      "CDR":{"historical_code":"110","current_d3_code":"011","current_name":"CDR"},
      "COND":{"historical_code":"111","current_d3_code":"110","current_name":"COND"}}

def verify(inv,src,his,state,low,ledger,doc):
    assert src["checks"]["d10_preselection_sha"]=="34efd273000e3de8510441764cb59acbb5ab284b"
    assert src["checks"]["d10_selected_preselection"]==631
    assert src["status"]=="SOURCE-PINNED-RESEARCH-SELECTED-UNRATIFIED"
    live_n=len(inv["rows"])
    assert inv["accounting"]["selected_semantic_candidates"]==live_n
    assert inv["accounting"]["law_forced_coordinates"]==256
    assert inv["accounting"]["unplaced_selected_candidates"]==live_n-256
    assert inv["accounting"]["remaining_semantic_inventory"]==1024-live_n
    assert inv["accounting"]["ratified_d10_residents"]==0
    assert state["target"]["selected_semantic_candidates"]==live_n
    assert state["target"]["unplaced_selected_candidates"]==live_n-256
    assert state["target"]["remaining_semantic_candidates"]==1024-live_n
    assert state["target"]["ratified_residents"]==0
    assert f"D10 selected              {live_n}/1024" in doc
    assert f"unplaced                  {live_n-256}" in doc
    assert f"remaining                 {1024-live_n}" in doc

    # Validate the immutable historical 634-row Gray snapshot separately from
    # whatever source-backed append-only D10 rows have landed since then.
    gray=rewind_to_snapshot(inv,his,POST)
    assert blob(gray)==POST
    assert len(gray["rows"])==gray["accounting"]["selected_semantic_candidates"]==634
    assert gray["accounting"]["law_forced_coordinates"]==256
    assert gray["accounting"]["unplaced_selected_candidates"]==378
    assert gray["accounting"]["remaining_semantic_inventory"]==390
    assert gray["accounting"]["ratified_d10_residents"]==0
    assert [r["semantic_name"] for r in gray["rows"][-2:]]==list(NAMES)
    assert gray["sources"][-1]=="knowledge/d10-gray-reflected-binary-research-v1.json"
    original=copy.deepcopy(gray)
    original["rows"]=original["rows"][:-2]
    original["sources"]=original["sources"][:-1]
    original["accounting"]["selected_semantic_candidates"]=632
    original["accounting"]["unplaced_selected_candidates"]=376
    original["accounting"]["remaining_semantic_inventory"]=392
    assert blob(original)==PRE, "old 632 rows changed, not append-only"
    records=[r for r in his["transitions"] if r["id"]==GRAY_EVENT]
    assert len(records)==1
    transition=records[0]
    assert transition["previous_inventory_blob_sha"]==PRE
    assert transition["resulting_inventory_blob_sha"]==POST
    assert transition["delta_selected"]==2
    assert transition["coordinates_added"]==transition["ratified_added"]==0
    assert transition["added_stable_ids"]==[r["stable_id"] for r in gray["rows"][-2:]]
    lower={str(n).upper() for v in low["domains"].values() for n in v["residents"].values()}
    ledgerrows=list(csv.DictReader(io.StringIO(ledger),delimiter="\t"))
    for idx,(r,s) in enumerate(zip(gray["rows"][-2:],src["rows"])):
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
        assert r["positive_witnesses"]==s["positive_witnesses"]
        assert r["falsifiers"]==s["falsifiers"]
        assert r["source_path"]=="knowledge/d10-gray-reflected-binary-research-v1.json"
        candidate_id="D10P-"+str(9+idx).zfill(4)
        matches=[x for x in ledgerrows if x["proposal_id"]==candidate_id]
        assert len(matches)==1, "historical Gray proposal missing or duplicated"
        l=matches[0]
        assert l["semantic_name"]==r["semantic_name"]
        assert l["ratified"]=="0" and l["status"]=="pending-review"
        assert l["dedup_check"]==f"D1-D9@09d1d71c39d1484dfd005a5068dbb18b76f0f0d4=NO-MATCH;D10@{PRE}=NO-MATCH"
        assert f"juv4uk/sens@{DONOR}:" in l["donor_provenance"]
    assert len({r["semantic_name"] for r in inv["rows"]})==live_n
    assert len({r["stable_id"] for r in inv["rows"]})==live_n
    return True

def models():
    def encode(w,n):
        assert isinstance(w,int) and w>=0 and 0<=n<1<<w
        return n^(n>>1)
    def decode(w,g):
        assert isinstance(w,int) and w>=0 and 0<=g<1<<w
        rank=0; prefix=0
        for i in range(w-1,-1,-1):
            prefix^=(g>>i)&1
            rank|=prefix<<i
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
            assert decode(w,g)==i and encode(w,decode(w,g))==g
            if w>=1: assert (g^encoded[(i+1)%n]).bit_count()==1
            total+=1
    return total

def append_test_row(inv,his,state,doc):
    current=copy.deepcopy(inv)
    base_sha=blob(current)
    row=copy.deepcopy(current["rows"][-1])
    row.update({"stable_id":"d10.test.post-gray-append.v1","semantic_name":"TEST-POST-GRAY-APPEND",
                "behavior":"synthetic selected row used only to prove archival checker monotonicity",
                "source_path":"knowledge/test-post-gray-append.json","coordinate":None,
                "coordinate_basis":"UNPLACED","ratified_resident":False,"status":"SELECTED-RESEARCH-CANDIDATE"})
    source="knowledge/test-post-gray-append.json"
    current["rows"].append(row); current["sources"].append(source)
    current["accounting"]["selected_semantic_candidates"]+=1
    current["accounting"]["unplaced_selected_candidates"]+=1
    current["accounting"]["remaining_semantic_inventory"]-=1
    event={"id":"test.post-gray.append","previous_inventory_blob_sha":base_sha,
           "resulting_inventory_blob_sha":blob(current),"added_stable_ids":[row["stable_id"]],
           "appended_sources":[source],"coordinates_added":0,"ratified_added":0,"delta_selected":1,
           "previous_selected":len(inv["rows"]),"resulting_selected":len(current["rows"])}
    h=copy.deepcopy(his); h["transitions"].append(event)
    s=copy.deepcopy(state); s["target"]["selected_semantic_candidates"]+=1
    s["target"]["unplaced_selected_candidates"]+=1; s["target"]["remaining_semantic_candidates"]-=1
    d=doc.replace(f"D10 selected              {len(inv['rows'])}/1024",f"D10 selected              {len(current['rows'])}/1024")
    d=d.replace(f"unplaced                  {len(inv['rows'])-256}",f"unplaced                  {len(current['rows'])-256}")
    d=d.replace(f"remaining                 {1024-len(inv['rows'])}",f"remaining                 {1024-len(current['rows'])}")
    return current,h,s,d

def adversarial(inv,src,his,state,low,led,doc):
    def reject(mut):
        x,y,z,w=copy.deepcopy(inv),copy.deepcopy(src),copy.deepcopy(his),copy.deepcopy(state)
        mut(x,y,z,w)
        try:verify(x,y,z,w,low,led,doc)
        except (AssertionError,KeyError,TypeError,ValueError):return
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
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); args=p.parse_args()
    objects=[read(path) for path in (INV,SRC,HIS,STATE,LOW)]
    ledger=LED.read_text(encoding="utf-8"); doc=DOC.read_text(encoding="utf-8")
    verify(*objects,ledger,doc); total=models()
    if args.self_test:
        adversarial(*objects,ledger,doc)
        grown,growth_history,growth_state,growth_doc=append_test_row(objects[0],objects[2],objects[3],doc)
        assert verify(grown,objects[1],growth_history,growth_state,objects[4],ledger,growth_doc)
        unrecorded=copy.deepcopy(grown)
        try:
            verify(unrecorded,objects[1],objects[2],growth_state,objects[4],ledger,growth_doc)
        except (AssertionError,KeyError,TypeError,ValueError):
            pass
        else:
            raise AssertionError("unrecorded growth accepted")
        print("APPEND-ONLY-GROWTH: PASS recorded extension accepted, unrecorded extension rejected")
        excerpt=subprocess.check_output(["git","show",DONOR+":knowledge/d10-gray-reflected-binary-research-v1.json"],cwd=ROOT,text=True).splitlines()
        assert '"semantic_name": "GRAY-ENCODE-WORD"' in excerpt[35]
        assert '"semantic_name": "GRAY-DECODE-WORD"' in excerpt[57]
    print(f"D10-GRAY PASS historical 632→634; live={len(objects[0]['rows'])}, {total} exact round-trip ranks; 0 coordinates, 0 ratified")
if __name__=="__main__":main()
