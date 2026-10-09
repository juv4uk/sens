#!/usr/bin/env python3
"""Fail-closed, read-only review of three *historical* D10 donor ledgers."""
import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DONORS = (
    ("knowledge/d10-crossrepo-linguistic-v1.json", 9),
    ("knowledge/d10-crossrepo-domain-v1.json", 11),
    ("knowledge/d10-crossrepo-knowledge-tooling-v1.json", 8),
)
INVENTORY = "knowledge/d10-v1-semantic-inventory.json"
ALLOWED = {"SELECT", "HOLD", "PROJECTION", "MECHANISM-ONLY"}
def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def verify(donors, inventory):
    rows = inventory["rows"]
    counts = inventory["accounting"]
    require(len(rows) == counts["selected_semantic_candidates"], "invalid canonical inventory count")
    require(counts["ratified_d10_residents"] == 0, "review-only checker cannot ratify D10")
    total = 0
    for (path, expected), doc in zip(DONORS, donors):
        chunk = doc["rows"]
        require(len(chunk) == expected, "unexpected donor row count: " + path)
        for r in chunk:
            require(r.get("semantic_name") and r.get("repository"), "missing provenance/identity: " + path)
            require(r.get("decision") in ALLOWED, "unknown/released decision: " + path)
            require(r.get("coordinate") is None, "invented bit coordinate: " + path)
            require(bool(r.get("source") or r.get("path/source")), "missing source: " + path)
            require(bool(r.get("behavior") or r.get("behavior/law")), "missing law: " + path)
        if "ratification" in doc:
            require(doc["ratification"] is False, "ratification false required")
        if "inventory_mutation" in doc:
            require(doc["inventory_mutation"] is False or doc["inventory_mutation"] == "NONE", "inventory mutation forbidden")
        if "acceptance_state" in doc:
            require(doc["acceptance_state"]["inventory_mutation"] == "NONE", "linguistic donor changed inventory")
            require(doc["acceptance_state"]["ratification_effect"] == "NONE", "linguistic donor ratified")
        total += len(chunk)
    require(total == 28, "donor corpus changed unexpectedly")
    return {"donor_rows": total, "promoted_selected": 0,
            "new_coordinates": 0, "ratified": 0,
            "canonical_selected_unchanged": counts["selected_semantic_candidates"]}

def run_self_tests(donors, inventory):
    verify(donors, inventory)
    def must_reject(edit):
        xs = copy.deepcopy(donors)
        edit(xs)
        try:
            verify(xs, inventory)
        except ValueError:
            return
        raise ValueError("mutation incorrectly accepted")
    must_reject(lambda x: x[0]["rows"][0].__setitem__("coordinate", "0000000000"))
    must_reject(lambda x: x[1].__setitem__("ratification", True))
    must_reject(lambda x: x[0]["rows"][0].__setitem__("decision", "RATIFIED"))
    must_reject(lambda x: x[0]["rows"][0].__setitem__("behavior", ""))
    must_reject(lambda x: x[2]["rows"].pop())
    print("SELF-TEST PASS: 5 adverse mutations blocked")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    def load(path):
        return json.loads((ROOT/path).read_text(encoding="utf-8"))
    donors = [load(path) for path, _ in DONORS]
    inventory = load(INVENTORY)
    result = verify(donors, inventory)
    if args.self_test:
        run_self_tests(donors, inventory)
    print("D10-ARCHIVE-DONOR-GUARD PASS", json.dumps(result, sort_keys=True))
if __name__ == "__main__":
    main()
