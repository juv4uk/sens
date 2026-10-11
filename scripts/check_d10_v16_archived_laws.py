#!/usr/bin/env python3
"""D10 v16: 32 source-anchored research descriptions; no oracle or ratification."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST="knowledge/d10-v16-archived-source-law-review-20261012.json"

def need(ok,what):
    if not ok: raise ValueError("D10_V16_RESEARCH_BLOCK:"+what)

def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def pinned(root,loc,digest):
    p=(root/loc).resolve()
    need(p.is_relative_to(root) and p.is_file(),"source missing "+loc)
    b=p.read_bytes()
    need(blob(b)==digest,"source sha mismatch "+loc)
    return b

def verify(prev,current,batch,source,foundation):
    need(current["schema"]=="d10-v16-semantic-inventory/v1","schema")
    need(current["previous_inventory"]["git_blob"]==batch["previous"]["git_blob"],"previous sha")
    need(len(prev["rows"])==938 and current["rows"][:938]==prev["rows"],"append-only previous")
    need(len(current["rows"])==970 and len(batch["candidates"])==32,"count")
    need(batch["counts"]==dict(added=32,selected=970,placed=719,unplaced=251,
                             remaining=54,ratified=0,coordinates_added=0,
                             executed_F2=0,verified_F3=0),"batch counts")
    need(current["sources"][-1]==MANIFEST,"source chain")
    low={str(x).upper() for d in foundation["domains"].values()
         for x in d.get("residents",{}).values()}
    names={r["semantic_name"].upper() for r in prev["rows"]}
    ids={r["stable_id"] for r in prev["rows"]}
    used_source_slots=set()
    for record,e in zip(current["rows"][938:],batch["candidates"]):
        name=e["name"];ident=e["id"];n=e["source_slot_index"]
        need(name.upper() not in names|low,"duplicate lower/current "+name)
        need(ident not in ids and n not in used_source_slots,"duplicate candidate")
        names.add(name.upper());ids.add(ident);used_source_slots.add(n)
        need(0<=n<len(source["slots"]),"source slot bound")
        origin=source["slots"][n]
        need(origin["semantic_name"]==name and
             origin.get("observable_law")==e["law"]==record["behavior"] and
             origin.get("positive_witness")==e["positive_illustrative_claim"]==record["positive_witness_claim"] and
             origin.get("negative_falsifier")==e["negative_illustrative_claim"]==record["negative_witness_claim"],"text law witness drift")
        need(origin["coordinate"]==e["historical_noncanonical_coordinate"]==record["source_provisional_coordinate"],"source slot drift")
        need(record["stable_id"]==ident and record["semantic_name"]==name
             and record["source_slot_index"]==n
             and record["source_path"]==batch["source"]["path"]
             and record["source_git_blob"]==batch["source"]["git_blob"]
             and record["source_primary"]==e["primary"]
             and record["core_vs_library_review"]==e["core_vs_library"],"row source drift")
        need(record["coordinate"] is None and
             record["coordinate_basis"]=="UNPLACED-NO_F2_F3"
             and record["ratified_resident"] is False
             and record["physical_t5_authorized"] is False
             and record["independent_oracle"]=="NOT-EXECUTED-FOR-SENS"
             and record["witness_independence"]=="PENDING","forged authority")
        need(e["F1"]=="ARCHIVE-SHA-PINNED" and e["F2"]=="HOLD_DONOR_NOT_RUN"
             and e["F3"]=="HOLD_DISTINCTNESS_UNPROVEN"
             and e["F4"]=="NO_COORDINATE" and e["ratified"] is False,"forged gate")
    coords=[x["coordinate"] for x in current["rows"] if x.get("coordinate") is not None]
    need(len(coords)==len(set(coords))==719,"coordinates")
    a=current["accounting"]
    need((a["selected_semantic_candidates"],a["unplaced_selected_candidates"],
          a["placed_selected_candidates"],a["remaining_semantic_inventory"],
          a["ratified_d10_residents"],a["archived_source_law_v16_research_added"])==
         (970,251,719,54,0,32),"inventory accounting")
    return {"selected":970,"placed":719,"unplaced":251,"remaining":54,
            "new_research_only":32,"executed_F2":0,"verified_F3":0}

def check(root=ROOT,self_test=False):
    root=root.resolve()
    ptr=json.loads((root/"knowledge/d10-current-inventory.json").read_text())
    active=ptr["canonical_current"]
    current=ptr.get("historical_v16_research_inventory",active)
    old=ptr["historical_v15_research_inventory"]
    selected=ptr["current_v16_archived_law_selection"]
    pin=selected["manifest"]
    need(pin["path"]==MANIFEST and
         selected["previous_inventory"]==old["path"],"pointer paths")
    batch=json.loads(pinned(root,MANIFEST,pin["git_blob"]))
    need(batch["previous"]["git_blob"]==old["git_blob"] and
         batch["source"]==selected["source"],"manifest pointer")
    prev=json.loads(pinned(root,old["path"],old["git_blob"]))
    live=json.loads(pinned(root,current["path"],current["git_blob"]))
    active_rows=json.loads(pinned(root,active["path"],active["git_blob"]))["rows"]
    need(len(active_rows)>=len(live["rows"]) and
         active_rows[:len(live["rows"])]==live["rows"],"live rewrote frozen v16")
    source=json.loads(pinned(root,batch["source"]["path"],
                             batch["source"]["git_blob"]))
    foundation=json.loads(pinned(root,batch["foundation"]["path"],
                                 batch["foundation"]["git_blob"]))
    ret=verify(prev,live,batch,source,foundation)
    need((current["selected"],current["placed"],current["unplaced"],current["ratified"])==
         (970,719,251,0),"live pointer")
    if self_test:
        for key,bad in [("behavior","not law"),("coordinate","0000000000"),
                        ("ratified_resident",True)]:
            mut=copy.deepcopy(live);mut["rows"][938][key]=bad
            try: verify(prev,mut,batch,source,foundation)
            except ValueError: pass
            else: raise ValueError("D10_V16_RESEARCH_BLOCK:accepted negative mutant "+key)
    return ret

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    options=p.parse_args()
    print(json.dumps(check(self_test=options.self_test),sort_keys=True))
