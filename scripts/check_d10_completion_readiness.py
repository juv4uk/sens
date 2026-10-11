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
    ignored = {"d10-v1-semantic-inventory.json", "d10-fill-v1-state.json",
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
    inv = json.loads(data)
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
    missing = [r["semantic_name"] for r in rows[625:] if r["semantic_name"].upper() not in proposed]
    if missing:
        errors.append("SELECTED-WITHOUT-PROPOSAL")
    # Research-stage allocation is a separately pinned coordinate map. It does
    # not grant normative D10 placement, executable opcodes, or ratification.
    research_allocated = 0
    gauge_path = k / "d10-selected-coordinate-allocation-v1.json"
    if gauge_path.exists():
        try:
            gauge = json.loads(gauge_path.read_text(encoding="utf-8"))
            pending = [r for r in rows if r.get("coordinate") is None]
            taken = set(placed)
            free_words = [format(i, "010b") for i in range(capacity)
                          if format(i, "010b") not in taken]
            proposals = gauge["rows"]
            good = (
                gauge.get("schema") == "d10-selected-coordinate-allocation/v1"
                and gauge.get("status") == "OWNER-DIRECTED-RESEARCH-COORDINATE-ALLOCATION-UNRATIFIED"
                and gauge.get("source_inventory_git_blob") == sha(data)
                and len(proposals) == len(pending)
                and all(
                    p.get("stable_id") == r.get("stable_id")
                    and p.get("semantic_name") == r.get("semantic_name")
                    and p.get("coordinate") == free_words[i]
                    and p.get("ratified_resident") is False
                    for i, (p, r) in enumerate(zip(proposals, pending))
                )
            )
            if good:
                research_allocated = len(proposals)
            else:
                errors.append("RESEARCH-COORDINATE-ALLOCATION-DRIFT")
        except (OSError, ValueError, KeyError, TypeError):
            errors.append("RESEARCH-COORDINATE-ALLOCATION-INVALID")
    inventory_full = len(rows) == capacity
    placement_full = len(placed) == capacity
    return {"schema": "d10-completion-readiness/v1",
            "inventory_blob": sha(data), "capacity": capacity,
            "selected": len(rows), "remaining": capacity-len(rows),
            "placed": len(placed), "unplaced": len(rows)-len(placed),
            "ratified": ratified, "inventory_full": inventory_full,
            "research_gauge_allocated": research_allocated,
            "selected_research_mapped": len(placed) + research_allocated,
            "selected_research_unmapped": len(rows) - len(placed) - research_allocated,
            "research_gauge_is_normative": False,
            "placement_full": placement_full,
            "ready_for_owner_review": inventory_full and placement_full and not errors,
            "ready_to_start_d11": inventory_full and placement_full and ratified == capacity and not errors,
            "source_queue": source_queue(k, set(names), proposed),
            "blocking_errors": errors,
            "caution": "Donor names do not equal proven nonduplicate laws. No coordinates or ratification issued."}

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
