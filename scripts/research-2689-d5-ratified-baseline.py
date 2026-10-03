#!/usr/bin/env python3
"""#2689 — standing guard for the owner-ratified Core D5 baseline.

This guard consumes the merged #2510 D5 closure-map generator. It does not
rebuild or reinterpret the map. Its only job is to make the current owner
ratification executable:

    8 selector-generated semantic residents
    24 UNKNOWN/free non-residents
    0 manual non-selector residents

Any occupancy change must therefore update the ratified baseline deliberately
rather than arriving as incidental research fallout.
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
CLOSURE = REPO / "benchmarks" / "d5-closure-map" / "run.py"

WIDTH = 5
CAPACITY = 1 << WIDTH
RATIFIED_GENERATED = {
    "10100",
    "10101",
    "10110",
    "10111",
    "11000",
    "11001",
    "11010",
    "11011",
}
EXPECTED_UNKNOWN = CAPACITY - len(RATIFIED_GENERATED)


def fail(message: str) -> None:
    raise AssertionError(f"D5 ratified-baseline drift: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def build_result() -> dict[str, Any]:
    closure = runpy.run_path(str(CLOSURE))
    rows = closure["build_map"]()
    acct = closure["accounting"](rows)

    require(len(rows) == CAPACITY, f"expected {CAPACITY} rows, got {len(rows)}")
    require(len({row["coordinate"] for row in rows}) == CAPACITY, "duplicate coordinate")
    require(all(row["width"] == WIDTH for row in rows), "row width drift")
    require(all(row["domain"] == "D5" for row in rows), "row domain drift")
    require(all(row["domain_ratified"] is True for row in rows), "unratified D5 row")

    generated = [row for row in rows if row["status"] == "generated"]
    unknown = [row for row in rows if row["status"] == "UNKNOWN/free"]
    other = [
        row for row in rows
        if row["status"] not in {"generated", "UNKNOWN/free"}
    ]

    generated_words = {row["coordinate"] for row in generated}
    unknown_words = {row["coordinate"] for row in unknown}

    require(generated_words == RATIFIED_GENERATED, (
        "generated set drift: "
        f"expected={sorted(RATIFIED_GENERATED)} actual={sorted(generated_words)}"
    ))
    require(len(unknown) == EXPECTED_UNKNOWN, (
        f"expected {EXPECTED_UNKNOWN} UNKNOWN rows, got {len(unknown)}"
    ))
    require(not other, f"unexpected manual/other statuses: {other}")

    for row in generated:
        require(row["semantic_family"] == "selector", (
            f"{row['coordinate']}: generated row is not selector family"
        ))
        require(row["semantic_law"] == "selector projection composition", (
            f"{row['coordinate']}: semantic law drift"
        ))
        require(row["semantic_law_authority"] == "#2158", (
            f"{row['coordinate']}: semantic law authority drift"
        ))
        require(row["certificate_replay_ok"] is True, (
            f"{row['coordinate']}: selector certificate no longer replays"
        ))
        require(row["certificate"] is not None, (
            f"{row['coordinate']}: generated row lacks certificate"
        ))
        require(row["semantic_member_of_ratified_domain"] is True, (
            f"{row['coordinate']}: generated row lost semantic membership"
        ))
        require(row["manual_resident_required"] is False, (
            f"{row['coordinate']}: generated selector became manual resident"
        ))
        require(row["placement_ref"] == "", (
            f"{row['coordinate']}: generated selector unexpectedly has placement_ref"
        ))
        require(row["collision"] is False, (
            f"{row['coordinate']}: generated selector collision"
        ))

    for row in unknown:
        coordinate = row["coordinate"]
        require(row["semantic_member_of_ratified_domain"] is False, (
            f"{coordinate}: UNKNOWN row became semantic member without baseline update"
        ))
        require(row["placement_ref"] == "", (
            f"{coordinate}: UNKNOWN row has placement_ref"
        ))
        require(row["manual_resident_required"] is False, (
            f"{coordinate}: UNKNOWN row marked manual resident"
        ))
        require(row["semantic_family"] == "", (
            f"{coordinate}: UNKNOWN row gained semantic family"
        ))
        require(row["semantic_law"] == "", (
            f"{coordinate}: UNKNOWN row gained semantic law"
        ))
        require(row["semantic_law_authority"] == "", (
            f"{coordinate}: UNKNOWN row gained semantic law authority"
        ))
        require(row["certificate"] is None, (
            f"{coordinate}: UNKNOWN row gained generation certificate"
        ))
        require(row["certificate_replay_ok"] is False, (
            f"{coordinate}: UNKNOWN row claims certificate replay"
        ))
        require(row["collision"] is False, (
            f"{coordinate}: UNKNOWN row collision"
        ))

    require(generated_words.isdisjoint(unknown_words), "generated/UNKNOWN overlap")
    require(generated_words | unknown_words == {
        format(value, "05b") for value in range(CAPACITY)
    }, "map does not partition all D5 coordinates")

    require(acct["domain_ratified"] is True, "accounting lost ratified-domain flag")
    require(acct["generated_coordinate_count"] == len(RATIFIED_GENERATED), (
        "accounting generated count drift"
    ))
    require(acct["unknown_free_count"] == EXPECTED_UNKNOWN, (
        "accounting UNKNOWN count drift"
    ))

    excluded = acct["excluded_or_unplaced_nonselector_capabilities"]
    expected_exclusions = {
        "SET-SETQ": "d5-ineligible-shared-location-family",
        "RETURN": "d5-ineligible-proven-root-domain-unresolved",
        "FEXPR-FSUBR": "d5-ineligible-carrier-family",
        "TRANSFORMER": "d5-ineligible-policy-over-carrier",
    }
    require(set(excluded) == set(expected_exclusions), (
        f"D5 post-D4 exclusion set drift: {sorted(excluded)}"
    ))
    for capability, expected_decision in expected_exclusions.items():
        require(excluded[capability]["decision"] == expected_decision, (
            f"{capability} D5 exclusion drift: "
            f"{excluded[capability]['decision']} != {expected_decision}"
        ))
        require(excluded[capability]["evidence"], (
            f"{capability} D5 exclusion lost evidence"
        ))

    return {
        "schema": "d5-ratified-baseline-guard/v1",
        "authority": "#2414/#2510/#2689",
        "domain": "Core D5",
        "width": WIDTH,
        "capacity": CAPACITY,
        "domain_ratified": True,
        "baseline_ratified": True,
        "generated_count": len(generated),
        "unknown_count": len(unknown),
        "manual_nonselector_count": len(other),
        "collision_count": sum(bool(row["collision"]) for row in rows),
        "generated_coordinates": sorted(generated_words),
        "unknown_coordinates": sorted(unknown_words),
        "owner_update_required_for_occupancy_change": True,
        "unknown_is_spare_capacity": False,
        "core_math_may_fill_core_d5_by_analogy": False,
        "status": "PASS",
        "non_conclusions": [
            "historical presence is not Core D5 occupancy",
            "UNKNOWN/free is a protected epistemic state, not permission",
            "research overlays do not become residents",
            "same-bit or same-transform Core-Math evidence cannot populate Core D5",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    result = build_result()

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print("D5-RATIFIED-BASELINE=PASS")
    print(f"width={result['width']}")
    print(f"capacity={result['capacity']}")
    print(f"generated={result['generated_count']}")
    print(f"unknown={result['unknown_count']}")
    print(f"manual={result['manual_nonselector_count']}")
    print(f"collisions={result['collision_count']}")
    print("owner-update-required-for-occupancy-change=yes")
    print("unknown-is-spare-capacity=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
