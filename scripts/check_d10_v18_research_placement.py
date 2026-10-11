#!/usr/bin/env python3
"""D10 v18 1024-code canonical RESEARCH placement; no F1-F3 or T5 admission."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE="knowledge/d10-v17-semantic-inventory.json"
DEST="knowledge/d10-v18-semantic-inventory.json"
MANIFEST="knowledge/d10-v18-coordinate-transfer-20261012.json"
GAUGE="knowledge/d10-v17-complete-research-gauge-20261012.json"

def require(ok,reason):
    if not ok: raise ValueError("D10_V18_GAUGE_BLOCK:"+reason)

def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def pinned(root,rec):
    path=(root/rec["path"]).resolve()
    require(path.is_relative_to(root) and path.is_file(),"missing or unsafe path")
    raw=path.read_bytes()
    require(blob(raw)==rec["git_blob"],"git blob mismatch "+rec["path"])
    return json.loads(raw)

def verify(source, current, gauge, manifest, ptr):
    require(source["schema"]=="d10-v17-semantic-inventory/v1","source schema")
    require(current["schema"]=="d10-v18-semantic-inventory/v1","dest schema")
    require(current["status"]=="RESEARCH-UNRATIFIED-PARTIAL","research status")
    require(manifest["authority"]=="OWNER-DIRECTED-CANONICAL-RESEARCH-COORDINATES-NOT-RATIFICATION","authority")
    require(manifest["source_inventory"]=={"path":SOURCE,"git_blob":ptr["historical_v17_research_inventory"]["git_blob"]},"source pin")
    require(manifest["proposed_research_gauge"]==ptr["current_v18_research_coordinate_placement"]["research_gauge"],"gauge pin")
    require(manifest["destination_inventory_path"]==DEST,"dest path")
    require(ptr["canonical_current"]["path"]==DEST and ptr["canonical_current"]["selected"]==1024
            and ptr["canonical_current"]["placed"]==1024 and
            ptr["canonical_current"]["unplaced"]==ptr["canonical_current"]["ratified"]==0,"live pointer")
    require(len(source["rows"])==len(current["rows"])==len(gauge["rows"])==1024,"row count")
    require(current["previous_inventory"]["git_blob"]==manifest["source_inventory"]["git_blob"],"version chain")
    require(current["sources"]==source["sources"]+[MANIFEST],"source chain")
    require(current["rules"][:-1]==source["rules"],"historic rules drift")
    require(current["rules"][-1].startswith("v18: 305 research gauge"),"migration disclaimer")
    used=set();old_count=0;new_count=0;patches=[]
    for i,(before,after,mapped) in enumerate(zip(source["rows"],current["rows"],gauge["rows"])):
        require(mapped["index"]==i and mapped["stable_id"]==before["stable_id"]
                and mapped["semantic_name"]==before["semantic_name"],"map row ID/name")
        require(after["stable_id"]==before["stable_id"] and
                after["semantic_name"]==before["semantic_name"],"dest row ID/name")
        c=mapped["coordinate"]
        require(isinstance(c,str) and re.fullmatch("[01]{10}",c) and c not in used,"invalid or repeated code")
        used.add(c)
        require(after["coordinate"]==c,"coordinate differs from pinned gauge")
        require(after.get("ratified_resident") is False,"forged ratification")
        require(not after.get("physical_t5_authorized",False),"forged runtime authorization")
        if before["coordinate"] is None:
            require(mapped["assignment"]=="PROPOSED_ORDERED_FREE_RESEARCH_GAUGE","not provisional")
            require(after["coordinate_basis"]=="OWNER-DIRECTED-ORDERED-FREE-CODE-RESEARCH-GAUGE","unsupported authority")
            old=copy.deepcopy(after); old["coordinate"]=before["coordinate"];old["coordinate_basis"]=before["coordinate_basis"]
            require(old==before,"semantic/source fields changed")
            patches.append({"index":i,"stable_id":before["stable_id"],
                            "semantic_name":before["semantic_name"],"coordinate":c})
            new_count+=1
        else:
            require(mapped["assignment"]=="PRESERVED_LIVE_RESEARCH_COORDINATE","not preserved")
            require(after==before,"existing coordinate or semantics changed")
            old_count+=1
    require((old_count,new_count,len(used))==(719,305,1024),"count conservation")
    require(used=={format(i,"010b") for i in range(1024)},"incomplete coordinate bijection")
    require(patches==manifest["new_placements"],"source-to-code ledger changed")
    require(manifest["counts"]=={
      "selected":1024,"preserved_old_codes":719,"transferred_new_codes":305,
      "total_placed":1024,"unplaced":0,"unique_10_bit_codes":1024,
      "ratified":0,"physical_authorized_new":0,
      "independent_oracle_attestations_added":0,
      "semantic_distinctness_certificates_added":0}, "evidence accounting")
    a=current["accounting"]
    require(a["selected_semantic_candidates"]==1024 and
            a["placed_selected_candidates"]==1024 and
            a["unplaced_selected_candidates"]==0 and
            a["remaining_semantic_inventory"]==0 and
            a["ratified_d10_residents"]==0 and
            a["law_forced_coordinates"]==256 and
            a["owner_gauge_coordinates"]==768 and
            a["new_owner_research_gauge_v18_coordinates"]==305,"canonical accounting")
    oldacc=dict(a)
    for key in ("placed_selected_candidates","unplaced_selected_candidates","owner_gauge_coordinates","new_owner_research_gauge_v18_coordinates"):
        oldacc.pop(key,None)
    oldsource=dict(source["accounting"])
    for key in ("placed_selected_candidates","unplaced_selected_candidates","owner_gauge_coordinates"):
        oldsource.pop(key,None)
    require(oldacc==oldsource,"historical selection counts changed")
    return {"selected":1024,"placed":1024,"added":305,"preserved":719,
            "unplaced":0,"ratified":0,"physical_t5_authorized":0}

def check(root=ROOT,self_test=False):
    root=root.resolve()
    ptr=json.loads((root/"knowledge/d10-current-inventory.json").read_text(encoding="utf-8"))
    live=ptr["canonical_current"]
    hook=ptr["current_v18_research_coordinate_placement"]
    require(hook["manifest"]["path"]==MANIFEST and
            ptr["historical_v17_research_inventory"]["path"]==SOURCE,
            "manifest/frozen refs")
    source=pinned(root,ptr["historical_v17_research_inventory"])
    current=pinned(root,live)
    gauge=pinned(root,hook["research_gauge"])
    manifest=pinned(root,hook["manifest"])
    result=verify(source,current,gauge,manifest,ptr)
    if self_test:
        for name,fn in [
            ("collision",lambda o:o["rows"][719].update(coordinate=o["rows"][0]["coordinate"])),
            ("semantic drift",lambda o:o["rows"][719].update(behavior="FORGED")),
            ("old moved",lambda o:o["rows"][0].update(coordinate="1111111111")),
            ("fake ratification",lambda o:o["rows"][719].update(ratified_resident=True)),
            ("physical T5",lambda o:o["rows"][1023].update(physical_t5_authorized=True)),
            ("short map",lambda o:o["rows"].pop()),
        ]:
            bad=copy.deepcopy(current);fn(bad)
            try:verify(source,bad,gauge,manifest,ptr)
            except (ValueError,KeyError,IndexError):pass
            else:raise ValueError("D10_V18_GAUGE_BLOCK:escaped mutant "+name)
        result["negative_mutations_rejected"]=6
    return result

if __name__=="__main__":
    arg=argparse.ArgumentParser()
    arg.add_argument("--self-test",action="store_true")
    args=arg.parse_args()
    print(json.dumps(check(self_test=args.self_test),sort_keys=True))
