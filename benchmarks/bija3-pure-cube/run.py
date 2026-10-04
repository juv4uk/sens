#!/usr/bin/env python3
"""#3194: pure D3/bīja3 cube search with no D4+, legacy tables or current-placement reward."""
from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

RESIDENTS = ("EMPTY", "CONS", "CAR", "CDR", "ATOM", "EQ", "QUOTE", "COND")
CODES = tuple(f"{i:03b}" for i in range(8))
PAIRS = (
    ("EMPTY", "CONS"),
    ("CAR", "CDR"),
    ("ATOM", "EQ"),
    ("QUOTE", "COND"),
)
FAMILY = {
    "EMPTY": "structure", "CONS": "structure",
    "CAR": "selector", "CDR": "selector",
    "ATOM": "predicate", "EQ": "predicate",
    "QUOTE": "control", "COND": "control",
}
FAMILY_EDGES = (
    ("structure", "selector"),
    ("structure", "predicate"),
    ("predicate", "control"),
)
USER = {
    "EMPTY": "000", "QUOTE": "001", "ATOM": "010", "CDR": "011",
    "CAR": "100", "EQ": "101", "COND": "110", "CONS": "111",
}


def bxor(a: str, b: str) -> str:
    return f"{int(a, 2) ^ int(b, 2):03b}"


def hamming(a: str, b: str) -> int:
    return bxor(a, b).count("1")


def evaluate(mapping: dict[str, str]) -> dict:
    masks = tuple(bxor(mapping[a], mapping[b]) for a, b in PAIRS)
    uniform = len(set(masks)) == 1
    common = masks[0] if uniform else None
    single_axis = bool(common and common.count("1") == 1)
    family_hits = -1
    family_codes = None

    if single_axis:
        axis = common.index("1")
        grouped: dict[str, set[str]] = {}
        for resident in RESIDENTS:
            bits = mapping[resident]
            quotient = bits[:axis] + bits[axis + 1:]
            grouped.setdefault(FAMILY[resident], set()).add(quotient)
        if all(len(values) == 1 for values in grouped.values()):
            family_codes = {name: next(iter(values)) for name, values in grouped.items()}
            family_hits = sum(
                hamming(family_codes[a], family_codes[b]) == 1
                for a, b in FAMILY_EDGES
            )

    return {
        "uniform_pair_xor": uniform,
        "pair_xor_mask": common,
        "pair_xor_hamming_weight": common.count("1") if common else None,
        "single_member_axis": single_axis,
        "family_edge_hits": family_hits,
        "family_codes": family_codes,
    }


def natural_orientation(mapping: dict[str, str]) -> bool:
    return (
        mapping["EMPTY"] == "000"
        and mapping["CONS"] == "001"
        and mapping["CAR"].endswith("0")
        and mapping["CDR"].endswith("1")
        and mapping["ATOM"].endswith("0")
        and mapping["EQ"].endswith("1")
        and mapping["QUOTE"].endswith("0")
        and mapping["COND"].endswith("1")
    )


def solve() -> dict:
    counts = Counter()
    canonical = []

    for perm in itertools.permutations(CODES[1:]):
        mapping = {"EMPTY": "000", **dict(zip(RESIDENTS[1:], perm, strict=True))}
        row = evaluate(mapping)
        counts["total"] += 1

        if row["uniform_pair_xor"]:
            counts["uniform_xor"] += 1
        if row["single_member_axis"]:
            counts["single_axis"] += 1
        if row["family_edge_hits"] == len(FAMILY_EDGES):
            counts["all_family_edges"] += 1
            if row["pair_xor_mask"] == "001" and natural_orientation(mapping):
                canonical.append(mapping)

    expected_counts = {
        "total": 5040,
        "uniform_xor": 336,
        "single_axis": 144,
        "all_family_edges": 48,
    }
    assert dict(counts) == expected_counts, counts
    assert len(canonical) == 2, canonical

    canonical.sort(key=lambda m: tuple(m[r] for r in RESIDENTS))
    representative, axis_swap = canonical

    expected = {
        "EMPTY": "000", "CONS": "001",
        "CAR": "010", "CDR": "011",
        "ATOM": "100", "EQ": "101",
        "QUOTE": "110", "COND": "111",
    }
    expected_swap = {
        "EMPTY": "000", "CONS": "001",
        "CAR": "100", "CDR": "101",
        "ATOM": "010", "EQ": "011",
        "QUOTE": "110", "COND": "111",
    }
    assert representative == expected
    assert axis_swap == expected_swap

    user = evaluate(USER)
    assert user["uniform_pair_xor"]
    assert user["pair_xor_mask"] == "111"
    assert user["pair_xor_hamming_weight"] == 3

    return {
        "schema": "bija3-pure-cube/v1",
        "issue": 3194,
        "authority": "research-only",
        "closed_world": list(RESIDENTS),
        "forbidden_inputs": [
            "D4-D8",
            "historical code tables",
            "current placement reward",
            "migration cost",
        ],
        "counts": expected_counts,
        "user_antipodal_candidate": {
            "mapping": USER,
            "evaluation": user,
        },
        "factorized_equivalence_class": {
            "canonical_representative": representative,
            "axis_swapped_equivalent": axis_swap,
            "member_law": "sibling = code XOR 001",
            "family_law": "family = first two bits",
            "families": {
                "00": "structure",
                "01": "selector",
                "10": "predicate",
                "11": "control",
            },
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

    print("BĪJA3-PURE-CUBE: PASS")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
