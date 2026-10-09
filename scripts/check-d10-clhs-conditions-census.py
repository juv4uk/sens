#!/usr/bin/env python3
"""Захист дослідницького перепису CLHS §9.2; без автоматичної D10-селекції."""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "knowledge/d10-clhs-conditions-census-20261009.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
KINDS = {"condition-type", "function", "macro", "variable", "system-class", "restart"}
DECISIONS = {"DUPLICATE", "DERIVED", "HOLD", "PROPOSE"}
BODY = "https://www.lispworks.com/documentation/HyperSpec/Body/"
TARGET = "function:COMPUTE-RESTARTS"
INDEX = "https://www.lispworks.com/documentation/HyperSpec/Body/c_condit.htm"


def validate(census: dict, inventory: dict, foundation: dict) -> list[str]:
    errors: list[str] = []
    if census.get("schema") != "d10-clhs-conditions-census/v1":
        errors.append("invalid census schema")
    if census.get("status") != "RESEARCH-CENSUS-ONLY-NOT-SELECTED":
        errors.append("census cannot be admitted as selected")
    if census.get("source_index") != INDEX:
        errors.append("source index replaced without review")
    seen: set[str] = set()
    decisions = {name: 0 for name in DECISIONS}
    proposed = []
    # Freeze the original 630-row evidence cohort while permitting a legitimate
    # append-only increase in the current D10 inventory. The global transition
    # SHA checker separately verifies each later suffix.
    anchor = census.get("snapshot", {}).get("selected_d10")
    if not isinstance(anchor, int) or anchor < 630 or len(inventory["rows"]) < anchor:
        errors.append("missing frozen historical census baseline")
        anchor = min(630, len(inventory["rows"]))
    selected = {r["semantic_name"].upper() for r in inventory["rows"][:anchor]}
    lower = {str(name).upper()
             for domain in foundation["domains"].values()
             for name in domain.get("residents", {}).values()}
    rows = census.get("rows", [])
    counts = {kind: 0 for kind in KINDS}
    for i, row in enumerate(rows):
        kind, name = row.get("clhs_kind"), row.get("name")
        key = str(kind) + ":" + str(name)
        if kind not in KINDS or row.get("key") != key or key in seen:
            errors.append(f"row {i}: duplicate/incorrect kind or key")
        seen.add(key)
        if kind in counts:
            counts[kind] += 1
        if row.get("source_index") != INDEX:
            errors.append(f"row {i}: unpinned index")
        url = row.get("primary_entry_url")
        donor = row.get("donor_primary_url")
        if (not isinstance(donor, str) or not donor.startswith(BODY)
                or not donor.endswith(".htm") or donor == INDEX or donor != url):
            errors.append(f"row {i}: missing or incorrect direct CLHS primary page")
        decision = row.get("decision")
        if decision not in DECISIONS:
            errors.append(f"row {i}: missing DUPLICATE/DERIVED/HOLD/PROPOSE verdict")
        else:
            decisions[decision] += 1
        if not row.get("behavioral_dedup") or not row.get("owner_boundary"):
            errors.append(f"row {i}: no behavioral dedup or ownership analysis")
        if decision == "PROPOSE":
            proposed.append(row)
            if (row.get("key") != TARGET
                    or len(row.get("positive_witnesses", [])) < 2
                    or len(row.get("falsifiers", [])) < 2):
                errors.append(f"row {i}: source-level proposal without witnesses/falsifiers")
        if row.get("d10_selected_exact_name") is not (str(name).upper() in selected):
            errors.append(f"row {i}: stale/misclassified D10 name")
        if row.get("d1_d9_exact_name") is not (str(name).upper() in lower):
            errors.append(f"row {i}: stale/misclassified lower name")
        if row.get("coordinate") is not None or row.get("ratified") is not False:
            errors.append(f"row {i}: unauthorized coordinate or ratification")
        if row.get("selected") is not False:
            errors.append(f"row {i}: a census entry is not a selected D10 meaning")
        decision = row.get("decision")
        if decision not in {"DUPLICATE", "DERIVED", "HOLD", "PROPOSE"}:
            errors.append(f"row {i}: missing evidence-based decision")
        if not row.get("decision_reason") or not row.get("dependency_derivability"):
            errors.append(f"row {i}: no derivability/decision evidence")
        url = row.get("donor_primary_url")
        if not isinstance(url, str) or not url.startswith("https://www.lispworks.com/documentation/HyperSpec/Body/"):
            errors.append(f"row {i}: missing source-grade CLHS primary URL")
        if row.get("donor_primary_scope") not in {"INDIVIDUAL-CLHS-ENTRY", "CLHS-9.2-SECTION-INDEX-NOT-ENTRY"}:
            errors.append(f"row {i}: source specificity unmarked")
        if not row.get("behavioral_dedup_d1_d9") or not row.get("behavioral_dedup_d10"):
            errors.append(f"row {i}: behavioral dedup not recorded")
        if decision in {"DUPLICATE", "DERIVED"} and (not row.get("semantic_law") or not row.get("falsifier")):
            errors.append(f"row {i}: duplicate/derived claim lacks falsification evidence")
        if decision == "PROPOSE":
            if row.get("clhs_kind") != "function" or not row.get("semantic_law"):
                errors.append(f"row {i}: proposed law cannot be a nameless mechanism")
            if len(row.get("two_positive_witnesses", [])) < 2 or not row.get("falsifier"):
                errors.append(f"row {i}: missing positive and falsifier witnesses")
            if row.get("d10_proposal_id") != "D10P-4896":
                errors.append(f"row {i}: untracked proposal id")
        if row.get("name_collision_is_not_behavior_proof") is not True:
            errors.append(f"row {i}: name collision overclaims behavior proof")
    acc = census.get("accounted", {})
    if (acc.get("entries") != 51 or len(rows) != 51
            or acc.get("by_kind") != counts):
        errors.append("dictionary entry/kind accounting mismatch")
    if acc.get("exact_name_D10") != sum(bool(r["d10_selected_exact_name"]) for r in rows):
        errors.append("D10 exact-name count mismatch")
    if acc.get("exact_name_lower") != sum(bool(r["d1_d9_exact_name"]) for r in rows):
        errors.append("lower exact-name count mismatch")
    if acc.get("no_exact_name") != sum(not r["d1_d9_exact_name"] and not r["d10_selected_exact_name"] for r in rows):
        errors.append("no-match count mismatch")
    if acc.get("by_decision") != decisions or acc.get("donor_primary_url_complete") != 51:
        errors.append("decision/primary URL census accounting mismatch")
    if len(proposed) != 1 or proposed[0].get("key") != TARGET:
        errors.append("only the reviewed COMPUTE-RESTARTS observation may be proposed")
    if acc.get("selected_added") != 0 or acc.get("ratified_added") != 0:
        errors.append("Census may not claim selected/ratified additions")
    if census.get("snapshot", {}).get("d10_inventory_blob") != "3db40a04c1094c9ea13b0c8d6099ef1d882cf203":
        errors.append("historical 635 census SHA changed")
    expected_decisions = {"HOLD": 50, "PROPOSE": 1, "DERIVED": 0, "DUPLICATE": 0}
    actual_decisions = {d: sum(r.get("decision") == d for r in rows) for d in expected_decisions}
    if census.get("accounted", {}).get("decision_counts") != actual_decisions or actual_decisions != expected_decisions:
        errors.append("decision map does not match reviewed 51-row census")
    if sum(r.get("decision") == "PROPOSE" and r.get("name") == "COMPUTE-RESTARTS" for r in rows) != 1:
        errors.append("first Conditions milestone missing or duplicated")
    return errors


