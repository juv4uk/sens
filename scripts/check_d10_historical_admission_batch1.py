#!/usr/bin/env python3
"""Fail-closed D10 monotonic growth: preserve all 625 earlier laws and select two reviewed laws.

This checks registry provenance and reference-model consistency; it does NOT
assert SENS runtime parity or ratify executable D10 coordinates.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge/d10-growth-baseline-v1.json"
BATCH = ROOT / "knowledge/d10-historical-primary-admission-batch1-v1.json"
INV = ROOT / "knowledge/d10-v1-semantic-inventory.json"
STATE = ROOT / "knowledge/d10-fill-v1-state.json"
SOURCE = ROOT / "knowledge/d10-historical-primary-manual-reconciliation-20261009.json"
DOC = ROOT / "docs/architecture/ARCHIPELAGO-V1.uk.md"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def check_growth(inv, baseline=None):
    baseline = baseline or read(BASE)
    assert baseline["schema"] == "d10-growth-baseline/v1"
    assert baseline["origin_inventory_git_blob"] == "73dd518469f972c55411e004b70b054ba8b3ec86"
    n = baseline["frozen_count"]
    assert n == len(baseline["rows"]) == 625
    assert len(inv["rows"]) >= n
    for i, prior in enumerate(baseline["rows"]):
        for field in baseline["protected_fields"]:
            assert inv["rows"][i].get(field) == prior[field], (i, field, "historical identity was changed")
    ids = [r["stable_id"] for r in inv["rows"]]
    names = [r["semantic_name"].upper() for r in inv["rows"]]
    assert len(ids) == len(set(ids)) and len(names) == len(set(names))
    assert len(inv["rows"]) == inv["accounting"]["selected_semantic_candidates"]
    assert inv["accounting"]["remaining_semantic_inventory"] == 1024-len(ids)
    assert inv["accounting"]["unplaced_selected_candidates"] == len(ids)-256
    assert inv["accounting"]["law_forced_coordinates"] == 256
    assert inv["accounting"]["ratified_d10_residents"] == 0
    for row in inv["rows"][n:]:
        assert row["coordinate"] is None and row["coordinate_basis"] == "UNPLACED"
        assert row["ratified_resident"] is False
        assert row["status"] == "SELECTED-RESEARCH-CANDIDATE"
    return True

def check(inv, batch, state, source, doc):
    check_growth(inv)
    assert batch["schema"] == "d10-historical-primary-admission-batch1/v1"
    assert batch["status"] == "SELECTED-RESEARCH-UNPLACED-NOT-RATIFIED"
    assert batch["frozen_base_git_blob"] == read(BASE)["origin_inventory_git_blob"]
    assert batch["original_selected"] == 625
    assert batch["added_selected"] == len(batch["rows"]) == 2
    assert batch["new_selected"] == 627
    assert batch["coordinate_added"] == batch["ratified_added"] == 0
    assert {r["semantic_name"] for r in batch["rows"]} == {"DPB","ARRAY-DISPLACEMENT"}
    by_name = {r["semantic_name"]:r for r in inv["rows"]}
    proposals = {p["historical_name"]:p for p in source["proposals"]}
    for row in batch["rows"]:
        assert by_name[row["semantic_name"]] == row
        assert row["source_class"] == "HISTORICAL-PRIMARY-LAW-TRANCHE-20261009"
        assert row["proposal_status"] == "pending-owner-review"
        assert row["status"] == "SELECTED-RESEARCH-CANDIDATE"
        assert row["coordinate"] is None and not row["ratified_resident"]
        assert row["physical_t5_authorized"] is False
        assert row["surface_uk"] and row["surface_ukr"]
        assert row["behavior"] and row["argument_shape"] and row["falsifier_spec"]
        assert len(row["positive_witnesses"]) >= 2
        assert row["dedup_check"] and row["nearby_existing"]
        donor = proposals[row["semantic_name"]]
        assert donor["triage"] == "D10-PROPOSAL-REVIEW"
        assert donor["primary_name_attested"] is True
        assert row["primary_url"] == donor["source_url"]
        assert row["source_section"] == donor["source_section"]
        assert row["source_class"] in ("HISTORICAL-PRIMARY-LAW-TRANCHE-20261009",)
    assert "knowledge/d10-historical-primary-admission-batch1-v1.json" in inv["sources"]
    assert state["target"]["selected_semantic_candidates"] == len(inv["rows"])
    assert state["target"]["remaining_semantic_candidates"] == 1024-len(inv["rows"])
    assert state["target"]["unplaced_selected_candidates"] == len(inv["rows"])-256
    assert state["target"]["law_forced_coordinates"] == 256
    assert state["target"]["ratified_residents"] == 0
    assert f'D10 selected              {len(inv["rows"])}/1024' in doc
    assert f'unplaced                  {len(inv["rows"])-256}' in doc
    assert f'remaining                 {1024-len(inv["rows"])}' in doc
    return True

def model_dpb(newbyte, width, offset, target):
    assert width >= 0 and offset >= 0
    low = (1 << width) - 1
    field = low << offset
    return (target & ~field) | ((newbyte & low) << offset)

def reference_model_tests():
    assert model_dpb(1,1,10,0) == 1024
    assert model_dpb(-2,2,10,0) == 2048
    assert model_dpb(1,2,10,2048) == 1024
    assert model_dpb(7,0,10,-3) == -3
    assert model_dpb(11,3,2,0b11100001) == 0b11101101
    print("REFERENCE-MODEL DPB examples PASS (not SENS execution)")

def self_test(inv, batch, state, source, doc):
    check(inv,batch,state,source,doc)
    mutated = copy.deepcopy(inv)
    mutated["rows"][0]["behavior"] = "silently mutated"
    try: check_growth(mutated)
    except AssertionError: pass
    else: raise AssertionError("history tampering accepted")
    mutated = copy.deepcopy(inv)
    mutated["rows"][-1]["coordinate"] = "0000000000"
    try: check_growth(mutated)
    except AssertionError: pass
    else: raise AssertionError("unproved coordinate accepted")
    mutated = copy.deepcopy(batch)
    mutated["rows"][0]["ratified_resident"] = True
    try: check(inv,mutated,state,source,doc)
    except AssertionError: pass
    else: raise AssertionError("unauthorized ratification accepted")
    print("GROWTH-BASELINE adverse cases PASS")

def main():
    inv,batch,state,source=(read(x) for x in (INV,BATCH,STATE,SOURCE))
    doc=DOC.read_text(encoding="utf-8")
    check(inv,batch,state,source,doc)
    reference_model_tests()
    import sys
    if "--self-test" in sys.argv: self_test(inv,batch,state,source,doc)
    print("D10-HISTORICAL-ADMISSION-BATCH1 PASS: 627/1024, two source-backed selected, 0 coords, 0 ratified")
if __name__ == "__main__":
    main()
