#!/usr/bin/env python3
"""Verify 634->635 D10 research selection with byte-identical history."""
from __future__ import annotations
import argparse, copy, csv, hashlib, io, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INV=ROOT/"knowledge/d10-v1-semantic-inventory.json"
STATE=ROOT/"knowledge/d10-fill-v1-state.json"
HISTORY=ROOT/"knowledge/d10-selection-transition-history.json"
LOWER=ROOT/"knowledge/d1-d9-foundation.json"
LEDGER=ROOT/"knowledge/d10-proposal-ledger.tsv"
DOSSIER=ROOT/"knowledge/d10-gf2-minimal-recurrence-research-v1.json"
DOC=ROOT/"docs/architecture/ARCHIPELAGO-V1.uk.md"
PRE="65014431ac3e64633cd0be3630cfafc5e7a9aea3"
POST="b652f14efbbc5fdec30132a66107e81580c8a8c9"
NAME="BINARY-LFSR-MINIMAL-RECURRENCE"
STABLE="d10.fpga.gf2.minimum-recurrence.20261009"
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def gitsha(obj):
    raw=(json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def verify(inv,state,history,low,ledger,dossier,doc):
    assert gitsha(inv)==POST
    assert len(inv["rows"])==inv["accounting"]["selected_semantic_candidates"]==635
    assert inv["accounting"]["law_forced_coordinates"]==256
    assert inv["accounting"]["unplaced_selected_candidates"]==379
    assert inv["accounting"]["remaining_semantic_inventory"]==389
    assert inv["accounting"]["ratified_d10_residents"]==0
    assert state["target"]["selected_semantic_candidates"]==635
    assert state["target"]["unplaced_selected_candidates"]==379
    assert state["target"]["remaining_semantic_candidates"]==389
    assert state["target"]["ratified_residents"]==0
    assert "D10 selected              635/1024" in doc
    assert "unplaced                  379" in doc
    assert "remaining                 389" in doc
    assert inv["sources"][-1]=="knowledge/d10-gf2-minimal-recurrence-research-v1.json"
    row=inv["rows"][-1]
    assert row["semantic_name"]==NAME and row["stable_id"]==STABLE
    assert row["source_path"]==str(DOSSIER.relative_to(ROOT))
    assert row["source_class"]=="GF2-FINITE-RECURRENCE-HOBBY-20261009"
    assert row["status"]=="SELECTED-RESEARCH-CANDIDATE"
    assert row["proposal_status"]=="pending-owner-review"
    assert row["ratified_resident"] is False
    assert row["physical_t5_authorized"] is False
    assert row["coordinate"] is None and row["coordinate_basis"]=="UNPLACED"
    assert len({x["stable_id"] for x in inv["rows"]})==635
    assert len({x["semantic_name"] for x in inv["rows"]})==635
    previous=copy.deepcopy(inv)
    previous["rows"]=previous["rows"][:-1]
    previous["sources"]=previous["sources"][:-1]
    previous["accounting"]["selected_semantic_candidates"]=634
    previous["accounting"]["unplaced_selected_candidates"]=378
    previous["accounting"]["remaining_semantic_inventory"]=390
    assert gitsha(previous)==PRE,"existing 634 historical rows are immutable"
    event=history["transitions"][-1]
    assert event["id"]=="d10.hobby.gf2.minimal-recurrence.20261009"
    assert event["previous_inventory_blob_sha"]==PRE
    assert event["resulting_inventory_blob_sha"]==POST
    assert event["added_stable_ids"]==[STABLE]
    assert event["delta_selected"]==1
    assert event["previous_selected"]==634 and event["resulting_selected"]==635
    assert event["coordinates_added"]==event["ratified_added"]==0
    proposals=list(csv.DictReader(io.StringIO(ledger),delimiter="\t"))
    proposal=next(x for x in proposals if x["semantic_name"]==NAME)
    assert proposal["proposal_id"]=="D10P-4952"
    assert proposal["status"]=="pending-review" and proposal["ratified"]=="0"
    assert proposal["surface_uk"]==row["surface_uk"]
    assert proposal["surface_ukr"]==row["surface_ukr"]
    assert proposal["dedup_check"]==f"D1-D9@09d1d71c39d1484dfd005a5068dbb18b76f0f0d4=NO-MATCH;D10@{PRE}=NO-MATCH"
    assert proposal["donor_provenance"].startswith("juv4uk/sens@0a05dd1caf7b8fd9cb91ebf8c0c16bdf975f4911:")
    lower={str(x).upper() for d in low["domains"].values() for x in d["residents"].values()}
    assert NAME not in lower
    assert dossier["candidate"]["semantic_name"]==NAME
    assert dossier["candidate"]["coordinate"] is None and dossier["candidate"]["ratified"] is False
    assert row["positive_witnesses"] and row["falsifiers"]
def self_test(args):
    verify(*args)
    def bad(mut):
        p=[copy.deepcopy(x) for x in args[:6]]+[args[6]]
        mut(p)
        try: verify(*p)
        except AssertionError: return
        raise AssertionError("invalid modification accepted")
    bad(lambda p:p[0]["rows"][-1].__setitem__("coordinate","1111111111"))
    bad(lambda p:p[0]["rows"][-1].__setitem__("ratified_resident",True))
    bad(lambda p:p[0]["rows"][0].__setitem__("behavior","tampered"))
    bad(lambda p:p[0]["rows"][-1].__setitem__("semantic_name","CAR"))
    bad(lambda p:p[0]["sources"].pop())
    bad(lambda p:p[1]["target"].__setitem__("selected_semantic_candidates",634))
    bad(lambda p:p[2]["transitions"][-1].__setitem__("previous_inventory_blob_sha","0"*40))
    bad(lambda p:p[5]["candidate"].__setitem__("ratified",True))
    print("8 negative controls rejected")
def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--self-test",action="store_true")
    opts=pa.parse_args()
    args=(read(INV),read(STATE),read(HISTORY),read(LOWER),LEDGER.read_text(encoding="utf-8"),read(DOSSIER),DOC.read_text(encoding="utf-8"))
    if opts.self_test:self_test(args)
    else:verify(*args)
    print("PASS: new GF2 D10 research candidate 634->635, 0 ratifications, 0 new coordinates")
if __name__=="__main__":main()
