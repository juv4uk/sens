#!/usr/bin/env python3
"""#3508 — cross-width family-law atlas ratchet.

Evidence/ontology guard only.  It keeps width and semantic-family lineage as
independent axes and prevents coordinate automorphisms from silently becoming
semantic authority.
"""

from __future__ import annotations

import json
from pathlib import Path

ATLAS = Path("knowledge/cross-width-law-atlas.json")

ALLOWED_STATUSES = {
    "coordinate-automorphism",
    "family-semantic-law",
    "cross-width-lift",
    "domain-global-law",
    "unknown",
    "falsified",
}


def fail(message: str) -> None:
    raise SystemExit(f"CROSS-WIDTH-LAW-ATLAS=FAIL\n{message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def complement(bits: str) -> str:
    return "".join("1" if bit == "0" else "0" for bit in bits)


def expected_selector_bits(width: int) -> set[str]:
    suffix_len = width - 3
    out = set()
    for root in ("100", "011"):
        for suffix in range(1 << suffix_len):
            suffix_bits = "" if suffix_len == 0 else f"{suffix:0{suffix_len}b}"
            out.add(root + suffix_bits)
    return out


def expected_path(bits: str) -> str:
    root = {"100": "A", "011": "D"}[bits[:3]]
    suffix = "".join("A" if bit == "0" else "D" for bit in bits[3:])
    return root + suffix


def main() -> None:
    data = json.loads(ATLAS.read_text(encoding="utf-8"))

    require(data["schema"] == "cross-width-law-atlas/v1", "schema drift")
    require(data["parent_theorem"] == "#3499", "parent theorem drift")
    require(
        data["law_set_id"] == "sens-cross-width-lawset-2026-10-05-a",
        "law-set identity drift",
    )
    require(
        data["positive_witness_ids"] == [
            "SELECTOR-COMPLEMENT-D3",
            "SELECTOR-LIFT-D3-D4",
            "SELECTOR-LIFT-D4-D5",
        ],
        "positive witness-set drift",
    )
    require(
        data["negative_or_boundary_witness_ids"] == [
            "GLOBAL-D4-COMPLEMENT:NO-SEMANTIC-J",
            "DOMAIN-FIREWALL:SELECTORPATH-VS-QGROUPFACTOR",
            "AUTOMATIC-D6:FALSE",
        ],
        "negative/boundary witness-set drift",
    )
    require(data["axes"] == ["exact_width", "semantic_family"], "atlas axes must remain width × family")
    require(set(data["allowed_statuses"]) == ALLOWED_STATUSES, "status vocabulary drift")

    families = data["families"]
    require(len(families) == 1, "v1 atlas must contain exactly the proved selector positive control")
    selector = families[0]

    require(selector["family_id"] == "core-selector-path", "selector family id drift")
    require(selector["declared_domain"] == "Core.SelectorPath", "selector domain drift")
    require(selector["status"] == "family-semantic-law", "selector family law must remain explicit")
    require(selector["semantic_involution"] == "swap every CAR/CDR step", "semantic involution drift")
    require(selector["coordinate_action"] == "xor all ones at exact width", "coordinate action drift")
    require(selector["automatic_next_width"] is False, "cross-width proof must not imply automatic D6")

    levels = selector["levels"]
    require([row["width"] for row in levels] == [3, 4, 5], "proved selector widths must be exactly D3-D5")

    for level in levels:
        width = level["width"]
        members = level["members"]
        bits = {row["bits"] for row in members}
        require(bits == expected_selector_bits(width), f"D{width}: selector coordinate set drift")
        require(len(bits) == 2 ** (width - 2), f"D{width}: selector family cardinality drift")

        for row in members:
            require(len(row["bits"]) == width, f"D{width}: exact-width identity drift")
            require(row["path"] == expected_path(row["bits"]), f"D{width}: path/coordinate disagreement for {row['bits']}")

        listed_pairs = {frozenset(pair) for pair in level["complement_pairs"]}
        expected_pairs = {
            frozenset((bits_value, complement(bits_value)))
            for bits_value in bits
        }
        require(listed_pairs == expected_pairs, f"D{width}: complement-pair coverage drift")

        by_bits = {row["bits"]: row["path"] for row in members}
        for left in bits:
            right = complement(left)
            expected_dual_path = "".join("D" if step == "A" else "A" for step in by_bits[left])
            require(by_bits[right] == expected_dual_path, f"D{width}: coordinate complement lost semantic path duality")

    lifts = selector["lifts"]
    require(
        [(row["source_width"], row["target_width"]) for row in lifts] == [(3, 4), (4, 5)],
        "cross-width lift coverage must remain D3->D4 and D4->D5",
    )
    for row in lifts:
        require(row["status"] == "cross-width-lift", "lift status drift")
        require(
            row["equation"] == "C_{n+1}(G_b(p)) = G_{1-b}(C_n(p))",
            "commuting equation drift",
        )
        require(row["executable_witness"] == "PR #3509", "executable witness drift")

    global_rows = data["global_hypotheses"]
    require(len(global_rows) == 1, "v1 atlas expects one global negative-control hypothesis")
    d4 = global_rows[0]
    require(d4["hypothesis_id"] == "GLOBAL-D4-COMPLEMENT", "global hypothesis id drift")
    require(d4["status"] == "unknown", "global D4 complement must remain UNKNOWN until semantic J exists")
    require(d4["semantic_law_id"] is None, "UNKNOWN global complement must not acquire a semantic law id by coordinates")
    require(d4["falsifier_issue"] == "#3507", "global falsifier issue drift")

    controls = data["domain_firewall_controls"]
    require(len(controls) == 1, "v1 atlas expects #2508 firewall control")
    firewall = controls[0]
    require(firewall["authority"] == "#2508", "domain firewall authority drift")
    require(firewall["left_domain"] != firewall["right_domain"], "firewall domains collapsed")
    require(firewall["shared_semantic_authority"] is False, "same mechanism must not imply shared semantic authority")

    conclusions = set(data["non_conclusions"])
    require(
        "D5 selector evidence does not automatically admit D6 runtime semantics" in conclusions,
        "D6 non-conclusion missing",
    )

    print("CROSS-WIDTH-LAW-ATLAS=PASS")
    print(f"LAW-SET-ID={data['law_set_id']}")
    print("POSITIVE-WITNESSES=3")
    print("NEGATIVE-OR-BOUNDARY-WITNESSES=3")
    print("AXES=exact_width×semantic_family")
    print("PROVED-FAMILY=core-selector-path")
    print("PROVED-WIDTHS=D3,D4,D5")
    print("CROSS-WIDTH-LIFTS=2")
    print("GLOBAL-D4-COMPLEMENT=UNKNOWN")
    print("DOMAIN-FIREWALL=#2508")
    print("AUTOMATIC-D6=FALSE")


if __name__ == "__main__":
    main()
