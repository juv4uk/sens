#!/usr/bin/env python3
"""Audit 23 historic source-pinned D10 research candidates added directly to main.

Selection into v3 is not Core ratification or proof of all independent oracles.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POINTER = "knowledge/d10-current-inventory.json"
ARCHIVE = "research/domain-archive/20261011/pr5600/knowledge/d10-existing-ledger-semantic-tranche23-20261011.json"

class Error(ValueError):
    pass

def require(ok, why):
    if not ok:
        raise Error(why)

def sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def load(root=ROOT):
    info=json.loads((root / POINTER).read_text(encoding="utf-8"))
    if info.get("canonical_current", {}).get("path") in ("knowledge/d10-v4-semantic-inventory.json", "knowledge/d10-v5-semantic-inventory.json", "knowledge/d10-v6-semantic-inventory.json", "knowledge/d10-v7-semantic-inventory.json", "knowledge/d10-v8-semantic-inventory.json", "knowledge/d10-v9-semantic-inventory.json"):
        info["canonical_current"] = info["historical_v3_research_inventory"]
        info["status"] = "OWNER-DIRECTED-ARCHIVAL-RESEARCH-SELECTION-698-UNRATIFIED"
    current_ref=info["canonical_current"]
    old_ref=info["historical_v2_coordinate_inventory"]
    donor_ref=info["current_archival_candidate_selection"]
    def pinned(path, expected):
        require(".." not in path and (path.startswith("knowledge/") or path.startswith("research/")), "bad source path")
        raw=(root / path).read_bytes()
        require(sha(raw)==expected, "SHA drift: "+path)
        return json.loads(raw)
    current=pinned(current_ref["path"], current_ref["git_blob"])
    old=pinned(old_ref["path"], old_ref["git_blob"])
    donor=pinned(donor_ref["source_path"], donor_ref["source_git_blob"])
    foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))
    return info,current,old,donor,foundation

def verify(info,current,old,donor,foundation,root=ROOT,check_files=False):
    ref=info["canonical_current"]
    prior=info["historical_v2_coordinate_inventory"]
    source=info["current_archival_candidate_selection"]
    require(info.get("schema")=="d10-current-inventory-pointer/v1", "pointer schema")
    require(info.get("status")=="OWNER-DIRECTED-ARCHIVAL-RESEARCH-SELECTION-698-UNRATIFIED", "pointer status")
    require(ref.get("path")=="knowledge/d10-v3-semantic-inventory.json", "wrong live map")
    require(prior.get("path")=="knowledge/d10-v2-semantic-inventory.json", "old map not frozen")
    require(source.get("source_path")==ARCHIVE, "archival source path")
    require(info.get("branch_policy")=="MAIN-ONLY; NO-NEW-BRANCHES", "branch policy")
    require(current.get("schema")=="d10-v3-semantic-inventory/v1", "current schema")
    require(current.get("status")=="RESEARCH-UNRATIFIED-PARTIAL", "v3 became ratified")
    require(old.get("schema")=="d10-v2-semantic-inventory/v1", "historical v2 changed")
    require(current.get("previous_inventory")=={
        "path":prior["path"],"git_blob":prior["git_blob"],
        "role":"PRE-23-RESEARCH-STAGE-PLACEMENT"}, "v2 trace")
    require(current.get("candidate_selection_source")=={
        "path":ARCHIVE,"git_blob":source["source_git_blob"],
        "status":"RESEARCH-ONLY-OWNER-CORE-VS-LIBRARY-PENDING",
        "selected_delta":23,"starting_selected":675,"ending_selected":698,
        "source_pins_verified":18,"physical_t5_effect":"NONE",
        "ratification_effect":"NONE","witness_independence":"PENDING"}, "research admission boundary")
    require(donor.get("schema")=="d10-existing-canonical-proposal-tranche23/v1"
            and donor.get("status")=="SELECTED-RESEARCH-NOT-RATIFIED", "donor research status")
    require(len(donor.get("sources",[]))==18 and len(donor.get("records",[]))==23, "source count")
    require(len(old.get("rows",[]))==675 and len(current.get("rows",[]))==698, "selected count")
    require(current["rows"][:675]==old["rows"], "v2 historical entries rewritten")
    require(current["sources"]==old["sources"]+[ARCHIVE], "source list lost")
    for field in ["authority","current_foundation","rules","domain","width","capacity"]:
        require(current.get(field)==old.get(field), "semantic foundation drift: "+field)
    require(current.get("accounting")=={
        "selected_semantic_candidates":698,
        "law_forced_coordinates":256,
        "unplaced_selected_candidates":0,
        "remaining_semantic_inventory":326,
        "ratified_d10_residents":0,
        "placed_selected_candidates":698,
        "owner_gauge_coordinates":442,
        "research_ledger_candidates_added":23}, "accounting drift")
    require(all(ref.get(k)==n for k,n in
                [("selected",698),("placed",698),("unplaced",0),("ratified",0)]), "current pointer count")
    lower={str(y).upper() for x in foundation["domains"].values() for y in x["residents"].values()}
    existing_names={r["semantic_name"].upper() for r in old["rows"]}
    used={r["coordinate"] for r in old["rows"]}
    remain=[format(i,"010b") for i in range(1024) if format(i,"010b") not in used]
    require(len(remain)==349, "base capacity")
    names=set(existing_names)
    for index,(record, row) in enumerate(zip(donor["records"],current["rows"][675:])):
        name=record["semantic_name"]
        require(name.upper() not in lower and name.upper() not in names, "semantic name collision "+name)
        names.add(name.upper())
        required={
            "stable_id":record["stable_id"],
            "semantic_name":name,
            "status":"SELECTED-RESEARCH-CANDIDATE",
            "source_class":"ARCHIVED-CANONICAL-LEDGER-TRANCHE23",
            "relation_class":"SOURCE-PINNED-EXPLICIT-OBSERVABLE-LAW",
            "behavior":record["observable_law"],
            "coordinate":remain[index],
            "coordinate_basis":"OWNER-DIRECTED-ARCHIVAL-RESEARCH-GAUGE",
            "surface_uk":record["surface_uk"],
            "surface_ukr":record["surface_ukr"],
            "proposal_id":record["proposal_id"],
            "source_path":record["source_path"],
            "source_git_blob":record["source_git_blob"],
            "provenance":[record["source_path"],record["ledger_donor_provenance"],ARCHIVE],
            "historical_ledger_dedup":record["historical_ledger_dedup"],
            "owner_core_vs_library_review":record["historical_status"],
            "source_root_test":record["ownership_test"],
            "witness_independence":"NOT-PROVEN-BY-THIS-ADMISSION",
            "ratified_resident":False,
            "physical_t5_authorized":False
        }
        require(row==required, "candidate data or code changed: "+name)
        require(record.get("research_selection") is True
                and record.get("ratified") is False
                and record.get("physical_t5_authorized") is False,
                "donor authority not research only")
    all_rows=current["rows"]
    coords=[r["coordinate"] for r in all_rows]
    require(len(coords)==len(set(coords))==698 and
            all(isinstance(c,str) and re.fullmatch(r"[01]{10}",c) for c in coords), "coordinate collision")
    require(len({r["stable_id"] for r in all_rows})==698, "duplicate ID")
    require(all(r.get("ratified_resident") is False for r in all_rows), "fake ratification")
    if check_files:
        for item in donor["sources"]:
            raw=(root / item["path"]).read_bytes()
            require(sha(raw)==item["sha"], "source donor changed: "+item["path"])
    return {"selected":698,"new_candidates":23,"base":675,"placed":698,"missing":326,
            "ratified":0,"source_pins":18}

def self_test(info,current,old,donor,foundation):
    mutations=[
        ("duplicate candidate",lambda i,n,o,d: n["rows"][677].update(coordinate=n["rows"][676]["coordinate"])),
        ("name forged",lambda i,n,o,d: n["rows"][-1].update(semantic_name="FORGED")),
        ("donor source forged",lambda i,n,o,d: d["records"][0].update(source_git_blob="0"*40)),
        ("selector changed",lambda i,n,o,d: n["rows"][300].update(coordinate="1111111111")),
        ("ratification forged",lambda i,n,o,d: n["rows"][-1].update(ratified_resident=True)),
        ("source lost",lambda i,n,o,d: n["sources"].pop()),
        ("owner status forged",lambda i,n,o,d: i.update(status="RATIFIED")),
        ("missing row",lambda i,n,o,d: n["rows"].pop()),
    ]
    for label,action in mutations:
        i,n,o,d=copy.deepcopy(info),copy.deepcopy(current),copy.deepcopy(old),copy.deepcopy(donor)
        action(i,n,o,d)
        try:
            verify(i,n,o,d,foundation)
        except Error:
            continue
        raise Error("negative mutation escaped "+label)
    return len(mutations)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    info,current,old,donor,foundation=load()
    report=verify(info,current,old,donor,foundation,check_files=True)
    if args.self_test:
        report["negative_mutations_rejected"]=self_test(info,current,old,donor,foundation)
    print("D10-V3-ARCHIVAL-CANDIDATES: PASS "+json.dumps(report,sort_keys=True))

if __name__=="__main__":
    try:
        main()
    except (Error,ValueError,KeyError,OSError) as err:
        raise SystemExit("D10-V3-ARCHIVAL-CANDIDATES: BLOCK "+str(err))
