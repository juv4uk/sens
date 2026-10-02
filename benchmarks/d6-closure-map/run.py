#!/usr/bin/env python3
"""#2422 exact D6 closure map from already admitted selector roots/laws.

Research-only closure/accounting witness.

This script does NOT allocate D6 semantics. It classifies only what follows
from already admitted Core evidence:
- D3 selector roots 101 and 110;
- selector composition law;
- canonical coordinate realization root_bits || suffix.

Everything else remains UNKNOWN/free.
"""

from __future__ import annotations

import argparse
import csv
import json
from itertools import product
from pathlib import Path

WIDTH = 6
ROOTS = {
    "101": {"root_name": "CAR", "root_choice": 0},
    "110": {"root_name": "CDR", "root_choice": 1},
}
LAW_BITS = {
    "0": "compose-first-projection",
    "1": "compose-rest-projection",
}


def selector_rows() -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    suffix_width = WIDTH - 3
    for root_bits, meta in ROOTS.items():
        for suffix_tuple in product("01", repeat=suffix_width):
            suffix = "".join(suffix_tuple)
            coordinate = root_bits + suffix
            assert len(coordinate) == WIDTH
            rows[coordinate] = {
                "coordinate": coordinate,
                "width": WIDTH,
                "semantic_family": "selector",
                "status": "generated",
                "root_basis": root_bits,
                "root_name": meta["root_name"],
                "law_path": suffix,
                "law_steps": [LAW_BITS[bit] for bit in suffix],
                "semantic_law": "selector-composition/v1",
                "coordinate_realization": "canonical-root-bits-concatenated-with-law-path",
                "certificate_ref": (
                    f"selector.v1:root_choice={meta['root_choice']};"
                    f"depth={suffix_width};path={suffix}"
                ),
                "law_authority": ["#2410", "#2329", "#2345"],
                "anti_numerology_ref": "#2366",
                "collision": False,
                "core_admissible": False,
                "admission_reason": "generated evidence exists; D6 still requires separate owner ratification",
                "research_overlay_refs": [],
            }
    return rows


def build_map() -> list[dict[str, object]]:
    generated = selector_rows()
    rows: list[dict[str, object]] = []
    for n in range(1 << WIDTH):
        coordinate = format(n, f"0{WIDTH}b")
        if coordinate in generated:
            row = generated[coordinate]
        else:
            row = {
                "coordinate": coordinate,
                "width": WIDTH,
                "semantic_family": "",
                "status": "UNKNOWN/free",
                "root_basis": "",
                "root_name": "",
                "law_path": "",
                "law_steps": [],
                "semantic_law": "",
                "coordinate_realization": "",
                "certificate_ref": "",
                "law_authority": [],
                "anti_numerology_ref": "#2366",
                "collision": False,
                "core_admissible": False,
                "admission_reason": "no admitted Core law/root evidence for this coordinate",
                "research_overlay_refs": [],
            }
        rows.append(row)

    assert len(rows) == 64
    assert len({row["coordinate"] for row in rows}) == 64
    assert all(len(str(row["coordinate"])) == WIDTH for row in rows)
    assert sum(row["status"] == "generated" for row in rows) == 16
    assert sum(row["status"] == "UNKNOWN/free" for row in rows) == 48
    assert not any(bool(row["core_admissible"]) for row in rows)

    generated_coords = [row["coordinate"] for row in rows if row["status"] == "generated"]
    assert generated_coords == sorted(generated_coords)
    assert all(str(c).startswith(("101", "110")) for c in generated_coords)

    return rows


def report(rows: list[dict[str, object]]) -> str:
    generated = [row for row in rows if row["status"] == "generated"]
    unknown = [row for row in rows if row["status"] == "UNKNOWN/free"]
    collisions = [row for row in rows if row["collision"]]
    admissible = [row for row in rows if row["core_admissible"]]

    lines = [
        "# D6 closure map — #2422",
        "",
        "This is a closure map, not an allocation table.",
        "",
        "| class | count |",
        "|---|---:|",
        f"| exact D6 coordinates | {len(rows)} |",
        f"| generated selector coordinates | {len(generated)} |",
        f"| UNKNOWN/free | {len(unknown)} |",
        f"| collisions | {len(collisions)} |",
        f"| core-admissible before D6 owner ratification | {len(admissible)} |",
        "",
        "Generated positive-control coordinates are exactly the D3 selector roots",
        "101/110 extended by every three-step selector composition path.",
        "",
        "Semantic authority and coordinate realization are kept separate:",
        "- semantic law: selector composition;",
        "- canonical realization: root bits || law-path bits;",
        "- #2366 forbids treating the bit formula itself as representation-independent semantics.",
        "",
        "All 16 generated rows remain core_admissible=false until separate D6 owner ratification.",
        "All other 48 coordinates remain literally UNKNOWN/free.",
        "",
        "NON-CONCLUSIONS:",
        "- UNKNOWN/free does not mean candidate residue;",
        "- free capacity is not a request for named residents;",
        "- Core-Math hypotheses do not alter this Core closure;",
        "- generation certificate evidence does not itself ratify D6.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    rows = build_map()

    fields = [
        "coordinate",
        "width",
        "semantic_family",
        "status",
        "root_basis",
        "root_name",
        "law_path",
        "law_steps",
        "semantic_law",
        "coordinate_realization",
        "certificate_ref",
        "law_authority",
        "anti_numerology_ref",
        "collision",
        "core_admissible",
        "admission_reason",
        "research_overlay_refs",
    ]

    with (args.out / "d6-closure-map.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                **row,
                "law_steps": "|".join(row["law_steps"]),
                "law_authority": "|".join(row["law_authority"]),
                "research_overlay_refs": "|".join(row["research_overlay_refs"]),
            })

    payload = {
        "schema": "d6-closure-map/v1",
        "authority": "research-only",
        "width": WIDTH,
        "capacity": 64,
        "core_inputs": {
            "ratified_foundation": "#2410",
            "selector_forecast": "#2329",
            "generation_certificates": "#2345",
            "anti_numerology": "#2366",
        },
        "core_math_overlay_policy": (
            "separate candidate overlay only; never changes Core closure without ratification"
        ),
        "counts": {
            "generated": 16,
            "ratified-root": 0,
            "ratified-residue": 0,
            "UNKNOWN/free": 48,
            "collisions": 0,
            "core-admissible": 0,
        },
        "rows": rows,
    }
    (args.out / "d6-closure-map.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    text = report(rows)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
