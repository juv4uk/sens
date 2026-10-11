#!/usr/bin/env python3
"""Strict source-pinned D10 combinatorial research selection, no coordinates/ratification.

Historical source-era HOLD records remain immutable; only an independent admission
dossier can establish the selected-but-unplaced status at current D10 head.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESELECT_SHA = "d3d913ea48730f21764903860444f437b4e111be"
SOURCE_BLOBS = {
    "DE-BRUIJN-BINARY-CYCLE?": "9c989ef46a7fc2798a21267a92a7d8690ecaad84",
    "BINARY-LYNDON-FACTORIZATION": "7c7633e2e1041075bf589937e0b4f6ce72be0dcd",
    "STERN-BROCOT-RUN-PATH": "37cd7d1e77881d0818641d04c8d8b2ac4a605892",
}

def need(condition, message):
    if not condition:
        raise ValueError(message)

def get(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def source_bundle():
    return get("knowledge/d10-existing-combinatorial-laws-selected-20261011.json")

def verify_promoted(name, row, proof=None):
    proof = proof if proof is not None else source_bundle()
    need(proof.get("status") == "SOURCE-PINNED-RESEARCH-SELECTED-NO-RATIFICATION",
         "unapproved proof-bundle status")
    need(proof.get("preselection_inventory_blob") == PRESELECT_SHA,
         "preselection snapshot mismatch")
    claims = [r for r in proof["records"] if r["semantic_name"] == name]
    need(len(claims) == 1, "no unique promotion witness: " + name)
    claim = claims[0]
    need(SOURCE_BLOBS[name] == claim["source_git_blob"], "donor git blob drift")
    need(claim["research_selected"] is True and claim["coordinate"] is None
         and claim["ratified"] is False, "evidence pretends to ratify or place")
    need(row.get("stable_id") == claim["stable_id"] and
         row.get("behavior") == claim["law"], "canonical selected law differs")
    need(row.get("coordinate") is None and row.get("coordinate_basis") == "UNPLACED"
         and row.get("ratified_resident") is False,
         "unproved coordinate or ratification")
    need(row.get("status") == "SELECTED-RESEARCH-CANDIDATE", "not research selected")
    need("knowledge/d10-existing-combinatorial-laws-selected-20261011.json" in
         row.get("provenance", []), "no linked admission artifact")
    need(row.get("historical_source_blob") == claim["source_git_blob"],
         "source provenance lost")
    return claim

def verify(proof, inventory, foundation, ledger):
    need(proof.get("schema") == "d10-existing-combinatorial-laws-selection/v1",
         "wrong proof schema")
    need(proof.get("status") == "SOURCE-PINNED-RESEARCH-SELECTED-NO-RATIFICATION",
         "evidence status drift")
    need(proof.get("preselection_inventory_blob") == PRESELECT_SHA,
         "preselection SHA drift")
    need(proof.get("ratified_d1_d9_blob") ==
         "09d1d71c39d1484dfd005a5068dbb18b76f0f0d4", "ratified foundation snapshot drift")
    need(proof.get("accounting") == {
        "previous_selected": 658, "added": 3, "next_selected": 661,
        "remaining": 363, "forced_coordinates": 256,
        "unplaced_selected": 405, "ratified": 0,
    }, "selection accounting corrupted")
    need(len(proof.get("records", [])) == 3 and
         {x["semantic_name"] for x in proof["records"]} == set(SOURCE_BLOBS),
         "candidate set tampered")
    selected = inventory["rows"]
    need(len(selected) == 661 and
         {r["semantic_name"] for r in selected[-3:]} == set(SOURCE_BLOBS),
         "canonical append-only suffix changed")
    need(len({x["stable_id"] for x in selected}) == len(selected)
         and len({x["semantic_name"] for x in selected}) == len(selected),
         "selected identity duplicated")
    need(inventory["sources"][-1] ==
         "knowledge/d10-existing-combinatorial-laws-selected-20261011.json",
         "inventory source tail absent")
    need(inventory["accounting"] == {
        "selected_semantic_candidates": 661,
        "law_forced_coordinates": 256,
        "unplaced_selected_candidates": 405,
        "remaining_semantic_inventory": 363,
        "ratified_d10_residents": 0,
    }, "canonical accounting drift")
    lower = {str(x).upper() for d in foundation["domains"].values()
             for x in d["residents"].values()}
    need(not (lower & set(SOURCE_BLOBS)), "ratified D1-D9 exact collision")
    candidates = {x["semantic_name"]: x for x in selected[-3:]}
    proposals = [x for x in ledger if x["semantic_name"] in SOURCE_BLOBS]
    need(len(proposals) == 3 and
         {x["semantic_name"] for x in proposals} == set(SOURCE_BLOBS),
         "no unique proposal for each selected law")
    for name, row in candidates.items():
        evidence = verify_promoted(name, row, proof)
        need(len(evidence["positive_witnesses"]) >= 4 and
             len(evidence["falsifiers"]) >= 4, "inadequate positive/negative witnesses")
        need(evidence.get("distinct_from"), "no behavioral neighbor comparison")
        need(all((ROOT / t).is_file() for t in evidence["oracle_scripts"]),
             "missing existing oracle scripts")
        p = next(x for x in proposals if x["semantic_name"] == name)
        need(p["status"] == "pending-review" and p["ratified"] == "0",
             "unapproved ledger ratification")
        need(p["surface_uk"] == evidence["surface_uk"]
             and p["surface_ukr"] == evidence["surface_ukr"],
             "proposal surface mismatch")
        need("D1-D9@" in p["dedup_check"] and
             f"D10@{PRESELECT_SHA}=NO-MATCH" in p["dedup_check"],
             "historical preselection semantic dedup pin missing")
    excludes = proof.get("exclusions", [])
    need(len(excludes) == 1 and
         excludes[0]["semantic_name"] == "EXACT-SYMMETRIC-SQUARED-CHAMFER"
         and excludes[0]["status"] == "HOLD-CORE-VS-LIBRARY",
         "source-HOLD contrary to dossier")
    return {"selected": 661, "added": 3, "placed": 256,
            "unplaced": 405, "remaining": 363, "ratified": 0}

def adversarial(proof, inv, lower, ledger):
    tests = [
        ("wrong source", lambda p, i, f, l: p["records"][0].__setitem__("source_git_blob", "0"*40)),
        ("invent coordinate", lambda p, i, f, l: i["rows"][-1].__setitem__("coordinate", "1111111111")),
        ("ratify without owner", lambda p, i, f, l: i["rows"][-2].__setitem__("ratified_resident", True)),
        ("break law", lambda p, i, f, l: i["rows"][-3].__setitem__("behavior", "wrong")),
        ("omit original proof", lambda p, i, f, l: p["records"].pop()),
        ("forge ledger pin", lambda p, i, f, l: next(x for x in l if x["semantic_name"] == "STERN-BROCOT-RUN-PATH").__setitem__("dedup_check", "PENDING")),
        ("forge selected count", lambda p, i, f, l: i["accounting"].__setitem__("selected_semantic_candidates", 1024)),
        ("unhold rejected candidate", lambda p, i, f, l: p["exclusions"].clear()),
    ]
    for name, mutate in tests:
        p, i, f, l = copy.deepcopy(proof), copy.deepcopy(inv), copy.deepcopy(lower), copy.deepcopy(ledger)
        mutate(p, i, f, l)
        try:
            verify(p, i, f, l)
        except (ValueError, KeyError, IndexError, TypeError):
            continue
        raise RuntimeError("unsafe mutation accepted: " + name)
    return len(tests)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    doc, inv, d1d9 = (source_bundle(), get("knowledge/d10-v1-semantic-inventory.json"),
                      get("knowledge/d1-d9-foundation.json"))
    with (ROOT / "knowledge/d10-proposal-ledger.tsv").open(encoding="utf-8", newline="") as fh:
        ledger = list(csv.DictReader(fh, delimiter="\t"))
    answer = verify(doc, inv, d1d9, ledger)
    if args.self_test:
        answer["mutation_rejections"] = adversarial(doc, inv, d1d9, ledger)
    print(json.dumps(answer, sort_keys=True))

if __name__ == "__main__":
    main()
