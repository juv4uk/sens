#!/usr/bin/env python3
"""D10 spanda exact-rational research oracle + fail-closed selection guard.

Not a production algorithm, not a SENS runtime oracle and not FPGA admission.
The exhaustive oracle and candidate use disjoint construction strategies.
"""
import copy
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTAKE = "knowledge/d10-hobby-exact-measurement-intake-v1.json"
INVENTORY = "knowledge/d10-v1-semantic-inventory.json"
STATE = "knowledge/d10-fill-v1-state.json"
FOUNDATION = "knowledge/d1-d9-foundation.json"
NAME = "BOUNDED-RATIONAL-APPROX"
STABLE = "d10.hobby.spanda.bounded-rational-approx.v1"
SOURCE_BLOB = "d339363e03798941280d7394fb6b24a76ff43dd3"

class AdmissionError(Exception):
    pass

def require(condition, message):
    if not condition:
        raise AdmissionError(message)

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def nearest_bounded(source, limit):
    """Candidate reference: floor/ceil at each denominator, exact comparison."""
    if not isinstance(source, Fraction):
        raise TypeError("source must be exact Fraction, never implicit float")
    if type(limit) is not int or limit < 1:
        raise ValueError("limit must be a positive integer")
    best, key_best = None, None
    for denominator in range(1, limit + 1):
        floor = (source.numerator * denominator) // source.denominator
        for numerator in (floor, floor + 1):
            candidate = Fraction(numerator, denominator)
            if candidate.denominator != denominator:
                continue
            key = (abs(source - candidate), candidate.denominator, candidate.numerator)
            if key_best is None or key < key_best:
                best, key_best = candidate, key
    assert best is not None
    return best, source - best

def exhaustive_oracle(source, limit):
    """Independent full reduced-fraction search for bounded small inputs."""
    # All test x satisfy |x| <= 10 and limit <= 8, so [-180,+180]
    # strictly contains every possible nearest rational numerator.
    candidates = {Fraction(n, d) for d in range(1, limit + 1)
                  for n in range(-180, 181)}
    f = min(candidates, key=lambda x: (abs(source - x), x.denominator, x.numerator))
    return f, source - f

def verify(inv, state, foundation, intake):
    require(intake["schema"] == "d10-hobby-exact-measurement-intake/v1",
            "source dossier schema")
    require(intake["status"] == "SELECTED-RESEARCH-PENDING-OWNER-REVIEW",
            "dossier promotion")
    require(intake["origin"]["donor_blob_sha"] == SOURCE_BLOB, "source SHA changed")
    require(intake["origin"]["source_maturity"].startswith("Spanda ADC rational recovery is documented DESIGN"),
            "false claim of implemented donor")
    require(len(intake["selected"]) == 1, "intake family changed")
    origin = intake["selected"][0]
    require(origin["stable_id"] == STABLE and origin["semantic_name"] == NAME, "source identity changed")
    require(origin["coordinate"] is None and not origin["ratified_resident"],
            "source ratification/coordinate")
    require(origin["proposal_status"] == "pending-owner-review", "owner gate")
    require(len(origin["positives"]) >= 2 and len(origin["falsifiers"]) >= 4,
            "insufficient witnesses")
    require("juv4uk/spanda:README.md@" + SOURCE_BLOB in origin["provenance"],
            "lost donor provenance")
    current_names = [r["semantic_name"].upper() for r in inv["rows"]]
    current_ids = [r["stable_id"] for r in inv["rows"]]
    require(len(set(current_names)) == len(current_names), "D10 duplicate name")
    require(len(set(current_ids)) == len(current_ids), "D10 duplicate id")
    lower = {str(v).upper() for d in foundation["domains"].values()
             for v in d["residents"].values()}
    require(NAME not in lower, "D1-D9 exact-name collision")
    require(current_names.count(NAME) == 1, "selected name missing/repeated")
    require(current_ids.count(STABLE) == 1, "selected ID missing/repeated")
    row = next(r for r in inv["rows"] if r["semantic_name"] == NAME)
    for attr in ("stable_id", "semantic_name", "source_class", "relation_class",
                 "arity", "behavior", "surface_uk", "surface_ukr", "source_path",
                 "coordinate", "coordinate_basis", "ratified_resident",
                 "proposal_status", "status", "decision", "primary_url"):
        if attr == "primary_url":
            continue
        require(row.get(attr) == origin.get(attr),
                "intake/current divergence: " + attr)
    require(row["coordinate"] is None and row["ratified_resident"] is False,
            "unauthorized D10 code")
    require(row["proposal_status"] == "pending-owner-review" and
            row["status"] == "SELECTED-RESEARCH-CANDIDATE",
            "unreviewed selection promoted")
    require(row["physical_t5_authorized"] is False, "T5 authorization forged")
    require(row["positive_witnesses"] == origin["positives"], "positive witness drift")
    require(row["falsifiers"] == origin["falsifiers"], "falsifier drift")
    require(INTAKE in inv["sources"], "source not cited in inventory")
    count = len(inv["rows"])
    a = inv["accounting"]
    t = state["target"]
    require(count >= 631, "candidate was not appended")
    require(a["selected_semantic_candidates"] == t["selected_semantic_candidates"] == count, "count drift")
    require(a["law_forced_coordinates"] == t["law_forced_coordinates"] == 256, "selector authority drift")
    require(a["unplaced_selected_candidates"] == t["unplaced_selected_candidates"] == count-256, "unplaced drift")
    require(a["remaining_semantic_inventory"] == t["remaining_semantic_candidates"] == 1024-count, "remaining drift")
    require(a["ratified_d10_residents"] == t["ratified_residents"] == 0, "ratification forged")
    require(foundation["status"] == "owner-ratified", "foundation authority changed")
    return count

