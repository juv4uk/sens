#!/usr/bin/env python3
"""#3198: test universal domain-growth laws through D7.

Pure cube section derives from bit geometry only.
Selector section uses only the D3 candidate from #3196 plus a local A/D generator.
Current D4-D6 maps are read only as non-authoritative falsification data.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAR = "100"
CDR = "011"

def bits(width: int) -> list[str]:
    return [format(i, f"0{width}b") for i in range(1 << width)]

def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b, strict=True))

def edges(width: int) -> set[tuple[str, str]]:
    out = set()
    for a in bits(width):
        for axis in range(width):
            b = a[:axis] + ("1" if a[axis] == "0" else "0") + a[axis + 1:]
            out.add(tuple(sorted((a, b))))
    return out

def complement(code: str) -> str:
    return "".join("1" if b == "0" else "0" for b in code)

def verify_cube_growth(max_width: int = 7) -> list[dict]:
    report = []
    for width in range(1, max_width + 1):
        q = bits(width)
        e = edges(width)
        expected_edges = width * (1 << (width - 1))
        assert len(q) == 1 << width
        assert len(e) == expected_edges
        for code in q:
            anti = complement(code)
            assert complement(anti) == code
            assert anti != code
            assert hamming(code, anti) == width
        row = {
            "width": width,
            "capacity": len(q),
            "edge_count": len(e),
            "antipodal_pair_count": 1 << (width - 1),
        }
        if width < max_width:
            next_edges = edges(width + 1)
            for a, b in e:
                assert tuple(sorted((a + "0", b + "0"))) in next_edges
                assert tuple(sorted((a + "1", b + "1"))) in next_edges
            for p in q:
                assert tuple(sorted((p + "0", p + "1"))) in next_edges
            row["children_per_parent"] = 2
            row["next_width_parent_count"] = len(q)
            row["new_axis_matching_edges"] = len(q)
        report.append(row)
    return report

def selector_letters(code: str) -> str:
    if code[:3] == CAR:
        letters = ["A"]
    elif code[:3] == CDR:
        letters = ["D"]
    else:
        raise ValueError(code)
    for bit in code[3:]:
        letters.append("A" if bit == "0" else "D")
    return "".join(letters)

def selector_name(code: str) -> str:
    return "C" + selector_letters(code) + "R"

def dual_selector_name(name: str) -> str:
    return "C" + "".join("D" if x == "A" else "A" for x in name[1:-1]) + "R"

def selector_level(width: int) -> dict[str, str]:
    suffix_width = width - 3
    out = {}
    for root in (CAR, CDR):
        for i in range(1 << suffix_width):
            suffix = format(i, f"0{suffix_width}b") if suffix_width else ""
            code = root + suffix
            out[code] = selector_name(code)
    return out

def verify_selector_family(max_width: int = 7) -> list[dict]:
    rows = []
    previous = None
    for width in range(3, max_width + 1):
        level = selector_level(width)
        assert len(level) == 1 << (width - 2)
        for code, name in level.items():
            anti = complement(code)
            assert anti in level
            assert level[anti] == dual_selector_name(name)
        if previous is not None:
            for code in level:
                assert code[:-1] in previous
        rows.append({
            "width": width,
            "selector_count": len(level),
            "selector_fraction_of_domain": "1/4",
            "antipodal_selector_pair_count": len(level) // 2,
        })
        previous = level
    return rows

def grouped(rows: list[dict], key: str) -> dict[str, list[dict]]:
    out = defaultdict(list)
    for row in rows:
        out[row[key]].append(row)
    return out

def complement_same(rows: list[dict], width: int, coord_key: str, cat_key: str) -> list[int]:
    by = {r[coord_key]: r for r in rows}
    seen = set()
    same = 0
    total = 0
    for code in sorted(by):
        if code in seen:
            continue
        anti = complement(code)
        seen.add(code)
        seen.add(anti)
        total += 1
        if by[code][cat_key] == by[anti][cat_key]:
            same += 1
    return [same, total]

def external_non_authoritative_audit() -> dict:
    corpus = json.loads((ROOT / "knowledge/exact-width-admitted-corpus.json").read_text(encoding="utf-8"))
    d5 = json.loads((ROOT / "knowledge/d5-historical-full-map.json").read_text(encoding="utf-8"))
    d6 = json.loads((ROOT / "knowledge/d6-historical-full-map.json").read_text(encoding="utf-8"))

    d4 = [r for r in corpus["rows"] if r["width"] == 4]
    d4g = grouped([{**r, "parent": r["word"][:-1]} for r in d4], "parent")
    assert len(d4g) == 8 and all(len(rs) == 2 for rs in d4g.values())
    d4_same_role = sum(len({r["role"] for r in rs}) == 1 for rs in d4g.values())

    d4_by = {r["word"]: r for r in d4}
    seen = set()
    d4_comp_role = 0
    d4_comp_total = 0
    for code in sorted(d4_by):
        if code in seen:
            continue
        anti = complement(code)
        seen.add(code)
        seen.add(anti)
        d4_comp_total += 1
        if d4_by[code]["role"] == d4_by[anti]["role"]:
            d4_comp_role += 1

    d5rows = d5["coordinates"]
    d5g = grouped(d5rows, "parent_d4")
    assert len(d5g) == 16 and all(len(rs) == 2 for rs in d5g.values())
    d5_same_cat = sum(len({r["category"] for r in rs}) == 1 for rs in d5g.values())

    d6rows = d6["coordinates"]
    d6g = grouped(d6rows, "parent_d5")
    assert len(d6g) == 32 and all(len(rs) == 2 for rs in d6g.values())
    d6_same_cat = sum(len({r["category"] for r in rs}) == 1 for rs in d6g.values())

    d7_source = (ROOT / "benchmarks/d7-ratification-conformance/validate.py").read_text(encoding="utf-8")
    d7_is_role_domain = (
        "D7 = Sound7/Sanskrit sound-related objects" in d7_source
        and "D7 != general arithmetic Number" in d7_source
        and "OCCUPANCY-CLAIM=NONE" in d7_source
    )
    assert d7_is_role_domain

    return {
        "authority": "NON-AUTHORITATIVE-FALSIFICATION-ONLY",
        "prefix_fibre_coherence": {
            "D3_to_D4": {"all_parents_have_two_children": True, "same_role_pairs": [d4_same_role, 8]},
            "D4_to_D5": {"all_parents_have_two_children": True, "same_category_pairs": [d5_same_cat, 16]},
            "D5_to_D6": {"all_parents_have_two_children": True, "same_category_pairs": [d6_same_cat, 32]},
        },
        "global_complement_category_coherence": {
            "D4_same_role": [d4_comp_role, d4_comp_total],
            "D5_same_category": complement_same(d5rows, 5, "coordinate", "category"),
            "D6_same_category": complement_same(d6rows, 6, "coordinate", "category"),
        },
        "D7_current_ontology": {
            "is_role_domain_not_core_occupancy_map": True,
            "roles": ["sound-cell", "local-ordinal"],
            "core_prefix_continuation_claim": False,
        },
    }

def solve() -> dict:
    cube = verify_cube_growth(7)
    selectors = verify_selector_family(7)
    external = external_non_authoritative_audit()
    assert [r["capacity"] for r in cube] == [2, 4, 8, 16, 32, 64, 128]
    assert [r["selector_count"] for r in selectors] == [2, 4, 8, 16, 32]
    assert external["prefix_fibre_coherence"]["D4_to_D5"]["same_category_pairs"] == [13, 16]
    assert external["prefix_fibre_coherence"]["D5_to_D6"]["same_category_pairs"] == [29, 32]
    assert external["global_complement_category_coherence"]["D5_same_category"] == [0, 16]
    assert external["global_complement_category_coherence"]["D6_same_category"] == [0, 32]
    return {
        "schema": "domain-growth-qn-through-d7/v1",
        "issue": 3198,
        "authority": "research-only",
        "universal_candidate": {
            "name": "recursive-hypercube-fibre",
            "equation": "Q(n+1) = Qn box K2; child = parent || bit",
            "status": "PASS-PURE-GEOMETRY-D1-THROUGH-D7",
            "semantic_rule": "new bit is structural child coordinate; meaning is local-law-owned",
        },
        "antipodal_candidate": {
            "equation": "anti_n(x) = x XOR (2^n - 1)",
            "status": "PASS-AS-GEOMETRIC-AUTOMORPHISM",
            "semantic_status": "NOT-UNIVERSAL; family-specific proof required",
        },
        "cube_levels": cube,
        "selector_positive_control": {
            "roots": {"CAR": CAR, "CDR": CDR},
            "local_child_law": {"0": "compose-CAR/A", "1": "compose-CDR/D"},
            "levels": selectors,
            "result": "extends exactly through D7 and occupies one quarter",
            "antipodal_result": "inside selector family, complement flips every A<->D",
        },
        "external_non_authoritative_audit": external,
        "D7_conclusion": {
            "pure_geometry_capacity": 128,
            "selector_subtree_capacity": 32,
            "current_repo_semantics": "Sound7/local-ordinal role domain; not proven Core.D6 prefix continuation",
            "architectural_choice": "keep D7 separate or define distinct Core.D7 before claiming uninterrupted Core ladder",
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
    print("DOMAIN-GROWTH-QN-THROUGH-D7: PASS")
    for row in result["cube_levels"]:
        print(f"D{row['width']} capacity={row['capacity']} edges={row['edge_count']} antipodal_pairs={row['antipodal_pair_count']}")
    print("SELECTORS=" + ",".join(str(r["selector_count"]) for r in result["selector_positive_control"]["levels"]))
    print("D7-CURRENT-CORE-CONTINUATION=NO-PROOF")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
