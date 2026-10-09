#!/usr/bin/env python3
"""Verify the immutable 635->636 GF2 selection snapshot across later append-only D10 growth."""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "knowledge/d10-v1-semantic-inventory.json"
STATE = ROOT / "knowledge/d10-fill-v1-state.json"
HISTORY = ROOT / "knowledge/d10-selection-transition-history.json"
LOWER = ROOT / "knowledge/d1-d9-foundation.json"
LEDGER = ROOT / "knowledge/d10-proposal-ledger.tsv"
DOSSIER = ROOT / "knowledge/d10-gf2-minimal-recurrence-research-v1.json"
DOC = ROOT / "docs/architecture/ARCHIPELAGO-V1.uk.md"
PRE = "3db40a04c1094c9ea13b0c8d6099ef1d882cf203"
POST = "292ef3086114ad0dfe71776c831c2a31b39352a8"
NAME = "BINARY-LFSR-MINIMAL-RECURRENCE"
STABLE = "d10.fpga.gf2.minimum-recurrence.20261009"
EVENT_ID = "d10.hobby.gf2.minimal-recurrence.after-bayes.20261009"
SOURCE = "knowledge/d10-gf2-minimal-recurrence-research-v1.json"
CAPACITY = 1024
LAW_FORCED = 256


class GateFailure(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise GateFailure(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def gitsha(obj):
    raw = (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


def rewind_to_snapshot(live, history, target_sha):
    """Reverse only explicit source-pinned append events; fail on any unrecorded drift."""
    work = copy.deepcopy(live)
    if gitsha(work) == target_sha:
        return work
    records = history.get("transitions", [])
    visited = set()
    while gitsha(work) != target_sha:
        current_sha = gitsha(work)
        require(current_sha not in visited, "cycle in D10 selection transition history")
        visited.add(current_sha)
        events = [r for r in records if r.get("resulting_inventory_blob_sha") == current_sha]
        require(len(events) == 1, "live D10 differs from the GF2 snapshot without a unique append event")
        event = events[0]
        count = event.get("delta_selected")
        ids = event.get("added_stable_ids", [])
        sources = event.get("appended_sources", [])
        require(isinstance(count, int) and count > 0 and count == len(ids),
                "later transition has invalid append size")
        require(event.get("resulting_selected") == len(work.get("rows", [])),
                "later transition resulting count differs from inventory")
        require(event.get("previous_selected", -1) + count == event.get("resulting_selected"),
                "later transition count arithmetic mismatch")
        require(event.get("coordinates_added") == 0 and event.get("ratified_added") == 0,
                "later transition adds coordinate or ratification authority")
        tail = work["rows"][-count:]
        require([r.get("stable_id") for r in tail] == ids, "live rows are not the declared append tail")
        for row in tail:
            require(row.get("status") == "SELECTED-RESEARCH-CANDIDATE",
                    "later appended row is not research-only")
            require(row.get("coordinate") is None and row.get("coordinate_basis") == "UNPLACED",
                    "later appended row is placed")
            require(row.get("ratified_resident") is False, "later appended row is ratified")
        require(isinstance(sources, list), "later transition source list is malformed")
        if sources:
            require(work.get("sources", [])[-len(sources):] == sources,
                    "live source paths are not an append-only tail")
            del work["sources"][-len(sources):]
        del work["rows"][-count:]
        work["accounting"]["selected_semantic_candidates"] = event["previous_selected"]
        work["accounting"]["unplaced_selected_candidates"] = event["previous_selected"] - LAW_FORCED
        work["accounting"]["remaining_semantic_inventory"] = CAPACITY - event["previous_selected"]
        work["accounting"]["ratified_d10_residents"] = 0
        require(gitsha(work) == event.get("previous_inventory_blob_sha"),
                "previous inventory SHA mismatch after reversing an append")
    return work


def verify(inv, state, history, low, ledger, dossier, doc):
    # Live authority is dynamic: future research appends must not invalidate this historical guard.
    live_n = len(inv["rows"])
    acc = inv["accounting"]
    require(acc.get("selected_semantic_candidates") == live_n, "live selected count drift")
    require(acc.get("law_forced_coordinates") == LAW_FORCED, "selector-law count changed")
    require(acc.get("unplaced_selected_candidates") == live_n - LAW_FORCED, "live unplaced count drift")
    require(acc.get("remaining_semantic_inventory") == CAPACITY - live_n, "live remaining count drift")
    require(acc.get("ratified_d10_residents") == 0, "D10 ratification is not authorized")
    require(state["target"].get("selected_semantic_candidates") == live_n, "live fill-state selected count drift")
    require(state["target"].get("unplaced_selected_candidates") == live_n - LAW_FORCED,
            "live fill-state unplaced count drift")
    require(state["target"].get("remaining_semantic_candidates") == CAPACITY - live_n,
            "live fill-state remaining count drift")
    require(state["target"].get("ratified_residents") == 0, "live fill-state ratification must remain zero")
    require(f"D10 selected              {live_n}/1024" in doc, "live Archipelago selected count drift")
    require(f"unplaced                  {live_n-LAW_FORCED}" in doc, "live Archipelago unplaced count drift")
    require(f"remaining                 {CAPACITY-live_n}" in doc, "live Archipelago remaining count drift")

    # Rewind post-GF2 append events, if any, to the pinned 636-row historical view.
    snap = rewind_to_snapshot(inv, history, POST)
    require(gitsha(snap) == POST, "GF2 historical snapshot SHA mismatch")
    require(len(snap["rows"]) == snap["accounting"]["selected_semantic_candidates"] == 636,
            "GF2 historical snapshot must be exactly 636 rows")
    require(snap["accounting"]["law_forced_coordinates"] == LAW_FORCED, "GF2 snapshot selector-law drift")
    require(snap["accounting"]["unplaced_selected_candidates"] == 380, "GF2 snapshot unplaced drift")
    require(snap["accounting"]["remaining_semantic_inventory"] == 388, "GF2 snapshot remaining drift")
    require(snap["accounting"]["ratified_d10_residents"] == 0, "GF2 snapshot ratification drift")
    require(snap["sources"][-1] == SOURCE, "GF2 snapshot source tail drift")
    row = snap["rows"][-1]
    require(row.get("semantic_name") == NAME and row.get("stable_id") == STABLE,
            "GF2 historical row is no longer the pinned append")
    require(row.get("source_path") == SOURCE, "GF2 source path drift")
    require(row.get("source_class") == "GF2-FINITE-RECURRENCE-HOBBY-20261009",
            "GF2 source classification drift")
    require(row.get("status") == "SELECTED-RESEARCH-CANDIDATE", "GF2 row is not research-selected")
    require(row.get("proposal_status") == "pending-owner-review", "GF2 owner review gate disappeared")
    require(row.get("ratified_resident") is False and row.get("physical_t5_authorized") is False,
            "GF2 row gained authority")
    require(row.get("coordinate") is None and row.get("coordinate_basis") == "UNPLACED",
            "GF2 row acquired a coordinate")
    live_match = [r for r in inv["rows"] if r.get("stable_id") == STABLE]
    snap_match = [r for r in snap["rows"] if r.get("stable_id") == STABLE]
    require(len(live_match) == len(snap_match) == 1, "GF2 stable ID missing or duplicated")
    require(live_match[0] == snap_match[0], "GF2 row mutated after its pinned snapshot")

    # Reverse the historical GF2 row and source, proving that every prior 635 row is unchanged.
    previous = copy.deepcopy(snap)
    del previous["rows"][-1]
    del previous["sources"][-1]
    previous["accounting"]["selected_semantic_candidates"] = 635
    previous["accounting"]["unplaced_selected_candidates"] = 379
    previous["accounting"]["remaining_semantic_inventory"] = 389
    require(gitsha(previous) == PRE, "previous 635-row D10 inventory is not byte-identical")

    events = [e for e in history["transitions"] if e.get("id") == EVENT_ID]
    require(len(events) == 1, "GF2 append event missing or duplicated")
    event = events[0]
    require(event.get("previous_inventory_blob_sha") == PRE and event.get("resulting_inventory_blob_sha") == POST,
            "GF2 transition hashes drift")
    require(event.get("previous_selected") == 635 and event.get("resulting_selected") == 636
            and event.get("delta_selected") == 1, "GF2 transition counts drift")
    require(event.get("added_stable_ids") == [STABLE] and event.get("appended_sources") == [SOURCE],
            "GF2 transition row/source tail drift")
    require(event.get("coordinates_added") == 0 and event.get("ratified_added") == 0,
            "GF2 transition minted semantic authority")

    proposals = list(csv.DictReader(io.StringIO(ledger), delimiter="\t"))
    matches = [p for p in proposals if p.get("proposal_id") == "D10P-4952"]
    require(len(matches) == 1, "GF2 proposal ledger ID missing or duplicated")
    proposal = matches[0]
    require(proposal.get("semantic_name") == NAME, "GF2 proposal name drift")
    require(proposal.get("status") == "pending-review" and proposal.get("ratified") == "0",
            "GF2 ledger claims owner ratification")
    require(proposal.get("surface_uk") == row.get("surface_uk")
            and proposal.get("surface_ukr") == row.get("surface_ukr"), "GF2 surfaces drift")
    require(proposal.get("dedup_check") ==
            f"D1-D9@09d1d71c39d1484dfd005a5068dbb18b76f0f0d4=NO-MATCH;D10@{PRE}=NO-MATCH",
            "GF2 ledger dedup snapshot drift")
    require(proposal.get("donor_provenance", "").startswith(
            "juv4uk/sens@0a05dd1caf7b8fd9cb91ebf8c0c16bdf975f4911:"),
            "GF2 donor provenance drift")

    lower_names = {str(n).upper() for d in low["domains"].values() for n in d["residents"].values()}
    require(NAME not in lower_names, "GF2 exact-name collision in ratified D1-D9")
    require(dossier["candidate"].get("semantic_name") == NAME, "GF2 donor dossier name drift")
    require(dossier["candidate"].get("coordinate") is None and dossier["candidate"].get("ratified") is False,
            "GF2 source dossier gained authority")
    require(dossier["candidate"].get("selected") is False, "immutable GF2 source dossier was rewritten as selected")
    require(row.get("positive_witnesses") and row.get("falsifiers"), "GF2 row lost witnesses/falsifiers")
    return {"historical_gf2_selected": 636, "live_selected": live_n, "live_unplaced": live_n-LAW_FORCED,
            "live_remaining": CAPACITY-live_n, "gf2_rows": 1, "ratified": 0, "coordinate": None}


def synthetic_append(inv, state, history, doc):
    """Test-only legal append transition to prove the guard supports monotonic growth."""
    current = copy.deepcopy(inv)
    new_state = copy.deepcopy(state)
    new_history = copy.deepcopy(history)
    previous_sha = gitsha(current)
    row = copy.deepcopy(current["rows"][-1])
    source = "knowledge/d10-test-gf2-guard-append.json"
    row.update({
        "stable_id": "d10.test.gf2-guard-append.v1",
        "semantic_name": "TEST-GF2-GUARD-APPEND",
        "source_class": "TEST-ONLY",
        "source_path": source,
        "behavior": "synthetic selected row used only to test historical growth",
        "provenance": ["synthetic guard fixture"],
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
    new_history["transitions"].append({
        "id": "test.d10.gf2-guard-append.v1",
        "authority": "synthetic test fixture only",
        "previous_inventory_blob_sha": previous_sha,
        "resulting_inventory_blob_sha": gitsha(current),
        "added_stable_ids": [row["stable_id"]],
        "appended_sources": [source],
        "coordinates_added": 0,
        "ratified_added": 0,
        "delta_selected": 1,
        "previous_selected": len(inv["rows"]),
        "resulting_selected": len(current["rows"]),
        "decision": "synthetic test-only append",
    })
    new_state["target"]["selected_semantic_candidates"] += 1
    new_state["target"]["unplaced_selected_candidates"] += 1
    new_state["target"]["remaining_semantic_candidates"] -= 1
    doc = doc.replace(f"D10 selected              {len(inv['rows'])}/1024",
                      f"D10 selected              {len(current['rows'])}/1024")
    doc = doc.replace(f"unplaced                  {len(inv['rows'])-LAW_FORCED}",
                      f"unplaced                  {len(current['rows'])-LAW_FORCED}")
    doc = doc.replace(f"remaining                 {CAPACITY-len(inv['rows'])}",
                      f"remaining                 {CAPACITY-len(current['rows'])}")
    return current, new_state, new_history, doc


def self_test(args):
    verify(*args)
    controls = [
        ("fake coordinate", lambda p: next(r for r in p[0]["rows"] if r["stable_id"] == STABLE).__setitem__("coordinate", "1111111111")),
        ("fake ratification", lambda p: next(r for r in p[0]["rows"] if r["stable_id"] == STABLE).__setitem__("ratified_resident", True)),
        ("old law changed", lambda p: p[0]["rows"][0].__setitem__("behavior", "tampered")),
        ("GF2 name forged", lambda p: next(r for r in p[0]["rows"] if r["stable_id"] == STABLE).__setitem__("semantic_name", "CAR")),
        ("source dropped", lambda p: p[0]["sources"].pop()),
        ("state count changed", lambda p: p[1]["target"].__setitem__("selected_semantic_candidates", 635)),
        ("transition hash changed", lambda p: next(e for e in p[2]["transitions"] if e["id"] == EVENT_ID).__setitem__("previous_inventory_blob_sha", "0"*40)),
        ("dossier claims ratification", lambda p: p[5]["candidate"].__setitem__("ratified", True)),
    ]
    for label, mutate in controls:
        p = [copy.deepcopy(x) for x in args]
        mutate(p)
        try:
            verify(*p)
        except (GateFailure, AssertionError, KeyError, TypeError):
            continue
        raise GateFailure("negative control accepted: " + label)

    grown, grown_state, grown_history, grown_doc = synthetic_append(args[0], args[1], args[2], args[6])
    verify(grown, grown_state, grown_history, args[3], args[4], args[5], grown_doc)
    unrecorded, unrecorded_state, _history, unrecorded_doc = synthetic_append(args[0], args[1], args[2], args[6])
    try:
        verify(unrecorded, unrecorded_state, args[2], args[3], args[4], args[5], unrecorded_doc)
    except (GateFailure, AssertionError, KeyError, TypeError):
        pass
    else:
        raise GateFailure("unrecorded D10 growth accepted")
    print("D10-GF2-SELECTION: PASS; 8/8 authority mutations rejected; recorded append accepted; unrecorded growth rejected")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    opts = parser.parse_args()
    args = (
        read(INV), read(STATE), read(HISTORY), read(LOWER),
        LEDGER.read_text(encoding="utf-8"), read(DOSSIER), DOC.read_text(encoding="utf-8")
    )
    try:
        if opts.self_test:
            self_test(args)
        result = verify(*args)
        print("D10-GF2-SELECTION: PASS " + json.dumps(result, sort_keys=True))
    except (GateFailure, AssertionError, KeyError, TypeError, ValueError) as error:
        print("D10-GF2-SELECTION: FAIL " + str(error), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