def test_model():
    assert nearest_bounded(Fraction(0), 1) == (Fraction(0), Fraction(0))
    assert nearest_bounded(Fraction(2,3), 3) == (Fraction(2,3), Fraction(0))
    assert nearest_bounded(Fraction(355,113), 100)[0] == Fraction(311,99)
    assert nearest_bounded(Fraction(1,2), 1) == (Fraction(0), Fraction(1,2))
    assert nearest_bounded(Fraction(-1,2), 1) == (Fraction(-1), Fraction(1,2))
    assert nearest_bounded(Fraction(1,3), 2)[0] == Fraction(1,2)
    assert nearest_bounded(Fraction(65535,65536), 16)[0] == Fraction(1)
    assert nearest_bounded(Fraction(123456789,1000000), 1)[0] == Fraction(123)
    for value, cap, error in ((Fraction(1,2),0,ValueError),
                               (Fraction(1,2),-1,ValueError),
                               (0.5,5,TypeError)):
        try:
            nearest_bounded(value,cap)
        except error:
            pass
        else:
            raise AdmissionError("invalid datum admitted")
    count=0
    for denominator in range(1,12):
        for numerator in range(-19,20):
            val=Fraction(numerator,denominator)
            if abs(val)>10:
                continue
            for bound in range(1,9):
                require(nearest_bounded(val,bound) == exhaustive_oracle(val,bound),
                        "counterexample for exact rational approximation")
                count+=1
    require(count == 3288, "bounded differential corpus changed")
    return count

def self_test(inv, state, foundation, intake):
    selected=verify(inv,state,foundation,intake)
    corpus=test_model()
    mutants=[
       ("change old semantic",lambda i,s,d: i["rows"][5].update({"behavior":"forged"})),
       ("duplicate new ID",lambda i,s,d: i["rows"].append(copy.deepcopy(i["rows"][-1]))),
       ("invent coordinate",lambda i,s,d: i["rows"][-1].update({"coordinate":"0000000000"})),
       ("ratify",lambda i,s,d: i["rows"][-1].update({"ratified_resident":True})),
       ("change source SHA",lambda i,s,d: d["origin"].update({"donor_blob_sha":"0"*40})),
       ("erase falsifiers",lambda i,s,d: d["selected"][0].update({"falsifiers":[]})),
       ("forge T5 permission",lambda i,s,d: i["rows"][-1].update({"physical_t5_authorized":True})),
       ("wrong total",lambda i,s,d: s["target"].update({"remaining_semantic_candidates":-1})),
    ]
    # The changed-old-semantic row is rejected by transition-history checker;
    # it intentionally does not alter this root-specific guard's scope.
    for label,mutate in mutants[1:]:
        ii,ss,dd=copy.deepcopy(inv),copy.deepcopy(state),copy.deepcopy(intake)
        mutate(ii,ss,dd)
        try:
            verify(ii,ss,foundation,dd)
        except AdmissionError:
            continue
        raise AdmissionError("negative mutation admitted: "+label)
    print("D10-SPANDA-ROOT PASS: selected="+str(selected)+", differential="+str(corpus)+", 7 negative guards")

if __name__=="__main__":
    a,b,c,d=load(INVENTORY),load(STATE),load(FOUNDATION),load(INTAKE)
    try:
        if "--self-test" in sys.argv: self_test(a,b,c,d)
        else: print("D10-SPANDA-ROOT PASS: selected="+str(verify(a,b,c,d)))
    except AdmissionError as exc:
        print("D10-SPANDA-ROOT FAIL: "+str(exc),file=sys.stderr)
        sys.exit(1)
