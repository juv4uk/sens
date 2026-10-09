#!/usr/bin/env python3
"""Fail-closed R7RS historical source review; no D10 admission or allocation."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "knowledge/d10-r7rs-primary-manual-slice-v1.json"
INV = ROOT / "knowledge/d10-v1-semantic-inventory.json"
LOW = ROOT / "knowledge/d1-d9-foundation.json"
SOURCE = "https://standards.scheme.org/r7rs-html5/index.html"
ALLOWED = {"HOLD-D2-DERIVABILITY", "HOLD-DERIVABILITY",
           "HOLD-TYPE-DERIVED", "HOLD-D2-SYNTAX",
           "HOLD-D2-CONTROL", "HOLD-EFFECT-DERIVABILITY",
           "HOLD-EFFECT-CONTINUATION"}
EXPECTED = ["DELAY-FORCE","MAKE-PROMISE","PROMISE?","CASE-LAMBDA","DEFINE-RECORD-TYPE","RAISE-CONTINUABLE","BYTEVECTOR-COPY!","CALL-WITH-PORT","WITH-EXCEPTION-HANDLER","DEFINE-VALUES","GUARD"]

def verify(doc: dict, inv: dict, foundation: dict) -> dict:
    assert doc["schema"] == "sens-d10-r7rs-primary-manual-slice/v1"
    assert doc["status"] == "RESEARCH-ONLY-NOT-D10-SELECTED"
    assert doc["source_coverage"].endswith("a bounded non-exhaustive slice")
    assert len(inv["rows"]) == inv["accounting"]["selected_semantic_candidates"]
    assert inv["accounting"]["ratified_d10_residents"] == 0
    assert len(inv["rows"]) >= doc["snapshot"]["selected"]
    assert doc["snapshot"]["ratified"] == 0
    known = {x["semantic_name"].upper() for x in inv["rows"]}
    lower = {str(name).upper()
             for domain in foundation["domains"].values()
             for name in domain.get("residents", {}).values()}
    assert len(doc["rows"]) == len(EXPECTED) == 11
    assert [x["historical_spelling"] for x in doc["rows"]] == EXPECTED
    assert len({x["review_id"] for x in doc["rows"]}) == 11
    assert not (set(EXPECTED) & known)
    assert not (set(EXPECTED) & lower)
    assert not (set(EXPECTED) & set(doc["overlap_guard"]["already_proposed_in_pr_4837"]))
    assert "DELAY" in known and "FORCE" in known
    assert "VALUES" in lower
    for i, x in enumerate(doc["rows"], 1):
        assert x["review_id"] == f"R7RS-HIST-{i:03d}"
        assert x["reference_report"] == "R7RS-small-2013"
        assert x["source_type"] == "PRIMARY-STANDARD"
        assert x["primary_url"] == SOURCE
        assert x["section"] and x["section"][0].isdigit()
        assert x["observable_law"] and x["positive_witness_spec"] and x["falsifier_spec"]
        assert x["existing_semantic_neighbors"]
        assert x["status"] in ALLOWED
        assert x["owner_review"] == "PENDING"
        assert x["semantic_distinctness"] == "UNPROVED"
        assert x["coordinate"] is None
        assert x["selected_in_d10"] is False
        assert x["ratified"] is False
        assert x["physical_t5_authorized"] is False
    return {"historical_source_rows": len(doc["rows"]),
            "selected_increase": 0, "ratified_increase": 0,
            "new_coordinates": 0, "verified_name_collisions": 0}

def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def self_test(d: dict, i: dict, f: dict) -> None:
    verify(d, i, f)
    failures = [
        ("coordinate", "0000000000"),
        ("selected_in_d10", True),
        ("ratified", True),
        ("physical_t5_authorized", True),
        ("falsifier_spec", ""),
        ("positive_witness_spec", ""),
        ("primary_url", "https://example.invalid"),
        ("semantic_distinctness", "PROVED"),
        ("status", "RATIFIED")
    ]
    for field, value in failures:
        bad = copy.deepcopy(d)
        bad["rows"][0][field] = value
        try:
            verify(bad, i, f)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"negative self-test FAILED for {field}")
    bad = copy.deepcopy(d)
    bad["rows"][0]["historical_spelling"] = "FORCE"
    try:
        verify(bad, i, f)
    except AssertionError:
        pass
    else:
        raise AssertionError("already-selected FORCE must reject")
    bad = copy.deepcopy(d)
    bad["rows"][0]["historical_spelling"] = "CASE-LAMBDA"
    try:
        verify(bad, i, f)
    except AssertionError:
        pass
    else:
        raise AssertionError("duplicate names must reject")
    print("R7RS HISTORY SELF-TEST PASS 11 negative cases")

def main() -> None:
    doc, inv, foundation = read(LEDGER), read(INV), read(LOW)
    result = verify(doc, inv, foundation)
    if "--self-test" in sys.argv:
        self_test(doc, inv, foundation)
    print("D10 R7RS PRIMARY-SLICE PASS", json.dumps(result, sort_keys=True))
if __name__ == "__main__":
    main()
