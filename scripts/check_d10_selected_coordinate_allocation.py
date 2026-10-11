#!/usr/bin/env python3
"""Check all 419 owner-allocated D10 research coordinates without granting ratification."""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = "knowledge/d10-selected-coordinate-allocation-v1.json"
INV = "knowledge/d10-v1-semantic-inventory.json"
SEED = "knowledge/d10-selector-seed.json"

class AllocationError(ValueError):
    pass

def need(value, msg):
    if not value:
        raise AllocationError(msg)

def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def load():
    raw_inventory = (ROOT / INV).read_bytes()
    raw_seed = (ROOT / SEED).read_bytes()
    return (json.loads((ROOT / MAP).read_text(encoding="utf-8")),
            json.loads(raw_inventory), json.loads(raw_seed),
            blob(raw_inventory), blob(raw_seed))

def verify(m, inv, seed, inventory_sha, seed_sha):
    need(m.get("schema") == "d10-selected-coordinate-allocation/v1", "schema")
    need(m.get("status") == "OWNER-DIRECTED-RESEARCH-COORDINATE-ALLOCATION-UNRATIFIED", "ratification/status drift")
    need(m.get("domain") == "D10" and m.get("width") == 10 and m.get("capacity") == 1024, "domain/width/capacity")
    need(m.get("source_inventory_path") == INV and m.get("source_inventory_git_blob") == inventory_sha, "source inventory SHA drift")
    need(m.get("source_selector_seed_path") == SEED and m.get("source_selector_seed_git_blob") == seed_sha, "source seed SHA drift")
    need(inv.get("status") == "RESEARCH-UNRATIFIED-PARTIAL", "canonical inventory authority changed")
    need(len(inv.get("rows", [])) == 675 and len({r["stable_id"] for r in inv["rows"]}) == 675, "selected inventory identity")
    need(all(r.get("ratified_resident") is False for r in inv["rows"]), "unauthorized ratification")

    forced = [r for r in inv["rows"] if r.get("coordinate") is not None]
    unknown = [r for r in inv["rows"] if r.get("coordinate") is None]
    need(len(forced) == len(seed.get("rows", [])) == 256 and len(unknown) == 419, "historical counts")
    need(all(r.get("coordinate_basis") == "PROVED-SELECTOR-GENERATOR" for r in forced), "missing selector law")
    fixed = {r["stable_id"]: r["coordinate"] for r in forced}
    need(len(fixed) == 256, "duplicate selector ID")
    need(all(fixed.get(x["stable_id"]) == x["coordinate"] for x in seed["rows"]), "selector address changed")

    used = [r["coordinate"] for r in forced]
    need(len(set(used)) == 256 and all(isinstance(s,str) and re.fullmatch(r"[01]{10}",s) for s in used), "invalid forced bits")
    available = [format(n,"010b") for n in range(1024) if format(n,"010b") not in set(used)]
    assignments = m.get("rows", [])
    need(len(assignments) == 419, "incomplete assigned coordinates")
    for i, (current, entry) in enumerate(zip(unknown, assignments)):
        need(entry.get("stable_id") == current["stable_id"], "misassigned stable ID")
        need(entry.get("semantic_name") == current["semantic_name"], "misassigned semantic name")
        need(entry.get("selected_inventory_index") == inv["rows"].index(current), "historical ordering changed")
        need(entry.get("coordinate") == available[i], "coordinate not first available")
        need(entry.get("coordinate_basis") == "ORDER-PRESERVING-FREE-CODE-GAUGE", "coordinate basis forged")
        need(entry.get("ratified_resident") is False, "mapping falsely ratified")
    all_coordinates = used + [x["coordinate"] for x in assignments]
    need(len(all_coordinates) == len(set(all_coordinates)) == 675, "duplicate coordinate")
    need(all(re.fullmatch(r"[01]{10}",x) for x in all_coordinates), "malformed coordinate")
    need(m.get("accounting") == {
        "selected":675, "law_forced":256, "allocated_from_unplaced":419,
        "total_assigned":675, "still_unassigned_selected":0,
        "missing_semantics":349, "ratified":0
    }, "accounting drift")
    return {"selected":675,"forced":256,"allocated":419,"mapped":675,"free":349,"ratified":0}

def reject_mutations(m,inv,seed,hi,hs):
    cases = [
      ("duplicate address",lambda a,b,c:a["rows"][1].update(coordinate=a["rows"][0]["coordinate"])),
      ("unlawful address",lambda a,b,c:a["rows"][0].update(coordinate="1111111111")),
      ("wrong stable ID",lambda a,b,c:a["rows"][0].update(stable_id="FORGED")),
      ("source repin",lambda a,b,c:a.update(source_inventory_git_blob="0"*40)),
      ("selector changed",lambda a,b,c:c["rows"][0].update(coordinate="1111111111")),
      ("ratification fabricated",lambda a,b,c:a["rows"][0].update(ratified_resident=True)),
      ("row deleted",lambda a,b,c:a["rows"].pop()),
      ("accounting fabricated",lambda a,b,c:a["accounting"].update(total_assigned=1024)),
    ]
    for label,change in cases:
        a,b,c=copy.deepcopy(m),copy.deepcopy(inv),copy.deepcopy(seed)
        change(a,b,c)
        try:
            verify(a,b,c,hi,hs)
        except AllocationError:
            continue
        raise AllocationError("negative test escaped: "+label)
    return len(cases)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    m,inv,seed,hi,hs=load()
    result=verify(m,inv,seed,hi,hs)
    if args.self_test:
        result["negative_tests_rejected"]=reject_mutations(m,inv,seed,hi,hs)
    print("D10-419-ALLOCATION: PASS "+json.dumps(result,sort_keys=True))

if __name__ == "__main__":
    try:
        main()
    except (AllocationError,OSError,ValueError) as e:
        raise SystemExit("D10-419-ALLOCATION: BLOCK "+str(e))
