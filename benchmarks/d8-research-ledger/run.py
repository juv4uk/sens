#!/usr/bin/env python3
"""#3673 — consolidated D8 research accounting ledger.

This is research coverage accounting only. It is not D8 occupancy authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
D6_AUTHORITY_PATH = REPO / "knowledge" / "d6-ratified.json"
D3_SELECTOR_ROOTS = ("011", "100")
CAPACITY = 256


def load_d6_authority():
    raw = D6_AUTHORITY_PATH.read_bytes()
    doc = json.loads(raw)
    assert doc["schema"] == "d6-ratified/v1"
    assert doc["status"] == "owner-ratified"
    assert doc["authority"] == "#3393"
    by_name = {name: coordinate for coordinate, name in doc["residents"].items()}
    required = {
        "TAKE": "110000",
        "DROP": "110001",
        "ANY": "111100",
        "ALL": "111101",
        "REDUCE": "101110",
        "SCAN": "101111",
    }
    for name, coordinate in required.items():
        assert by_name[name] == coordinate
    return {
        "path": str(D6_AUTHORITY_PATH.relative_to(REPO)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "authority": doc["authority"],
        "resolved": required,
    }


def selector_candidates():
    out = {
        root + "".join(bits)
        for root in D3_SELECTOR_ROOTS
        for bits in product("01", repeat=5)
    }
    assert len(out) == 64
    return out


def family(anchor, sibling, name, novel_middle, fixed_novel, evidence, status):
    footprint = [anchor + suffix for suffix in ("00", "01", "10", "11")]
    return {
        "name": name,
        "evidence": evidence,
        "status": status,
        "anchor_d6": anchor,
        "sibling_d6": sibling,
        "footprint": footprint,
        "fixed_base_duplicate": {
            "coordinate": anchor + "00",
            "status": "LOWER-DOMAIN-DUPLICATE",
        },
        "middle_gauge_orbit": {
            "coordinates": [anchor + "01", anchor + "10"],
            "status": "GAUGE-ORBIT",
            "contains": [
                sibling + " lower-domain meaning",
                novel_middle,
            ],
            "absolute_assignment": "UNRESOLVED",
        },
        "fixed_novel": {
            "coordinate": anchor + "11",
            "meaning": fixed_novel,
            "status": "GENERATED-FIXED-CANDIDATE",
        },
    }


def run():
    d6 = load_d6_authority()
    selectors = selector_candidates()

    families = [
        family(
            "110000",
            "110001",
            "TAKE/DROP × edge",
            "TAKE-right",
            "DROP-right",
            "#3667 / #3622",
            "PRODUCT-CANDIDATE",
        ),
        family(
            "111100",
            "111101",
            "ANY/ALL × predicate polarity",
            "ANY(NOT p)",
            "ALL(NOT p)",
            "#3668 / #3663",
            "PRODUCT-CANDIDATE",
        ),
        family(
            "101110",
            "101111",
            "REDUCE/SCAN × direction",
            "REDUCE-right",
            "SCAN-right",
            "#3675 / #3674",
            "PRODUCT-CANDIDATE-NONEMPTY",
        ),
    ]

    footprints = set()
    for item in families:
        current = set(item["footprint"])
        assert len(current) == 4
        assert current.isdisjoint(selectors)
        assert current.isdisjoint(footprints)
        footprints |= current

    analyzed = selectors | footprints
    assert len(footprints) == 12
    assert len(analyzed) == 76

    untouched = {
        f"{value:08b}"
        for value in range(CAPACITY)
        if f"{value:08b}" not in analyzed
    }
    assert len(untouched) == 180

    fixed_novel = [item["fixed_novel"] for item in families]
    full_fixed = [
        row for row, item in zip(fixed_novel, families)
        if item["status"] == "PRODUCT-CANDIDATE"
    ]
    boundary_fixed = [
        row for row, item in zip(fixed_novel, families)
        if item["status"] == "PRODUCT-CANDIDATE-NONEMPTY"
    ]

    return {
        "schema": "d8-research-ledger/v1",
        "status": "RESEARCH-UNRATIFIED",
        "authority": {
            "d8": "NONE",
            "umbrella": "#3281",
            "ledger_task": "#3673",
            "d6_source": d6,
        },
        "forbidden_interpretation": "analyzed-coordinate != resident != primitive occupancy",
        "accounting": {
            "capacity": CAPACITY,
            "selector_candidate_coordinates": len(selectors),
            "product_family_footprint_coordinates": len(footprints),
            "analyzed_unique_coordinates": len(analyzed),
            "untouched_coordinates": len(untouched),
            "fixed_novel_coordinate_candidates_full": len(full_fixed),
            "fixed_novel_coordinate_candidates_protocol_bounded": len(boundary_fixed),
            "gauge_unresolved_novel_semantics": len(families),
            "fixed_lower_domain_duplicate_coordinates": len(families),
            "gauge_orbits": len(families),
            "falsified_axis_hypotheses": 5,
        },
        "selector_family": {
            "evidence": "#3646",
            "status": "SELECTOR-CANDIDATE",
            "count": len(selectors),
            "coordinates": sorted(selectors),
            "ancestry": "current D6 selector × W2; D7 excluded",
        },
        "product_families": families,
        "fixed_novel_candidates": fixed_novel,
        "untouched_coordinates": sorted(untouched),
        "falsified_axes": {
            "evidence": "#3670 / #3669",
            "count": 5,
            "items": [
                "LENGTH/LENGTH-ONTO × reverse",
                "MIN-LIST/MAX-LIST × NEG conjugation",
                "ADD1/SUB1 × NEG conjugation",
                "INTEGERP/RATIONALP × NEG",
                "REMAINDER/GCD × argument swap",
            ],
        },
        "non_conclusions": [
            "76 analyzed coordinates do not mean 76 D8 residents.",
            "Generated meanings need not become primitives.",
            "Gauge-orbit meanings do not have fixed absolute middle coordinates.",
            "The REDUCE/SCAN fixed candidate is restricted to the nonempty protocol.",
            "D8 remains unratified and fail-closed.",
        ],
    }


def render(report):
    a = report["accounting"]
    lines = [
        "# D8 research ledger — #3673",
        "",
        "Status: **RESEARCH-UNRATIFIED**",
        "",
        f"- capacity: {a['capacity']}",
        f"- selector candidate coordinates: {a['selector_candidate_coordinates']}",
        f"- product-family footprint coordinates: {a['product_family_footprint_coordinates']}",
        f"- analyzed unique coordinates: {a['analyzed_unique_coordinates']}",
        f"- untouched coordinates: {a['untouched_coordinates']}",
        f"- fixed novel candidates (full): {a['fixed_novel_coordinate_candidates_full']}",
        f"- fixed novel candidates (protocol-bounded): {a['fixed_novel_coordinate_candidates_protocol_bounded']}",
        f"- gauge-unresolved novel semantics: {a['gauge_unresolved_novel_semantics']}",
        f"- falsified second-axis hypotheses: {a['falsified_axis_hypotheses']}",
        "",
        "Fixed generated 11-corner candidates:",
    ]
    for row in report["fixed_novel_candidates"]:
        lines.append(f"- {row['coordinate']} = {row['meaning']}")
    lines += [
        "",
        "Important: analyzed coordinate != resident != primitive occupancy.",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    report = run()
    text = render(report)

    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "ledger.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.out / "report.md").write_text(text, encoding="utf-8")

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
