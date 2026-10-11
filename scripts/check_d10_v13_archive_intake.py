#!/usr/bin/env python3
"""Verify D10 v13 archived 70 research descriptions; not runtime oracles/F3."""
import argparse
import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST="knowledge/d10-v13-standards-provisional-intake-20261011.json"

def need(ok,code):
    if not ok: raise ValueError("D10_V13_BLOCKED:"+code)

def git_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def pinned(root,meta):
    location=(root/meta["path"]).resolve()
    need(location.is_relative_to(root) and location.is_file(),"SOURCE_MISSING")
    data=location.read_bytes()
    need(git_sha(data)==meta["git_blob"],"PIN_MISMATCH:"+meta["path"])
    return data

def verify(prev,current,manifest,catalog,authored,foundation):
    need(current["schema"]=="d10-v13-semantic-inventory/v1","INVENTORY_SCHEMA")
    need(len(prev["rows"])==827 and len(current["rows"])==897,"COUNT")
    need(current["rows"][:827]==prev["rows"],"APPEND_ONLY_PREFIX")
    need(current["sources"][-1]==MANIFEST,"MANIFEST_NOT_IN_SOURCE_CHAIN")
    need(current["previous_inventory"]["git_blob"]==manifest["previous"]["git_blob"],"PARENT_SOURCE_SHA")
    need(len(manifest["candidates"])==70 and len(authored["laws"])==70,"CANDIDATE_LOSS")
    checks=manifest["counts"]
    need(checks=={
        "prior_selected":827,"research_added":70,"selected_after":897,
        "placed_after":719,"unplaced_after":178,"remaining":127,
        "ratified":0,"allocated_coordinates":0,"executed_F2_proofs":0,
        "verified_F3_proofs":0
    },"COUNTS_MANIFEST")
    raw=list(csv.DictReader(catalog.decode("utf-8").splitlines(),delimiter="\t",strict=True))
    need(len(raw)==1809,"CATALOG_COUNT")
    names={r["semantic_name"].upper() for r in prev["rows"]}
    ids={r["stable_id"] for r in prev["rows"]}
    lower={str(name).upper() for d in foundation["domains"].values()
           for name in d.get("residents",{}).values()}
    index={r["candidate_id"]:r for r in raw}
    need(len(index)==len(raw),"SOURCE_ID_DUPLICATE")
    for r,p in zip(current["rows"][827:],manifest["candidates"]):
        name=p["name"]; identity=p["id"]
        need(r["stable_id"]==identity and r["semantic_name"]==name,"IDENTITY")
        need(identity not in ids and name.upper() not in (names|lower),"DUPLICATE")
        ids.add(identity);names.add(name.upper())
        src=index.get(identity)
        need(src and src["semantic_name"]==name and
             src["current_d10_selected"]=="NOT_SELECTED","NO_UNSELECTED_DONOR")
        other=sorted(x["candidate_id"] for x in raw
                     if x["semantic_name"]==name and x["candidate_id"]!=identity
                     and x["current_d10_selected"]=="NOT_SELECTED")
        need(p["co_named_archive_ids"]==r["co_named_archive_ids"]==other,
             "HISTORICAL_NAMESAKE_LOSS")
        need(r["behavior"]==p["law"]==authored["laws"][name]["law"],"LAW_DRIFT")
        need(r["illustrative_positive"]==p["positive_illustrative_claim"]==
             authored["laws"][name]["positive"],"POSITIVE_DRAFT_DRIFT")
        need(r["illustrative_negative"]==p["negative_illustrative_claim"]==
             authored["laws"][name]["negative"],"NEGATIVE_DRAFT_DRIFT")
        for key,field in (
            ("donor_provenance_claims","donor_claims"),
            ("source_records_sha_pinned","source_records_sha_pinned"),
            ("semantic_law_variants","archived_law_claims"),
        ):
            claims=json.loads(src[key])
            need(claims==p[field],"SOURCE_CLAIM_CHANGED:"+key)
            if key=="donor_provenance_claims":
                need(r["donor_provenance_claims"]==claims and bool(claims),"DONOR")
            if key=="source_records_sha_pinned":
                need(r["source_records_sha_pinned"]==claims and
                     len(claims)==int(src["source_record_count"]),"SOURCE_LOST")
        need(r["source_path"]==manifest["catalog"]["path"] and
             r["source_git_blob"]==manifest["catalog"]["git_blob"] and
             r["source_candidate_id"]==identity,"CATALOG_PIN")
        need(r["coordinate"] is None and
             r["ratified_resident"] is False and
             r["physical_t5_authorized"] is False and
             r["witness_independence"]=="PENDING" and
             r["independent_oracle"]=="NOT_EXECUTED" and
             p["F2"]=="HOLD_NOT_RUN" and
             p["F3"]=="HOLD_DEDUP_UNPROVEN" and
             p["F4"]=="NO_COORDINATE" and
             p["ratified"] is False,"FAKE_ADMISSION")
    coords=[r["coordinate"] for r in current["rows"] if r.get("coordinate") is not None]
    need(len(coords)==len(set(coords))==719,"COORDINATE_COLLISION")
    need(not any(r.get("ratified_resident") is True for r in current["rows"]),
         "RATIFICATION_FABRICATED")
    a=current["accounting"]
    need((a["selected_semantic_candidates"],a["placed_selected_candidates"],
          a["unplaced_selected_candidates"],a["remaining_semantic_inventory"],
          a["ratified_d10_residents"],a["standards_provisional_research_v13_added"])==
         (897,719,178,127,0,70),"ACCOUNTING")
    return {"selected":897,"remaining":127,"placed":719,"unplaced":178,
            "new_preliminary":70,"ratified":0,"F2_pass":0,"F3_proven":0}

