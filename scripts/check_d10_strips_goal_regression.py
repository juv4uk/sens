#!/usr/bin/env python3
"""Source-grounded historical STRIPS regression with real SWI-Prolog donor.

No binary SENS or D10 selected/ratification claim. Actual source donor tests
are run with --real-donor, never simulated as passing.
"""
import argparse
import copy
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-strips-goal-regression-research-v1.json"
ORACLE = ROOT / "tests/oracles/d10_strips_regression_swi.pl"
FOUND = ROOT / "knowledge/d1-d9-foundation.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
NAME = "STRIPS-GOAL-REGRESSION"
SOURCE = "https://www.sciencedirect.com/science/article/pii/0004370271900105"
FORMAL = "https://artint.info/2e/html2e/ArtInt2e.Ch6.S3.html"
EXPECT = (
    "persists_frame",
    "regresses_frame",
    "delete_conflict",
    "relevant_add",
    "irrelevant_but_sound",
    "no_forced_action_usefulness",
    "precondition_must_hold",
    "goal_not_precondition",
    "before_preconditions",
    "empty_goal_requires_preconditions",
    "empty_preconditions",
    "add_del_disjoint_required",
    "unsorted_set_rejected",
    "duplicate_set_rejected",
    "variable_symbol_rejected",
    "nonatom_term_rejected",
    "non_ground_goal_rejected",
    "delete_list_does_not_mean_negated_precondition",
    "negative_goal_is_out_of_scope",
    "two_step_plan_backwards",
    "two_step_plan_forwards",
    "impossible_goal_even_with_precondition",
    "independent_goal_survives",
    "exhaustive_forward_backward_equivalence",
)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(dossier, found, inventory, prolog):
    assert dossier["schema"] == "d10-historical-symbolic-ai-strips-regression/v1"
    assert dossier["status"] == "RESEARCH-ONLY-HOLD-CORE-VS-LIBRARY"
    assert dossier["selected_additions"] == 0
    assert dossier["ratified_additions"] == 0
    assert dossier["coordinates_added"] == 0
    assert dossier["prior_d10_inventory_blob"] == "65014431ac3e64633cd0be3630cfafc5e7a9aea3"
    assert len(dossier["historical_sources"]) == 3
    assert dossier["historical_sources"][1]["url"] == SOURCE
    assert dossier["historical_sources"][1]["year"] == 1971
    assert dossier["historical_sources"][0]["year"] == 1959
    assert dossier["historical_sources"][2]["url"] == FORMAL
    row = dossier["semantic_candidate"]
    assert row["stable_id"] == "d10.symbolic-ai.strips-ground-positive-regress.v1"
    assert row["semantic_name"] == NAME
    assert row["status"] == "REVIEW-HOLD-NOT-SELECTED"
    assert row["selected"] is False
    assert row["ratified"] is False
    assert row["coordinate"] is None
    assert row["native_SENS_parity"] is False
    assert row["source_primary_url"] == SOURCE
    assert row["source_semantics_url"] == FORMAL
    assert row["surface_uk"] and row["surface_ukr"]
    assert "G\\Add" in row["law"] and "G\\Add" in row["law"]
    assert "not required" in row["law"].lower() or "NOT required" in row["law"]
    assert "closed" in row["scope"].lower()
    assert len(row["positive_witnesses"]) >= 4
    assert len(row["falsifiers"]) >= 4
    assert row["prolog_oracle"]["individual_observations"] == len(EXPECT) == 24
    assert row["prolog_oracle"]["exhaustive_ground_models"] == 13824
    assert dossier["domain"] == "D10" and dossier["width"] == 10
    assert len(dossier["research_holds"]) == 4
    assert all(h["status"].startswith("HOLD-") for h in dossier["research_holds"])
    assert found["status"] == "owner-ratified"
    assert inventory["domain"] == "D10" and inventory["width"] == 10
    assert inventory["accounting"]["selected_semantic_candidates"] == len(inventory["rows"])
    assert inventory["accounting"]["ratified_d10_residents"] == 0
    assert len(inventory["rows"]) >= 634
    lower = {str(n).upper() for d in found["domains"].values() for n in d["residents"].values()}
    assert NAME not in lower
    selected = {r["semantic_name"] for r in inventory["rows"]}
    if NAME in selected:
        target = next(r for r in inventory["rows"] if r["semantic_name"] == NAME)
        # Later owner-approved selection can grow the research inventory, but
        # cannot retroactively ratify this historical donor dossier.
        assert target.get("coordinate") is None
        assert target.get("ratified_resident") is False
        assert target.get("source_path") == "knowledge/d10-strips-goal-regression-research-v1.json"
    evidence = re.findall(r'witness\(([a-z][a-z0-9_]*)\s*,', prolog)
    assert tuple(evidence) == EXPECT, "changed real donor test IDs"
    assert "all_small_ground_models(13824)" in prolog
    assert "valid_operator" in prolog and "regress" in prolog
    assert "progress" in prolog and "same_regression_semantics" in prolog
    return {"source_laws": 1, "held_neighbours": 4, "oracle_cases": len(EXPECT),
            "ground_model_comparisons": 13824, "d10_selected": len(inventory["rows"])}


