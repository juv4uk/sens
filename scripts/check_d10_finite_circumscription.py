#!/usr/bin/env python3
"""Research-only finite McCarthy circumscription, never a new SENS opcode.

Two independently structured finite exact reference solvers:
(1) pairwise strict-dominance, (2) grouped minimal-projection antichains.
Neither is an actual historical Advice Taker / ASP / SAT donor runtime.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-mccarthy-finite-circumscription-20261009.json"
LEDGER = ROOT / "knowledge/d10-proposal-ledger.tsv"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
EXPECTED_NAME = "FINITE-PREDICATE-CIRCUMSCRIPTION"
EXPECTED_ID = "D10P-0012"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def git_blob_sha(path):
    b = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()

def parameters(width, models, minimized, fixed):
    if type(width) is not int or not (1 <= width <= 8):
        raise ValueError("explicit finite word width required (1..8)")
    full = (1 << width) - 1
    if any(type(m) is not int or m < 0 or m > full for m in (minimized, fixed)):
        raise ValueError("invalid minimized or fixed predicate mask")
    if minimized & fixed:
        raise ValueError("minimized and fixed predicates must be disjoint")
    if not isinstance(models, (list, tuple)) or any(
        type(m) is not int or m < 0 or m > full for m in models
    ):
        raise ValueError("models must be explicit finite valuations")
    if len(set(models)) != len(models):
        raise ValueError("duplicate full valuations are not a canonical set")
    return sorted(models)

def strict_preferred(a, b, minimized, fixed):
    """a dominates b only inside the same fixed-signature equivalence class."""
    amin, bmin = a & minimized, b & minimized
    return (a & fixed) == (b & fixed) and amin != bmin and (amin & bmin) == amin

def by_pairwise(width, models, minimized, fixed):
    vals = parameters(width, models, minimized, fixed)
    if not vals:
        return {"status": "NO-MODELS", "models": []}
    preferred = [
        m for m in vals if not any(
            strict_preferred(other, m, minimized, fixed)
            for other in vals if other != m
        )
    ]
    return {"status": "PREFERRED-MODELS", "models": preferred}

def by_projected_antichains(width, models, minimized, fixed):
    """Independent method: form sets of minimal projected abnormality masks."""
    vals = parameters(width, models, minimized, fixed)
    if not vals:
        return {"status": "NO-MODELS", "models": []}
    groups = {}
    for value in vals:
        groups.setdefault(value & fixed, set()).add(value & minimized)
    minimal = {}
    for signature, masks in groups.items():
        antichain = set()
        for value in masks:
            strict_smaller = any(
                (candidate & value) == candidate and candidate != value
                for candidate in masks
            )
            if not strict_smaller:
                antichain.add(value)
        minimal[signature] = antichain
    preferred = [v for v in vals if (v & minimized) in minimal[v & fixed]]
    return {"status": "PREFERRED-MODELS", "models": preferred}

def query_status(result, atom_bit):
    if result["status"] == "NO-MODELS":
        return "NO-MODELS"
    truths = [bool(v & (1 << atom_bit)) for v in result["models"]]
    if all(truths):
        return "SKEPTICALLY-TRUE"
    if not any(truths):
        return "SKEPTICALLY-FALSE"
    return "UNDECIDED"

def guard(proposal, ledger_text, inventory, foundation):
    assert proposal["schema"] == "d10-mccarthy-finite-predicate-circumscription/v1"
    assert proposal["proposed_semantic_name"] == EXPECTED_NAME
    assert proposal["proposal_id"] == EXPECTED_ID
    assert proposal["status"] == "PENDING-REVIEW-UNSELECTED-UNRATIFIED"
    assert proposal["selected"] is False
    assert proposal["ratified"] is False
    assert proposal["coordinate"] is None
    assert proposal["physical_t5_authorized"] is False
    assert proposal["review"]["owner_required"] is True
    assert proposal["review"]["new_core_function_not_proven"] is True
    assert proposal["review"]["expressibility_as_library_open"] is True
    assert proposal["review"]["independent_external_solver_not_run"] is True
    assert proposal["snapshot"]["foundation_blob"] == git_blob_sha(FOUNDATION)
    assert proposal["snapshot"]["d10_ratified_at_review"] == 0
    assert inventory["accounting"]["selected_semantic_candidates"] >= proposal["snapshot"]["d10_selected_at_review"]
    assert inventory["accounting"]["ratified_d10_residents"] == 0
    assert len(inventory["rows"]) == inventory["accounting"]["selected_semantic_candidates"]
    ratified_names = {
        str(name).upper()
        for domain in foundation["domains"].values()
        for name in domain["residents"].values()
    }
    selected_names = {row["semantic_name"].upper() for row in inventory["rows"]}
    assert EXPECTED_NAME not in ratified_names
    assert EXPECTED_NAME not in selected_names, "another agent selected this: reconcile"
    assert proposal["semantics"]["scope"].startswith("Ground propositional finite")
    assert "NOT" in proposal["semantics"]["boundary"]
    assert len(proposal["examples"]) >= 6
    assert len(proposal["crossdomain"]) >= 4
    assert proposal["historical_origin"]["doi"] == "10.1016/0004-3702(80)90011-9"
    lines = [line.split("\t") for line in ledger_text.strip().splitlines()]
    assert all(len(cells) == 12 for cells in lines)
    assert lines[0] == [
        "proposal_id","surface_uk","surface_ukr","semantic_name","semantic_law",
        "width","donor_provenance","dedup_check","ownership_test",
        "blocked_source","status","ratified",
    ]
    assert len({row[0] for row in lines[1:]}) == len(lines)-1
    assert len({row[3] for row in lines[1:]}) == len(lines)-1
    matching = [row for row in lines[1:] if row[0] == EXPECTED_ID]
    assert len(matching) == 1
    row = matching[0]
    assert row[3] == EXPECTED_NAME and row[5] == "D10"
    assert row[1] == proposal["surface_uk"] and row[2] == proposal["surface_ukr"]
    assert row[6] == ("juv4uk/sens@9e79f08935dd9d92c23047a4b2b89b10a76ea32f:docs/mccarthy-machine-map.md:89")
    assert row[7] == (f"D1-D9@{proposal['snapshot']['foundation_blob']}=NO-MATCH;"
                      f"D10@{proposal['snapshot']['d10_inventory_blob_at_review']}=NO-MATCH")
    assert row[8].startswith("UNIVERSAL-BORDER: ") and "Core-vs-library HOLD" in row[8]
    assert row[9:] == ["NOT-A-MIGRATION-BLOCK","pending-review","0"]
    assert len(proposal["nearby_existing"]["D9"]) >= 3
    return True

def witness_tests(proposal):
    cases = 0
    for example in proposal["examples"]:
        args = (example["width"], example["models"],
                example["minimize_mask"], example["fixed_mask"])
        a = by_pairwise(*args)
        b = by_projected_antichains(*args)
        assert a == b
        assert a["models"] == example["want"], example["label"]
        assert a["status"] == example.get("status", "PREFERRED-MODELS")
        cases += 1
    # Cardinality ranking would incorrectly reject 3 when compared with 4.
    assert by_pairwise(3, [3,4], 7, 0)["models"] == [3,4]
    # Two distinct full models with the same minimized projection both survive.
    assert by_pairwise(3, [0,2], 1, 0)["models"] == [0,2]
    # Defeasible: new hard evidence can withdraw a previous minimization.
    assert by_pairwise(2, [0,1], 1, 0)["models"] == [0]
    assert by_pairwise(2, [1], 1, 0)["models"] == [1]
    # Unknown is not false: models disagree about an unminimized proposition.
    assert query_status(by_pairwise(3, [0,4], 1, 0), 2) == "UNDECIDED"
    assert query_status(by_pairwise(2, [], 1, 0), 0) == "NO-MODELS"
    return cases + 5

def exhaustive_crosscheck():
    cases = 0
    for width in (1,2,3):
        values = list(range(1 << width))
        for minmask in values:
            for fixedmask in values:
                if minmask & fixedmask:
                    continue
                for subset in range(1 << len(values)):
                    models = [m for m in values if (subset >> m) & 1]
                    a = by_pairwise(width, models, minmask, fixedmask)
                    b = by_projected_antichains(width, models, minmask, fixedmask)
                    assert a == b
                    assert a["models"] == sorted(set(a["models"]))
                    # A nonpreferred valuation has an explicit strict dominator.
                    if models:
                        assert a["status"] == "PREFERRED-MODELS"
                        for rejected in set(models) - set(a["models"]):
                            assert any(strict_preferred(v, rejected, minmask, fixedmask)
                                       for v in models)
                    else:
                        assert a["status"] == "NO-MODELS"
                    assert a == by_pairwise(width, list(reversed(models)), minmask, fixedmask)
                    cases += 1
    rng = random.Random(1959)
    for width, iterations in ((4,750),(5,300)):
        all_models = list(range(1 << width))
        for _ in range(iterations):
            bits = list(range(width))
            rng.shuffle(bits)
            minmask = 0
            fixedmask = 0
            for bit in bits:
                k = rng.randrange(3)
                if k == 0:
                    minmask |= 1 << bit
                elif k == 1:
                    fixedmask |= 1 << bit
            models = [m for m in all_models if rng.randrange(3) == 0]
            assert by_pairwise(width, models, minmask, fixedmask) == (
                by_projected_antichains(width, models, minmask, fixedmask)
            )
            cases += 1
    return cases

def negative_controls(proposal, ledger_text, inventory, foundation):
    failures = 0
    def expect_bad(mutator):
        nonlocal failures
        p = copy.deepcopy(proposal)
        l = ledger_text
        i = copy.deepcopy(inventory)
        mutator(p, i)
        try:
            guard(p, l, i, foundation)
        except (AssertionError, ValueError):
            failures += 1
            return
        raise AssertionError("unsafe metadata mutation was allowed")
    expect_bad(lambda p,i: p.__setitem__("selected",True))
    expect_bad(lambda p,i: p.__setitem__("ratified",True))
    expect_bad(lambda p,i: p.__setitem__("coordinate","0000000000"))
    expect_bad(lambda p,i: p.__setitem__("status","SELECTED"))
    expect_bad(lambda p,i: p.__setitem__("proposed_semantic_name","CAR"))
    expect_bad(lambda p,i: p["snapshot"].__setitem__("foundation_blob","0"*40))
    expect_bad(lambda p,i: p["review"].__setitem__("owner_required",False))
    expect_bad(lambda p,i: i["rows"].append({
        "semantic_name":EXPECTED_NAME
    }))
    for args in [
        (0, [0], 0, 0),
        (2, [0,1], 1, 1),
        (2, [0,4], 1, 0),
        (2, [0,0], 1, 0),
        (2, [0,True], 1, 0),
        (2, [0], 4, 0),
    ]:
        try: by_pairwise(*args)
        except ValueError: failures += 1
        else: raise AssertionError("invalid input admitted")
    return failures

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    opts = parser.parse_args()
    p = read(DOSSIER)
    ledger = LEDGER.read_text(encoding="utf-8")
    inv, fnd = read(INVENTORY), read(FOUNDATION)
    guard(p, ledger, inv, fnd)
    n = witness_tests(p)
    count = exhaustive_crosscheck()
    neg = negative_controls(p, ledger, inv, fnd) if opts.self_test else 0
    print(f"FINITE CIRCUMSCRIPTION RESEARCH PASS: primary examples={n}; independent finite crosschecks={count}; negative controls={neg}; D10 selected unchanged={inv['accounting']['selected_semantic_candidates']}; ratified=0; coordinate=null")

if __name__ == "__main__":
    main()
