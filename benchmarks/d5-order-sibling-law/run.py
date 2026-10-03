#!/usr/bin/env python3
"""#3004 — prove/falsify the local D5 LESSP/GREATERP sibling law.

Research-only. This does not change OD-005 coordinates and does not infer
D4 EVLIS parenthood.

Claim under test:
    GREATERP(a,b) == LESSP(b,a)

Authority consumed:
- OD-005 D5 owner map for exact coordinates 01110 / 01111;
- Lisp 1.5 arithmetic ingest for historical numeric domains and partiality;
- #2720 factorization for the order-family classification.

The current modern D1 runtime carrier is not re-derived here. It remains a
separate runtime-admission check owned by the D1/D5 cutover.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER_MAP = ROOT / "knowledge" / "d5-historical-full-map.json"
HISTORICAL_LEDGER = ROOT / "docs" / "research" / "2709-lisp15-arithmetic-ledger.json"


@dataclass(frozen=True)
class HistoricalNumber:
    value: Fraction
    carrier: str  # fixed | float


def lessp(a: HistoricalNumber, b: HistoricalNumber) -> bool:
    return a.value < b.value


def greaterp(a: HistoricalNumber, b: HistoricalNumber) -> bool:
    return a.value > b.value


def main() -> int:
    owner = json.loads(OWNER_MAP.read_text(encoding="utf-8"))
    ledger = json.loads(HISTORICAL_LEDGER.read_text(encoding="utf-8"))

    coordinates = {row["coordinate"]: row for row in owner["coordinates"]}
    assert coordinates["01110"]["name"] == "LESSP"
    assert coordinates["01111"]["name"] == "GREATERP"
    assert coordinates["01110"]["parent_d4"] == "0111"
    assert coordinates["01111"]["parent_d4"] == "0111"

    historical = {
        row["historical_name"].upper(): row
        for row in ledger["rows"]
        if row["historical_name"].upper() in {"LESSP", "GREATERP"}
    }
    assert set(historical) == {"LESSP", "GREATERP"}
    assert historical["LESSP"]["historical_behavior"] == "x < y"
    assert historical["GREATERP"]["historical_behavior"] == "x > y"
    assert historical["LESSP"]["historical_numeric_domain"] == "fixed-or-floating"
    assert historical["GREATERP"]["historical_numeric_domain"] == "fixed-or-floating"
    assert historical["LESSP"]["partiality"] == "nonnumeric -> error"
    assert historical["GREATERP"]["partiality"] == "nonnumeric -> error"
    assert historical["LESSP"]["historical_result"] == historical["GREATERP"]["historical_result"]

    values = [
        HistoricalNumber(Fraction(-3), "fixed"),
        HistoricalNumber(Fraction(-1, 2), "fixed"),
        HistoricalNumber(Fraction(0), "fixed"),
        HistoricalNumber(Fraction(2), "fixed"),
        HistoricalNumber(Fraction(-5, 2), "float"),
        HistoricalNumber(Fraction(0), "float"),
        HistoricalNumber(Fraction(3, 2), "float"),
        HistoricalNumber(Fraction(7), "float"),
    ]

    checks = 0
    equal_cases = 0
    cross_carrier_cases = 0

    for left in values:
        for right in values:
            lhs = greaterp(left, right)
            rhs = lessp(right, left)
            assert lhs == rhs, (left, right, lhs, rhs)

            # Equality must make both strict predicates false.
            if left.value == right.value:
                assert not lessp(left, right)
                assert not greaterp(left, right)
                equal_cases += 1

            if left.carrier != right.carrier:
                cross_carrier_cases += 1

            checks += 1

    # The sibling relation is semantic at the pair level, but the D4 prefix
    # remains only a coordinate-parent fact in this result. EVLIS semantics are
    # not used to derive either comparison.
    result = {
        "schema": "d5-order-sibling-law/v1",
        "domain": "Core.D5",
        "owner_occupancy_authority": "OD-005",
        "coordinates": {
            "01110": "LESSP",
            "01111": "GREATERP",
        },
        "law": "GREATERP(a,b) = LESSP(b,a)",
        "historical_domain": "fixed-or-floating",
        "partiality": "nonnumeric -> error on both siblings",
        "checks": checks,
        "equal_cases": equal_cases,
        "cross_carrier_cases": cross_carrier_cases,
        "classification": "LOCAL-SIBLING-LAW",
        "relation_class": "SEMANTIC-LAW",
        "d4_prefix": "0111",
        "d4_parenthood": "NOT-INFERRED",
        "modern_d1_result_carrier": "DOWNSTREAM-RUNTIME-GUARD",
        "owner_map_mutation": "NONE",
        "global_d5_suffix_theorem": "NOT-CLAIMED",
        "domain_firewall": "Core-Math order similarity does not supply Core.D5 authority",
    }

    print("D5-ORDER-SIBLING-LAW=PASS")
    print(f"checks={checks}")
    print(f"equal-cases={equal_cases}")
    print(f"cross-carrier-cases={cross_carrier_cases}")
    print("01110=LESSP")
    print("01111=GREATERP")
    print("LAW=GREATERP(a,b)==LESSP(b,a)")
    print("CLASSIFICATION=LOCAL-SIBLING-LAW")
    print("RELATION=SEMANTIC-LAW")
    print("D4-EVLIS-PARENTHOOD=NOT-INFERRED")
    print("OWNER-MAP-MUTATION=NONE")
    print("GLOBAL-D5-SUFFIX-THEOREM=NOT-CLAIMED")

    out = ROOT / "benchmarks" / "d5-order-sibling-law" / "result.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
