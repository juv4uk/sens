#!/usr/bin/env python3
"""#3032 — classify Core.D5 ZEROP/NUMBERP as a typed entailment.

Research-only. Reuses the merged historical numeric-predicate factor model.
No owner coordinate or production numeric mechanism is changed.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OWNER_MAP = ROOT / "knowledge" / "d5-historical-full-map.json"
DONOR = ROOT / "benchmarks" / "lisp15-numeric-predicate-factor" / "run.py"
OUT = ROOT / "knowledge" / "d5-zerop-numberp-pair.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_donor():
    spec = importlib.util.spec_from_file_location("lisp15_numeric_predicate_factor", DONOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def owner_row(owner: dict[str, Any], coordinate: str) -> dict[str, Any]:
    rows = [row for row in owner["coordinates"] if row["coordinate"] == coordinate]
    assert len(rows) == 1
    return rows[0]


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render() -> dict[str, Any]:
    owner = load_json(OWNER_MAP)
    donor = load_donor()

    assert owner["domain"] == "Core.D5"
    assert owner["width"] == 5
    assert owner["status_counts"]["total"] == 32
    assert owner["status_counts"]["unallocated"] == 0

    zerop = owner_row(owner, "01000")
    numberp = owner_row(owner, "01001")
    assert zerop["name"] == "ZEROP"
    assert numberp["name"] == "NUMBERP"
    assert zerop["parent_d4"] == numberp["parent_d4"] == "0100"

    decisions = {row["historical_row"]: row for row in donor.decision_rows()}
    assert decisions["ZEROP"]["relation"] == "DERIVED"
    assert decisions["NUMBERP"]["relation"] == "BRIDGE-CANDIDATE"
    assert "tolerance" in decisions["ZEROP"]["modern_domain"]
    assert "carrier classifier" in decisions["NUMBERP"]["modern_domain"]

    HistoricalNumber = donor.HistoricalNumber
    epsilon = donor.EPSILON

    def historical_numberp(value: object) -> bool:
        # This is the carrier predicate already modeled by #2720: fixed/float
        # historical numeric values are the domain of historical ZEROP.
        return isinstance(value, HistoricalNumber)

    numeric_corpus = [
        HistoricalNumber(donor.Fraction(0), "fixed"),
        HistoricalNumber(epsilon, "float"),
        HistoricalNumber(epsilon - donor.Fraction(1, 10_000_000), "float"),
        HistoricalNumber(epsilon + donor.Fraction(1, 10_000_000), "float"),
        HistoricalNumber(donor.Fraction(1), "fixed"),
        HistoricalNumber(donor.Fraction(-2), "fixed"),
    ]

    implication_checks = 0
    zerop_yes_cases = 0
    for value in numeric_corpus:
        z = donor.historical_zerop(value)
        n = historical_numberp(value)
        if z:
            zerop_yes_cases += 1
            assert n, value
        implication_checks += 1

    assert zerop_yes_cases >= 2

    # Converse falsifier: one is numeric but not zero under the historical
    # tolerance policy.
    one = HistoricalNumber(donor.Fraction(1), "fixed")
    assert historical_numberp(one)
    assert not donor.historical_zerop(one)

    # Carrier boundary: a nonnumeric S-expression is not NUMBERP. We do not
    # feed it to historical_zerop because #2720 models ZEROP over numeric
    # magnitude; that precondition is exactly what yields the implication.
    nonnumeric = ("PAIR", "A", "B")
    assert not historical_numberp(nonnumeric)

    # Historical tolerance remains visible and must not collapse to exact zero.
    boundary = HistoricalNumber(epsilon, "float")
    assert donor.historical_zerop(boundary)
    assert not donor.exact_q_zerop(donor.bridge_exact_value(boundary))

    result = {
        "schema": "d5-zerop-numberp-pair/1",
        "domain": "Core.D5",
        "owner_map_authority": owner["authority"],
        "owner_map_mutation": "NONE",
        "pair": {
            "prefix_d4": "0100",
            "child0": {"coordinate": "01000", "historical_name": "ZEROP"},
            "child1": {"coordinate": "01001", "historical_name": "NUMBERP"},
        },
        "law": "ZEROP(x)=YES implies NUMBERP(x)=YES on the declared historical numeric carrier",
        "converse": "FALSIFIED",
        "converse_counterexample": "historical numeric 1: NUMBERP=YES, ZEROP=NO",
        "classification": "ENTAILMENT-LAW",
        "relation_class": "SEMANTIC-LAW",
        "local_one_bit_sibling_transform": False,
        "d4_parenthood": "NOT-INFERRED",
        "global_d5_suffix_theorem": "NOT-PROVED",
        "historical_tolerance_preserved": True,
        "implication_checks": implication_checks,
        "zerop_yes_cases": zerop_yes_cases,
        "evidence": ["#2720/#2730", "#3019", "#2508"],
        "falsifier": "any declared historical numeric input with ZEROP=YES and NUMBERP!=YES",
    }
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    result = render()
    if args.write:
        OUT.write_text(canonical(result), encoding="utf-8")
    if args.check:
        assert OUT.exists(), "D5 ZEROP/NUMBERP report missing"
        assert json.loads(OUT.read_text(encoding="utf-8")) == result, (
            "D5 ZEROP/NUMBERP report stale"
        )

    print("D5-ZEROP-NUMBERP-PAIR=PASS")
    print("coordinates=01000,01001")
    print("classification=ENTAILMENT-LAW")
    print("law=ZEROP-YES-implies-NUMBERP-YES")
    print("converse=FALSIFIED")
    print("local-one-bit-sibling-transform=no")
    print("d4-parenthood=NOT-INFERRED")
    print("global-d5-suffix-theorem=NOT-PROVED")
    print("owner-map-mutation=NONE")


if __name__ == "__main__":
    main()
