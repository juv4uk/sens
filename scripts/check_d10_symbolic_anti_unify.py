#!/usr/bin/env python3
"""Finite GROUND anti-unification: test model, witness checker, source admission.

Not an implementation of SENS binary opcodes; Prolog runtime separately checks
historical donor via tests/d10_symbolic_anti_unify_donor.pl.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = "knowledge/d10-symbolic-ai-anti-unification-v1.json"
INVENTORY = "knowledge/d10-v1-semantic-inventory.json"
FOUNDATION = "knowledge/d1-d9-foundation.json"
NAME = "FINITE-GROUND-ANTI-UNIFY"
ID = "d10.symbolic-ai.finite-ground-anti-unify.v1"
MANUAL = "https://www.swi-prolog.org/pldoc/man?predicate=term_subsumer%2F3"


class ResearchFailure(Exception):
    pass


def check(condition, message):
    if not condition:
        raise ResearchFailure(message)


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def ground(term, active=None):
    if active is None:
        active = set()
    if isinstance(term, str) or (isinstance(term, int) and not isinstance(term, bool)):
        return
    check(isinstance(term, dict) and set(term) == {"f", "a"}, "non-ground, untyped, or malformed term")
    check(isinstance(term["f"], str) and bool(term["f"]), "bad functor")
    check(isinstance(term["a"], list), "bad argument list")
    ident = id(term)
    check(ident not in active, "cyclic input term")
    active.add(ident)
    for t in term["a"]:
        ground(t, active)
    active.remove(ident)


def node(functor, *args):
    return {"f": functor, "a": list(args)}


def anti_unify(left, right):
    ground(left)
    ground(right)
    seen = {}
    left_witness = {}
    right_witness = {}

    def rec(a, b):
        if a == b:
            return copy.deepcopy(a)
        if isinstance(a, dict) and isinstance(b, dict):
            if a["f"] == b["f"] and len(a["a"]) == len(b["a"]):
                return node(a["f"], *(rec(x, y) for x, y in zip(a["a"], b["a"])))
        key = json.dumps([a, b], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if key not in seen:
            name = "G" + str(len(seen))
            seen[key] = name
            left_witness[name] = copy.deepcopy(a)
            right_witness[name] = copy.deepcopy(b)
        return {"v": seen[key]}

    pattern = rec(left, right)
    return pattern, left_witness, right_witness


def apply(pattern, bindings):
    if isinstance(pattern, dict) and set(pattern) == {"v"}:
        check(pattern["v"] in bindings, "unbound generalization variable")
        return copy.deepcopy(bindings[pattern["v"]])
    if isinstance(pattern, dict) and set(pattern) == {"f", "a"}:
        return node(pattern["f"], *(apply(x, bindings) for x in pattern["a"]))
    return copy.deepcopy(pattern)


def pattern_vars(pattern):
    if isinstance(pattern, dict) and set(pattern) == {"v"}:
        return [pattern["v"]]
    if isinstance(pattern, dict) and set(pattern) == {"f", "a"}:
        return [v for arg in pattern["a"] for v in pattern_vars(arg)]
    return []


def verify_witness(left, right, result):
    pat, lw, rw = result
    check(apply(pat, lw) == left and apply(pat, rw) == right, "reconstruction mismatch")
    variables = set(pattern_vars(pat))
    check(variables == set(lw) == set(rw), "witness domain mismatch")
    check(set(lw) == {"G" + str(i) for i in range(len(lw))}, "noncanonical variable order")
    # The inverse substitutions must distinguish different mismatch pairs.
    inverse = {(json.dumps(lw[v], sort_keys=True), json.dumps(rw[v], sort_keys=True))
               for v in variables}
    check(len(inverse) == len(variables), "distinct disagreement pairs incorrectly aliased")
    check(pat == anti_unify(right, left)[0], "swapping sources should preserve pattern")
    return True


def model_cases():
    examples = [
      (node("f", "a", "a"), node("f", "b", "b"), node("f", {"v": "G0"}, {"v": "G0"})),
      (node("f", "a", "a"), node("f", "b", "c"), node("f", {"v": "G0"}, {"v": "G1"})),
      (node("f", "a", "b"), node("f", "a", "c"), node("f", "a", {"v": "G0"})),
      (node("f", "a"), node("g", "a"), {"v": "G0"}),
      (node("f", "a", "b"), node("f", "a", "b"), node("f", "a", "b")),
      (node("f", node("g", "a"), node("g", "a")),
       node("f", node("g", "b"), node("g", "b")),
       node("f", node("g", {"v": "G0"}), node("g", {"v": "G0"}))),
      (node("p", 1, 1), node("p", 2, 2), node("p", {"v": "G0"}, {"v": "G0"})),
      (node("p", 1, 2), node("p", 2, 1), node("p", {"v": "G0"}, {"v": "G1"})),
    ]
    for a, b, expected in examples:
        pat, lw, rw = anti_unify(a, b)
        check(pat == expected, "fixture mismatch " + repr((a, b)))
        verify_witness(a, b, (pat, lw, rw))
    atoms = ["a", "b", "c", 0, 1]
    terms = atoms + [node(f, a) for f in ("f", "g") for a in atoms]
    terms += [node(f, x, y) for f in ("f", "g") for x in atoms[:3] for y in atoms[:3]]
    terms += [node("h", node("f", a), b) for a in atoms[:3] for b in atoms[:3]]
    count = 0
    for a in terms:
        for b in terms:
            verify_witness(a, b, anti_unify(a, b))
            count += 1
    check(count >= 1500, "tiny corpus is not exhaustive enough")
    # Reject unsupported domains (not silently coerce to a grounded Prolog term).
    invalid = [{"v": "X"}, [], True, 1.25, {"f": "f", "a": "a"}]
    for t in invalid:
        try:
            anti_unify(t, "a")
        except ResearchFailure:
            continue
        raise ResearchFailure("invalid/non-ground input was admitted: " + repr(t))
    cycle = node("loop")
    cycle["a"].append(cycle)
    try:
        anti_unify(cycle, "a")
    except ResearchFailure:
        pass
    else:
        raise ResearchFailure("cyclic input accepted without consent")
    return len(examples), count, len(invalid) + 1


def audit(dossier, inv, foundation):
    check(dossier["schema"] == "d10-symbolic-ai-anti-unification-research/v1", "schema changed")
    check(dossier["status"] == "SOURCE-AND-ORACLE-RESEARCH-HOLD-CORE-VS-LIBRARY",
          "research HOLD promoted without review")
    check(dossier["primary_source"]["manual"] == MANUAL, "primary donor changed")
    c = dossier["candidate"]
    check(c["stable_id"] == ID and c["semantic_name"] == NAME, "candidate identity changed")
    check(c["selected_in_d10"] is False and c["ratified_resident"] is False, "unapproved admission")
    check(c["coordinate"] is None and dossier["authority"]["new_coordinates"] == 0,
          "invented binary coordinate")
    check(dossier["authority"]["new_ratifications"] == 0 and dossier["authority"]["physical_t5"] is False,
          "no T5/ratification authority")
    check(dossier["authority"]["d2_control_unchanged"] is True, "D2 authority violated")
    check(c["proposal_status"] == "pending-owner-and-derivability-review", "owner review bypass")
    check(len(c["positive_witnesses"]) >= 5 and len(c["falsifiers"]) >= 6, "insufficient falsifiers")
    check("SWI-Prolog" in dossier["primary_source"]["provider"], "donor oracle absent")
    check("SUBSUMES" not in c["semantic_name"] and "UNIFY" in c["semantic_name"], "identity drift")
    lower = {str(v).upper() for d in foundation["domains"].values()
             for v in d["residents"].values()}
    check(NAME not in lower, "D1-D9 exact-name duplicate")
    check(NAME not in {str(r["semantic_name"]).upper() for r in inv["rows"]}, "already selected D10")
    check(inv["accounting"]["ratified_d10_residents"] == 0, "unexpected ratification")
    check(inv["accounting"]["law_forced_coordinates"] == 256, "selector authority drift")
    check(len(inv["rows"]) >= dossier["baseline"]["selected_semantic_candidates"], "historical shrink")
    check(foundation["status"] == "owner-ratified", "D1-D9 authority missing")
    return len(inv["rows"])


def negative_metadata_tests(d, inv, f):
    audit(d, inv, f)
    cases = [
      ("ratify",lambda v:v["candidate"].update({"ratified_resident":True})),
      ("select",lambda v:v["candidate"].update({"selected_in_d10":True})),
      ("coordinate",lambda v:v["candidate"].update({"coordinate":"1111111111"})),
      ("donor",lambda v:v["primary_source"].update({"manual":"https://example.invalid"})),
      ("owner",lambda v:v["candidate"].update({"proposal_status":"ratified"})),
      ("without falsifiers",lambda v:v["candidate"].update({"falsifiers":[]})),
      ("claimed physical T5",lambda v:v["authority"].update({"physical_t5":True})),
      ("change identity",lambda v:v["candidate"].update({"stable_id":"ANOTHER"})),
      ("D2 admission",lambda v:v["authority"].update({"d2_control_unchanged":False})),
    ]
    for name,mutate in cases:
        broken = copy.deepcopy(d)
        mutate(broken)
        try:
            audit(broken, inv, f)
        except ResearchFailure:
            continue
        raise ResearchFailure("negative metadata mutation accepted: " + name)
    return len(cases)


if __name__ == "__main__":
    dossier, inv, foundation = read(DOSSIER), read(INVENTORY), read(FOUNDATION)
    try:
        selected = audit(dossier, inv, foundation)
        if "--self-test" in sys.argv:
            fixtures, differential, invalid = model_cases()
            mutations = negative_metadata_tests(dossier, inv, foundation)
            print(f"D10-ANTI-UNIFY: PASS {fixtures} fixed, {differential} exhaustive ordered pairs, "
                  f"{invalid} rejected malformed inputs, {mutations} negative authority mutations; "
                  f"main-selected={selected}, admission=0, ratification=0")
        else:
            print(f"D10-ANTI-UNIFY: PASS research HOLD, selected={selected}, admission=0")
    except (ResearchFailure, RecursionError) as e:
        print(f"D10-ANTI-UNIFY: FAIL {e}", file=sys.stderr)
        raise SystemExit(1)