def adversarial_controls(d, f, i, oracle):
    cases = [
        ("counterfeit_source", lambda x: x["historical_sources"][1].update(url="https://invalid.example")),
        ("fictitious_ratification", lambda x: x["semantic_candidate"].update(ratified=True)),
        ("fictitious_coordinate", lambda x: x["semantic_candidate"].update(coordinate="0000000000")),
        ("fake_selected", lambda x: x["semantic_candidate"].update(selected=True)),
        ("fake_runtime_parity", lambda x: x["semantic_candidate"].update(native_SENS_parity=True)),
        ("remove_falsifiers", lambda x: x["semantic_candidate"].update(falsifiers=[])),
        ("claim_new_resident", lambda x: x.update(selected_additions=1)),
        ("make_1959_paper_STRIPS", lambda x: x["historical_sources"][0].update(year=1971)),
        ("erase_held_neighbours", lambda x: x.update(research_holds=[])),
    ]
    for tag, change in cases:
        bad = copy.deepcopy(d)
        change(bad)
        try:
            validate(bad, f, i, oracle)
        except (AssertionError, KeyError):
            continue
        raise AssertionError("unsafe metadata mutation accepted: " + tag)
    bad_oracle = oracle.replace("exhaustive_forward_backward_equivalence", "forged_claim", 1)
    try:
        validate(d, f, i, bad_oracle)
    except AssertionError:
        pass
    else:
        raise AssertionError("forged oracle witness ID accepted")
    print("D10 STRIPS historical source+geometry adversarial controls PASS 10/10")


def real_swi(binary):
    run = subprocess.run([binary, "-q", "-s", str(ORACLE)], cwd=ROOT,
                         capture_output=True, text=True, timeout=120, check=False)
    if run.returncode:
        raise AssertionError("real SWI donor failed\n" + run.stdout + "\n" + run.stderr)
    witnessed = []
    summary = []
    for line in run.stdout.splitlines():
        if line.startswith("OBS\t"):
            fields = line.split("\t")
            assert len(fields) == 3 and fields[2] == "PASS", line
            witnessed.append(fields[1])
        elif line.startswith("STRIPS-SUMMARY\t"):
            summary.append(line)
        elif line.strip():
            raise AssertionError("unrecognized Prolog donor output: " + line)
    assert tuple(witnessed) == EXPECT
    assert summary == ["STRIPS-SUMMARY\tSWI-PROLOG\t24\tEXHAUSTIVE-13824"]
    version = subprocess.run([binary, "--version"], capture_output=True, text=True,
                             check=True, timeout=10).stdout.strip()
    print("D10 STRIPS real " + version + " oracle PASS 24/24 + exhaustive 13824/13824")
    print("Claim boundary: source-grounded mathematical model, NOT physical SENS parity")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-donor", action="store_true")
    parser.add_argument("--swipl", default="swipl")
    args = parser.parse_args()
    d, f, i = read(DOSSIER), read(FOUND), read(INVENTORY)
    text = ORACLE.read_text(encoding="utf-8")
    state = validate(d, f, i, text)
    adversarial_controls(d, f, i, text)
    print("D10 STRIPS historical review: STATIC PASS", json.dumps(state, sort_keys=True))
    if args.real_donor:
        real_swi(args.swipl)
