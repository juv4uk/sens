#!/usr/bin/env python3
"""D10 v12: source claims checked, not F2/F3, no coordinates or ratification."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "knowledge/d10-historical-identity-types-v12-20261011.json"
CATALOG = "knowledge/d10-source-snapshots/d10-v9-unified-catalog-1809.tsv"

def need(ok, name):
    if not ok: raise ValueError("D10_V12_BLOCKED:" + name)

def sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\x00" + raw).hexdigest()

def pinned(root, path, expected):
    full=(root/path).resolve()
    need(full.is_relative_to(root) and full.is_file(), "UNSAFE_OR_MISSING:"+path)
    raw=full.read_bytes()
    need(sha(raw)==expected, "SHA_DRIFT:"+path)
    return raw

def verify(v11,v12,m,index,foundation):
    need(v12["schema"]=="d10-v12-semantic-inventory/v1", "SCHEMA")
    need(v12["previous_inventory"]["git_blob"]==m["previous"]["git_blob"],"PARENT_SHA")
    need(len(v11["rows"])==823 and len(v12["rows"])==827 and
         v12["rows"][:823]==v11["rows"],"APPEND_ONLY_823_PREFIX")
    need(v12["sources"][-1]==MANIFEST,"MISSING_MANIFEST_SOURCE")
    need(len(m["candidates"])==4 and
         m["counts"]=={"prior_selected":823,"research_added":4,
                       "after_selected":827,"after_placed":719,
                       "after_unplaced":108,"remaining":197,"ratified":0,
                       "new_coordinates":0,"executed_F2_receipts":0,
                       "F3_proofs":0},"COUNTS_MANIFEST")
    rows=list(csv.DictReader(index.decode("utf-8").splitlines(),delimiter="\t",strict=True))
    need(len(rows)==1809 and all(None not in r and
         all(v is not None for v in r.values()) for r in rows),"CATALOG_INTEGRITY")
    by_id={r["candidate_id"]:r for r in rows}
    need(len(by_id)==1809,"CATALOG_ID_DUP")
    lower={str(x).upper() for d in foundation["domains"].values()
           for x in d.get("residents",{}).values()}
    names={r["semantic_name"].upper() for r in v11["rows"]}
    ids={r["stable_id"] for r in v11["rows"]}
    mapping=[("semantic_law_variants","law_variants",None),
             ("donor_provenance_claims","donor_claims","donor_provenance_claims"),
             ("positive_witness_claims","positive_witness_claims","positive_witness_claims"),
             ("falsifier_claims","negative_witness_claims","negative_witness_claims"),
             ("source_records_sha_pinned","source_records_sha_pinned","source_records_sha_pinned")]
    for r,mr in zip(v12["rows"][823:],m["candidates"]):
        name,ident=mr["name"],mr["id"]
        need((r["stable_id"],r["semantic_name"])==(ident,name),"IDENTITY")
        need(name.upper() not in names|lower and ident not in ids,"DUPLICATE_SURFACE_OR_ID")
        names.add(name.upper());ids.add(ident)
        original=by_id.get(ident)
        need(original is not None and original["semantic_name"]==name and
             original["current_d10_selected"]=="NOT_SELECTED","HISTORICAL_SOURCE_NOT_PENDING")
        others=sorted(x["candidate_id"] for x in rows
                      if x["semantic_name"]==name and x["candidate_id"]!=ident)
        need(mr["co_named_archive_ids"]==others and
             r["co_named_archive_ids"]==others,"OTHER_IDS_DROPPED")
        for sourcefield,target,rowfield in mapping:
            values=json.loads(original[sourcefield])
            need(isinstance(values,list) and values==mr[target],"SOURCE_CLAIMS_CHANGED:"+sourcefield)
            if rowfield:
                need(r[rowfield]==values,"INVENTORY_SOURCE_CLAIMS_CHANGED:"+sourcefield)
            if sourcefield=="semantic_law_variants":
                need(values and r["behavior"]==mr["law"]==values[0],"LAW_MISMATCH")
            if sourcefield=="donor_provenance_claims":
                need(values,"EMPTY_DONOR_CLAIM")
            if sourcefield=="source_records_sha_pinned":
                need(len(values)==int(original["source_record_count"]),"SOURCE_OCCURRENCES_LOST")
        need(r["source_path"]==m["source"]["path"]==CATALOG and
             r["source_git_blob"]==m["source"]["git_blob"] and
             r["source_candidate_id"]==ident,"SOURCE_PIN")
        need(r["coordinate"] is None and
             r["coordinate_basis"]=="F2-F3-HOLD-NO-COORDINATE" and
             r["ratified_resident"] is False and
             r["physical_t5_authorized"] is False and
             r["independent_oracle"]=="NOT-EXECUTED" and
             r["witness_independence"]=="PENDING","FORGED_ADMISSION")
        need(mr["F2"]=="HOLD_NOT_RUN" and mr["F3"]=="HOLD_DEDUP_UNPROVEN" and
             mr["F4"]=="NO_COORDINATE" and mr["ratified"] is False,
             "FORGED_F2_F3")
    coords=[r["coordinate"] for r in v12["rows"] if r.get("coordinate") is not None]
    need(len(coords)==len(set(coords))==719,"COORD_COLLISION")
    need(not any(r.get("ratified_resident") is True for r in v12["rows"]),
         "RATIFICATION_FABRICATED")
    a=v12["accounting"]
    need((a["selected_semantic_candidates"],a["placed_selected_candidates"],
          a["unplaced_selected_candidates"],a["remaining_semantic_inventory"],
          a["ratified_d10_residents"],
          a["historical_identity_type_research_v12_added"]) ==
         (827,719,108,197,0,4),"ACCOUNTING_DRIFT")
    return {"selected":827,"placed":719,"unplaced":108,"remaining":197,
            "research_only_added":4,"ratified":0,"F2_pass":0,"F3_proven":0}

def check(root=ROOT,self_test=False):
    root=root.resolve()
    ptr=json.loads((root/"knowledge/d10-current-inventory.json").read_text())
    cur=ptr["canonical_current"]
    frozen=ptr["historical_v11_research_inventory"]
    hook=ptr["current_v12_historical_identity_type_selection"]
    need(cur["path"]=="knowledge/d10-v12-semantic-inventory.json" and
         frozen["path"]=="knowledge/d10-v11-semantic-inventory.json","INVENTORY_POINTER")
    mp=hook["manifest"]
    need(mp["path"]==MANIFEST,"MANIFEST_POINTER")
    m=json.loads(pinned(root,MANIFEST,mp["git_blob"]))
    need(m["previous"]["git_blob"]==frozen["git_blob"] and
         hook["previous_inventory"]==frozen["path"] and
         hook["source"]["git_blob"]==m["source"]["git_blob"],"MANIFEST_CHAIN")
    prior=json.loads(pinned(root,frozen["path"],frozen["git_blob"]))
    current=json.loads(pinned(root,cur["path"],cur["git_blob"]))
    src=pinned(root,m["source"]["path"],m["source"]["git_blob"])
    f=m["foundation"]
    foundation=json.loads(pinned(root,f["path"],f["git_blob"]))
    result=verify(prior,current,m,src,foundation)
    need((cur["selected"],cur["placed"],cur["unplaced"],cur["ratified"])==
         (827,719,108,0),"POINTER_COUNTS")
    if self_test:
        for key,bad in [("coordinate","0000000000"),("behavior","FABRICATED"),
                        ("physical_t5_authorized",True),("ratified_resident",True)]:
            evil=deepcopy(current)
            evil["rows"][823][key]=bad
            try: verify(prior,evil,m,src,foundation)
            except ValueError: pass
            else: raise ValueError("D10_V12_BLOCKED:NEGATIVE_MUTANT_PASSED:"+key)
    return result

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--self-test",action="store_true")
    print(json.dumps(check(self_test=a.parse_args().self_test),sort_keys=True))
