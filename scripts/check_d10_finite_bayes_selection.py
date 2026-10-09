#!/usr/bin/env python3
"""Fail-closed guard for the one-row finite Bayesian update D10 selection."""
from __future__ import annotations
import copy
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
STATE = ROOT / "knowledge/d10-fill-v1-state.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
DOSSIER = ROOT / "knowledge/d10-finite-bayes-update-research-v1.json"
LEDGER = ROOT / "knowledge/d10-proposal-ledger.tsv"
HISTORY = ROOT / "knowledge/d10-selection-transition-history.json"
NAME = "FINITE-BAYES-UPDATE-EXACT"
STABLE_ID = "d10.math.finite-bayes-update-exact.20261009"
TRANSITION_ID = "d10.hobby.finite-bayes-update-exact.20261009"
SOURCE = "knowledge/d10-finite-bayes-update-research-v1.json"
PRIMARY = "https://plato.stanford.edu/entries/epistemology-bayesian/"

class GateFailure(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise GateFailure(message)

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def ledger_rows(ledger_text):
    return list(csv.DictReader(ledger_text.splitlines(), delimiter="\t"))

def verify(inv, state, foundation, dossier, ledger_text, history):
    rows = inv["rows"]
    names = [str(r.get("semantic_name", "")).upper() for r in rows]
    ids = [r.get("stable_id") for r in rows]
    require(len(names) == len(set(names)), "duplicate D10 semantic name")
    require(len(ids) == len(set(ids)), "duplicate D10 stable ID")
    count = len(rows)
    acc = inv["accounting"]
    require(acc["selected_semantic_candidates"] == count, "live selected count drift")
    require(acc["law_forced_coordinates"] == 256, "selector-law count changed")
    require(acc["unplaced_selected_candidates"] == count - 256, "unplaced accounting drift")
    require(acc["remaining_semantic_inventory"] == 1024 - count, "remaining accounting drift")
    require(acc["ratified_d10_residents"] == 0, "D10 ratification is not authorized")
    require(state["target"]["selected_semantic_candidates"] == count, "fill-state selected count drift")
    require(state["target"]["unplaced_selected_candidates"] == count - 256, "fill-state unplaced drift")
    require(state["target"]["remaining_semantic_candidates"] == 1024 - count, "fill-state remaining drift")
    require(state["target"]["ratified_residents"] == 0, "fill-state ratification must remain zero")
    lower_names = {
        str(name).upper()
        for domain in foundation["domains"].values()
        for name in domain["residents"].values()
    }
    require(NAME not in lower_names, "D1-D9 exact-name collision")
    matching = [r for r in rows if str(r.get("semantic_name", "")).upper() == NAME]
    require(len(matching) == 1, "expected exactly one selected finite Bayesian update row")
    row = matching[0]
    require(row.get("stable_id") == STABLE_ID, "stable ID drift")
    require(row.get("status") == "SELECTED-RESEARCH-CANDIDATE", "candidate status drift")
    require(row.get("decision") == "SELECT-D10-RESEARCH-CANDIDATE", "research selection decision drift")
    require(row.get("proposal_status") == "pending-owner-review", "owner review was bypassed")
    require(row.get("coordinate") is None and row.get("coordinate_basis") == "UNPLACED",
            "finite Bayesian candidate was assigned a coordinate")
    require(row.get("donor_coordinate_authority") == "NONE", "donor coordinates imported")
    require(row.get("ratified_resident") is False, "candidate was ratified by the selection PR")
    require(row.get("physical_t5_authorized") is False, "candidate incorrectly authorizes T5")
    require(row.get("language_visible") is True and row.get("mechanism_only") is False,
            "language visibility / mechanism classification drift")
    require(row.get("source_path") == SOURCE and SOURCE in inv["sources"], "source provenance missing")
    require(row.get("primary_url") == PRIMARY, "primary source URL drift")
    require(row.get("positive_witnesses") == dossier.get("witnesses"), "witness payload differs from reviewed dossier")
    require(len(row.get("falsifiers", [])) >= 4, "too few recorded falsifiers")
    require("PENDING-OWNER-REVIEW" in row.get("derivability_review", ""),
            "Core-vs-library derivability caveat disappeared")
    require(dossier.get("selected") is False and dossier.get("ratified") is False,
            "original source dossier snapshot must remain proposal-only")
    require(dossier.get("coordinate") is None and dossier.get("physical_t5_authorized") is False,
            "source dossier gained coordinate/T5 authority")
    proposals = [r for r in ledger_rows(ledger_text) if r.get("semantic_name", "").upper() == NAME]
    require(len(proposals) == 1, "expected one proposal-ledger row for the candidate")
    require(proposals[0].get("width") == "D10", "proposal width is not D10")
    require(proposals[0].get("ratified") == "0", "proposal ledger claims ratification")
    events = [e for e in history["transitions"] if e.get("id") == TRANSITION_ID]
    require(len(events) == 1, "missing or duplicate append-only selection event")
    event = events[0]
    require(event.get("added_stable_ids") == [STABLE_ID], "transition does not name exactly this stable ID")
    require(event.get("appended_sources") == [SOURCE], "transition source append drift")
    require(event.get("previous_selected") == 634 and event.get("resulting_selected") == 635,
            "historical transition count drift")
    require(event.get("delta_selected") == 1, "selection was not a single-row append")
    require(event.get("coordinates_added") == 0 and event.get("ratified_added") == 0,
            "selection event claimed coordinates/ratification")
    require(event.get("previous_inventory_blob_sha") == dossier["dedup"]["D10_before_blob"],
            "transition does not begin at the reviewed 634-row snapshot")
    require(event.get("resulting_inventory_blob_sha") and len(event["resulting_inventory_blob_sha"]) == 40,
            "transition lacks the canonical resulting inventory SHA")
    return {"selected": count, "unplaced": count-256, "remaining": 1024-count,
            "finite_bayes_rows": 1, "ratified": 0, "coordinate": None, "transition": TRANSITION_ID}

def self_test(inv, state, foundation, dossier, ledger_text, history):
    verify(inv, state, foundation, dossier, ledger_text, history)
    controls = [
      ("fake coordinate", lambda i, s, d, h: next(r for r in i["rows"] if r["stable_id"] == STABLE_ID).update({"coordinate":"1111111111"})),
      ("fake ratification", lambda i, s, d, h: next(r for r in i["rows"] if r["stable_id"] == STABLE_ID).update({"ratified_resident":True})),
      ("fake T5", lambda i, s, d, h: next(r for r in i["rows"] if r["stable_id"] == STABLE_ID).update({"physical_t5_authorized":True})),
      ("lost falsifier", lambda i, s, d, h: next(r for r in i["rows"] if r["stable_id"] == STABLE_ID).update({"falsifiers":[]})),
      ("forgot derivability HOLD", lambda i, s, d, h: next(r for r in i["rows"] if r["stable_id"] == STABLE_ID).update({"derivability_review":"proven irreducible"})),
      ("missing provenance", lambda i, s, d, h: i["sources"].remove(SOURCE)),
      ("wrong accounting", lambda i, s, d, h: i["accounting"].update({"remaining_semantic_inventory":1024})),
      ("fake transition delta", lambda i, s, d, h: next(e for e in h["transitions"] if e["id"] == TRANSITION_ID).update({"delta_selected":2})),
    ]
    for label, mutate in controls:
        i, st, ds, hs = copy.deepcopy(inv), copy.deepcopy(state), copy.deepcopy(dossier), copy.deepcopy(history)
        mutate(i, st, ds, hs)
        try:
            verify(i, st, foundation, ds, ledger_text, hs)
        except GateFailure:
            continue
        raise GateFailure("negative control accepted: " + label)
    print("D10-FINITE-BAYES-SELECTION: PASS; 8/8 negative mutations rejected")

def main():
    inv, state, foundation, dossier, history = (
        load(INVENTORY), load(STATE), load(FOUNDATION), load(DOSSIER), load(HISTORY)
    )
    ledger_text = LEDGER.read_text(encoding="utf-8")
    try:
        if sys.argv[1:] == ["--self-test"]:
            self_test(inv, state, foundation, dossier, ledger_text, history)
        result = verify(inv, state, foundation, dossier, ledger_text, history)
        print("D10-FINITE-BAYES-SELECTION: PASS " + json.dumps(result, sort_keys=True))
        return 0
    except (GateFailure, KeyError, ValueError, TypeError) as error:
        print("D10-FINITE-BAYES-SELECTION: FAIL " + str(error), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
