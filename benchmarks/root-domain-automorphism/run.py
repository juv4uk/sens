#!/usr/bin/env python3
"""#2668 — automorphism falsifier for a one-root independent domain.

A separately declared parentless-root domain is not semantic progress if its
only content is "put the proven root in some free binary coordinate".

With one root and no internal domain law:
- every coordinate of a fixed n-bit cube is equivalent under XOR translation;
- every tested width can hold the same one-root set;
- therefore neither coordinate nor width is selected by semantics.

Research-only. No domain or coordinate is admitted.
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ROOT_MIN = ROOT / "benchmarks" / "post-d4-root-min-closeout" / "run.py"
D5_GRAPH = ROOT / "benchmarks" / "d5-structural-discovery" / "factor-graph.json"


def sole_root() -> dict[str, Any]:
    rows = runpy.run_path(str(ROOT_MIN))["ROWS"]
    roots = [row for row in rows if row["root_status"] == "PROVEN-ROOT"]
    assert len(roots) == 1
    root = roots[0]
    assert root["factor"] == "non-local-exit"
    assert root["width"] == "UNKNOWN"
    assert root["coordinate"] == "UNPLACED"
    return root


def xor_orbit(width: int, word: int) -> set[int]:
    assert width >= 1
    capacity = 1 << width
    assert 0 <= word < capacity
    return {word ^ mask for mask in range(capacity)}


def transitivity_table(max_width: int = 8) -> list[dict[str, Any]]:
    rows = []
    for width in range(1, max_width + 1):
        capacity = 1 << width
        orbit = xor_orbit(width, 0)
        assert orbit == set(range(capacity))
        rows.append(
            {
                "width": width,
                "capacity": capacity,
                "one_root_fits": True,
                "xor_orbit_size": len(orbit),
                "all_coordinates_equivalent_without_extra_law": True,
                "canonical_coordinate_selected": False,
            }
        )
    return rows


def selector_control() -> dict[str, Any]:
    graph = json.loads(D5_GRAPH.read_text(encoding="utf-8"))
    summary = graph["summary"]
    assert summary["d5_selector_generated"] == 8
    assert summary["d5_unknown_free"] == 24
    return {
        "domain": "Core-D5-selector-family",
        "generated_coordinates": summary["d5_selector_generated"],
        "unknown_free": summary["d5_unknown_free"],
        "why_not_table_relocation": (
            "coordinates are constrained by admitted CAR/CDR roots plus the "
            "selector composition generator; occupancy is not supplied by an "
            "arbitrary one-row root table"
        ),
    }


def build_result() -> dict[str, Any]:
    root = sole_root()
    widths = transitivity_table()
    selector = selector_control()

    # One root fits every tested positive width, so cardinality alone cannot
    # choose among them.
    assert all(row["one_root_fits"] for row in widths)
    assert len({row["width"] for row in widths}) > 1
    assert all(
        row["all_coordinates_equivalent_without_extra_law"] for row in widths
    )
    assert not any(row["canonical_coordinate_selected"] for row in widths)

    return {
        "schema": "independent-root-domain-automorphism/v1",
        "phase": "SENS-DERIVATION",
        "authority": "research-only-no-domain-admission",
        "positive_control": {
            "root": root["factor"],
            "status": root["root_status"],
            "width": root["width"],
            "coordinate": root["coordinate"],
            "evidence": root["evidence"],
        },
        "one_root_domain_attack": {
            "tested_widths": widths,
            "semantic_root_count": 1,
            "internal_relation_laws": 0,
            "generator_laws": 0,
            "result": "TABLE-RELOCATION",
            "reason": (
                "for each fixed width all coordinates are one XOR orbit, and "
                "one root fits every tested width; without an additional "
                "domain law neither coordinate nor width is invariant"
            ),
        },
        "generated_family_negative_control": selector,
        "verdict": {
            "root_domain": "TABLE-RELOCATION-UNDER-CURRENT-EVIDENCE",
            "exact_width": "UNRESOLVED",
            "coordinate": "UNPLACED",
            "new_domain_admitted": False,
            "new_residents": 0,
            "minimum_missing_evidence": (
                "an internal root-domain law/relation/carrier premise that "
                "breaks width and coordinate automorphisms independently of "
                "the root's human name"
            ),
        },
        "guards": [
            "one semantic root does not determine a bit width",
            "one row is not a domain law",
            "arbitrary coordinate orientation is not semantic identity",
            "declaring a new domain does not itself prove membership",
            "selector-generated families remain a positive law-driven control",
        ],
    }


def report(result: dict[str, Any]) -> str:
    v = result["verdict"]
    lines = [
        "# Independent root-domain automorphism attack — #2668",
        "",
        "Positive control: non-local-exit = sole post-D4 PROVEN-ROOT.",
        "",
        "| width | capacity | XOR orbit | canonical coordinate? |",
        "|---:|---:|---:|---|",
    ]
    for row in result["one_root_domain_attack"]["tested_widths"]:
        lines.append(
            f"| {row['width']} | {row['capacity']} | "
            f"{row['xor_orbit_size']} | no |"
        )
    lines += [
        "",
        "Result:",
        f"- ROOT-DOMAIN={v['root_domain']}",
        f"- EXACT-WIDTH={v['exact_width']}",
        f"- COORDINATE={v['coordinate']}",
        f"- NEW-DOMAIN-ADMITTED={str(v['new_domain_admitted']).lower()}",
        f"- NEW-RESIDENTS={v['new_residents']}",
        "",
        "Interpretation:",
        "A one-root domain with no internal law is only a renamed lookup table.",
        "An admissible independent root domain still needs a law that breaks the",
        "coordinate/width symmetries. The selector family is the negative control:",
        "its coordinates are generated by admitted semantic actions.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    result = build_result()
    (args.out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "report.md").write_text(report(result), encoding="utf-8")

    print("ROOT-DOMAIN-AUTOMORPHISM=PASS")
    print("ROOT-DOMAIN=TABLE-RELOCATION-UNDER-CURRENT-EVIDENCE")
    print("EXACT-WIDTH=UNRESOLVED")
    print("COORDINATE=UNPLACED")
    print("NEW-DOMAIN-ADMITTED=no")
    print("NEW-RESIDENTS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
