#!/usr/bin/env python3
"""#2725 — D6 ratification non-contagion guard.

This guard is deliberately future-compatible with #2723.

It accepts either:
1. the current pre-application state where D6:001111 is still non-resident; or
2. the post-owner-decision state where exactly D6:001111 is a manual resident.

In both states, residency must not spread to:
- 001100 (parent duplicate),
- 001101 / 001110 (proof intermediates), or
- any of the 44 PURE-UNKNOWN coordinates.

The guard mutates copies of the canonical map to prove those promotions fail.
It never mutates repository occupancy.
"""

from __future__ import annotations

import argparse
import copy
import json
import runpy
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
CLOSURE = REPO / "benchmarks/d6-closure-map/run.py"
PLACEMENT = REPO / "benchmarks/post-d4-semantic-placement/placement.json"

TARGET = "001111"
PARENT_DUPLICATE = "001100"
MIDDLE = {"001101", "001110"}
OVERLAY = {PARENT_DUPLICATE, *MIDDLE, TARGET}
PROTECTED_HISTORY = {"SET", "RETURN", "FEXPR", "FSUBR", "TRANSFORMER"}


class GuardFailure(AssertionError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GuardFailure(message)


def load_rows() -> list[dict[str, Any]]:
    ns = runpy.run_path(str(CLOSURE))
    rows = ns["build_map"]()
    return copy.deepcopy(rows)


def index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["coordinate"]: row for row in rows}


def is_member(row: dict[str, Any]) -> bool:
    return bool(row.get("semantic_member_of_ratified_domain"))


def is_generated(row: dict[str, Any]) -> bool:
    return row.get("status") == "generated" or bool(row.get("core_closure"))


def placement(row: dict[str, Any]) -> str:
    value = row.get("placement_ref", "")
    return "" if value is None else str(value)


def classify_mode(rows: list[dict[str, Any]]) -> str:
    target = index(rows)[TARGET]
    return "POST-RATIFICATION" if is_member(target) else "PRE-RATIFICATION"


def validate_historical_nontransfer(mode: str) -> None:
    data = json.loads(PLACEMENT.read_text(encoding="utf-8"))
    rows = {row["operation"]: row for row in data["rows"]}
    require("SETQ" in rows, "SETQ missing from placement ledger")

    for operation in sorted(PROTECTED_HISTORY):
        require(operation in rows, f"{operation} missing from placement ledger")
        row = rows[operation]
        exact = str(row.get("exact_domain", ""))
        coordinate = str(row.get("coordinate", ""))
        candidate = str(row.get("candidate_coordinate", ""))
        require(exact != "D6", f"{operation} inherited D6 exact domain")
        require(not coordinate.startswith("D6:"), f"{operation} inherited D6 coordinate")
        require("D6:" not in candidate, f"{operation} inherited D6 candidate coordinate")

    setq = rows["SETQ"]
    evidence = " ".join(
        str(setq.get(key, ""))
        for key in (
            "exact_domain", "coordinate", "candidate_coordinate",
            "placement_kind", "resident_required",
        )
    )
    require("001111" in evidence, f"{mode}: SETQ lost 001111 placement evidence")


