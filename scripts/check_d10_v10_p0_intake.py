#!/usr/bin/env python3
"""Provisional D10 v10 source-claim check. Never claim F2/F3 or ratification."""
import argparse
import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST="knowledge/d10-p0-research-intake-v10-20261011.json"

def fail(ok,msg):
    if not ok: raise ValueError("D10_V10_BLOCK:"+msg)

def sha(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def pinned(root,path,digest):
    file=(root/path).resolve()
    fail(file.is_relative_to(root) and file.is_file(),"missing "+path)
    raw=file.read_bytes()
    fail(sha(raw)==digest,"pin "+path)
    return raw

def verify(v9,v10,manifest,source,foundation):
    fail(v10["schema"]=="d10-v10-semantic-inventory/v1","schema")
    fail(v10["previous_inventory"]["git_blob"]==manifest["previous"]["git_blob"],"parent pin")
    fail(len(v9["rows"])==759 and v10["rows"][:759]==v9["rows"],"v9 prefix drift")
    fail(len(v10["rows"])==799 and len(manifest["candidates"])==40,"selection count")
    fail(v10["sources"][-1]==MANIFEST,"source chain")
    lower={str(n).upper() for d in foundation["domains"].values()
           for n in d.get("residents",{}).values()}
    used_names={r["semantic_name"].upper() for r in v9["rows"]}
    used_ids={r["stable_id"] for r in v9["rows"]}
    entries={}
    for r in csv.DictReader(source.decode("utf-8").splitlines(),delimiter="\t",strict=True):
        fail(None not in r and all(x is not None for x in r.values()),"source ragged")
        fail(r["candidate_id"] not in entries,"source repeated ID")
        entries[r["candidate_id"]]=r
    fail(len(entries)==1809,"source identity count")
    fields={"semantic_law_variants":"law","donor_provenance_claims":"donor_claims",
            "positive_witness_claims":"positive_witness_claims",
            "falsifier_claims":"negative_witness_claims",
            "source_records_sha_pinned":"source_records_sha_pinned"}
    for r,m in zip(v10["rows"][759:],manifest["candidates"]):
        name,identity=m["name"],m["id"]
        fail(r["semantic_name"]==name and r["stable_id"]==identity,"row identity")
        fail(name.upper() not in lower|used_names,"duplicate surface "+name)
        fail(identity not in used_ids,"duplicate ID")
        used_names.add(name.upper());used_ids.add(identity)
        old=entries.get(identity)
        fail(old is not None and old["semantic_name"]==name and
             old["current_d10_selected"]=="NOT_SELECTED","source selection mismatch")
        for col,target in fields.items():
            values=json.loads(old[col])
            fail(isinstance(values,list) and len(values)>0,"missing text claim "+col)
            if col=="semantic_law_variants":
                fail(values[0]==m["law"]==r["behavior"],"law drift")
            else:
                fail(values==m[target],"manifest evidence drift "+col)
                if col=="source_records_sha_pinned":
                    fail(values==r["source_records_sha_pinned"] and
                         len(values)==int(old["source_record_count"]),"source losses")
                else: fail(values==r["donor_provenance_claims" if col=="donor_provenance_claims" else target],
                           "row evidence drift "+col)
        fail(r["source_git_blob"]==manifest["candidate_index"]["git_blob"] and
             r["source_path"]==manifest["candidate_index"]["path"] and
             r["source_candidate_id"]==identity,"catalog pin")
        fail(r["coordinate"] is None and
             r["coordinate_basis"]=="UNPLACED-F2-F3-NOT_PROVED" and
             r["ratified_resident"] is False and
             r["physical_t5_authorized"] is False and
             r["witness_independence"]=="PENDING" and
             r["independent_oracle"]=="NOT-EXECUTED-FOR-SENS","forged approval")
        fail(m["F2"]=="HOLD_NOT_RUN" and m["F3"]=="HOLD_BEHAVIORAL_DEDUP_UNPROVEN" and
             m["F4"]=="NO_COORDINATE" and m["ratified"] is False,"forged evidence")
    coords=[r["coordinate"] for r in v10["rows"] if r.get("coordinate") is not None]
    fail(len(coords)==len(set(coords))==719,"coordinate collision")
    fail(not any(r.get("ratified_resident") for r in v10["rows"]),"ratification")
    a=v10["accounting"]
    fail((a["selected_semantic_candidates"],a["placed_selected_candidates"],
          a["unplaced_selected_candidates"],a["remaining_semantic_inventory"],
          a["ratified_d10_residents"],
          a["historical_p0_text_witness_research_v10_added"])==
         (799,719,80,225,0,40),"accounting")
    return {"selected":799,"placed":719,"unplaced":80,"remaining":225,
            "ratified":0,"new_research_only":40,"F2_executed":0,"F3_admitted":0}

def check(root=ROOT,self_test=False):
    root=root.resolve()
    pointer=json.loads((root/"knowledge/d10-current-inventory.json").read_text())
    live=pointer["canonical_current"]
    cur=pointer.get("historical_v10_research_inventory",live)
    prev=pointer["historical_v9_research_inventory"]
    index=pointer["current_v10_p0_text_witness_selection"]
    fail(cur["path"]=="knowledge/d10-v10-semantic-inventory.json","frozen v10 pointer")
    fail(prev["path"]=="knowledge/d10-v9-semantic-inventory.json","frozen pointer")
    mp=index["manifest"]
    fail(mp["path"]==MANIFEST,"manifest path")
    m=json.loads(pinned(root,MANIFEST,mp["git_blob"]))
    fail(m["previous"]["git_blob"]==prev["git_blob"],"previous pin")
    fail(all(m["candidate_index"][key]==index["source_catalog"][key]
             for key in ("path","git_blob")) and
         m["candidate_index"]["candidate_rows"]==1809,"catalog index pin")
    v9=json.loads(pinned(root,prev["path"],prev["git_blob"]))
    v10=json.loads(pinned(root,cur["path"],cur["git_blob"]))
    source=pinned(root,m["candidate_index"]["path"],m["candidate_index"]["git_blob"])
    f=m["foundation"]
    foundation=json.loads(pinned(root,f["path"],f["git_blob"]))
    result=verify(v9,v10,m,source,foundation)
    fail((cur["selected"],cur["placed"],cur["unplaced"],cur["ratified"])==
         (799,719,80,0),"live pointer counts")
    live_rows=json.loads(pinned(root,live["path"],live["git_blob"]))["rows"]
    fail(len(live_rows)>=799 and live_rows[:799]==v10["rows"],"frozen v10 archive rewritten")
    if self_test:
        for field,bad in [("coordinate","0000000000"),("behavior","FAKE"),
                          ("ratified_resident",True)]:
            mutant=deepcopy(v10)
            mutant["rows"][759][field]=bad
            try: verify(v9,mutant,m,source,foundation)
            except ValueError: pass
            else: raise ValueError("D10_V10_BLOCK:mutant accepted "+field)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    print(json.dumps(check(self_test=a.self_test),sort_keys=True))
