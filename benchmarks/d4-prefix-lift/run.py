#!/usr/bin/env python3
"""#3212 — mechanical verifier for the D4 prefix-lift cutover.

This is NOT a semantic scoring search. Semantic work is already upstream.
It selects one deterministic representative from remaining gauge freedom by
lifting the owner-ratified D3 permutation to the D4 prefix and preserving
the existing one-bit pair orientation.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "benchmarks/d3-d8-remap-solver/d3-d4-fixture.json"

NEW_D3 = {
    "NIL": "000",
    "QUOTE": "001",
    "ATOM": "010",
    "CDR": "011",
    "CAR": "100",
    "EQ": "101",
    "COND": "110",
    "CONS": "111",
}

EXPECTED_D4 = {
    "APPLY": "0000",
    "EVAL": "0001",
    "LAMBDA": "0010",
    "DEFINE": "0011",
    "NOT": "0100",
    "arithmetic-family-A": "0101",
    "CDAR": "0110",
    "CDDR": "0111",
    "CAAR": "1000",
    "CADR": "1001",
    "LOOKUP": "1010",
    "BIND": "1011",
    "EVCON": "1100",
    "EVLIS": "1101",
    "LIST": "1110",
    "arithmetic-family-M": "1111",
}

SELECTORS = {
    "CAAR": "1000",
    "CADR": "1001",
    "CDAR": "0110",
    "CDDR": "0111",
}

def main() -> int:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    d3 = data["domains"]["D3"]["residents"]
    d4 = data["domains"]["D4"]["residents"]

    old_d3 = {r["report_label"]: r["current_bits"] for r in d3}
    assert set(old_d3) == set(NEW_D3)

    prefix_perm = {old_d3[name]: NEW_D3[name] for name in NEW_D3}
    assert len(prefix_perm) == 8
    assert len(set(prefix_perm.values())) == 8

    candidate = {}
    migration = []
    for row in d4:
        old = row["current_bits"]
        label = row["report_label"]
        new = prefix_perm[old[:3]] + old[3]
        candidate[label] = new
        if old != new:
            migration.append({"resident": label, "old": old, "new": new})

    # 16/16 exact bijection and exact resident preservation.
    assert len(candidate) == 16
    assert len(set(candidate.values())) == 16
    assert set(candidate) == set(EXPECTED_D4)
    assert candidate == EXPECTED_D4

    # New selector law is satisfied exactly.
    for name, bits in SELECTORS.items():
        assert candidate[name] == bits

    # Every previous two-member D4 fibre keeps its suffix orientation.
    old_by_prefix = {}
    for row in d4:
        old_by_prefix.setdefault(row["current_bits"][:3], []).append(row)
    assert set(len(rows) for rows in old_by_prefix.values()) == {2}
    for rows in old_by_prefix.values():
        suffixes = {r["current_bits"][-1]: r["report_label"] for r in rows}
        assert set(suffixes) == {"0", "1"}
        for suffix, label in suffixes.items():
            assert candidate[label][-1] == suffix

    # Expected migration economy under the deterministic lift.
    unchanged = 16 - len(migration)
    assert len(migration) == 10
    assert unchanged == 6

    report = {
        "schema": "d4-prefix-lift/v1",
        "issue": 3212,
        "status": "mechanically-verified-canonical-representative",
        "semantic_note": "prefix lift is a gauge tie-break, not a new semantic law",
        "prefix_permutation": prefix_perm,
        "candidate": candidate,
        "moved": len(migration),
        "unchanged": unchanged,
        "migration": migration,
    }

    out = ROOT / "benchmarks/d4-prefix-lift/result.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("D4-PREFIX-LIFT: PASS")
    print("residents=16/16")
    print("selectors=4/4")
    print("pair-orientation=8/8")
    print(f"moved={len(migration)} unchanged={unchanged}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
