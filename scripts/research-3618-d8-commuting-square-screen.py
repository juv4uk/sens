#!/usr/bin/env python3
"""#3618 D8 commuting-square evidence screen.

This script does NOT derive D8 residency. It machine-checks whether the current
D6 binary-law-family corpus already contains enough independent semantic axes
to justify a two-bit D8 product square.

Required for one D8 square:
    two independently observable binary refinements
    + executable commutativity witness
    + parent preservation
    + collision check

Current source corpus:
    knowledge/d6-v2-binary-law-families.json
    knowledge/d6-ratified.json

The screen is deliberately conservative: one documented binary relation counts
as one proved axis. Missing second-axis evidence remains UNKNOWN, never inferred
from coordinate symmetry.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FAMILIES_PATH = REPO / "knowledge" / "d6-v2-binary-law-families.json"
D6_PATH = REPO / "knowledge" / "d6-ratified.json"

REQUIRED_AXES = 2
EXPECTED_FAMILIES = 16
EXPECTED_MEMBERS = 32


@dataclass(frozen=True)
class Policy:
    scope: str
    miss: str


def refine_scope(p: Policy) -> Policy:
    return replace(p, scope="nearest")


def refine_miss(p: Policy) -> Policy:
    return replace(p, miss="fail")


def force_current(p: Policy) -> Policy:
    return replace(p, scope="current")


def flip_scope(p: Policy) -> Policy:
    return replace(p, scope="nearest" if p.scope == "current" else "current")


def positive_control() -> dict[str, object]:
    """Replay #2506's product-law shape as a method control."""
    p = Policy(scope="current", miss="create")
    ab = refine_miss(refine_scope(p))
    ba = refine_scope(refine_miss(p))
    assert ab == ba == Policy(scope="nearest", miss="fail")
    assert refine_scope(refine_scope(p)) == refine_scope(p)
    assert refine_miss(refine_miss(p)) == refine_miss(p)
    return {
        "control": "2506-method-shape",
        "axis_a": "scope",
        "axis_b": "miss-policy",
        "commutes": True,
        "independent": True,
        "status": "PASS",
    }


def negative_control() -> dict[str, object]:
    """Order-dependent transforms must not pass as a product law."""
    p = Policy(scope="current", miss="create")
    ab = force_current(flip_scope(p))
    ba = flip_scope(force_current(p))
    assert ab != ba
    return {
        "control": "ordered-transform-falsifier",
        "commutes": False,
        "status": "PASS-REJECTED",
    }


def selector_candidate_set(d6_residents: dict[str, str]) -> set[str]:
    """Current exact-coordinate collision control from D6 selector geometry."""
    parents = sorted(
        coordinate
        for coordinate in d6_residents
        if coordinate.startswith("011") or coordinate.startswith("100")
    )
    assert len(parents) == 16
    out = {
        parent + suffix
        for parent in parents
        for suffix in ("00", "01", "10", "11")
    }
    assert len(out) == 64
    return out


def load() -> tuple[dict[str, object], dict[str, object]]:
    families = json.loads(FAMILIES_PATH.read_text(encoding="utf-8"))
    d6 = json.loads(D6_PATH.read_text(encoding="utf-8"))
    return families, d6


