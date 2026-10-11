#!/usr/bin/env python3
"""Fail-closed D10 v15 append-only archival-law research intake.

The archive supplies textual law and illustrative witnesses. This checker
does NOT run historical donors, prove F3 independence, allocate coordinates,
or ratify the domain. Checks must work with Python -O (never use assert).
"""
import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST="knowledge/d10-v15-source-law-intake-20261012.json"

def require(condition,why):
    if not condition:
        raise ValueError("D10_V15_BLOCKED:"+why)

def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest()

def pinned(root,path,digest):
    p=(root/path).resolve()
    require(p.is_relative_to(root) and p.is_file(),"missing "+path)
    data=p.read_bytes()
    require(blob(data)==digest,"wrong Git SHA "+path)
    return data

def verify(previous,current,manifest,source,foundation):
    require(previous["schema"]=="d10-v14-semantic-inventory/v1","frozen prior schema")
    require(current["schema"]=="d10-v15-semantic-inventory/v1","v15 schema")
    require(manifest["schema"]=="d10-v15-source-law-intake/v1","manifest schema")
    require(len(previous["rows"])==919 and len(current["rows"])==938,"row count")
    require(current["rows"][:919]==previous["rows"],"rewrote historical v13")
    require(current["previous_inventory"]["git_blob"]==manifest["previous"]["git_blob"],
            "previous pin")
    require(current["sources"][-1]==MANIFEST,"manifest missing in inventory sources")
    expected={"added":19,"selected":938,"placed":719,"unplaced":219,
              "remaining":86,"ratified":0,"coordinates_added":0,
              "executed_F2":0,"verified_F3":0}
    require(manifest["counts"]==expected and len(manifest["candidates"])==19,
            "manifest accounting")
    require(manifest["policy"]["not_ratified"] is True and
            manifest["policy"]["unplaced_only"] is True and
            manifest["policy"]["do_not_infer_semantic_independence"] is True,
            "unsupported F2 or F3")
    require(len(source["slots"])==1024,"archive source size")
    low={str(x).upper() for v in foundation["domains"].values()
         for x in v.get("residents",{}).values()}
    names={r["semantic_name"].upper() for r in previous["rows"]}
    ids={r["stable_id"] for r in previous["rows"]}
    seen_slots=set()
    for row,record in zip(current["rows"][919:],manifest["candidates"]):
        n=record["name"].upper()
        id=record["id"]
        require(n not in names and n not in low and id not in ids,
                "duplicate or lower-domain name")
        names.add(n);ids.add(id)
        ix=record["source_slot_index"]
        require(type(ix)==int and ix not in seen_slots and 0<=ix<1024,
                "missing or repeated source slot locator")
        seen_slots.add(ix)
        original=source["slots"][ix]
        evidence=original.get("source_evidence",{})
        require(original["semantic_name"]==record["name"],"source name drift")
        require(all(isinstance(evidence.get(x),str) and evidence[x].strip()
                    for x in ("law","positive","negative")),"incomplete law")
        require(evidence["law"]==record["law"]==row["behavior"],"law changed")
        require(evidence["positive"]==record["positive_illustrative_claim"]==
                row["positive_witness_claim"],"positive example changed")
        require(evidence["negative"]==record["negative_illustrative_claim"]==
                row["negative_witness_claim"],"negative example changed")
        require(evidence==record["source_detail"],"source metadata altered")
        require(evidence["status"]==record["source_status"]==
                row["source_evidence_status"],"source status altered")
        require(row["source_path"]==manifest["source"]["path"] and
                row["source_git_blob"]==record["source_git_blob"]==
                manifest["source"]["git_blob"],"source SHA changed")
        require(row["source_slot_index"]==ix and
                row["stable_id"]==id and row["semantic_name"]==record["name"],
                "source candidate identity changed")
        require(row["coordinate"] is None and
                row["coordinate_basis"]=="UNPLACED-NOT-F2-F3-PROVED" and
                row["ratified_resident"] is False and
                row["physical_t5_authorized"] is False and
                row["witness_independence"]=="PENDING" and
                row["independent_oracle"]=="NOT-EXECUTED-FOR-SENS",
                "fabricated F2, F3 or coordinate")
        require(record["F2"]=="HOLD_DONOR_NOT_RUN" and
                record["F3"]=="HOLD_DISTINCTNESS_UNPROVEN" and
                record["F4"]=="NO_COORDINATE" and
                record["ratified"] is False,"false certificate")
    used=[x["coordinate"] for x in current["rows"] if x.get("coordinate") is not None]
    require(len(used)==len(set(used))==719 and
            not any(x.get("ratified_resident") is True for x in current["rows"]),
            "coordinate collision or ratification")
    a=current["accounting"]
    require((a["selected_semantic_candidates"],a["placed_selected_candidates"],
             a["unplaced_selected_candidates"],a["remaining_semantic_inventory"],
             a["ratified_d10_residents"],a["source_archive_law_v15_research_added"])==
            (938,719,219,86,0,19),"inventory arithmetic")
    return {"selected":938,"added":19,"placed":719,"unplaced":219,
            "remaining":86,"ratified":0,"F2_executed":0,"F3_verified":0}

def check(root=ROOT,self_test=False):
    root=root.resolve()
    ptr=json.loads((root/"knowledge/d10-current-inventory.json").read_text())
    live=ptr.get("historical_v15_research_inventory",ptr["canonical_current"])
    active=ptr["canonical_current"]
    frozen=ptr["historical_v14_research_inventory"]
    intake=ptr["current_v15_source_law_selection"]
    pin=intake["manifest"]
    require(pin["path"]==MANIFEST,"unexpected manifest")
    m=json.loads(pinned(root,MANIFEST,pin["git_blob"]))
    require(m["previous"]["git_blob"]==frozen["git_blob"],"frozen source pin")
    require(intake["source"]["git_blob"]==m["source"]["git_blob"] and
            intake["source"]["path"]==m["source"]["path"],"index pin drift")
    prior=json.loads(pinned(root,frozen["path"],frozen["git_blob"]))
    current=json.loads(pinned(root,live["path"],live["git_blob"]))
    active_rows=json.loads(pinned(root,active["path"],active["git_blob"]))["rows"]
    require(len(active_rows)>=len(current["rows"]) and
            active_rows[:len(current["rows"])]==current["rows"],
            "live D10 rewrote archived v15")
    source=json.loads(pinned(root,m["source"]["path"],m["source"]["git_blob"]))
    f=m["foundation"]
    foundation=json.loads(pinned(root,f["path"],f["git_blob"]))
    answer=verify(prior,current,m,source,foundation)
    require((live["selected"],live["placed"],live["unplaced"],live["ratified"])==
            (938,719,219,0),"current pointer counts")
    if self_test:
        for field,bad in (("coordinate","0000000000"),("behavior","FAKE"),
                          ("ratified_resident",True),("source_slot_index",65535)):
            corrupted=deepcopy(current)
            corrupted["rows"][919][field]=bad
            try:
                verify(prior,corrupted,m,source,foundation)
            except ValueError:
                pass
            else:
                raise ValueError("D10_V15_BLOCKED:mutant accepted "+field)
    return answer

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    print(json.dumps(check(self_test=args.self_test),sort_keys=True))
