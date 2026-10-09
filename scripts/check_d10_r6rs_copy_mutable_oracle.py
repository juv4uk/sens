#!/usr/bin/env python3
"""Research-only D10 R6RS copy/mutability donor gate; NO semantic admission."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "knowledge/d10-r6rs-copy-mutable-oracle-v1.json"
DONOR = ROOT / "knowledge/d10-r6rs-hashtable-hygiene-audit-v1.json"
D10 = ROOT / "knowledge/d10-v1-semantic-inventory.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
ORACLE = ROOT / "tests/d10_r6rs_hashtable_copy_mutable.ss"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify(report, donor, foundation, inventory):
    assert report["schema"] == "d10-r6rs-copy-mutable-research/v1"
    assert report["status"] == "HOLD-OWNER-SEMANTIC-REVIEW-NO-SELECTED-ADMISSION"
    assert report["baseline"]["foundation_blob"] == "09d1d71c39d1484dfd005a5068dbb18b76f0f0d4"
    assert report["baseline"]["d10_blob"] == "73dd518469f972c55411e004b70b054ba8b3ec86"
    assert report["baseline"]["selected_at_audit"] == 625
    assert report["baseline"]["ratified_at_audit"] == 0
    assert inventory["accounting"]["selected_semantic_candidates"] == len(inventory["rows"])
    assert inventory["accounting"]["ratified_d10_residents"] == 0
    assert inventory["capacity"] == 1024
    assert report["admission"]["new_selected"] == 0
    assert report["admission"]["new_coordinates"] == 0
    assert report["admission"]["new_ratified"] == 0
    assert report["admission"]["oracle_is_sens_runtime"] is False
    assert len(report["rows"]) == 2
    assert {x["historical_name"] for x in report["rows"]} == {
        "HASHTABLE-COPY", "HASHTABLE-MUTABLE?"
    }
    lower = {str(value).upper() for d in foundation["domains"].values()
             for value in d["residents"].values()}
    upper = {row["semantic_name"].upper() for row in inventory["rows"]}
    original = {r["historical_spelling"]: r for r in donor["rows"]}
    assert len(original) == 19
    for row in report["rows"]:
        name = row["historical_name"]
        assert name not in lower and name not in upper, f"re-review selected collision: {name}"
        assert row["status"] == "HOLD-RESEARCH-NO-ADMISSION"
        assert row["selected_in_d10"] is False and row["ratified"] is False
        assert row["coordinate"] is None and row["physical_t5_authorized"] is False
        assert row["surface_uk"] and row["surface_ukr"]
        assert row["law"] and row["arity"] and row["falsifiers"]
        assert len(row["positive_witnesses"]) >= 2 and len(row["falsifiers"]) >= 2
        assert row["semantic_neighbors"] and row["ownership_question"]
        old = original[name]
        assert row["reference_id"] == old["review_id"]
        assert row["section"] == old["section"]
        assert old["owner_boundary"] == "D10-CANDIDATE-OWNERSHIP-REVIEW"
        assert old["status"] == "HOLD-RESEARCH-NO-ADMISSION"
        assert old["coordinate"] is None and old["ratified"] is False
        assert old["primary_url"] == report["source"]["url"]
        assert old["exact_in_D1_D9"] is False
        assert old["exact_in_current_D10_selected"] is False
    assert ORACLE.read_text(encoding="utf-8").startswith("#!r6rs")
    return {"research_laws": 2, "new_selected": 0,
            "d10_live_selected": len(upper), "ratified": 0}


def self_test(report, donor, foundation, inventory):
    assert verify(report, donor, foundation, inventory)["research_laws"] == 2
    tests = [
        lambda x: x["rows"][0].__setitem__("coordinate", "0000000000"),
        lambda x: x["rows"][0].__setitem__("selected_in_d10", True),
        lambda x: x["rows"][0].__setitem__("ratified", True),
        lambda x: x["rows"][0].__setitem__("physical_t5_authorized", True),
        lambda x: x["rows"][0].__setitem__("law", ""),
        lambda x: x["rows"][1].__setitem__("positive_witnesses", []),
        lambda x: x["rows"][1].__setitem__("reference_id", "R6RS-06"),
        lambda x: x["source"].__setitem__("url", "https://example.com/fake"),
        lambda x: x["admission"].__setitem__("new_selected", 2),
    ]
    for index, mutate in enumerate(tests):
        changed = copy.deepcopy(report)
        mutate(changed)
        try:
            verify(changed, donor, foundation, inventory)
        except AssertionError:
            continue
        raise AssertionError(f"unsafe mutation {index} accepted")
    changed = copy.deepcopy(donor)
    next(x for x in changed["rows"] if x["review_id"] == "R6RS-06")["status"] = "ADMITTED"
    try:
        verify(report, changed, foundation, inventory)
    except AssertionError:
        pass
    else:
        raise AssertionError("donor HOLD mutation accepted")
    print("D10 R6RS COPY/MUTABLE 10 adversarial cases PASS")


def main():
    report, donor, foundation, inventory = [read(path)
        for path in (REPORT, DONOR, FOUNDATION, D10)]
    print("D10 R6RS COPY/MUTABLE research gate PASS",
          json.dumps(verify(report, donor, foundation, inventory), sort_keys=True))
    if "--self-test" in sys.argv:
        self_test(report, donor, foundation, inventory)


if __name__ == "__main__":
    main()
