#!/usr/bin/env python3
"""Verify the current D10 v2 coordinate-complete canonical *research* inventory.

Historical D10 v1 remains byte-pinned; no ratification or physical opcode is implied.
All validation is explicit, including under python -O.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POINTER = "knowledge/d10-current-inventory.json"

class V2Error(ValueError):
    pass

def need(ok, why):
    if not ok:
        raise V2Error(why)

def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def load(root=ROOT):
    meta = json.loads((root / POINTER).read_text(encoding="utf-8"))
    def take(key):
        record=meta[key]
        path=record["path"]
        need(path.startswith("knowledge/d10-") and ".." not in path, "unsafe source path")
        raw=(root / path).read_bytes()
        need(git_blob(raw)==record["git_blob"], "pinned blob changed: "+key)
        return json.loads(raw)
    return meta,take("canonical_current"),take("historical_selection"),take("historical_address_allocation")

def verify(meta, now, old, allocation):
    need(meta.get("schema")=="d10-current-inventory-pointer/v1", "pointer schema")
    need(meta.get("status")=="OWNER-DIRECTED-PLACED-RESEARCH-UNRATIFIED", "pointer status")
    cp, hp, ap = (meta[k] for k in ("canonical_current", "historical_selection", "historical_address_allocation"))
    need(cp["path"]=="knowledge/d10-v2-semantic-inventory.json", "canonical path")
    need(hp["path"]=="knowledge/d10-v1-semantic-inventory.json", "historical path")
    need(ap["path"]=="knowledge/d10-selected-coordinate-allocation-v1.json", "allocation path")
    need(allocation.get("source_inventory_git_blob")==hp["git_blob"], "unrelated allocation source")
    need(now.get("schema")=="d10-v2-semantic-inventory/v1", "v2 schema")
    need(now.get("status")=="RESEARCH-UNRATIFIED-PARTIAL", "not research-only")
    need(old.get("schema")=="d10-v1-semantic-inventory/v1", "historical schema")
    need(now.get("previous_inventory")=={
        "path":hp["path"],"git_blob":hp["git_blob"],"role":"HISTORICAL-SELECTED-UNPLACED-ARCHIVE"}, "preplacement reference")
    need(now.get("placement_source")=={
        "path":ap["path"],"git_blob":ap["git_blob"],"rule":"ORDERED-MINIMUM-FREE-CODE",
        "new_coordinates":419,"existing_selector_codes_unchanged":256,
        "ratification_effect":"NONE","physical_t5_effect":"NONE"}, "source law")
    need(len(now.get("rows", []))==len(old.get("rows", []))==675, "row count")
    need(len(allocation.get("rows", []))==419, "allocation count")
    need(now.get("capacity")==old.get("capacity")==1024 and now.get("width")==old.get("width")==10, "10-bit capacity")
    need(now.get("domain")==old.get("domain")=="D10", "domain")
    need(now.get("sources")==old.get("sources"), "historical sources changed")
    need(now.get("rules")==old.get("rules"), "semantic rules changed")
    need(now.get("current_foundation")==old.get("current_foundation"), "foundation drift")
    need(now.get("parent_domain")==old.get("parent_domain"), "parent domain drift")
    need(now.get("accounting")=={
        **old["accounting"],
        "unplaced_selected_candidates":0,
        "placed_selected_candidates":675,
        "owner_gauge_coordinates":419}, "accounting")
    need(cp.get("selected")==675 and cp.get("placed")==675 and cp.get("unplaced")==0
        and cp.get("ratified")==0, "pointer counts")
    need(allocation.get("accounting", {}).get("allocated_from_unplaced")==419, "allocation accounting")
    alloc_by_id = {r["stable_id"]:r for r in allocation["rows"]}
    need(len(alloc_by_id)==419, "duplicate stable IDs")
    seen=set()
    sourced=0
    law_forced=0
    for position,(before,after) in enumerate(zip(old["rows"],now["rows"])):
        expected=copy.deepcopy(before)
        if before["coordinate"] is None:
            entry=alloc_by_id.get(before["stable_id"])
            need(entry is not None, "orphan selected identity")
            need(entry.get("selected_inventory_index")==position, "selection order drift")
            need(entry.get("semantic_name")==before["semantic_name"], "semantic identity mismatch")
            expected["coordinate"]=entry["coordinate"]
            expected["coordinate_basis"]="OWNER-DIRECTED-ORDERED-FREE-CODE-GAUGE"
            sourced+=1
        else:
            need(before.get("coordinate_basis")=="PROVED-SELECTOR-GENERATOR", "selector generator overwritten")
            law_forced+=1
        need(after==expected, "semantic changes outside coordinates on row "+str(position))
        code=after["coordinate"]
        need(isinstance(code,str) and re.fullmatch(r"[01]{10}",code)!=None, "non 10-bit code")
        need(code not in seen, "colliding code "+code)
        seen.add(code)
        need(after.get("ratified_resident") is False, "unapproved ratification")
    need(sourced==419 and law_forced==256 and len(seen)==675, "placement counts")
    need(allocation.get("scope","").startswith("Research allocation"), "allocation authority drift")
    return {"selected":675,"placed":675,"law_forced":256,"owner_gauge":419,"unplaced":0,"capacity_left":349,"ratified":0}

def negative_tests(meta,now,old,alloc):
    negatives=[
        ("selector moved",lambda m,n,o,a: n["rows"][256].update(coordinate="1111111111")),
        ("gauge collision",lambda m,n,o,a: n["rows"][0].update(coordinate=n["rows"][1]["coordinate"])),
        ("semantic changed",lambda m,n,o,a: n["rows"][0].update(behavior="forged law")),
        ("ratification forged",lambda m,n,o,a: n["rows"][0].update(ratified_resident=True)),
        ("history source swapped",lambda m,n,o,a: m["historical_selection"].update(git_blob="0"*40)),
        ("wrong allocation ID",lambda m,n,o,a: a["rows"][0].update(stable_id="FORGED")),
        ("inventory count forged",lambda m,n,o,a: n["accounting"].update(placed_selected_candidates=1024)),
        ("source row dropped",lambda m,n,o,a: n["rows"].pop())
    ]
    for name,action in negatives:
        m,n,o,a=copy.deepcopy(meta),copy.deepcopy(now),copy.deepcopy(old),copy.deepcopy(alloc)
        action(m,n,o,a)
        try:
            verify(m,n,o,a)
        except (V2Error, KeyError, TypeError):
            continue
        raise V2Error("negative test escaped: "+name)
    return len(negatives)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    options=p.parse_args()
    meta,now,old,alloc=load()
    result=verify(meta,now,old,alloc)
    if options.self_test:
        result["negative_tests_rejected"]=negative_tests(meta,now,old,alloc)
    print("D10-CURRENT-V2: PASS "+json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:
        main()
    except (V2Error,ValueError,KeyError,OSError) as exc:
        raise SystemExit("D10-CURRENT-V2: BLOCK "+str(exc))
