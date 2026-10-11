#!/usr/bin/env python3
"""Fail closed on D10 v4's 9 reviewed-but-unratified source laws.

Historical v1/v2/v3 remain SHA-pinned. Candidate admission is neither Core
ratification nor an independent executable oracle.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCES=[
 ("flavors","knowledge/d10-flavors-restarts-research-v1.json",[
    "APPLICABLE-METHODS","NEXT-METHOD-AVAILABLE?","STANDARD-METHOD-COMBINATION","FIND-RESTART"]),
 ("time","knowledge/d10-time-law-review-v2.json",[
    "CIVIL-FROM-DAYS","INTERNET-TIME-FIELDS->OBSERVATION","INTERNET-TIME-OBSERVATION->UTC",
    "TIMEZONE-DECLARATIONS->OBSERVATION","TIMEZONE-CONFIG"])
]

class Invalid(ValueError):
    pass

def need(value,message):
    if not value:
        raise Invalid(message)

def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def load(root=ROOT):
    ptr=json.loads((root/"knowledge/d10-current-inventory.json").read_text(encoding="utf-8"))
    if re.fullmatch(r"knowledge/d10-v(?:[5-9]|[1-9][0-9]+)-semantic-inventory\.json", ptr.get("canonical_current", {}).get("path", "")):
        ptr["canonical_current"] = ptr["historical_v4_research_inventory"]
        ptr["status"] = "OWNER-DIRECTED-RESEARCH-SELECTION-707-UNRATIFIED"
    records=[ptr["canonical_current"],ptr["historical_v3_research_inventory"]]
    results=[]
    for entry in records:
        path=entry["path"]
        need(path.startswith("knowledge/d10-v") and ".." not in path,"unsafe source")
        raw=(root/path).read_bytes()
        need(blob(raw)==entry["git_blob"],"inventory historical SHA mismatch")
        results.append(json.loads(raw))
    docs=[]
    for _,path,_ in SOURCES:
        raw=(root/path).read_bytes()
        docs.append((blob(raw),json.loads(raw)))
    return ptr,results[0],results[1],docs

def verify(ptr,current,previous,docs):
    cur=ptr["canonical_current"]
    old=ptr["historical_v3_research_inventory"]
    need(cur["path"]=="knowledge/d10-v4-semantic-inventory.json","canonical path")
    need(old["path"]=="knowledge/d10-v3-semantic-inventory.json","v3 path")
    need(ptr["status"]=="OWNER-DIRECTED-RESEARCH-SELECTION-707-UNRATIFIED","unratified pointer status")
    need(current["schema"]=="d10-v4-semantic-inventory/v1","schema")
    need(current["status"]=="RESEARCH-UNRATIFIED-PARTIAL","ratification")
    need(current["previous_inventory"]=={
        "path":old["path"],"git_blob":old["git_blob"],
        "role":"PRE-NINE-RESEARCH-CANDIDATES"},"historical source")
    need(len(previous["rows"])==698 and len(current["rows"])==707,"count")
    need(current["rows"][:698]==previous["rows"],"old 698 data changed")
    need(current.get("accounting")=={
        "selected_semantic_candidates":707,
        "law_forced_coordinates":256,
        "unplaced_selected_candidates":0,
        "remaining_semantic_inventory":317,
        "ratified_d10_residents":0,
        "placed_selected_candidates":707,
        "owner_gauge_coordinates":451,
        "research_ledger_candidates_added":23,
        "research_review_candidates_added":9},"accounting drift")
    need(all(cur.get(k)==v for k,v in
        [("selected",707),("placed",707),("unplaced",0),("ratified",0)]),"pointer counts")
    need(current.get("historical_candidate_selection_source")==previous.get("candidate_selection_source"),
        "previous tranche evidence lost")
    need(current.get("sources")==previous.get("sources")+[
        SOURCES[0][1],SOURCES[1][1]],"source-provenance trace")
    for key in ["domain","width","capacity","current_foundation","rules","parent_domain"]:
        need(current.get(key)==previous.get(key),"domain law changed "+key)
    pins=current.get("research_candidate_sources")
    need(isinstance(pins,list) and len(pins)==len(docs)==2,"donor refs")
    available=[format(i,"010b") for i in range(1024) if format(i,"010b") not in {
        row["coordinate"] for row in previous["rows"]}]
    added=current["rows"][698:]
    offset=0
    for idx,((kind,path,names),(digest,doc)) in enumerate(zip(SOURCES,docs)):
        pin=pins[idx]
        need(pin=={
           "path":path,"git_blob":digest,"status":doc["status"],
           "selected_names":names,"selection_authority":"OWNER-DIRECTED-RESEARCH-ONLY",
           "independent_oracles":"PENDING"},"source SHA/status drift")
        for name in names:
            d=next((row for row in doc.get("rows",[]) if row.get("semantic_name")==name),None)
            need(d is not None and d.get("triage_status")=="SEMANTIC-CANDIDATE",
                 "donor did not offer research candidate: "+name)
            slug=re.sub("^-|-$","",re.sub("[^a-z0-9]+","-",name.lower()))
            expected={
             "stable_id":f"d10.research-review.{kind}.{slug}.20261011",
             "semantic_name":name,
             "status":"SELECTED-RESEARCH-CANDIDATE-REVIEW-PENDING",
             "source_class":"HISTORICAL-CLOS-FLAVORS-LAW-REVIEW" if kind=="flavors" else "EXACT-TIME-DATA-LAW-REVIEW",
             "relation_class":"SOURCE-PINNED-OBSERVABLE-LAW-UNRATIFIED",
             "behavior":d.get("semantic_law") or d.get("observable_law"),
             "coordinate":available[offset],
             "coordinate_basis":"OWNER-DIRECTED-UNRATIFIED-RESEARCH-GAUGE",
             "surface_uk":d["surface_uk"],
             "surface_ukr":d["surface_ukr"],
             "proposal_id":d["proposal_id"],
             "source_path":path,
             "source_git_blob":digest,
             "provenance":[path,d.get("source_url") or d.get("source_file") or "source-donor"],
             "falsifier":d["falsifier"],
             "positive_witnesses":d.get("witnesses"),
             "source_review_status":d["triage_status"],
             "owner_core_vs_library_review":d.get("owner_decision") or "PENDING",
             "independent_oracle":d.get("independent_language_oracle") or "NOT-YET-PROVED",
             "witness_independence":"NOT-PROVEN-BY-THIS-ADMISSION",
             "ratified_resident":False,
             "physical_t5_authorized":False
            }
            need(added[offset]==expected,"semantic/coordinate/witness mismatch: "+name)
            offset+=1
    need(offset==9,"added candidates")
    codes=[r["coordinate"] for r in current["rows"]]
    need(len(set(codes))==len(codes)==707 and
         all(isinstance(x,str) and re.fullmatch("[01]{10}",x) for x in codes),"nonunique/invalid code")
    need(len({r["stable_id"] for r in current["rows"]})==707 and
         len({r["semantic_name"].upper() for r in current["rows"]})==707,"semantic collision")
    need(all(r.get("ratified_resident") is False for r in current["rows"]),
         "unapproved ratification")
    need(ptr.get("current_research_candidate_selection",{}).get("selected_added")==9,
         "pointer selective delta")
    need(ptr.get("current_research_candidate_selection",{}).get("source_pins")==[
        {"path":p,"git_blob":docs[i][0]} for i,(_,p,_) in enumerate(SOURCES)],
        "source pins pointer")
    return {"selected":707,"prior":698,"new":9,"missing":317,"ratified":0,
            "independent_oracle":"PENDING"}

def negatives(ptr,current,previous,docs):
    controls=[
      ("duplicate address",lambda p,c,b,d:c["rows"][706].update(coordinate=c["rows"][705]["coordinate"])),
      ("falsifier removed",lambda p,c,b,d:c["rows"][699].update(falsifier="")),
      ("source forged",lambda p,c,b,d:c["research_candidate_sources"][0].update(git_blob="0"*40)),
      ("older row mutated",lambda p,c,b,d:c["rows"][0].update(semantic_name="FORGED")),
      ("ratification forged",lambda p,c,b,d:c["rows"][-1].update(ratified_resident=True)),
      ("semantic copied",lambda p,c,b,d:c["rows"][-1].update(semantic_name=c["rows"][698]["semantic_name"])),
      ("oracle forged",lambda p,c,b,d:c["rows"][698].update(independent_oracle="PROVEN")),
      ("donor law changed",lambda p,c,b,d:d[0][1]["rows"][0].update(semantic_law="FORGED")),
    ]
    for name,act in controls:
        p,c,b,d=copy.deepcopy((ptr,current,previous,docs))
        act(p,c,b,d)
        try:
            verify(p,c,b,d)
        except (Invalid,KeyError,TypeError):
            continue
        raise Invalid("escaped adversarial mutation: "+name)
    return len(controls)

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--self-test",action="store_true")
    args=arg.parse_args()
    stuff=load()
    result=verify(*stuff)
    if args.self_test:
        result["adversarial_mutations_rejected"]=negatives(*stuff)
    print("D10-V4-RESEARCH: PASS "+json.dumps(result,sort_keys=True))

if __name__=="__main__":
    try:
        main()
    except (Invalid,ValueError,OSError,KeyError) as e:
        raise SystemExit("D10-V4-RESEARCH: BLOCK "+str(e))
