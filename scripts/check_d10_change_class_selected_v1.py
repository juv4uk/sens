#!/usr/bin/env python3
"""Fail-closed D10 CHANGE-CLASS source/inventory proof; never ratifies a resident."""
from __future__ import annotations
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "knowledge/d10-change-class-selection-v1.json"
INVENTORY = "knowledge/d10-v1-semantic-inventory.json"
STATE = "knowledge/d10-fill-v1-state.json"
FOUNDATION = "knowledge/d1-d9-foundation.json"
DONOR = "knowledge/d10-historical-clos-interlisp-residual-review-v1.json"
HISTORY = "knowledge/d10-selection-transition-history.json"
LEDGER = "knowledge/d10-proposal-ledger.tsv"
EXPECTED_PRIOR = "7e13e929338baeef9b16c2139d24b78e23ea1e03"
EXPECTED_CURRENT = "ceb4b834020e9f91da632e3fcff2adbe95d86ab7"
EXPECTED_STABLE_ID = "d10.historical.clos.change-class.c03"
EXPECTED_URL = "https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/stagenfun_change-class.html"

class ContractError(ValueError):
    pass

def require(ok, why):
    if not ok:
        raise ContractError(why)

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def audit(manifest, inventory, state, foundation, donor, ledger_text, history, inventory_bytes):
    require(manifest.get("schema") == "d10-change-class-selection-v1/v1", "manifest schema")
    require(manifest.get("semantic_name") == "CHANGE-CLASS", "semantic identity")
    sel = manifest["selection"]
    require((sel["selected_prior"], sel["selected_after"], sel["delta_selected"]) == (647, 648, 1), "selection must be exactly 647→648")
    require(sel["coordinate"] is None and sel["ratified_added"] == sel["ratified_residents_after"] == 0, "no coordinate or ratification")
    require(sel["physical_t5_authorized"] is False, "no physical T5 authority")
    dedup = manifest["dedup"]
    require(dedup["lower_foundation_blob_sha"] == "09d1d71c39d1484dfd005a5068dbb18b76f0f0d4", "lower foundation pin drift")
    require(dedup["prior_inventory_blob_sha"] == EXPECTED_PRIOR, "prior inventory pin drift")

    rows = inventory.get("rows", [])
    names = [str(r.get("semantic_name", "")).upper() for r in rows]
    require(len(names) == len(set(names)), "duplicate selected D10 names")
    require(len(rows) == inventory.get("accounting", {}).get("selected_semantic_candidates") == 648, "inventory count mismatch")
    require(names.count("CHANGE-CLASS") == 1, "CHANGE-CLASS missing/duplicated")
    lower = {str(n).upper() for d in foundation.get("domains", {}).values() for n in d.get("residents", {}).values()}
    require("CHANGE-CLASS" not in lower, "lower-domain identity collision")
    row = next(r for r in rows if str(r.get("semantic_name", "")).upper() == "CHANGE-CLASS")
    require(row.get("stable_id") == EXPECTED_STABLE_ID == manifest.get("stable_id"), "stable identity drift")
    require(row.get("status") == "SELECTED-RESEARCH-CANDIDATE", "row not research-only")
    require(row.get("coordinate") is None and row.get("coordinate_basis") == "UNPLACED", "coordinate was assigned")
    require(row.get("ratified_resident") is False and row.get("physical_t5_authorized") is False, "row gained authority")
    require(row.get("surface_uk") == "змінити-клас-об’єкта" and row.get("surface_ukr") == "перевести-екземпляр-у-клас", "Ukrainian surfaces drift")
    require(row.get("historical_source") == EXPECTED_URL, "primary source drift")
    require(row.get("source_path") == MANIFEST and MANIFEST in inventory.get("sources", []), "manifest source link missing")
    require(manifest["provenance"]["dossier_blob_sha"] == "df8ed73011df39f9ec689046ce6936cc00892215", "source dossier pin drift")

    source_rows = [r for r in donor.get("rows", []) if r.get("proposal_id") == "CLOS-03"]
    require(len(source_rows) == 1, "CLOS-03 primary dossier row missing/duplicated")
    src = source_rows[0]
    require(src.get("historical_name") == "CHANGE-CLASS" and src.get("historical_source") == EXPECTED_URL, "CLOS-03 law/source mismatch")
    require(src.get("selected_in_d10") is False and src.get("coordinate") is None and src.get("ratified") is False, "historical dossier must remain nonnormative")

    a = inventory["accounting"]
    t = state["target"]
    require(t.get("selected_semantic_candidates") == a.get("selected_semantic_candidates") == 648, "state/inventory selected mismatch")
    require(t.get("remaining_semantic_candidates") == a.get("remaining_semantic_inventory") == 376, "state/inventory remaining mismatch")
    require(t.get("unplaced_selected_candidates") == a.get("unplaced_selected_candidates") == 392, "state/inventory unplaced mismatch")
    require(t.get("law_forced_coordinates") == a.get("law_forced_coordinates") == 256, "law-forced geometry changed")
    require(t.get("ratified_residents") == a.get("ratified_d10_residents") == 0, "ratification was smuggled")
    sr = state.get("change_class_historical_v1", {})
    require(sr.get("previous_selected") == 647 and sr.get("resulting_selected") == 648, "state transition record missing")

    ledger = list(csv.DictReader(io.StringIO(ledger_text), delimiter="\t"))
    matches = [r for r in ledger if r.get("semantic_name", "").strip().upper() == "CHANGE-CLASS"]
    require(len(matches) == 1, "proposal ledger row missing/duplicated")
    ent = matches[0]
    require(ent.get("proposal_id") == "D10P-0902" and ent.get("width") == "D10", "proposal id/domain mismatch")
    require(ent.get("surface_uk") == row["surface_uk"] and ent.get("surface_ukr") == row["surface_ukr"], "ledger surface mismatch")
    require(ent.get("status") == "pending-review" and ent.get("ratified") == "0", "ledger cannot ratify itself")
    require(ent.get("blocked_source") == "NOT-A-MIGRATION-BLOCK", "invented migration blocker")
    require(ent.get("donor_provenance", "").startswith("juv4uk/sens@c67db6cdd820dea8d3a110caed359507c0a2d7a4:knowledge/d10-historical-clos-interlisp-residual-review-v1.json:"), "donor commit/path pin missing")
    require(f"D1-D9@{dedup['lower_foundation_blob_sha']}=NO-MATCH;D10@{EXPECTED_PRIOR}=NO-MATCH" == ent.get("dedup_check"), "dedup must pin pre-selection snapshots")

    require(git_blob_sha(inventory_bytes) == EXPECTED_CURRENT, "canonical inventory blob differs from reviewed SHA")
    trs = history.get("transitions", [])
    require(bool(trs), "transition history missing")
    last = trs[-1]
    require(last.get("id") == "d10.historical.clos.change-class.c03.current-main.20261011", "selection history is not append-only for CHANGE-CLASS")
    require(last.get("previous_inventory_blob_sha") == EXPECTED_PRIOR and last.get("resulting_inventory_blob_sha") == EXPECTED_CURRENT, "transition SHA chain mismatch")
    require(last.get("added_stable_ids") == [EXPECTED_STABLE_ID] and last.get("appended_sources") == [MANIFEST], "transition rows/source mismatch")
    require(last.get("previous_selected") == 647 and last.get("resulting_selected") == 648 and last.get("delta_selected") == 1, "transition arithmetic mismatch")
    require(last.get("coordinates_added") == last.get("ratified_added") == 0, "transition altered authority")
    return {"selected":648,"unplaced":392,"remaining":376,"ratified":0,"inventory_blob_sha":EXPECTED_CURRENT,"proposal_rows":len(ledger)}

def main():
    read = lambda p: json.loads((ROOT/p).read_text(encoding="utf-8"))
    raw = (ROOT/INVENTORY).read_bytes()
    result = audit(read(MANIFEST), read(INVENTORY), read(STATE), read(FOUNDATION), read(DONOR),
                   (ROOT/LEDGER).read_text(encoding="utf-8"), read(HISTORY), raw)
    print("D10-CHANGE-CLASS-SELECTED-RESEARCH PASS " + json.dumps(result, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