def check(root=ROOT,negative=False):
    root=root.resolve()
    ptr=json.loads((root/"knowledge/d10-current-inventory.json").read_text())
    cur=ptr.get("historical_v13_research_inventory",ptr["canonical_current"])
    old=ptr["historical_v12_research_inventory"]
    hook=ptr["current_v13_standards_provisional_selection"]
    need(cur["path"]=="knowledge/d10-v13-semantic-inventory.json","CURRENT_PATH")
    need(old["path"]=="knowledge/d10-v12-semantic-inventory.json","ARCHIVED_PARENT")
    need(hook["manifest"]["path"]==MANIFEST,"MANIFEST_PATH")
    m=json.loads(pinned(root,hook["manifest"]))
    need(m["previous"]["git_blob"]==old["git_blob"],"ARCHIVED_SHA")
    need(m["catalog"]==hook["source"] and
         m["law_authors"]==hook["authoring"],"MANIFEST_DEPENDENCIES")
    prev=json.loads(pinned(root,old))
    current=json.loads(pinned(root,cur))
    cat=pinned(root,m["catalog"])
    draft=json.loads(pinned(root,m["law_authors"]))
    foundation=json.loads(pinned(root,m["foundation"]))
    result=verify(prev,current,m,cat,draft,foundation)
    need((cur["selected"],cur["placed"],cur["unplaced"],cur["ratified"])==
         (897,719,178,0),"POINTER_ACCOUNTING")
    if negative:
        for key,bad in (("coordinate","0000000000"),("behavior","BOGUS"),
                        ("ratified_resident",True),("physical_t5_authorized",True),
                        ("witness_independence","PASS")):
            changed=deepcopy(current)
            changed["rows"][827][key]=bad
            try: verify(prev,changed,m,cat,draft,foundation)
            except ValueError: pass
            else: raise ValueError("D10_V13_BLOCKED:NEGATIVE_MUTANT_PASSED:"+key)
    return result

if __name__=="__main__":
    args=argparse.ArgumentParser()
    args.add_argument("--self-test",action="store_true")
    op=args.parse_args()
    print(json.dumps(check(negative=op.self_test),sort_keys=True))
