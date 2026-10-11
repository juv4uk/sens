#!/usr/bin/env python3
"""Аудит семантичної повноти D10 та запасу готових до розгляду досліджень."""
import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def names_from_dossier(d):
    if not isinstance(d, dict):
        return
    for key in ("candidate", "proposal", "identity", "primary"):
        if isinstance(d.get(key), dict):
            yield d[key]
    for key in ("candidates", "proposals", "proposed_laws", "roots", "rows"):
        if isinstance(d.get(key), list):
            yield from (x for x in d[key] if isinstance(x, dict))

def source_queue(knowledge, selected, proposed):
    donor = defaultdict(list)
    ignored = {"d10-v1-semantic-inventory.json", "d10-v2-semantic-inventory.json",
               "d10-current-inventory.json", "d10-selected-coordinate-allocation-v1.json",
               "d10-v3-semantic-inventory.json", "d10-v4-semantic-inventory.json", "d10-v5-semantic-inventory.json", "d10-v6-semantic-inventory.json", "d10-v7-semantic-inventory.json", "d10-fill-v1-state.json",
               "d10-growth-baseline-v1.json", "d10-selection-transition-history.json",
               "d10-selector-seed.json"}
    for p in sorted(knowledge.glob("d10-*.json")):
        if p.name in ignored:
            continue
        try:
            data = p.read_bytes()
            obj = json.loads(data)
        except (ValueError, OSError):
            continue
        for c in names_from_dossier(obj):
            name = c.get("semantic_name") or c.get("proposed_semantic_name")
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9?!/+=*._-]+", name):
                continue
            law = c.get("law") or c.get("semantic_law") or c.get("behavior") or c.get("contract") or c.get("observable_law")
            yes = c.get("positive_witnesses") or c.get("positives") or c.get("witnesses") or c.get("examples")
            no = c.get("falsifiers") or c.get("negative_falsifiers")
            if law and yes and no:
                donor[name.upper()].append({"path": str(p.relative_to(knowledge.parent)), "git_blob": sha(data)})
    waiting = sorted(set(donor) - selected)
    return {"distinct_source_names_unselected": len(waiting),
            "with_proposal_already": sum(n in proposed for n in waiting),
            "without_proposal": sum(n not in proposed for n in waiting),
            "repeated_across_sources": sum(len(donor[n]) > 1 for n in waiting),
            "queue": [{"semantic_name": n, "sources": donor[n]} for n in waiting]}

