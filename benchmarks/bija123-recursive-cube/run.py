#!/usr/bin/env python3
"""#3196: derive bija3 as D2 x D1 with recursive complement duality.

Research-only. This witness admits only D1, D2 and the eight D3 residents.
It does not read D4-D8, historical/current opcode tables or migration cost.
"""
from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

D1 = {"0": "NO", "1": "YES"}
D2 = {"00": "separator", "01": "close", "10": "open", "11": "dot"}

RESIDENTS = ("EMPTY", "QUOTE", "ATOM", "CDR", "CAR", "EQ", "COND", "CONS")
CODES = tuple(f"{i:03b}" for i in range(8))

FIBRES = {
    "00": ("EMPTY", "QUOTE"),
    "01": ("ATOM", "CDR"),
    "10": ("CAR", "EQ"),
    "11": ("COND", "CONS"),
}

DUALS = (
    ("EMPTY", "CONS"),
    ("QUOTE", "COND"),
    ("ATOM", "EQ"),
    ("CDR", "CAR"),
)

USER = {
    "EMPTY": "000",
    "QUOTE": "001",
    "ATOM": "010",
    "CDR": "011",
    "CAR": "100",
    "EQ": "101",
    "COND": "110",
    "CONS": "111",
}

PURE_D3_FACTORIZED = {
    "EMPTY": "000",
    "CONS": "001",
    "CAR": "010",
    "CDR": "011",
    "ATOM": "100",
    "EQ": "101",
    "QUOTE": "110",
    "COND": "111",
}

SPINE_ZERO = {"EMPTY", "ATOM", "CAR", "COND"}

def bxor(a: str, b: str) -> str:
    return f"{int(a, 2) ^ int(b, 2):03b}"

def d2_fibre_hits(mapping: dict[str, str]) -> int:
    hits = 0
    for prefix, members in FIBRES.items():
        observed = {name for name, bits in mapping.items() if bits[:2] == prefix}
        if observed == set(members):
            hits += 1
    return hits

def exact_d2_fibres(mapping: dict[str, str]) -> bool:
    if d2_fibre_hits(mapping) != 4:
        return False
    for prefix, members in FIBRES.items():
        codes = {mapping[name] for name in members}
        if codes != {prefix + "0", prefix + "1"}:
            return False
    return True

def dual_mask(mapping: dict[str, str]) -> str | None:
    masks = {bxor(mapping[a], mapping[b]) for a, b in DUALS}
    return next(iter(masks)) if len(masks) == 1 else None

def recursive_complement(mapping: dict[str, str]) -> bool:
    return dual_mask(mapping) == "111"

def spine_orientation(mapping: dict[str, str]) -> bool:
    return {name for name, bits in mapping.items() if bits.endswith("0")} == SPINE_ZERO

def evaluate(mapping: dict[str, str]) -> dict:
    return {
        "d2_fibre_hits": d2_fibre_hits(mapping),
        "exact_d2_x_d1": exact_d2_fibres(mapping),
        "uniform_semantic_dual_mask": dual_mask(mapping),
        "recursive_complement_111": recursive_complement(mapping),
        "spine_zero_orientation": spine_orientation(mapping),
    }

def solve() -> dict:
    counts = Counter()
    uniform_maps = []
    complement_maps = []
    oriented_maps = []

    for perm in itertools.permutations(CODES[1:]):
        mapping = {"EMPTY": "000", **dict(zip(RESIDENTS[1:], perm, strict=True))}
        counts["total"] += 1

        if not exact_d2_fibres(mapping):
            continue
        counts["exact_d2_x_d1"] += 1

        mask = dual_mask(mapping)
        if mask is None:
            continue
        counts["uniform_semantic_dual"] += 1
        uniform_maps.append((mapping, mask))

        if mask != "111":
            continue
        counts["recursive_complement_111"] += 1
        complement_maps.append(mapping)

        if spine_orientation(mapping):
            counts["spine_zero_orientation"] += 1
            oriented_maps.append(mapping)

    expected = {
        "total": 5040,
        "exact_d2_x_d1": 8,
        "uniform_semantic_dual": 4,
        "recursive_complement_111": 2,
        "spine_zero_orientation": 1,
    }
    assert dict(counts) == expected, counts
    assert oriented_maps == [USER], oriented_maps

    complement_maps = sorted(
        complement_maps,
        key=lambda m: tuple(m[name] for name in RESIDENTS),
    )

    d2_complements = {
        code: f"{int(code, 2) ^ 0b11:02b}"
        for code in sorted(D2)
    }
    assert d2_complements == {"00": "11", "01": "10", "10": "01", "11": "00"}

    user_eval = evaluate(USER)
    pure_eval = evaluate(PURE_D3_FACTORIZED)
    assert user_eval["d2_fibre_hits"] == 4
    assert pure_eval["d2_fibre_hits"] == 0
    assert user_eval["recursive_complement_111"]

    return {
        "schema": "bija123-recursive-cube/v1",
        "issue": 3196,
        "authority": "research-only",
        "d1": D1,
        "d2": D2,
        "hard_exclusions": [
            "D4-D8",
            "historical code tables",
            "current D3 placement reward",
            "migration cost",
        ],
        "bridge_hypothesis": {
            "construction": "D3 = D2 prefix || one D1-sized extension bit",
            "fibres": {k: list(v) for k, v in FIBRES.items()},
            "warning": "bit-shape inheritance is not cross-domain identity collapse",
        },
        "recursive_duality_hypothesis": {
            "D1": "x XOR 1",
            "D2": "x XOR 11",
            "D3": "x XOR 111",
        },
        "counts": expected,
        "user_candidate": {
            "mapping": USER,
            "evaluation": user_eval,
        },
        "pure_d3_factorized_candidate": {
            "mapping": PURE_D3_FACTORIZED,
            "evaluation": pure_eval,
        },
        "remaining_after_recursive_complement": complement_maps,
        "optional_orientation_hypothesis": {
            "suffix_zero_spine": sorted(SPINE_ZERO),
            "unique_mapping": oriented_maps[0],
            "status": "hypothesis-not-constitution",
        },
        "production_mutation": False,
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    result = solve()
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print("BIJA123-RECURSIVE-CUBE: PASS")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
