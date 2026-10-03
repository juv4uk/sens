#!/usr/bin/env python3
"""#3003 — attack D5 arithmetic sibling laws before promoting them.

Research-only. OD-005 occupancy is immutable here.

The candidate "suffix 0 = direct combine, suffix 1 = combine inverse(rhs)"
would be a LOCAL-SIBLING-LAW only if the siblings differed by one observable
axis on the same full operation protocol.

This witness consumes the owner map + D4 authority + primary historical ledger
and checks whether that one-delta condition is even available.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER_MAP = ROOT / "knowledge" / "d5-historical-full-map.json"
WIDTH_CORPUS = ROOT / "knowledge" / "exact-width-admitted-corpus.json"
HISTORY = ROOT / "docs" / "research" / "2709-lisp15-arithmetic-ledger.json"


def main() -> int:
    owner = json.loads(OWNER_MAP.read_text(encoding="utf-8"))
    corpus = json.loads(WIDTH_CORPUS.read_text(encoding="utf-8"))
    history = json.loads(HISTORY.read_text(encoding="utf-8"))

    d5 = {row["coordinate"]: row for row in owner["coordinates"]}
    assert d5["01010"]["name"] == "PLUS"
    assert d5["01011"]["name"] == "DIFFERENCE"
    assert d5["10010"]["name"] == "TIMES"
    assert d5["10011"]["name"] == "QUOTIENT"

    d4 = {
        row["word"]: row
        for row in corpus["rows"]
        if row["width"] == 4
    }
    assert d4["0101"]["status"] == "unallocated"
    assert d4["1001"]["status"] == "unallocated"

    rows = {
        row["historical_name"].upper(): row
        for row in history["rows"]
        if row["historical_name"].upper()
        in {"PLUS", "DIFFERENCE", "TIMES", "QUOTIENT"}
    }
    assert set(rows) == {"PLUS", "DIFFERENCE", "TIMES", "QUOTIENT"}

    # Historical full-protocol comparison.
    assert rows["PLUS"]["arity"] == "variadic"
    assert rows["DIFFERENCE"]["arity"] == "2"
    assert rows["TIMES"]["arity"] == "variadic"
    assert rows["QUOTIENT"]["arity"] == "2"

    assert rows["PLUS"]["historical_behavior"] == "algebraic sum of arguments"
    assert rows["DIFFERENCE"]["historical_behavior"] == "x-y"
    assert rows["TIMES"]["historical_behavior"] == "product of arguments"
    assert rows["QUOTIENT"]["historical_behavior"] == "quotient of x and y"

    # The one-bit local sibling hypothesis says "same operation protocol +
    # one orientation delta". Historical evidence already exposes an
    # independent arity delta for both pairs, so the full-operation one-delta
    # theorem is falsified before any algebraic inverse law is imported.
    additive_axes = ("operation-orientation", "arity")
    multiplicative_axes = ("operation-orientation", "arity", "fixed-quotient-policy")

    assert len(additive_axes) > 1
    assert len(multiplicative_axes) > 1

    # QUOTIENT has an independently documented historical fixed-point policy.
    # Do not replace it with Core-Math exact-Q reciprocal semantics by analogy.
    assert "number-theoretic quotient" in rows["QUOTIENT"]["partiality"]
    assert rows["QUOTIENT"]["relation_to_core_math"] == "comparison-only-no-shared-identity"

    result = {
        "schema": "d5-arithmetic-sibling-law/v1",
        "domain": "Core.D5",
        "owner_occupancy_authority": "OD-005",
        "coordinates": {
            "01010": "PLUS",
            "01011": "DIFFERENCE",
            "10010": "TIMES",
            "10011": "QUOTIENT",
        },
        "d4_prefixes": {
            "0101": "UNALLOCATED",
            "1001": "UNALLOCATED",
        },
        "candidate_law": "suffix selects direct-vs-inverse rhs orientation",
        "additive_full_protocol_delta_axes": list(additive_axes),
        "multiplicative_full_protocol_delta_axes": list(multiplicative_axes),
        "additive_classification": "MULTI-DELTA-NOT-LOCAL-SIBLING-LAW",
        "multiplicative_classification": "MULTI-DELTA-NOT-LOCAL-SIBLING-LAW",
        "relation_class": "COORDINATE-LAW",
        "binary_restriction_possible": "UNRESOLVED",
        "core_math_inverse_law_transfer": "FORBIDDEN-WITHOUT-BRIDGE",
        "d4_parenthood": "NOT-PROVED",
        "owner_map_mutation": "NONE",
        "global_d5_suffix_theorem": "NOT-CLAIMED",
    }

    out = ROOT / "benchmarks" / "d5-arithmetic-sibling-law" / "result.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print("D5-ARITH-SIBLING-LAW=PASS")
    print("PLUS/DIFFERENCE=FULL-PROTOCOL-MULTI-DELTA")
    print("TIMES/QUOTIENT=FULL-PROTOCOL-MULTI-DELTA")
    print("ADDITIVE-AXES=operation-orientation,arity")
    print("MULTIPLICATIVE-AXES=operation-orientation,arity,fixed-quotient-policy")
    print("D4-0101=UNALLOCATED")
    print("D4-1001=UNALLOCATED")
    print("RELATION=COORDINATE-LAW")
    print("CORE-MATH-LAW-TRANSFER=FORBIDDEN-WITHOUT-BRIDGE")
    print("OWNER-MAP-MUTATION=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