def audit(root):
    k = root / "knowledge"
    data = (k / "d10-v1-semantic-inventory.json").read_bytes()
    ptr0 = json.loads((k / "d10-current-inventory.json").read_text(encoding="utf-8"))
    current_path = ptr0["canonical_current"]["path"]
    current_bytes = (root / current_path).read_bytes()
    inv = json.loads(current_bytes)
    hist = json.loads((k / "d10-selection-transition-history.json").read_text())
    with (k / "d10-proposal-ledger.tsv").open(newline="", encoding="utf-8") as f:
        ledger = list(csv.DictReader(f, delimiter="\t"))
    rows = inv["rows"]
    capacity = inv["capacity"]
    names = [r["semantic_name"].upper() for r in rows]
    ids = [r["stable_id"] for r in rows]
    placed = [r["coordinate"] for r in rows if r.get("coordinate") is not None]
    ratified = sum(r.get("ratified_resident") is True for r in rows)
    errors = []
    if capacity != 1024 or inv["width"] != 10 or len(rows) > capacity:
        errors.append("CAPACITY")
    if len(names) != len(set(names)) or len(ids) != len(set(ids)):
        errors.append("DUPLICATE-IDENTITY")
    if len(placed) != len(set(placed)) or any(not isinstance(c, str) or not re.fullmatch("[01]{10}", c) for c in placed):
        errors.append("INVALID-PLACEMENT")
    a = inv["accounting"]
    if (a["selected_semantic_candidates"] != len(rows)
            or a["remaining_semantic_inventory"] != capacity-len(rows)
            or a["unplaced_selected_candidates"] != len(rows)-len(placed)
            or a["ratified_d10_residents"] != ratified):
        errors.append("ACCOUNTING-DRIFT")
    transitions = hist.get("transitions", [])
    if transitions and transitions[-1].get("resulting_inventory_blob_sha") != sha(data):
        errors.append("APPEND-SHA-DRIFT")
    proposed = {x["semantic_name"].upper() for x in ledger}
    # Historical v1 selection chain, v2 419-gauge, v3 23-donor selection
    # and v4 nine independent review records have distinct SHA-pinned roles.
    research_allocated = 0
    source_review_exceptions = set()
    try:
        ptr = json.loads((k/"d10-current-inventory.json").read_text(encoding="utf-8"))
        v2raw = (k/"d10-v2-semantic-inventory.json").read_bytes()
        v3raw = (k/"d10-v3-semantic-inventory.json").read_bytes()
        v4raw = (k/"d10-v4-semantic-inventory.json").read_bytes()
        v5raw = (k/"d10-v5-semantic-inventory.json").read_bytes()
        v6raw = (k/"d10-v6-semantic-inventory.json").read_bytes()
        v2, v3, v4, v5, v6 = json.loads(v2raw), json.loads(v3raw), json.loads(v4raw), json.loads(v5raw), json.loads(v6raw)
        archive = ptr["current_archival_candidate_selection"]
        donor_raw = (root/archive["source_path"]).read_bytes()
        historical = json.loads(donor_raw)
        added = historical["records"]
        source_items = ptr["current_research_candidate_selection"]["source_pins"]
        recent = v4["rows"][698:]
        sources_good = len(source_items)==2 and len(recent)==9
        all_review_names=set()
        for pin in source_items:
            pth = pin["path"]
            if pth not in ("knowledge/d10-flavors-restarts-research-v1.json",
                           "knowledge/d10-time-law-review-v2.json"):
                sources_good=False
                continue
            source_data=(root/pth).read_bytes()
            if sha(source_data)!=pin["git_blob"]:
                sources_good=False
                continue
            donor_obj=json.loads(source_data)
            for row in recent:
                if row.get("source_path")==pth:
                    match=next((z for z in donor_obj["rows"] if z.get("semantic_name")==row["semantic_name"]),None)
                    if (match is None or match.get("triage_status")!="SEMANTIC-CANDIDATE"
                        or row.get("source_git_blob")!=pin["git_blob"]
                        or row.get("behavior")!=(match.get("semantic_law") or match.get("observable_law"))
                        or row.get("falsifier")!=match.get("falsifier")
                        or row.get("ratified_resident") is not False):
                        sources_good=False
                    else:
                        all_review_names.add(row["semantic_name"].upper())
        sources_good = sources_good and len(all_review_names)==9
        legacy_ok = (
            ptr["canonical_current"]["git_blob"] == sha(current_bytes)
            and ptr["canonical_current"]["path"] == current_path
            and ptr["historical_v6_research_inventory"]["path"] == "knowledge/d10-v6-semantic-inventory.json"
            and ptr["historical_v6_research_inventory"]["git_blob"]==sha(v6raw)
            and ptr["historical_v4_research_inventory"]["git_blob"]==sha(v4raw)
            and ptr["historical_v5_research_inventory"]["git_blob"]==sha(v5raw)
            and ptr["historical_v3_research_inventory"]["git_blob"]==sha(v3raw)
            and ptr["historical_v2_coordinate_inventory"]["git_blob"]==sha(v2raw)
            and ptr["historical_selection"]["git_blob"]==sha(data)
            and archive["source_git_blob"]==sha(donor_raw)
            and len(v2["rows"])==675 and len(v3["rows"])==698 and len(v4["rows"])==707 and len(v5["rows"])==715 and len(v6["rows"])==719
            and len(rows)==721 and rows[:719]==v6["rows"]
            and v6["rows"][:715]==v5["rows"]
            and v5["rows"][:707]==v4["rows"]
            and v4["rows"][:698]==v3["rows"]
            and v3["rows"][:675]==v2["rows"]
            and len(added)==23
            and all(r["stable_id"]==d["stable_id"]
                    and r["semantic_name"]==d["semantic_name"]
                    and r["behavior"]==d["observable_law"]
                    for r,d in zip(v3["rows"][675:],added))
        )
        v5_good=True
        v5_source_names=set()
        new_pins=ptr["current_v5_candidate_selection"]["source_pins"]
        if len(new_pins)!=3 or len(v5["rows"][707:])!=8:
            v5_good=False
        for pin in new_pins:
            path=pin["path"]
            if path not in ("knowledge/d10-crossrepo-linguistic-v1.json",
                            "knowledge/d10-clos-slot-state-historical-review-v1.json",
                            "knowledge/d10-clos-instance-lifecycle-residual-v1.json"):
                v5_good=False
                continue
            raw=(root/path).read_bytes()
            if sha(raw)!=pin["git_blob"]:
                v5_good=False
                continue
            dossier=json.loads(raw)
            for name in pin["names"]:
                row=next((r for r in v5["rows"][707:] if r["semantic_name"]==name),None)
                donor=next((d for d in dossier["rows"]
                            if (d.get("semantic_name") or d.get("historical_name"))==name),None)
                if (row is None or donor is None
                    or row["source_git_blob"]!=pin["git_blob"]
                    or row["source_path"]!=path
                    or row["behavior"]!=(donor.get("behavior") or donor.get("observable_law"))
                    or row["ratified_resident"] is not False
                    or row["physical_t5_authorized"] is not False):
                    v5_good=False
                else:
                    v5_source_names.add(name.upper())
        v5_good=v5_good and len(v5_source_names)==8
        if sources_good and legacy_ok and v5_good:
            research_allocated=len(placed)-256
            source_review_exceptions=all_review_names | v5_source_names
        else:
            errors.append("CURRENT-D10-RESEARCH-REVIEW-SHA-OR-LAW-DRIFT")
    except (OSError,ValueError,KeyError,TypeError):
        errors.append("CURRENT-D10-RESEARCH-REVIEW-INVALID")
    missing = [r["semantic_name"] for r in rows[625:]
               if r["semantic_name"].upper() not in proposed
               and r["semantic_name"].upper() not in source_review_exceptions]
    if missing:
        errors.append("SELECTED-WITHOUT-PROPOSAL")
    inventory_full = len(rows) == capacity
    placement_full = len(placed) == capacity
    return {"schema": "d10-completion-readiness/v1",
            "inventory_blob": sha(current_bytes), "historical_inventory_blob": sha(data),
            "current_inventory_path": current_path, "capacity": capacity,
            "selected": len(rows), "remaining": capacity-len(rows),
            "placed": len(placed), "unplaced": len(rows)-len(placed),
            "ratified": ratified, "inventory_full": inventory_full,
            "research_gauge_allocated": research_allocated,
            "selected_research_mapped": len(placed),
            "selected_research_unmapped": len(rows) - len(placed),
            "research_gauge_is_normative": False,
            "current_map_is_canonical_research": True,
            "placement_full": placement_full,
            "ready_for_owner_review": inventory_full and placement_full and not errors,
            "ready_to_start_d11": inventory_full and placement_full and ratified == capacity and not errors,
            "source_queue": source_queue(k, set(names), proposed),
            "blocking_errors": errors,
            "caution": "721 research-selected meanings; 719 are placed and 2 historical Common Lisp stream laws are unplaced pending semantic dedup and Core-vs-library review. 303 positions remain; none ratified."}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--require-full", action="store_true")
    a = p.parse_args()
    result = audit(a.root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return int(bool(result["blocking_errors"]) or a.require_full and not result["ready_for_owner_review"])

if __name__ == "__main__":
    raise SystemExit(main())
