#!/usr/bin/env python3
"""#3200 — L1-L5 bīja3 constitution hypothesis + mandatory D4 falsifier.

Clean-sheet rules:
- no D4+ placement tables;
- no historical opcode order;
- geometry may grow without semantic admission;
- only generated selector descendants receive D4 meanings in this witness.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

RESIDENTS = ("EMPTY", "QUOTE", "ATOM", "CDR", "CAR", "EQ", "COND", "CONS")
CODES3 = tuple(f"{i:03b}" for i in range(8))

D2_FIBRES = {
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

L5_ZERO_SPINE = {"EMPTY", "ATOM", "CAR", "COND"}

CANDIDATE_A = {
    "EMPTY": "000",
    "QUOTE": "001",
    "ATOM": "010",
    "CDR": "011",
    "CAR": "100",
    "EQ": "101",
    "COND": "110",
    "CONS": "111",
}

def complement(code: str) -> str:
    return "".join("1" if b == "0" else "0" for b in code)

def xor_mask(a: str, b: str) -> str:
    return f"{int(a, 2) ^ int(b, 2):0{len(a)}b}"

def exact_d2_fibres(mapping: dict[str, str]) -> bool:
    for prefix, names in D2_FIBRES.items():
        if {mapping[n] for n in names} != {prefix + "0", prefix + "1"}:
            return False
    return True

def uniform_dual_mask(mapping: dict[str, str]) -> str | None:
    masks = {xor_mask(mapping[a], mapping[b]) for a, b in DUALS}
    return next(iter(masks)) if len(masks) == 1 else None

def l5_orientation(mapping: dict[str, str]) -> bool:
    zero_side = {name for name, code in mapping.items() if code.endswith("0")}
    return zero_side == L5_ZERO_SPINE

def derive_d3() -> dict:
    counts = {
        "total": 0,
        "L1_L2": 0,
        "L1_L2_L3": 0,
        "L1_L2_L3_L4": 0,
        "L1_L2_L3_L4_L5": 0,
    }
    after_l4 = []
    after_l5 = []

    for perm in itertools.permutations(CODES3[1:]):
        mapping = {"EMPTY": "000", **dict(zip(RESIDENTS[1:], perm, strict=True))}
        counts["total"] += 1

        # L1 is EMPTY=000 by construction. L2 is exact D2-prefix fibres.
        if not exact_d2_fibres(mapping):
            continue
        counts["L1_L2"] += 1

        # L3: one uniform semantic-dual formula on the whole D3 cube.
        mask = uniform_dual_mask(mapping)
        if mask is None:
            continue
        counts["L1_L2_L3"] += 1

        # L4: recursive complement from D1/D2 predicts XOR 111 on D3.
        if mask != "111":
            continue
        counts["L1_L2_L3_L4"] += 1
        after_l4.append(mapping)

        # L5: suffix-0 is the evaluator/metalinguistic spine.
        if not l5_orientation(mapping):
            continue
        counts["L1_L2_L3_L4_L5"] += 1
        after_l5.append(mapping)

    expected = {
        "total": 5040,
        "L1_L2": 8,
        "L1_L2_L3": 4,
        "L1_L2_L3_L4": 2,
        "L1_L2_L3_L4_L5": 1,
    }
    assert counts == expected, counts
    assert after_l5 == [CANDIDATE_A], after_l5

    return {
        "counts": counts,
        "after_L4": after_l4,
        "after_L5": after_l5,
    }

def selector_name(code: str) -> str:
    if code[:3] == CANDIDATE_A["CAR"]:
        letters = ["A"]
    elif code[:3] == CANDIDATE_A["CDR"]:
        letters = ["D"]
    else:
        raise ValueError(code)
    for bit in code[3:]:
        letters.append("A" if bit == "0" else "D")
    return "C" + "".join(letters) + "R"

def selector_dual_name(name: str) -> str:
    return "C" + "".join("D" if x == "A" else "A" for x in name[1:-1]) + "R"

def selector_level(width: int) -> dict[str, str]:
    suffix_width = width - 3
    out = {}
    for root in (CANDIDATE_A["CAR"], CANDIDATE_A["CDR"]):
        for i in range(1 << suffix_width):
            suffix = format(i, f"0{suffix_width}b") if suffix_width else ""
            code = root + suffix
            out[code] = selector_name(code)
    return out

def d4_falsifier() -> dict:
    d4 = selector_level(4)
    expected = {
        "1000": "CAAR",
        "1001": "CADR",
        "0110": "CDAR",
        "0111": "CDDR",
    }
    assert d4 == expected, d4

    rows = []
    for code, name in sorted(d4.items()):
        anti = complement(code)
        observed = d4.get(anti)
        expected_dual = selector_dual_name(name)
        ok = observed == expected_dual
        assert ok, (code, name, anti, observed, expected_dual)
        rows.append({
            "code": code,
            "name": name,
            "antipode": anti,
            "antipode_name": observed,
            "expected_semantic_dual": expected_dual,
            "pass": ok,
        })

    all_d4 = {f"{i:04b}" for i in range(16)}
    known = set(d4)
    unknown = sorted(all_d4 - known)
    assert len(known) == 4
    assert len(unknown) == 12

    return {
        "selector_rows": rows,
        "selector_pass_count": 4,
        "selector_total": 4,
        "known_semantic_coordinates": sorted(known),
        "unknown_coordinates": unknown,
        "global_D4_semantic_complement": "UNPROVEN",
        "boundary": "complement is semantic on generated selector-family; no claim for other D4 coordinates",
    }

def selector_corollary_through_d7() -> list[dict]:
    rows = []
    for width in range(3, 8):
        level = selector_level(width)
        for code, name in level.items():
            anti = complement(code)
            assert anti in level
            assert level[anti] == selector_dual_name(name)
        rows.append({
            "width": width,
            "selector_count": len(level),
            "semantic_antipode_pass": len(level),
            "semantic_antipode_total": len(level),
        })
    return rows

def solve() -> dict:
    d3 = derive_d3()
    d4 = d4_falsifier()
    deeper = selector_corollary_through_d7()

    return {
        "schema": "l1-l5-bija3-d4-falsifier/v1",
        "issue": 3200,
        "authority": "research-only",
        "laws": {
            "L1": "000 = EMPTY",
            "L2": "D3 remembers D2 as exact prefix fibres",
            "L3": "one uniform D3 semantic-dual involution",
            "L4": "recursive complement predicts XOR 111 on D3",
            "L5": "suffix-0 = evaluator/metalinguistic spine",
        },
        "D3_derivation": d3,
        "candidate_A": CANDIDATE_A,
        "mandatory_D4_falsifier": d4,
        "selector_corollary_D3_to_D7": deeper,
        "theorem_boundary": {
            "seed_duality": "PASS",
            "path_duality": "PASS",
            "D4_selector_complement": "PASS-4/4",
            "global_D4_complement_semantics": "UNPROVEN",
            "interpretation": "geometry grows globally; semantic duality is family-local until separately proved",
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
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("L1-L5-D4-FALSIFIER: PASS")
    print("D3-CANDIDATES-AFTER-L4=2")
    print("D3-CANDIDATES-AFTER-L5=1")
    print("D4-SELECTOR-COMPLEMENT=4/4")
    print("D4-KNOWN=4")
    print("D4-UNKNOWN=12")
    print("GLOBAL-D4-COMPLEMENT-SEMANTICS=UNPROVEN")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
