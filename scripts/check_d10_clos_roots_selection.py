#!/usr/bin/env python3
"""Fail-closed research admission guard for three CLOS D10 roots.

Validates recorded historical research, not executable SENS-oracle parity.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = {
    "SLOT-BOUNDP": "d10.clos.slot-boundp.v1",
    "SLOT-MAKUNBOUND": "d10.clos.slot-makunbound.v1",
    "REMOVE-METHOD": "d10.clos.remove-method.v1",
}
PRIMARY = {
    "SLOT-BOUNDP": "https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_slot-boundp.html",
    "SLOT-MAKUNBOUND": "https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_slot-makunbound.html",
    "REMOVE-METHOD": "https://www.lispworks.com/documentation/HyperSpec/Body/f_rm_met.htm",
}
DONORS = {
    "SLOT-BOUNDP": "knowledge/d10-clos-slot-state-historical-review-v1.json",
    "SLOT-MAKUNBOUND": "knowledge/d10-clos-slot-state-historical-review-v1.json",
    "REMOVE-METHOD": "knowledge/d10-historical-clos-interlisp-residual-review-v1.json",
}

class GateFailure(Exception):
    pass

def check(condition, message):
    if not condition:
        raise GateFailure(message)

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def audit(inv, state, foundation, evidence):
    rows = inv["rows"]
    names = [str(r["semantic_name"]).upper() for r in rows]
    ids = [r["stable_id"] for r in rows]
    check(len(set(names)) == len(names), "duplicate D10 semantic name")
    check(len(set(ids)) == len(ids), "duplicate D10 stable_id")
    check(628 <= len(rows) <= 1024, "D10 selected count invalid")
    lower = {
        str(name).upper()
        for d in foundation["domains"].values()
        for name in d["residents"].values()
    }
    check(set(IDS).isdisjoint(lower), "D1-D9 exact-name duplicate")
    n = len(rows)
    accounting = inv["accounting"]
    target = state["target"]
    check(accounting["selected_semantic_candidates"] == n, "inventory selected drift")
    check(accounting["law_forced_coordinates"] == 256, "selector law drift")
    check(accounting["unplaced_selected_candidates"] == n - 256, "unplaced drift")
    check(accounting["remaining_semantic_inventory"] == 1024 - n, "remaining drift")
    check(accounting["ratified_d10_residents"] == 0, "unapproved ratification")
    check(target["selected_semantic_candidates"] == n, "state selected drift")
    check(target["unplaced_selected_candidates"] == n - 256, "state unplaced drift")
    check(target["remaining_semantic_candidates"] == 1024 - n, "state remaining drift")
    check(target["ratified_residents"] == 0, "state ratification drift")
    check(inv["current_foundation"] == "#4008 / Contract 11.8 / D1-D9", "foundation drift")
    check(foundation["status"] == "owner-ratified", "lower foundation not ratified")
    by_name = {row["semantic_name"]: row for row in rows}
    for name, stable_id in IDS.items():
        check(name in by_name, "missing selection " + name)
        row = by_name[name]
        check(row["stable_id"] == stable_id, "stable ID drift " + name)
        check(row["source_class"] == "HISTORICAL-CLOS-ROOT-REVIEW", "class drift " + name)
        check(row["status"] == "SELECTED-RESEARCH-CANDIDATE", "status drift " + name)
        check(row["decision"] == "SELECT-D10-CANDIDATE", "decision drift " + name)
        check(row["proposal_status"] == "pending-owner-review", "owner-review drift " + name)
        check(row["coordinate"] is None, "unproved coordinate " + name)
        check(row["coordinate_basis"] == "UNPLACED", "coordinate basis drift " + name)
        check(row["donor_coordinate_authority"] == "NONE", "borrowed authority " + name)
        check(row["ratified_resident"] is False, "illegal ratification " + name)
        check(row["primary_url"] == PRIMARY[name], "primary URL mismatch " + name)
        check(row["source_path"] == DONORS[name], "donor mismatch " + name)
        check(len(row["positive_witnesses"]) >= 2, "missing positive witnesses " + name)
        check(len(row["falsifiers"]) >= 2, "missing falsifiers " + name)
        check(bool(row["behavior"]) and bool(row["minimality"]), "missing law or minimality " + name)
        check(bool(row["surface_uk"]) and bool(row["surface_ukr"]), "missing Ukrainian surface " + name)
        check(DONORS[name] in inv["sources"], "source missing " + name)
        matches = [r for r in evidence[DONORS[name]]["rows"] if r.get("historical_name") == name]
        check(len(matches) == 1, "donor evidence missing " + name)
        check(matches[0].get("ratified") is False, "donor forged ratification " + name)
        check(matches[0].get("coordinate") is None, "donor forged coordinate " + name)
        check(matches[0].get("selected_in_d10") is False, "historical dossier mutated " + name)
    return True

def self_test(inv, state, foundation, evidence):
    audit(inv, state, foundation, evidence)
    # A CLOS-specific negative control must target a CLOS row by immutable ID,
    # not the final D10 row: other agents append other selected candidates later.
    def clos_row(current):
        return next(row for row in current["rows"]
                    if row["stable_id"] == IDS["REMOVE-METHOD"])
    mutations = [
        ("duplicate name", lambda i, s: i["rows"].append(copy.deepcopy(i["rows"][-1]))),
        ("fake coordinate", lambda i, s: clos_row(i).update({"coordinate":"1111111111"})),
        ("fake ratification", lambda i, s: clos_row(i).update({"ratified_resident":True})),
        ("missing falsifier", lambda i, s: clos_row(i).update({"falsifiers":[]})),
        ("wrong remaining", lambda i, s: s["target"].update({"remaining_semantic_candidates":-1})),
        ("forged source", lambda i, s: clos_row(i).update({"primary_url":"https://example.invalid"})),
        ("owner gate bypass", lambda i, s: clos_row(i).update({"proposal_status":"ratified"})),
    ]
    for title, change in mutations:
        i, s = copy.deepcopy(inv), copy.deepcopy(state)
        change(i, s)
        try:
            audit(i, s, foundation, evidence)
        except GateFailure:
            continue
        raise GateFailure("negative control accepted: " + title)
    print(f"D10-CLOS-ROOTS: PASS selected={len(inv['rows'])}; 7/7 negative mutations rejected")
    print("D10-CLOS-ROOTS: research only; ratified=0; runtime oracle not claimed")

if __name__ == "__main__":
    inventory = load("knowledge/d10-v1-semantic-inventory.json")
    state = load("knowledge/d10-fill-v1-state.json")
    foundation = load("knowledge/d1-d9-foundation.json")
    evidence = {p: load(p) for p in set(DONORS.values())}
    try:
        if sys.argv[1:] == ["--self-test"]:
            self_test(inventory, state, foundation, evidence)
        else:
            audit(inventory, state, foundation, evidence)
            print(f"D10-CLOS-ROOTS: PASS selected={len(inventory['rows'])}")
    except GateFailure as error:
        print("D10-CLOS-ROOTS: FAIL " + str(error), file=sys.stderr)
        sys.exit(1)
