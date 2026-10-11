#!/usr/bin/env python3
"""Fail-closed proof of exactly three source-backed D10 research selections.

The historical donor remains a source-only HOLD; the independently pinned 2026-10-11
admission is the only artifact changing canonical D10 SELECTED research occupancy.
This checker does not ratify any resident or issue a coordinate.
"""
from __future__ import annotations
import argparse
import copy
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = {"HADAMARD-VARIANCE", "FINITE-CONVOLUTION", "PHASE-UNWRAP"}
PIN = "7d8745cb6f183cf0c015812359a6c0f87c4c2ffb"
SOURCE_PINS = {
    "knowledge/d10-hadamard-variance-proposal-20261009.json": "617914598807262644b51ff1b51c346b7ac276f7",
    "knowledge/d10-crossdomain-math-signal-research-v1.json": "be9a340b28123d81b4203ccfbe3d1b20e707bbae",
}

def need(ok, message):
    if not ok:
        raise ValueError(message)

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def verify(proof, inv, foundation, ledger):
    need(proof.get("schema") == "d10-existing-exact-math-signal-selection/v1",
         "unexpected proof schema")
    need(proof.get("status") == "SELECTED-RESEARCH-BATCH-NO-RATIFICATION",
         "unauthorized admission")
    need(proof.get("source_d10_preselection", "").endswith("@" + PIN),
         "preselection SHA mismatch")
    need({(x["source"], x["blob"]) for x in proof["premises"]} ==
         set(SOURCE_PINS.items()), "immutable donor source mismatch")
    need(len(proof.get("selected", [])) == 3 and
         {x["semantic_name"] for x in proof["selected"]} == NAMES,
         "candidate identity mismatch")
    need(proof.get("admission") == {
        "selected_before": 655, "selected_after": 658, "selected_delta": 3,
        "unplaced_after": 402, "remaining_after": 366,
        "law_forced_placements": 256, "ratified": 0},
        "batch admission accounting mismatch")
    need(foundation.get("status") == "current-owner-ratified-D1-D9" or
         foundation.get("current_domains") == [f"D{i}" for i in range(1, 10)],
         "foundation drift")
    low = {str(x).upper() for dom in foundation["domains"].values()
           for x in dom["residents"].values()}
    need(not (low & NAMES), "current D1-D9 law collision")
    names = [r["semantic_name"] for r in inv["rows"]]
    need(len(names) == len(set(names)) and len(names) == 658, "canonical selected drift")
    need(all(x not in names[:655] for x in NAMES), "unreviewed preselection collision")
    need(set(names[-3:]) == NAMES, "append-only candidate tail corrupted")
    need(inv["accounting"].get("selected_semantic_candidates") == 658
         and inv["accounting"].get("unplaced_selected_candidates") == 402
         and inv["accounting"].get("remaining_semantic_inventory") == 366
         and inv["accounting"].get("law_forced_coordinates") == 256
         and inv["accounting"].get("ratified_d10_residents") == 0,
         "D10 occupancy/rule drift")
    need(inv["sources"][-1] == "knowledge/d10-existing-math-signal-selected-20261011.json",
         "missing source addition")
    proposals = {}
    for row in ledger:
        name = row["semantic_name"]
        if name in NAMES:
            need(name not in proposals and row["status"] == "pending-review"
                 and row["ratified"] == "0", "ledger duplicate or false ratification")
            proposals[name] = row
    need(set(proposals) == NAMES, "selected law missing from proposal ledger")
    for source in proof["selected"]:
        name = source["semantic_name"]
        row = next(r for r in inv["rows"] if r["semantic_name"] == name)
        need(row["stable_id"] == source["stable_id"], "stable identity differs")
        need(row["behavior"] == source["law"], "observed law differs")
        need(row["surface_uk"] == source["surface_uk"]
             and row["surface_ukr"] == source["surface_ukr"], "surfaces differ")
        need(row["coordinate"] is None and row["coordinate_basis"] == "UNPLACED"
             and row["ratified_resident"] is False, "false geometry or ratification")
        need(row["status"] == "SELECTED-RESEARCH-CANDIDATE", "not research selected")
        need(source["coordinate"] is None and source["ratified"] is False,
             "evidence invents placement")
        need(source["source_ref"] in SOURCE_PINS, "source outside pinned premises")
        need(row["source_class"] and row["relation_class"], "missing relation classification")
        need("knowledge/d10-existing-math-signal-selected-20261011.json" in
             row["provenance"], "source evidence missing from canonical selection")
        need(len(source["positive_witnesses"]) >= 3 and
             len(source["falsifiers"]) >= 3, "witness or falsifier omitted")
        need(source["tests"] and all((ROOT / p).is_file() for p in source["tests"]),
             "existing oracle artifact missing")
        need(source["behavioral_independence"], "missing behavioral comparison")
        need(proposals[name]["surface_uk"] == source["surface_uk"] and
             proposals[name]["surface_ukr"] == source["surface_ukr"],
             "proposal surfaces disagree")
        need("D1-D9@" in proposals[name]["dedup_check"] and
             "D10@" in proposals[name]["dedup_check"],
             "dedup reference disappeared")
        need(proposals[name]["semantic_law"], "empty ledger semantic law")
    return {"selected": 658, "added": 3, "proof_forced": 256,
            "unplaced": 402, "remaining": 366, "ratified": 0}

def negative_controls(proof, inventory, foundation, ledger):
    changes = [
        ("false coordinate", lambda p, i, f, l: i["rows"][-1].__setitem__("coordinate", "0000000000")),
        ("false ratification", lambda p, i, f, l: i["rows"][-2].__setitem__("ratified_resident", True)),
        ("law mutation", lambda p, i, f, l: i["rows"][-3].__setitem__("behavior", "false law")),
        ("preselection SHA mutation", lambda p, i, f, l: p.__setitem__("source_d10_preselection", "inventory@bad")),
        ("source evidence deletion", lambda p, i, f, l: p["premises"].pop()),
        ("missing candidate", lambda p, i, f, l: p["selected"].pop()),
        ("missing ledger entry", lambda p, i, f, l: l.pop(next(k for k, v in enumerate(l) if v["semantic_name"] == "PHASE-UNWRAP"))),
        ("canonical forged occupancy", lambda p, i, f, l: i["accounting"].__setitem__("selected_semantic_candidates", 1024)),
    ]
    for label, edit in changes:
        p, i, f, l = copy.deepcopy(proof), copy.deepcopy(inventory), copy.deepcopy(foundation), copy.deepcopy(ledger)
        edit(p, i, f, l)
        try:
            verify(p, i, f, l)
        except (ValueError, KeyError, IndexError, TypeError):
            continue
        raise RuntimeError("unsafe mutation accepted: " + label)
    return len(changes)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    proof = read("knowledge/d10-existing-math-signal-selected-20261011.json")
    inv = read("knowledge/d10-v1-semantic-inventory.json")
    foundation = read("knowledge/d1-d9-foundation.json")
    with (ROOT / "knowledge/d10-proposal-ledger.tsv").open(encoding="utf-8", newline="") as fh:
        ledger = list(csv.DictReader(fh, delimiter="\t"))
    results = verify(proof, inv, foundation, ledger)
    if args.self_test:
        results["rejected_mutations"] = negative_controls(proof, inv, foundation, ledger)
    print(json.dumps(results, sort_keys=True))

if __name__ == "__main__":
    main()
