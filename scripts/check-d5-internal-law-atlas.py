#!/usr/bin/env python3
"""#3066 — D5 internal-law atlas ratchet.

Research/CI guard only. It does not ratify owner doctrine or mutate production
coordinates. It ensures the evidence package cannot silently regress into a
universal suffix theorem or learn transitional MEMBER t/() as canonical law.
"""

from __future__ import annotations

import json
from pathlib import Path

ATLAS = Path("knowledge/d5-internal-law-atlas.json")
ALLOWED_CLASSES = {
    "SEMANTIC-GENERATOR",
    "LOCAL-ALGEBRA",
    "MULTI-DELTA-FAMILY",
    "COORDINATE-HISTORICAL",
}

def fail(msg: str) -> None:
    raise SystemExit(f"D5-INTERNAL-LAW-RATCHET=FAIL\n{msg}")

def require(cond: bool, msg: str) -> None:
    if not cond:
        fail(msg)

def main() -> None:
    data = json.loads(ATLAS.read_text(encoding="utf-8"))

    require(data["domain"] == "Core.D5", "domain drift")
    require(data["width"] == 5, "width drift")
    require(data.get("schema_version") == 2, "schema version must be 2 after #3261")

    authority = data.get("coordinate_authority", {})
    require(
        authority.get("current_coordinates") == "PRODUCTION-PROJECTION-OD-005",
        "CURRENT D5 coordinates must be projection authority only",
    )
    require(
        authority.get("d4_parentage_from_prefix") == "FORBIDDEN",
        "D4 parentage must never be inferred from D5 prefix shape",
    )
    require(
        authority.get("higher_selector_lineage") == "COLLISION-HELD-BY-#3209",
        "higher selector lineage must remain held by #3209",
    )
    require(
        authority.get("cleanroom_d4_authority") == "#3225",
        "clean-room D4 authority drift",
    )
    require(data["occupancy"] == {"used": 32, "capacity": 32}, "occupancy drift")

    doctrine = data["doctrine"]
    for key in (
        "global_suffix_law",
        "universal_d4_parent_theorem",
        "automatic_d6_propagation",
        "current_map_frozen_by_this_artifact",
        "core_math_law_transfer",
    ):
        require(doctrine.get(key) is False, f"{key} must remain false")

    pairs = data["pairs"]
    require(len(pairs) == 16, f"expected 16 pairs, got {len(pairs)}")
    prefixes = [row["prefix4"] for row in pairs]
    require(len(set(prefixes)) == 16, "duplicate prefix4")
    require(set(prefixes) == {f"{i:04b}" for i in range(16)}, "prefix set is not complete D4 space")

    child_bits = []
    counts = {cls: 0 for cls in ALLOWED_CLASSES}
    semantic_suffix_rows = 0
    historical_bonus_violations = []
    selector_parentage_rows = 0

    for row in pairs:
        prefix = row["prefix4"]
        require(row["relation_class"] in ALLOWED_CLASSES, f"{prefix}: invalid relation class")
        counts[row["relation_class"]] += 1
        require(row["evidence"], f"{prefix}: missing evidence")

        c0 = row["child0"]["bits"]
        c1 = row["child1"]["bits"]
        require(c0 == prefix + "0", f"{prefix}: child0 coordinate drift")
        require(c1 == prefix + "1", f"{prefix}: child1 coordinate drift")
        child_bits.extend([c0, c1])

        require(
            row.get("coordinate_status") == "CURRENT-PROJECTION",
            f"{prefix}: D5 coordinate must be marked CURRENT projection",
        )

        parentage = row.get("coordinate_parentage_status")
        if row["relation_class"] == "SEMANTIC-GENERATOR" and row["law_kind"] == "selector-projection-composition":
            require(
                parentage == "COLLISION-HELD-3209",
                f"{prefix}: selector coordinate parentage must be collision-held by #3209",
            )
            selector_parentage_rows += 1
        else:
            require(
                parentage == "NOT-INFERRED",
                f"{prefix}: non-selector D4 parentage must remain NOT-INFERRED",
            )

        if row["one_bit_suffix_law"]:
            semantic_suffix_rows += 1
            require(
                row["relation_class"] in {"SEMANTIC-GENERATOR", "LOCAL-ALGEBRA"},
                f"{prefix}: one-bit law attached to invalid class",
            )

        if row["relation_class"] == "COORDINATE-HISTORICAL":
            if row["shadow_constraint"] != "NO_SEMANTIC_BONUS" and row["shadow_constraint"] != "NEGATIVE_ADJACENCY_CONTROL":
                historical_bonus_violations.append(prefix)
            require(row["semantic_family"] is False, f"{prefix}: historical pair cannot claim semantic-family authority")
            require(row["one_bit_suffix_law"] is False, f"{prefix}: historical pair cannot claim suffix law")

        if row["relation_class"] == "MULTI-DELTA-FAMILY":
            require(row["semantic_family"] is True, f"{prefix}: multi-delta family must remain a semantic family")
            require(row["one_bit_suffix_law"] is False, f"{prefix}: multi-delta family cannot collapse to one bit")

    require(not historical_bonus_violations, f"historical pairs gained semantic bonus: {historical_bonus_violations}")
    require(selector_parentage_rows == 4, f"expected 4 collision-held selector rows, got {selector_parentage_rows}")
    require(len(set(child_bits)) == 32, "duplicate D5 child coordinate")
    require(set(child_bits) == {f"{i:05b}" for i in range(32)}, "D5 coordinate coverage drift")

    require(counts == {
        "SEMANTIC-GENERATOR": 4,
        "LOCAL-ALGEBRA": 6,
        "MULTI-DELTA-FAMILY": 2,
        "COORDINATE-HISTORICAL": 4,
    }, f"class-count drift: {counts}")

    member = next(row["child1"] for row in pairs if row["child1"]["bits"] == "11101")
    require(member["label"] == "MEMBER", "11101 report label drift")
    require(member["canonical_result_domain"] == "Core.D1", "MEMBER canonical result domain must be D1")
    require(member["canonical_yes"] == "1" and member["canonical_no"] == "0", "MEMBER PredicateBit law drift")
    require(member["runtime_transition_debt"].startswith("NONE"), "MEMBER runtime transition debt must be closed after #3060")

    require(
        data["stable_identity"]["status"] == "PENDING-STABLE-ID-BACKFILL",
        "do not invent stable resident IDs before #3051",
    )

    print("D5-INTERNAL-LAW-RATCHET=PASS")
    print("PAIR-COUNT=16")
    print("COORDINATE-AUTHORITY=PRODUCTION-PROJECTION-OD-005")
    print("D4-PARENTAGE-FROM-PREFIX=FORBIDDEN")
    print("SELECTOR-PARENTAGE=COLLISION-HELD-BY-3209")
    print("OCCUPANCY=32/32")
    print("SEMANTIC-GENERATOR=4")
    print("LOCAL-ALGEBRA=6")
    print("MULTI-DELTA-FAMILY=2")
    print("COORDINATE-HISTORICAL=4")
    print(f"ROWS-WITH-LOCAL-ONE-BIT-LAW={semantic_suffix_rows}")
    print("GLOBAL-SUFFIX-LAW=FALSE")
    print("UNIVERSAL-D4-PARENT=FALSE")
    print("D6-PROPAGATION=FALSE")
    print("CURRENT-MAP-FROZEN-BY-ATLAS=FALSE")
    print("MEMBER-CANONICAL-RESULT=Core.D1:1/0")
    print("STABLE-ID-BACKFILL=PENDING-3051")

if __name__ == "__main__":
    main()
