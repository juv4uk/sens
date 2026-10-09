#!/usr/bin/env python3
"""Поточний census CLHS §9.2 з прямими джерелами, рішеннями і негативними контролями."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "knowledge/d10-clhs-conditions-census-20261009.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
KINDS = {"condition-type", "function", "macro", "variable", "system-class", "restart"}
DECISIONS = {"DUPLICATE", "DERIVED", "HOLD", "PROPOSE"}
INDEX = "https://www.lispworks.com/documentation/HyperSpec/Body/c_condit.htm"
SOURCE_PREFIX = "https://www.lispworks.com/documentation/HyperSpec/Body/"


def git_blob_sha(obj: dict) -> str:
    payload = (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\x00" + payload).hexdigest()


def validate(census: dict, inventory: dict, foundation: dict) -> list[str]:
    errors: list[str] = []
    if census.get("schema") != "d10-clhs-conditions-census/v1":
        errors.append("invalid census schema")
    if census.get("status") != "RESEARCH-CENSUS-ONLY-NOT-SELECTED":
        errors.append("census cannot be admitted as selected")
    if census.get("source_index") != INDEX:
        errors.append("source index replaced without review")

    if census.get("snapshot", {}).get("d10_inventory_blob") != git_blob_sha(inventory):
        errors.append("census inventory SHA is not the live canonical blob")
    if census.get("snapshot", {}).get("lower_foundation_blob") != git_blob_sha(foundation):
        errors.append("census D1-D9 SHA is not the live canonical blob")
    if census.get("snapshot", {}).get("selected_d10") != len(inventory.get("rows", [])):
        errors.append("snapshot selected count differs from current inventory")
    if inventory.get("accounting", {}).get("ratified_d10_residents") != 0:
        errors.append("canonical D10 ratification must remain zero")

    selected = {str(r["semantic_name"]).upper() for r in inventory["rows"]}
    lower = {
        str(name).upper()
        for domain in foundation["domains"].values()
        for name in domain.get("residents", {}).values()
    }
    rows = census.get("rows", [])
    seen: set[str] = set()
    counts = {kind: 0 for kind in KINDS}
    decisions: dict[str, int] = {name: 0 for name in DECISIONS}
    for i, row in enumerate(rows):
        kind, name = row.get("clhs_kind"), row.get("name")
        key = str(kind) + ":" + str(name)
        if kind not in KINDS or row.get("key") != key or key in seen:
            errors.append(f"row {i}: duplicate/incorrect kind or key")
        seen.add(key)
        if kind in counts:
            counts[kind] += 1
        if row.get("source_index") != INDEX:
            errors.append(f"row {i}: unpinned CLHS index")
        primary = row.get("donor_primary_url")
        if not isinstance(primary, str) or not primary.startswith(SOURCE_PREFIX):
            errors.append(f"row {i}: missing direct primary CLHS entry URL")
        if row.get("primary_entry_url") != primary:
            errors.append(f"row {i}: legacy and canonical primary-entry URLs disagree")
        decision = row.get("decision")
        if decision not in DECISIONS or not row.get("decision_reason"):
            errors.append(f"row {i}: missing per-symbol decision/reason")
        else:
            decisions[decision] += 1
        lower_match = str(name).upper() in lower
        d10_match = str(name).upper() in selected
        if row.get("d10_selected_exact_name") is not d10_match:
            errors.append(f"row {i}: stale/misclassified D10 name")
        if row.get("d1_d9_exact_name") is not lower_match:
            errors.append(f"row {i}: stale/misclassified D1-D9 name")
        if row.get("coordinate") is not None or row.get("ratified") is not False:
            errors.append(f"row {i}: unauthorized coordinate or ratification")
        if row.get("name_collision_is_not_behavior_proof") is not True:
            errors.append(f"row {i}: name collision overclaims behavior proof")
        # A spelling overlap alone can trigger HOLD, never justify DUPLICATE.
        if (lower_match or d10_match) and decision == "DUPLICATE":
            errors.append(f"row {i}: exact-name overlap cannot itself establish DUPLICATE")

    acc = census.get("accounted", {})
    if acc.get("entries") != len(rows) or acc.get("by_kind") != {k: counts[k] for k in acc.get("by_kind", {})}:
        errors.append("dictionary entry/kind accounting mismatch")
    if acc.get("exact_name_D10") != sum(bool(r["d10_selected_exact_name"]) for r in rows):
        errors.append("D10 exact-name count mismatch")
    if acc.get("exact_name_lower") != sum(bool(r["d1_d9_exact_name"]) for r in rows):
        errors.append("D1-D9 exact-name count mismatch")
    if acc.get("no_exact_name") != sum(not r["d1_d9_exact_name"] and not r["d10_selected_exact_name"] for r in rows):
        errors.append("no-exact-name count mismatch")
    if acc.get("selected_added") != 0 or acc.get("ratified_added") != 0:
        errors.append("census may not claim selected/ratified additions")
    if len(rows) != 51:
        errors.append(f"expected 51 name+kind entries, got {len(rows)}")

    candidates = [r for r in census.get("behavior_followup", []) if r.get("decision") == "PROPOSE"]
    if len(candidates) != 1 or candidates[0].get("name") != "COMPUTE-RESTARTS":
        errors.append("exactly COMPUTE-RESTARTS must be the one source-grade candidate proposal")
    else:
        c = candidates[0]
        for field in ("source", "arity", "result_shape", "semantic_law", "falsifier", "owner_gate"):
            if not isinstance(c.get(field), str) or not c[field].strip():
                errors.append(f"COMPUTE-RESTARTS dossier missing {field}")
        if len(c.get("positive_witnesses", [])) < 2:
            errors.append("COMPUTE-RESTARTS requires at least two positive witnesses")
        dedup = c.get("behavioral_dedup", {})
        if not all(isinstance(dedup.get(k), str) and dedup[k].strip() for k in ("D1-D9", "D10")):
            errors.append("COMPUTE-RESTARTS needs separate D1-D9 and D10 behavioral dedup")
        row = next((r for r in rows if r.get("key") == "function:COMPUTE-RESTARTS"), None)
        if row is None or c.get("source") != row.get("donor_primary_url") or row.get("decision") != "PROPOSE":
            errors.append("proposal dossier disagrees with the per-symbol census row")
    if decisions["PROPOSE"] != 1:
        errors.append("per-symbol table must contain exactly one PROPOSE")

    return errors


def main() -> int:
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    errors = validate(census, inventory, foundation)
    mutants = [
        ("duplicate key", lambda j: j["rows"].append(copy.deepcopy(j["rows"][0]))),
        ("forged D10 name match", lambda j: j["rows"][0].update(d10_selected_exact_name=not j["rows"][0]["d10_selected_exact_name"])),
        ("forged D1-D9 name match", lambda j: j["rows"][0].update(d1_d9_exact_name=not j["rows"][0]["d1_d9_exact_name"])),
        ("forged coordinate", lambda j: j["rows"][0].update(coordinate="0" * 10)),
        ("forged ratification", lambda j: j["rows"][0].update(ratified=True)),
        ("falsified source", lambda j: j["rows"][0].update(donor_primary_url="https://invalid.example/")),
        ("empty decision", lambda j: j["rows"][0].update(decision="")),
        ("spelling masquerades as duplicate", lambda j: j["rows"][4].update(decision="DUPLICATE")),
        ("false accounting", lambda j: j["accounted"].update(entries=1)),
        ("proposal witness removed", lambda j: j["behavior_followup"][0].update(positive_witnesses=[])),
        ("proposal falsifier removed", lambda j: j["behavior_followup"][0].update(falsifier="")),
        ("false source snapshot", lambda j: j["snapshot"].update(selected_d10=625)),
    ]
    for title, mutation in mutants:
        candidate = copy.deepcopy(census)
        mutation(candidate)
        if not validate(candidate, inventory, foundation):
            errors.append(f"negative control passed unexpectedly: {title}")
    if errors:
        for error in errors:
            print("D10-CLHS-CONDITIONS: BLOCK", error)
        return 1
    decisions = {}
    for row in census["rows"]:
        decisions[row["decision"]] = decisions.get(row["decision"], 0) + 1
    print(f"D10-CLHS-CONDITIONS: PASS entries={len(census['rows'])}; "
          f"decisions={decisions}; 12 negative controls; selected_added=0, ratified_added=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
