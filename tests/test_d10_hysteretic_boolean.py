#!/usr/bin/env python3
"""Exact rational D10 hysteresis; research semantic oracle, not native SENS T5."""
from __future__ import annotations
import copy, itertools, json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-hysteretic-boolean-source-law-20261009.json"
CURRENT = ROOT / "knowledge/d10-v1-semantic-inventory.json"
LOWER = ROOT / "knowledge/d1-d9-foundation.json"
NAME = "HYSTERETIC-BOOLEAN-STEP"

def exact(v):
    if isinstance(v, bool) or isinstance(v, float):
        raise TypeError("exact rational required")
    return Fraction(v)

def step(state: bool, low, high, x) -> bool:
    if type(state) is not bool:
        raise TypeError("only D1 YES/NO")
    a, b, v = exact(low), exact(high), exact(x)
    if a >= b:
        raise ValueError("lower threshold must be strictly less")
    if v <= a:
        return False
    if v >= b:
        return True
    return state

def oracle(state: bool, low: Fraction, high: Fraction, x: Fraction) -> bool:
    # Independent boolean formula, no branches over the three sample regions.
    if state:
        return x > low
    return x >= high

def dossier_guard(doc: dict, inventory: dict, foundation: dict):
    root = doc["selection_root"]
    assert doc["schema"] == "sens-d10-hysteretic-state-intake/v1"
    assert root["semantic_name"] == NAME
    assert doc["impacts"]["selected_delta_if_admitted"] == 1
    assert doc["impacts"]["ratified_delta"] == 0
    assert doc["pinned_before"]["d10_inventory_git_blob"] == "34efd273000e3de8510441764cb59acbb5ab284b"
    assert root["coordinate"] is None and root["coordinate_basis"] == "UNPLACED"
    assert root["status"] == "SELECTED-RESEARCH-CANDIDATE"
    assert root["ratified_resident"] is False and root["physical_t5_authorized"] is False
    assert len(root["positive_witnesses"]) >= 3 and len(root["falsifier_spec"]) > 60
    assert len(doc["derived_or_hold"]) >= 3
    assert all(z["decision"] != "SELECTED" for z in doc["derived_or_hold"])
    assert all(p["url"].startswith("https://") for p in doc["primary_sources"])
    existing_names = {str(x["semantic_name"]).upper() for x in inventory["rows"]}
    lower_names = {str(n).upper() for d in foundation["domains"].values()
                   for n in d.get("residents", {}).values()}
    assert NAME not in lower_names
    assert sum(n == NAME for n in existing_names) <= 1
    # The tests support running both before append and after canonical selection.
    for row in inventory["rows"]:
        if row["semantic_name"] == NAME:
            assert row["stable_id"] == root["stable_id"]
            assert row["behavior"] == root["behavior"]
            assert row["ratified_resident"] is False and row["coordinate"] is None

def negative_controls(doc, inventory, foundation):
    mutations = [
        lambda x: x["selection_root"].update(coordinate="0" * 10),
        lambda x: x["selection_root"].update(ratified_resident=True),
        lambda x: x["selection_root"].update(physical_t5_authorized=True),
        lambda x: x["selection_root"].update(semantic_name="COND"),
        lambda x: x["selection_root"].update(status="RATIFIED"),
        lambda x: x["pinned_before"].update(d10_inventory_git_blob="0"*40),
        lambda x: x["impacts"].update(ratified_delta=1),
        lambda x: x["selection_root"].update(positive_witnesses=[]),
        lambda x: x["derived_or_hold"][0].update(decision="SELECTED"),
    ]
    for i, mutate in enumerate(mutations):
        mutant = copy.deepcopy(doc)
        mutate(mutant)
        try:
            dossier_guard(mutant, inventory, foundation)
        except (AssertionError, KeyError, TypeError):
            continue
        raise AssertionError(f"negative control {i} escaped")

def main():
    doc = json.loads(DOSSIER.read_text(encoding="utf-8"))
    inventory = json.loads(CURRENT.read_text(encoding="utf-8"))
    foundation = json.loads(LOWER.read_text(encoding="utf-8"))
    dossier_guard(doc, inventory, foundation)

    samples = [Fraction(n, d) for d in (1, 2, 3) for n in range(-5, 6)]
    samples = sorted(set(samples))
    trials = 0
    for low, high in itertools.combinations(samples, 2):
        for sample in samples:
            for prior in (False, True):
                got = step(prior, low, high, sample)
                expected = oracle(prior, low, high, sample)
                assert got is expected
                assert step(got, low, high, sample) is got, "idempotence"
                if low < sample < high:
                    assert got is prior, "state retention"
                if sample <= low:
                    assert got is False, "bottom saturation"
                if sample >= high:
                    assert got is True, "upper saturation"
                trials += 1

    assert step(False, Fraction(0), Fraction(2), Fraction(1)) is False
    assert step(True, Fraction(0), Fraction(2), Fraction(1)) is True
    assert step(False, Fraction(0), Fraction(2), Fraction(2)) is True
    assert step(True, Fraction(0), Fraction(2), Fraction(0)) is False
    assert step(False, Fraction(-1,2), Fraction(1,2), Fraction(1,4)) is False
    assert step(True, Fraction(-1,2), Fraction(1,2), Fraction(1,4)) is True

    invalid = [
        (False, 1, 1, 1), (False, 2, 1, 1),
        (3, 0, 2, 1), (False, 0.0, 2, 1), (False, 0, 2, float("nan")),
    ]
    for args in invalid:
        try:
            step(*args)
        except (ValueError, TypeError):
            pass
        else:
            raise AssertionError(f"invalid sample/threshold accepted: {args}")
    negative_controls(doc, inventory, foundation)
    print(f"D10-HYSTERESIS: PASS exact_cases={trials}, rejected_bad_inputs={len(invalid)}, negative_mutations=9")
    print("D10-HYSTERESIS: selection remains research only, coordinate=null ratified=0")

if __name__ == "__main__":
    main()