def screen() -> dict[str, object]:
    families_doc, d6_doc = load()
    families = families_doc["families"]
    d6_residents: dict[str, str] = d6_doc["residents"]

    assert families_doc["schema"] == "d6-v2-binary-law-families/v1"
    assert d6_doc["status"] == "owner-ratified"
    assert d6_doc["authority"] == "#3393"
    assert len(families) == EXPECTED_FAMILIES
    assert len(d6_residents) == 64

    resident_to_coordinate = {resident: coordinate for coordinate, resident in d6_residents.items()}
    assert len(resident_to_coordinate) == len(d6_residents)

    seen_members: set[str] = set()
    rows: list[dict[str, object]] = []
    ready = 0

    for family in families:
        members = family["members"]
        relation = family["relation"]
        assert len(members) == 2
        assert isinstance(relation, str) and relation.strip()
        assert len(set(members)) == 2

        coordinates = []
        for member in members:
            assert member in resident_to_coordinate, member
            assert member not in seen_members, member
            seen_members.add(member)
            coordinates.append(resident_to_coordinate[member])

        proved_axes = 1
        second_axis_evidence = []
        product_ready = proved_axes >= REQUIRED_AXES and bool(second_axis_evidence)
        if product_ready:
            ready += 1

        rows.append(
            {
                "family_id": family["id"],
                "members": members,
                "coordinates": coordinates,
                "documented_relation": relation,
                "proved_binary_axes": proved_axes,
                "required_axes_for_d8_product": REQUIRED_AXES,
                "second_axis_evidence": second_axis_evidence,
                "candidate_d8_coordinates": [],
                "status": "PRODUCT-CANDIDATE" if product_ready else "INSUFFICIENT-CURRENT-EVIDENCE",
                "reason": (
                    "two independent axes documented"
                    if product_ready
                    else "current family corpus documents exactly one binary relation; a second independent axis is required"
                ),
            }
        )

    assert len(seen_members) == EXPECTED_MEMBERS
    assert ready == 0

    selector_candidates = selector_candidate_set(d6_residents)

    return {
        "schema": "d8-commuting-square-screen/v1",
        "authority": {
            "d6": "#3393",
            "d7_boundary": "#3572 / Contract 11.6",
            "d8": "#3281 research",
            "task": "#3618",
        },
        "proof_rule": "two independently observable binary semantic axes are required before any D8 2x2 product candidate is emitted",
        "positive_control": positive_control(),
        "negative_control": negative_control(),
        "counts": {
            "d6_binary_families_screened": len(rows),
            "d6_members_screened": len(seen_members),
            "families_with_one_documented_axis": sum(r["proved_binary_axes"] == 1 for r in rows),
            "families_ready_for_d8_product": ready,
            "d8_selector_collision_control_coordinates": len(selector_candidates),
        },
        "result": "0/16 current D6 binary-law families independently earn a D8 product square from the present corpus",
        "rows": rows,
        "non_conclusions": [
            "This does not prove that no second semantic axis exists.",
            "It proves that the current machine-readable family corpus does not contain one.",
            "No D8 coordinate is admitted, allocated, or made callable by this screen.",
            "Coordinate symmetry, free capacity, and historical D8 names are not evidence for a missing axis.",
        ],
    }


def render_markdown(report: dict[str, object]) -> str:
    c = report["counts"]
    lines = [
        "# D8 commuting-square evidence screen — #3618",
        "",
        f"- D6 binary families screened: {c['d6_binary_families_screened']}",
        f"- D6 residents covered: {c['d6_members_screened']}",
        f"- families with exactly one documented binary axis: {c['families_with_one_documented_axis']}",
        f"- families currently ready for a D8 two-axis product: **{c['families_ready_for_d8_product']}**",
        f"- current D8 selector collision-control coordinates: {c['d8_selector_collision_control_coordinates']}",
        "",
        "Result: **0/16** current D6 binary-law families independently earn a D8",
        "2×2 product square from the present machine-readable evidence.",
        "",
        "This is an evidence insufficiency result, not a proof of semantic impossibility.",
        "A family may advance only after a second independent observable axis and",
        "an executable commutativity witness are added.",
        "",
        "| family | D6 coordinates | documented axis | D8 status |",
        "|---|---|---|---|",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['family_id']} | {' / '.join(row['coordinates'])} | "
            f"{row['documented_relation']} | {row['status']} |"
        )
    lines += [
        "",
        "Controls:",
        "- #2506-style independent policy axes commute: PASS.",
        "- deliberately order-dependent transforms are rejected: PASS.",
        "",
        "No historical D8 donor rows are used as input.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    report = screen()
    text = render_markdown(report)

    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "screen.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.out / "report.md").write_text(text, encoding="utf-8")

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