def main() -> int:
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    # Для нового дослідницького перепису використовується саме закріплений
    # snapshot; після руху main новий batch має окреме джерело й evidence.
    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    errors = validate(census, inventory, foundation)
    mutants = [
        ("duplicate key", lambda j: j["rows"].append(copy.deepcopy(j["rows"][0]))),
        ("forged D10 name match", lambda j: j["rows"][0].update(d10_selected_exact_name=not j["rows"][0]["d10_selected_exact_name"])),
        ("forged coordinate", lambda j: j["rows"][0].update(coordinate="0" * 10)),
        ("forged ratification", lambda j: j["rows"][0].update(ratified=True)),
        ("falsified source", lambda j: j["rows"][0].update(source_index="https://invalid.example/")),
        ("false accounting", lambda j: j["accounted"].update(entries=1)),
        ("forged absent source", lambda j: j["rows"][0].update(donor_primary_url="")),
        ("unwitnessed selected proposal", lambda j: next(r for r in j["rows"] if r["name"] == "COMPUTE-RESTARTS").update(two_positive_witnesses=[])),
        ("fake derived", lambda j: j["rows"][0].update(decision="DERIVED")),
        ("missing donor", lambda j: j["rows"][0].update(donor_primary_url=None)),
        ("fake verdict", lambda j: j["rows"][0].update(decision="PROPOSE")),
        ("empty dedup", lambda j: j["rows"][0].update(behavioral_dedup="")),
        ("witness removed", lambda j: next(r for r in j["rows"] if r["key"] == TARGET).update(falsifiers=[])),
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
    print(f"D10-CLHS-CONDITIONS: PASS entries={len(census['rows'])}; "
          "ten negative controls; one pending proposal; selected_added=0, ratified_added=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
