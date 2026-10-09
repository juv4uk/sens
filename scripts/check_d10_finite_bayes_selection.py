#!/usr/bin/env python3
"""Fail-closed Bayes selection guard with an immutable snapshot and append-only growth."""
from __future__ import annotations
import copy
import csv
import hashlib
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
BAYES_POST_BLOB = "3db40a04c1094c9ea13b0c8d6099ef1d882cf203"
BAYES_PRE_BLOB = "65014431ac3e64633cd0be3630cfafc5e7a9aea3"
CAPACITY = 1024
LAW_FORCED = 256


class GateFailure(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise GateFailure(message)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob(obj):
    raw = (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def ledger_rows(ledger_text):
    return list(csv.DictReader(ledger_text.splitlines(), delimiter="\t"))


def historical_bayes_view(current, history):
    """Rewind only hash-linked, research-only append events to the immutable 635 snapshot."""
    work = copy.deepcopy(current)
    if git_blob(work) == BAYES_POST_BLOB:
        return work
    records = history.get("transitions", [])
    visited = set()
    while git_blob(work) != BAYES_POST_BLOB:
        current_blob = git_blob(work)
        require(current_blob not in visited, "cycle while rewinding to Bayes selection snapshot")
        visited.add(current_blob)
        events = [e for e in records if e.get("resulting_inventory_blob_sha") == current_blob]
        require(len(events) == 1, "live inventory differs from Bayes snapshot without a unique append event")
        event = events[0]
        n = event.get("delta_selected")
        ids = event.get("added_stable_ids", [])
        sources = event.get("appended_sources", [])
        require(isinstance(n, int) and n > 0 and n == len(ids), "invalid append event size")
        require(event.get("resulting_selected") == len(work.get("rows", [])), "append event resulting count mismatch")
        require(event.get("previous_selected", -1) + n == event.get("resulting_selected"),
                "append event count arithmetic mismatch")
        require(event.get("coordinates_added") == 0 and event.get("ratified_added") == 0,
                "later append claims coordinate or ratification authority")
        tail = work["rows"][-n:]
        require([r.get("stable_id") for r in tail] == ids, "live rows are not the declared append tail")
        for row in tail:
            require(row.get("status") == "SELECTED-RESEARCH-CANDIDATE", "later row is not research-only")
            require(row.get("coordinate") is None and row.get("coordinate_basis") == "UNPLACED",
                    "later row has a coordinate")
            require(row.get("ratified_resident") is False, "later row is ratified")
        require(isinstance(sources, list), "append source list is malformed")
        if sources:
            require(work.get("sources", [])[-len(sources):] == sources, "source path list is not append-only")
            del work["sources"][-len(sources):]
        del work["rows"][-n:]
        work["accounting"]["selected_semantic_candidates"] = event["previous_selected"]
        work["accounting"]["unplaced_selected_candidates"] = event["previous_selected"] - LAW_FORCED
        work["accounting"]["remaining_semantic_inventory"] = CAPACITY - event["previous_selected"]
        work["accounting"]["ratified_d10_residents"] = 0
        require(git_blob(work) == event.get("previous_inventory_blob_sha"),
                "previous D10 blob mismatch after append rewind")
    require(len(work["rows"]) == 635, "Bayes historical snapshot must contain 635 selected rows")
    require(work["accounting"]["selected_semantic_candidates"] == 635, "Bayes snapshot count drift")
    require(work["accounting"]["unplaced_selected_candidates"] == 379, "Bayes snapshot unplaced drift")
    require(work["accounting"]["remaining_semantic_inventory"] == 389, "Bayes snapshot capacity drift")
    require(work["accounting"]["ratified_d10_residents"] == 0, "historical D10 ratification was forged")
    return work


def verify(inv, state, foundation, dossier, ledger_text, history):
    rows = inv["rows"]
    names = [str(r.get("semantic_name", "")).upper() for r in rows]
    ids = [r.get("stable_id") for r in rows]
    require(len(names) == len(set(names)), "duplicate D10 semantic name")
    require(len(ids) == len(set(ids)), "duplicate D10 stable ID")
    count = len(rows)
    acc = inv["accounting"]
    require(acc["selected_semantic_candidates"] == count, "live selected count drift")
    require(acc["law_forced_coordinates"] == LAW_FORCED, "selector-law count changed")
    require(acc["unplaced_selected_candidates"] == count - LAW_FORCED, "live unplaced accounting drift")
    require(acc["remaining_semantic_inventory"] == CAPACITY - count, "live remaining accounting drift")
    require(acc["ratified_d10_residents"] == 0, "D10 ratification is not authorized")
    require(state["target"]["selected_semantic_candidates"] == count, "live fill-state selected count drift")
    require(state["target"]["unplaced_selected_candidates"] == count - LAW_FORCED, "live fill-state unplaced drift")
    require(state["target"]["remaining_semantic_candidates"] == CAPACITY - count, "live fill-state remaining drift")
    require(state["target"]["ratified_residents"] == 0, "live fill-state ratification must remain zero")

    snapshot = historical_bayes_view(inv, history)
    bayes_snapshot_rows = [r for r in snapshot["rows"] if r.get("stable_id") == STABLE_ID]
    live_rows = [r for r in rows if r.get("stable_id") == STABLE_ID]
    require(len(bayes_snapshot_rows) == len(live_rows) == 1, "Bayes row missing or duplicated in historical/live inventory")
    require(live_rows[0] == bayes_snapshot_rows[0], "selected Bayes row mutated after its pinned snapshot")

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
    require(row.get("ratified_resident") is False, "candidate was ratified by a selection PR")
    require(row.get("physical_t5_authorized") is False, "candidate incorrectly authorizes T5")
    require(row.get("language_visible") is True and row.get("mechanism_only") is False,
            "language visibility / mechanism classification drift")
    require(row.get("source_path") == SOURCE and SOURCE in inv["sources"], "source provenance missing")
    require(row.get("primary_url") == PRIMARY, "primary source URL drift")
    require(row.get("positive_witnesses") == dossier.get("witnesses"), "witness payload differs from donor dossier")
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
    require(len(events) == 1, "missing or duplicate Bayes append-only selection event")
    event = events[0]
    require(event.get("added_stable_ids") == [STABLE_ID], "Bayes event does not name exactly its stable ID")
    require(event.get("appended_sources") == [SOURCE], "Bayes transition source append drift")
    require(event.get("previous_selected") == 634 and event.get("resulting_selected") == 635,
            "historical Bayes transition count drift")
    require(event.get("delta_selected") == 1, "Bayes selection was not a single-row append")
    require(event.get("coordinates_added") == 0 and event.get("ratified_added") == 0,
            "Bayes event claimed coordinates/ratification")
    require(event.get("previous_inventory_blob_sha") == dossier["dedup"]["D10_before_blob"] == BAYES_PRE_BLOB,
            "Bayes transition does not begin at its reviewed 634-row snapshot")
    require(event.get("resulting_inventory_blob_sha") == BAYES_POST_BLOB,
            "Bayes transition result no longer matches the pinned 635-row snapshot")
    return {
        "historical_bayes_selected": 635,
        "live_selected": count,
        "live_unplaced": count - LAW_FORCED,
        "live_remaining": CAPACITY - count,
        "finite_bayes_rows": 1,
        "ratified": 0,
        "coordinate": None,
        "transition": TRANSITION_ID,
    }


def synthetic_append(inv, state, history):
    """Create a test-only append with a valid event to prove future selection compatibility."""
    current = copy.deepcopy(inv)
    live_state = copy.deepcopy(state)
    new_history = copy.deepcopy(history)
    previous_blob = git_blob(current)
    row = copy.deepcopy(current["rows"][-1])
    source = "knowledge/d10-test-after-bayes-append.json"
    row.update({
        "stable_id": "d10.test.after-bayes-append.v1",
        "semantic_name": "TEST-AFTER-BAYES-APPEND",
        "source_class": "TEST-ONLY",
        "source_path": source,
        "behavior": "synthetic test-only row proving append history support",
        "provenance": ["synthetic append test fixture"],
        "coordinate": None,
        "coordinate_basis": "UNPLACED",
        "ratified_resident": False,
        "physical_t5_authorized": False,
        "status": "SELECTED-RESEARCH-CANDIDATE",
        "decision": "SELECT-D10-RESEARCH-CANDIDATE",
        "proposal_status": "pending-owner-review",
    })
    current["rows"].append(row)
    current["sources"].append(source)
    current["accounting"]["selected_semantic_candidates"] += 1
    current["accounting"]["unplaced_selected_candidates"] += 1
    current["accounting"]["remaining_semantic_inventory"] -= 1
    resulting_blob = git_blob(current)
    new_history["transitions"].append({
        "id": "test.d10.after-bayes.append.v1",
        "authority": "synthetic test fixture only",
        "previous_inventory_blob_sha": previous_blob,
        "resulting_inventory_blob_sha": resulting_blob,
        "added_stable_ids": [row["stable_id"]],
        "appended_sources": [source],
        "coordinates_added": 0,
        "ratified_added": 0,
        "delta_selected": 1,
        "previous_selected": len(inv["rows"]),
        "resulting_selected": len(current["rows"]),
        "decision": "synthetic only",
    })
    live_state["target"]["selected_semantic_candidates"] += 1
    live_state["target"]["unplaced_selected_candidates"] += 1
    live_state["target"]["remaining_semantic_candidates"] -= 1
    return current, live_state, new_history


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

    later, later_state, later_history = synthetic_append(inv, state, history)
    verify(later, later_state, foundation, dossier, ledger_text, later_history)
    unrecorded, unrecorded_state, _ = synthetic_append(inv, state, history)
    try:
        verify(unrecorded, unrecorded_state, foundation, dossier, ledger_text, history)
    except GateFailure:
        pass
    else:
        raise GateFailure("unrecorded post-Bayes growth was accepted")
    print("D10-FINITE-BAYES-SELECTION: PASS; 8/8 authority mutations rejected; recorded later append accepted; unrecorded growth rejected")


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