def validate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_coord = index(rows)
    require(len(rows) == 64, "D6 capacity changed")
    require(len(by_coord) == 64, "D6 coordinates are not unique")
    require(TARGET in by_coord, "missing D6:001111")
    require(OVERLAY <= set(by_coord), "binding-policy overlay coordinates missing")

    generated = [row for row in rows if is_generated(row)]
    require(len(generated) == 16, "selector-generated resident count changed")
    require(
        all(is_member(row) for row in generated),
        "generated selector row lost semantic membership",
    )

    generated_coords = {row["coordinate"] for row in generated}
    pure_coords = sorted(set(by_coord) - generated_coords - OVERLAY)
    require(len(pure_coords) == 44, "PURE-UNKNOWN orbit is not exactly 44 coordinates")

    target = by_coord[TARGET]
    mode = classify_mode(rows)

    if mode == "PRE-RATIFICATION":
        require(target.get("status") == "UNKNOWN/free", "pre-ratification 001111 must remain UNKNOWN/free")
        require(not is_member(target), "pre-ratification 001111 unexpectedly became a member")
        require(placement(target) == "", "pre-ratification 001111 unexpectedly has placement authority")
        expected_member_count = 16
        expected_unknown_count = 48
        expected_manual_count = 0
    else:
        require(not is_generated(target), "001111 must be manual/nonselector, not selector-generated")
        require(is_member(target), "post-ratification 001111 must be a semantic member")
        require(placement(target) != "", "post-ratification 001111 must carry explicit placement authority")
        if "manual_resident_required" in target:
            require(
                bool(target["manual_resident_required"]),
                "post-ratification 001111 must be marked manual resident when field is present",
            )
        expected_member_count = 17
        expected_unknown_count = 47
        expected_manual_count = 1

    # The three proof-square neighbors never inherit residency from 001111.
    for coordinate in sorted({PARENT_DUPLICATE, *MIDDLE}):
        row = by_coord[coordinate]
        require(not is_generated(row), f"{coordinate} unexpectedly became selector-generated")
        require(not is_member(row), f"{coordinate} inherited semantic membership")
        require(row.get("status") == "UNKNOWN/free", f"{coordinate} must remain UNKNOWN/free")
        require(placement(row) == "", f"{coordinate} inherited placement authority")

    # The 44 PURE-UNKNOWN coordinates remain untouched in either owner state.
    for coordinate in pure_coords:
        row = by_coord[coordinate]
        require(not is_generated(row), f"PURE-UNKNOWN {coordinate} became generated")
        require(not is_member(row), f"PURE-UNKNOWN {coordinate} became semantic member")
        require(row.get("status") == "UNKNOWN/free", f"PURE-UNKNOWN {coordinate} status drifted")
        require(placement(row) == "", f"PURE-UNKNOWN {coordinate} gained placement authority")

    semantic_members = [row for row in rows if is_member(row)]
    manual_members = [row for row in semantic_members if not is_generated(row)]
    unknown_rows = [row for row in rows if row.get("status") == "UNKNOWN/free"]

    require(
        len(semantic_members) == expected_member_count,
        f"{mode}: expected {expected_member_count} semantic members, got {len(semantic_members)}",
    )
    require(
        len(manual_members) == expected_manual_count,
        f"{mode}: expected {expected_manual_count} manual residents, got {len(manual_members)}",
    )
    require(
        len(unknown_rows) == expected_unknown_count,
        f"{mode}: expected {expected_unknown_count} UNKNOWN/free rows, got {len(unknown_rows)}",
    )

    if mode == "POST-RATIFICATION":
        require(
            [row["coordinate"] for row in manual_members] == [TARGET],
            "post-ratification manual residency spread beyond 001111",
        )

    return {
        "mode": mode,
        "capacity": len(rows),
        "generated": len(generated),
        "semantic_members": len(semantic_members),
        "manual_members": len(manual_members),
        "unknown_free": len(unknown_rows),
        "pure_unknown": len(pure_coords),
        "target_member": is_member(target),
        "target_placement_ref": placement(target),
        "protected_neighbors": sorted({PARENT_DUPLICATE, *MIDDLE}),
    }


