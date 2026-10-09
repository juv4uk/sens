#!/usr/bin/env python3
"""Fail-closed cross-domain evidence gate for D10 FIND-METHOD. No ratification."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "knowledge/d10-find-method-selection-v1.json"
INVENTORY = "knowledge/d10-v1-semantic-inventory.json"
STATE = "knowledge/d10-fill-v1-state.json"
FOUNDATION = "knowledge/d1-d9-foundation.json"
DONOR = "knowledge/d10-historical-clos-interlisp-residual-review-v1.json"

class ContractError(ValueError):
    pass

def require(ok, why):
    if not ok:
        raise ContractError(why)

def find_exact_method(methods, required_arity, qualifiers, specializers, errorp=True):
    """Small independent reference model, NOT SENS's implementation."""
    if len(specializers) != required_arity:
        raise ContractError("wrong required-specializer arity")
    for method in methods:
        if tuple(method["qualifiers"]) == tuple(qualifiers) and tuple(method["specializers"]) == tuple(specializers):
            return method
    if errorp:
        raise LookupError("exact method absent")
    return None

def audit(manifest, inventory, state, foundation, dossier):
    require(manifest["schema"] == "d10-find-method-selection-v1/v1", "manifest schema")
    require(manifest["candidate_selection_increment"] == 1, "must select only 1")
    require(manifest["ratified_increment"] == 0 and manifest["physical_t5_authorized"] is False, "no ratification/T5")
    require(manifest["admission"]["coordinate"] is None and manifest["admission"]["ratified_resident"] is False, "no coordinate/ratification")
    names = [r["semantic_name"].upper() for r in inventory["rows"]]
    require(len(names) == len(set(names)) == inventory["accounting"]["selected_semantic_candidates"], "inventory names/count/duplicates")
    require("FIND-METHOD" in names and names.count("FIND-METHOD") == 1, "FIND-METHOD missing/duplicated")
    lower = {str(n).upper() for d in foundation["domains"].values() for n in d.get("residents",{}).values()}
    require("FIND-METHOD" not in lower, "D1-D9 identity collision")
    row = next(r for r in inventory["rows"] if r["semantic_name"].upper()=="FIND-METHOD")
    require(row["stable_id"] == manifest["stable_id"], "identity drift")
    require(row["status"] == "SELECTED-RESEARCH-CANDIDATE", "selected research status")
    require(row["source_class"] == "HISTORICAL-CLOS-EXACT-METHOD-LOOKUP", "source class")
    require(row["coordinate"] is None and row["coordinate_basis"] == "UNPLACED" and row["ratified_resident"] is False, "no slot minted")
    require(row["proposal_status"] == "pending-owner-review", "owner review must remain")
    require(row["historical_source"] == manifest["historical_primary"]["url"], "historic source changed")
    source = next((r for r in dossier["rows"] if r["proposal_id"]=="CLOS-01"), None)
    require(source is not None and source["historical_name"]=="FIND-METHOD", "original dossier missing")
    require(source["historical_source"] == row["historical_source"], "source URL drift")
    require(source["selected_in_d10"] is False, "original evidence dossier must be kept nonnormative")
    a, s = inventory["accounting"], state["target"]
    require(s["selected_semantic_candidates"] == a["selected_semantic_candidates"] == len(names), "two ledgers disagree")
    require(s["remaining_semantic_candidates"] == a["remaining_semantic_inventory"] == 1024-len(names), "remaining ledger drift")
    require(s["ratified_residents"] == a["ratified_d10_residents"] == 0, "ratification was smuggled")
    require(s["law_forced_coordinates"] == a["law_forced_coordinates"] == 256, "law-forced selector geometry drift")
    require(s["unplaced_selected_candidates"] == a["unplaced_selected_candidates"] == len(names)-256, "unplaced accounting drift")
    require(len(names) >= 626, "baseline not incremented")
    require(MANIFEST in inventory.get("sources",[]), "manifest not linked")
    return {"selected":len(names),"unplaced":len(names)-256,"remaining":1024-len(names),"ratified":0}

def main():
    read = lambda name: json.loads((ROOT/name).read_text(encoding="utf-8"))
    result = audit(read(MANIFEST),read(INVENTORY),read(STATE),read(FOUNDATION),read(DONOR))
    print("D10-FIND-METHOD-SELECTED-RESEARCH PASS", json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
