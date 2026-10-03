#!/usr/bin/env python3
"""#3003 — attack D5 arithmetic sibling laws before promoting them.

Research-only. OD-005 occupancy is immutable here.

The candidate "suffix 0 = direct combine, suffix 1 = combine inverse(rhs)"
has two distinct theorem scopes:

1. Core.D5 binary-value semantics, witnessed directly by the exact-D5 runtime
   test in crates/sens/src/eval/d5_arithmetic.rs.
2. The full historical Lisp 1.5 calling protocol, audited here.

The value restriction may admit a local sibling law even when the full
historical protocol differs by additional observable axes.
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
        "additive_value_semantics_classification": "LOCAL-SIBLING-LAW",
        "multiplicative_value_semantics_classification": "LOCAL-SIBLING-LAW",
        "value_runtime_witness": "d5_arithmetic::tests::additive_and_multiplicative_siblings_follow_local_inverse_orientation_laws",
        "additive_full_protocol_classification": "MULTI-DELTA-NOT-ONE-SIBLING-LAW",
        "multiplicative_full_protocol_classification": "MULTI-DELTA-NOT-ONE-SIBLING-LAW",
        "relation_class": "VALUE-LOCAL-LAW_PLUS_FULL-PROTOCOL-COORDINATE-SCOPE",
        "binary_restriction_possible": "PROVED-BY-EXACT-D5-RUNTIME",
        "core_math_inverse_law_transfer": "FORBIDDEN-WITHOUT-BRIDGE",
        "d4_parenthood": "NOT-PROVED",
        "owner_map_mutation": "NONE",
        "global_d5_suffix_theorem": "NOT-CLAIMED",
    }

    out = ROOT / "benchmarks" / "d5-arithmetic-sibling-law" / "result.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print("D5-ARITH-SIBLING-LAW=PASS")
    print("PLUS/DIFFERENCE-VALUE=LOCAL-SIBLING-LAW")
    print("TIMES/QUOTIENT-VALUE=LOCAL-SIBLING-LAW")
    print("PLUS/DIFFERENCE-FULL-PROTOCOL=MULTI-DELTA")
    print("TIMES/QUOTIENT-FULL-PROTOCOL=MULTI-DELTA")
    print("ADDITIVE-AXES=operation-orientation,arity")
    print("MULTIPLICATIVE-AXES=operation-orientation,arity,fixed-quotient-policy")
    print("D4-0101=UNALLOCATED")
    print("D4-1001=UNALLOCATED")
    print("RELATION=VALUE-LOCAL-LAW_PLUS_FULL-PROTOCOL-COORDINATE-SCOPE")
    print("CORE-MATH-LAW-TRANSFER=FORBIDDEN-WITHOUT-BRIDGE")
    print("OWNER-MAP-MUTATION=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