def simulate_post_ratification(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = copy.deepcopy(rows)
    target = index(result)[TARGET]
    target["status"] = "ratified-manual-resident"
    target["semantic_family"] = "binding-policy/shared-location"
    target["semantic_law"] = "nearest-existing scope + fail-on-miss"
    target["semantic_law_authority"] = "#2723/#2538"
    target["semantic_member_of_ratified_domain"] = True
    target["manual_resident_required"] = True
    target["placement_ref"] = "#2723/#2538-OD-001"
    target["core_closure"] = False
    return result


def assert_mutation_rejected(rows: list[dict[str, Any]], coordinate: str) -> str:
    mutant = copy.deepcopy(rows)
    row = index(mutant)[coordinate]
    row["status"] = "ratified-manual-resident"
    row["semantic_member_of_ratified_domain"] = True
    row["manual_resident_required"] = True
    row["placement_ref"] = "#mutation-control"

    try:
        validate(mutant)
    except GuardFailure as exc:
        return str(exc)
    raise AssertionError(f"mutation control unexpectedly admitted {coordinate}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    current = load_rows()
    current_result = validate(current)
    validate_historical_nontransfer(current_result["mode"])

    # Future compatibility: on today's pre-ratification map, synthesize only the
    # exact owner-approved target transition and prove the same guard accepts it.
    if current_result["mode"] == "PRE-RATIFICATION":
        simulated_post = simulate_post_ratification(current)
        post_result = validate(simulated_post)
        require(post_result["mode"] == "POST-RATIFICATION", "post-ratification simulation did not enter POST mode")
    else:
        post_result = current_result

    # Mutation controls attack one middle corner and one PURE-UNKNOWN row in the
    # post-ratification state, where contagion pressure is strongest.
    post_rows = simulate_post_ratification(current) if current_result["mode"] == "PRE-RATIFICATION" else current
    by_coord = index(post_rows)
    generated_coords = {r["coordinate"] for r in post_rows if is_generated(r)}
    pure_coords = sorted(set(by_coord) - generated_coords - OVERLAY)
    pure_probe = pure_coords[0]

    mutation_controls = {
        "middle-001101": assert_mutation_rejected(post_rows, "001101"),
        "middle-001110": assert_mutation_rejected(post_rows, "001110"),
        "pure-unknown-probe": assert_mutation_rejected(post_rows, pure_probe),
    }

    artifact = {
        "schema": "d6-ratification-noncontagion/v1",
        "authority": "research-guard-only",
        "issue": "#2725",
        "ratification_parent": "#2723",
        "current": current_result,
        "post_ratification_control": post_result,
        "mutation_controls": mutation_controls,
        "pure_unknown_probe": pure_probe,
        "invariants": [
            "owner ratification is coordinate-specific",
            "001100 parent duplicate never inherits residency",
            "001101/001110 proof intermediates never inherit residency",
            "44 PURE-UNKNOWN coordinates remain non-members",
            "selector-generated count remains 16",
            "post-ratification manual resident set is exactly {001111}",
            "SET/RETURN/FEXPR/FSUBR/TRANSFORMER never inherit D6 residency",
        ],
        "non_conclusions": [
            "this guard does not ratify 001111",
            "this guard does not reopen owner placement theory",
            "future independent laws may separately reopen protected coordinates",
            "proof-square semantic states are not automatically language residents",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D6 ratification non-contagion — #2725",
        "",
        f"Current canonical mode: **{current_result['mode']}**",
        f"Current selector-generated residents: **{current_result['generated']}**",
        f"Current manual residents: **{current_result['manual_members']}**",
        f"Current UNKNOWN/free: **{current_result['unknown_free']}**",
        f"Protected PURE-UNKNOWN: **{current_result['pure_unknown']}**",
        "",
        "Future post-#2723 control:",
        f"- semantic members: {post_result['semantic_members']};",
        f"- manual residents: {post_result['manual_members']};",
        f"- UNKNOWN/free: {post_result['unknown_free']};",
        f"- PURE-UNKNOWN: {post_result['pure_unknown']}.",
        "",
        "Mutation controls:",
    ]
    for name, reason in mutation_controls.items():
        report.append(f"- {name}: REJECTED ({reason})")
    report += [
        "",
        "Interpretation:",
        "ratifying D6:001111 is a one-coordinate authority transition.",
        "Adjacency, shared prefix, and proof-square membership confer no residency.",
        "SETQ ratification also does not transfer residency to SET/RETURN/FEXPR/FSUBR/TRANSFORMER.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
