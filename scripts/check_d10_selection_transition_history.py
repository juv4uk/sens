#!/usr/bin/env python3
"""Prove selected D10 inventory grew by append-only, source-pinned transitions.

The pinned 625-row Git blob remains an *immutable historical fact*. We rewind
the current JSON by the explicitly logged appended rows/sources/count deltas
and require the reconstructed original Git SHA-1 to match. This makes
previously archived source ledgers compatible with legitimate future selections
without silently re-pinning their original SHA to moving main.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORY = "knowledge/d10-selection-transition-history.json"
INVENTORY = "knowledge/d10-v1-semantic-inventory.json"

class TransitionFailure(Exception):
    pass

def require(ok, message):
    if not ok:
        raise TransitionFailure(message)

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def git_blob_sha(obj):
    payload = (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\x00" + payload).hexdigest()

def verify_history(current, history):
    require(history["schema"] == "d10-selection-transition-history/v1", "history schema changed")
    require(history["status"] == "RESEARCH-ONLY-NO-RATIFICATION", "history promoted to ratified")
    transitions = history["transitions"]
    require(isinstance(transitions, list) and len(transitions) >= 1, "transition history missing")
    require(len({x["id"] for x in transitions}) == len(transitions), "duplicate transition id")
    rewind = copy.deepcopy(current)
    observed_current_blob = git_blob_sha(rewind)
    original_rows = len(rewind["rows"])
    for record in reversed(transitions):
        require(git_blob_sha(rewind) == record["resulting_inventory_blob_sha"],
                "transition resulting SHA mismatch " + record["id"])
        ids = record["added_stable_ids"]
        sources = record["appended_sources"]
        n = record["delta_selected"]
        require(n == len(ids) and n > 0, "selected delta disagrees with appended ids")
        require(len(ids) == len(set(ids)), "duplicate new stable IDs")
        require(rewind["accounting"]["selected_semantic_candidates"] == record["resulting_selected"],
                "selected accounting inconsistent with transition")
        require(record["previous_selected"] + n == record["resulting_selected"],
                "transition selected arithmetic invalid")
        require(record["coordinates_added"] == 0 and record["ratified_added"] == 0,
                "unapproved coordinates/ratifications")
        new_rows = rewind["rows"][-n:]
        require([r["stable_id"] for r in new_rows] == ids, "not an append-only selected row sequence")
        for row in new_rows:
            require(row["status"] == "SELECTED-RESEARCH-CANDIDATE", "new row isn't research only")
            require(row["ratified_resident"] is False, "new row ratified without owner")
            require(row["coordinate"] is None and row["coordinate_basis"] == "UNPLACED",
                    "new row placed without law")
        require(rewind["sources"][-len(sources):] == sources if sources else True,
                "new source list not appended exactly")
        if sources:
            del rewind["sources"][-len(sources):]
        del rewind["rows"][-n:]
        acc = rewind["accounting"]
        acc["selected_semantic_candidates"] -= n
        acc["unplaced_selected_candidates"] -= n
        acc["remaining_semantic_inventory"] += n
        require(git_blob_sha(rewind) == record["previous_inventory_blob_sha"],
                "old archive SHA mismatch after reversion " + record["id"])
    baseline = history["baseline"]
    require(git_blob_sha(rewind) == baseline["inventory_blob_sha"], "original pinned archival Git SHA changed")
    require(len(rewind["rows"]) == baseline["selected_count"], "archive selected size changed")
    require(rewind["accounting"]["law_forced_coordinates"] == baseline["selector_coordinates"],
            "fixed selector geometry changed")
    require(rewind["accounting"]["ratified_d10_residents"] == baseline["ratified_d10_residents"] == 0,
            "ratification forged")
    require(original_rows == current["accounting"]["selected_semantic_candidates"],
            "live selected count drift")
    require(current["accounting"]["remaining_semantic_inventory"] == 1024 - original_rows,
            "live capacity drift")
    return {"live_sha": observed_current_blob, "baseline_sha": baseline["inventory_blob_sha"],
            "baseline_count": baseline["selected_count"], "live_count": original_rows,
            "transition_ids": [x["id"] for x in transitions]}

def negative_tests(inv, history):
    verify_history(inv, history)
    controls = [
      ("old law edited", lambda i, h: i["rows"][3].update({"behavior": "FORGED"})),
      ("old position edited", lambda i, h: i["rows"][80].update({"coordinate": "0000000000"})),
      ("new id edited", lambda i, h: i["rows"][-1].update({"stable_id": "FORGED"})),
      ("new row legalized", lambda i, h: i["rows"][-1].update({"ratified_resident": True})),
      ("new bit invented", lambda i, h: i["rows"][-1].update({"coordinate": "1111111111"})),
      ("source dropped", lambda i, h: i["sources"].pop()),
      ("count fudged", lambda i, h: i["accounting"].update({"selected_semantic_candidates": 1024})),
      ("transition mutated", lambda i, h: h["transitions"][-1].update({"previous_inventory_blob_sha": "0"*40})),
    ]
    for label, change in controls:
        a, b = copy.deepcopy(inv), copy.deepcopy(history)
        change(a, b)
        try:
            verify_history(a, b)
        except TransitionFailure:
            continue
        raise TransitionFailure("negative mutation escaped: " + label)
    print("D10-APPEND-ONLY: PASS 8/8 mutation controls rejected")

if __name__ == "__main__":
    inventory, history = read(INVENTORY), read(HISTORY)
    try:
        result = verify_history(inventory, history)
        if sys.argv[1:] == ["--self-test"]:
            negative_tests(inventory, history)
        print("D10-APPEND-ONLY: PASS " + json.dumps(result, ensure_ascii=False, sort_keys=True))
    except TransitionFailure as e:
        print("D10-APPEND-ONLY: FAIL " + str(e), file=sys.stderr)
        sys.exit(1)
