#!/usr/bin/env python3
"""Research-only v17: verify 54 explicitly authored mathematical law DRAFTS.

Do not confuse mathematical definitions, illustrative examples, donor runs,
semantic distinctness certificates or domain ratification.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST="knowledge/d10-v17-exact-math-proposals-20261012.json"
GROUPS={"TRIT":11,"GPU-MATH":11,"LOGIC":11,"DSP":11,"COMPILER":10}

def need(ok,reason):
    if not ok: raise ValueError("D10_V17_BLOCKED:"+reason)

def sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def pinned(root,path,digest):
    p=(root/path).resolve()
    need(p.is_relative_to(root) and p.is_file(),"missing "+path)
    raw=p.read_bytes()
    need(sha(raw)==digest,"Git SHA drift "+path)
    return raw

def verify(prev,live,manifest,foundation):
    need(prev["schema"]=="d10-v16-semantic-inventory/v1" and
         live["schema"]=="d10-v17-semantic-inventory/v1","schema")
    need(len(prev["rows"])==970 and len(live["rows"])==1024,"count")
    need(live["rows"][:970]==prev["rows"],"rewrote earlier research")
    need(live["previous_inventory"]["git_blob"]==
         manifest["previous"]["git_blob"],"previous sha")
    need(live["sources"][-1]==MANIFEST,"source chain")
    need(manifest["counts"]=={
         "new_proposed":54,"selected":1024,"placed":719,
         "unplaced":305,"remaining":0,"ratified":0,
         "F2_executed":0,"F3_certified":0,"coordinates_added":0},
         "counted witness evidence")
    need(manifest["group_counts"]==GROUPS and len(manifest["candidates"])==54,"group counts")
    for k in ("not_ratified","mathematical_law_text_not_execution",
              "no_independent_donor_claim","no_f2_oracle_executed",
              "no_f3_semantic_independence_proven","no_new_coordinates"):
        need(manifest["policy"][k] is True,"false proof policy "+k)
    lower={str(x).upper() for d in foundation["domains"].values()
           for x in d.get("residents",{}).values()}
    names={r["semantic_name"].upper() for r in prev["rows"]}
    ids={r["stable_id"] for r in prev["rows"]}
    observed={}
    for row,item in zip(live["rows"][970:],manifest["candidates"]):
        key=item["semantic_name"].upper()
        need(key not in names|lower and item["id"] not in ids,
             "colliding surface or candidate identity")
        names.add(key);ids.add(item["id"])
        group=item["group"];observed[group]=observed.get(group,0)+1
        need(len(item["semantic_law"])>=40 and
             len(item["positive_illustrative_claim"])>=15 and
             len(item["negative_illustrative_claim"])>=15,
             "underspecified exact law, witness or falsifier")
        need((row["stable_id"],row["semantic_name"],row["behavior"],
              row["positive_witness_claim"],row["negative_witness_claim"],
              row["reference"],row["relation_class"])==
             (item["id"],item["semantic_name"],item["semantic_law"],
              item["positive_illustrative_claim"],item["negative_illustrative_claim"],
              item["reference"],group),"row/manifest evidence drift")
        need(row["source_path"]==MANIFEST and
             row["source_git_blob"]==manifest["_manifest_git_blob"],"manifest pin")
        need(row["source_class"]=="NEW-AUTHORED-EXACT-MATHEMATICAL-DEFINITION-V17" and
             row["source_evidence_status"]==item["evidence_class"] and
             item["F1"]=="NEW_PROPOSED_LAW_NOT_DONOR_ATTESTED" and
             item["F2"]=="HOLD_NOT_EXECUTED" and
             item["F3"]=="HOLD_NOT_PROVED_DISTINCT" and
             item["F4"]=="NO_COORDINATE","fabricated donor or proof")
        need(row["coordinate"] is None and
             row["ratified_resident"] is False and item["ratified"] is False and
             row["physical_t5_authorized"] is False and
             row["witness_independence"]=="PENDING" and
             row["independent_oracle"]=="NOT-EXECUTED-FOR-SENS",
             "fabricated physical or mathematical admission")
    need(observed==GROUPS,"lost proposed laws")
    c=[r["coordinate"] for r in live["rows"] if r.get("coordinate") is not None]
    need(len(c)==len(set(c))==719,"coordinate drift")
    a=live["accounting"]
    need((a["selected_semantic_candidates"],a["placed_selected_candidates"],
          a["unplaced_selected_candidates"],a["remaining_semantic_inventory"],
          a["ratified_d10_residents"],
          a["new_exact_mathematical_draft_research_v17_added"])==
         (1024,719,305,0,0,54),"accounting")
    return {"selected":1024,"placed":719,"unplaced":305,"remaining":0,
            "ratified":0,"new_draft_laws":54,"donor_verified":0,
            "F2_executed":0,"F3_certified":0}

def check(root=ROOT,self_test=False):
    root=root.resolve()
    ptr=json.loads((root/"knowledge/d10-current-inventory.json").read_text())
    old=ptr["historical_v16_research_inventory"]
    cur=ptr.get("historical_v17_research_inventory",ptr["canonical_current"])
    meta=ptr["current_v17_mathematical_draft_selection"]
    need(cur["path"]=="knowledge/d10-v17-semantic-inventory.json" and
         old["path"]=="knowledge/d10-v16-semantic-inventory.json",
         "current/archive pointer path")
    mp=meta["manifest"];need(mp["path"]==MANIFEST,"manifest pointer")
    m=json.loads(pinned(root,MANIFEST,mp["git_blob"]))
    need(m["previous"]["git_blob"]==old["git_blob"] and
         m["previous"]["path"]==old["path"],"manifest previous pointer")
    # Internal checker-only derived field; NEVER modify the persisted manifest.
    m["_manifest_git_blob"]=mp["git_blob"]
    prev=json.loads(pinned(root,old["path"],old["git_blob"]))
    live=json.loads(pinned(root,cur["path"],cur["git_blob"]))
    f=m["foundation"]
    foundation=json.loads(pinned(root,f["path"],f["git_blob"]))
    ans=verify(prev,live,m,foundation)
    need((cur["selected"],cur["placed"],cur["unplaced"],cur["ratified"])==
         (1024,719,305,0),"live pointer accounts")
    if self_test:
        for field,bad in (("behavior","forged law"),
                          ("coordinate","0000000000"),
                          ("ratified_resident",True),
                          ("source_git_blob","a"*40)):
            tampered=copy.deepcopy(live)
            tampered["rows"][970][field]=bad
            try: verify(prev,tampered,m,foundation)
            except ValueError: pass
            else: raise ValueError("D10_V17_BLOCKED:accepted mutant "+field)
    return ans

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    print(json.dumps(check(self_test=args.self_test),sort_keys=True))
