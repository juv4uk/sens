#!/usr/bin/env python3
"""#3263 — D4 -> D5 selector-boundary guard.

This guard does not choose a higher-selector encoding and does not mutate any
domain map. It makes one negative theorem executable:

    a lawful mechanical bit append at D4 does not authorize semantic
    inheritance into Core.D5.

Inputs are current repository artifacts, so a future D4 selector remap or D5
projection change automatically re-runs the collision analysis.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

D4 = Path("knowledge/d4-cleanroom.json")
D5_MAP = Path("knowledge/d5-historical-full-map.json")
D5_ATLAS = Path("knowledge/d5-internal-law-atlas.json")
D4_SELECTOR_RE = re.compile(r"^C[AD]{2}R$")


def fail(message: str) -> None:
    raise SystemExit(f"D4-D5-SELECTOR-BOUNDARY=FAIL\n{message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    d4 = load(D4)
    d5_map = load(D5_MAP)
    d5_atlas = load(D5_ATLAS)

    require(
        d4.get("schema") in {"d4-cleanroom/v1", "d4-ratified/v2"},
        f"unsupported D4 authority schema: {d4.get('schema')}",
    )
    require(d5_map.get("domain") == "Core.D5", "D5 projection domain drift")
    require(d5_map.get("width") == 5, "D5 projection width drift")
    require(d5_map.get("capacity") == 32, "D5 projection capacity drift")
    require(d5_map.get("status_counts", {}).get("unallocated") == 0, "D5 must remain fully occupied")

    doctrine = d5_atlas.get("doctrine", {})
    require(
        doctrine.get("universal_d4_parent_theorem") is False,
        "ratified D5 doctrine must keep universal D4 parenthood false",
    )
    require(
        doctrine.get("global_suffix_law") is False,
        "ratified D5 doctrine must keep global suffix law false",
    )
    require(
        d5_atlas.get("occupancy") == {"used": 32, "capacity": 32},
        "D5 internal-law atlas occupancy drift",
    )

    if d4.get("schema") == "d4-ratified/v2":
        residents = d4.get("residents", {})
        generated = set(d4.get("classification", {}).get("generated_selectors", []))
        require(generated, "ratified D4 generated-selector classification missing")
        selectors = {
            bits: label
            for bits, label in residents.items()
            if label in generated
        }
    else:
        admitted = d4.get("admitted", {})
        selectors = {
            bits: label
            for bits, label in admitted.items()
            if D4_SELECTOR_RE.fullmatch(label)
        }
    require(selectors, "no admitted clean-room D4 selectors found")
    require(
        all(len(bits) == 4 and set(bits) <= {"0", "1"} for bits in selectors),
        "invalid D4 selector coordinate",
    )

    d5_by_bits = {
        row["coordinate"]: row
        for row in d5_map.get("coordinates", [])
    }
    require(len(d5_by_bits) == 32, "D5 projection must contain all 32 coordinates")

    atlas_by_prefix = {
        row["prefix4"]: row
        for row in d5_atlas.get("pairs", [])
    }
    require(len(atlas_by_prefix) == 16, "D5 atlas must contain all 16 prefix pairs")

    collisions: list[dict[str, Any]] = []
    forbidden_inheritances = 0

    for parent_bits, parent_label in sorted(selectors.items()):
        for suffix in ("0", "1"):
            child_bits = parent_bits + suffix
            resident = d5_by_bits.get(child_bits)
            require(resident is not None, f"{child_bits}: D5 resident missing")
            atlas_pair = atlas_by_prefix.get(parent_bits)
            require(atlas_pair is not None, f"{parent_bits}: D5 atlas pair missing")
            atlas_child = atlas_pair[f"child{suffix}"]
            require(
                atlas_child["bits"] == child_bits,
                f"{child_bits}: D5 atlas/projection coordinate disagreement",
            )
            require(
                atlas_child["label"] == resident["name"],
                f"{child_bits}: D5 atlas/projection resident disagreement",
            )

            # The essential boundary theorem: current D4 selector semantics do
            # not make the exact D5 resident a generated selector child.
            if resident.get("category") != "selector":
                forbidden_inheritances += 1

            collisions.append(
                {
                    "d4_parent_bits": parent_bits,
                    "d4_parent_label": parent_label,
                    "suffix": suffix,
                    "naive_d5_bits": child_bits,
                    "ratified_d5_resident": resident["name"],
                    "ratified_d5_category": resident["category"],
                    "d5_relation_class": atlas_pair["relation_class"],
                    "d5_law_kind": atlas_pair["law_kind"],
                    "automatic_d4_parenthood": False,
                    "status": "BOUNDARY-COLLISION",
                }
            )

    expected = len(selectors) * 2
    require(
        forbidden_inheritances == expected,
        "one or more naive D4 selector extensions accidentally became D5 selector inheritance",
    )

    report = {
        "schema": "d4-d5-selector-boundary/v1",
        "issue": "#3263",
        "d4_schema": d4["schema"],
        "d4_authority": d4.get("authority"),
        "d5_projection_authority": d5_map.get("authority"),
        "d5_internal_law_authority": "OD-D5-LAW-001/#3055",
        "selector_parent_count": len(selectors),
        "naive_extension_count": expected,
        "boundary_collision_count": len(collisions),
        "automatic_prefix_inheritance": False,
        "higher_selector_encoding": "UNRESOLVED",
        "d5_occupancy_mutation": False,
        "collisions": collisions,
    }

    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("D4-D5-SELECTOR-BOUNDARY=PASS")
    print(f"D4-SELECTOR-PARENTS={len(selectors)}")
    print(f"NAIVE-D5-EXTENSIONS={expected}")
    print(f"BOUNDARY-COLLISIONS={len(collisions)}")
    for row in collisions:
        print(
            f"{row['d4_parent_bits']}:{row['d4_parent_label']}+{row['suffix']}"
            f"->{row['naive_d5_bits']}:{row['ratified_d5_resident']}"
        )
    print("AUTOMATIC-D4-PARENTHOOD=FALSE")
    print("GLOBAL-D5-SUFFIX-LAW=FALSE")
    print("HIGHER-SELECTOR-ENCODING=UNRESOLVED")
    print("D5-OCCUPANCY-MUTATION=FALSE")


if __name__ == "__main__":
    main()
