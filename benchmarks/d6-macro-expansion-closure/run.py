#!/usr/bin/env python3
"""#3083 — coordinate-independent D6 macro expansion step/closure witness.

Research-only. Models only the admitted relation:
one expansion step versus repeated application to a fixed point.
No hygiene, scope, CURRENT coordinates, or placement semantics are invented.
"""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

STEP_RESIDENT = "sr-nktdyaykppbg"
FULL_RESIDENT = "sr-ztbkmfrnrcjr"


def macro_step(form: Any) -> tuple[Any, bool]:
    """Apply at most one outer macro rewrite."""
    if not isinstance(form, list) or not form:
        return deepcopy(form), False

    head = form[0]
    args = form[1:]

    if head == "once" and len(args) == 1:
        x = deepcopy(args[0])
        return ["pair", x, deepcopy(x)], True

    if head == "twice" and len(args) == 1:
        return ["once", deepcopy(args[0])], True

    if head == "loop-a" and len(args) == 1:
        return ["loop-b", deepcopy(args[0])], True

    if head == "loop-b" and len(args) == 1:
        return ["loop-a", deepcopy(args[0])], True

    return deepcopy(form), False


def full_expand(form: Any, *, budget: int = 16) -> dict[str, Any]:
    current = deepcopy(form)
    ancestry: list[dict[str, Any]] = []

    for _ in range(budget + 1):
        nxt, changed = macro_step(current)
        if not changed:
            return {
                "status": "FIXED-POINT",
                "result": current,
                "steps": len(ancestry),
                "ancestry": ancestry,
            }

        if len(ancestry) >= budget:
            return {
                "status": "INCOMPLETE/RESOURCE-BOUND",
                "result": None,
                "partial": current,
                "steps": len(ancestry),
                "ancestry": ancestry,
            }

        ancestry.append({
            "before": deepcopy(current),
            "after": deepcopy(nxt),
        })
        current = nxt

    raise AssertionError("unreachable")


def replay_ancestry(result: dict[str, Any]) -> None:
    for edge in result["ancestry"]:
        replayed, changed = macro_step(edge["before"])
        assert changed
        assert replayed == edge["after"]


def zero_step_control() -> dict[str, Any]:
    form = ["pair", "a", "b"]
    stepped, changed = macro_step(form)
    full = full_expand(form)

    assert not changed
    assert stepped == form
    assert full["status"] == "FIXED-POINT"
    assert full["result"] == form
    assert full["steps"] == 0

    return {
        "form": form,
        "step_changed": changed,
        "full_status": full["status"],
        "full_steps": full["steps"],
    }


def one_step_control() -> dict[str, Any]:
    form = ["once", "a"]
    stepped, changed = macro_step(form)
    full = full_expand(form)

    assert changed
    assert stepped == ["pair", "a", "a"]
    assert full["status"] == "FIXED-POINT"
    assert full["result"] == stepped
    assert full["steps"] == 1
    replay_ancestry(full)

    fixed, changed_again = macro_step(full["result"])
    assert not changed_again
    assert fixed == full["result"]

    return {
        "form": form,
        "step_result": stepped,
        "full_result": full["result"],
        "full_steps": full["steps"],
        "step_equals_full": True,
        "fixed_point_reached": True,
    }


def multi_step_control() -> dict[str, Any]:
    form = ["twice", "a"]
    stepped, changed = macro_step(form)
    full = full_expand(form)

    assert changed
    assert stepped == ["once", "a"]
    assert full["status"] == "FIXED-POINT"
    assert full["result"] == ["pair", "a", "a"]
    assert full["steps"] == 2
    assert stepped != full["result"]
    replay_ancestry(full)

    fixed, changed_again = macro_step(full["result"])
    assert not changed_again
    assert fixed == full["result"]

    # Closure is idempotent once at fixed point.
    second_full = full_expand(full["result"])
    assert second_full["status"] == "FIXED-POINT"
    assert second_full["result"] == full["result"]
    assert second_full["steps"] == 0

    return {
        "form": form,
        "step_result": stepped,
        "full_result": full["result"],
        "full_steps": full["steps"],
        "step_equals_full": False,
        "fixed_point_reached": True,
        "closure_idempotent_at_fixed_point": True,
        "ancestry": full["ancestry"],
    }


def resource_bound_control() -> dict[str, Any]:
    form = ["loop-a", "x"]
    result = full_expand(form, budget=4)

    assert result["status"] == "INCOMPLETE/RESOURCE-BOUND"
    assert result["result"] is None
    assert result["steps"] == 4
    replay_ancestry(result)

    return {
        "form": form,
        "status": result["status"],
        "steps": result["steps"],
        "false_fixed_point_emitted": False,
        "ancestry": result["ancestry"],
    }


def falsifier() -> dict[str, Any]:
    multi = multi_step_control()
    assert multi["step_result"] != multi["full_result"]
    return {
        "candidate": "one-step-equals-full-for-all-macro-inputs",
        "status": "REFUTED",
        "counterexample": multi["form"],
        "one_step": multi["step_result"],
        "full": multi["full_result"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    zero = zero_step_control()
    one = one_step_control()
    multi = multi_step_control()
    bounded = resource_bound_control()
    false = falsifier()

    relation = {
        "schema": "d6-multilaw-relation/v1",
        "authority": "research-only",
        "parent": "#3077",
        "issue": "#3083",
        "stable_resident_ids": [STEP_RESIDENT, FULL_RESIDENT],
        "diagnostic_projection": {
            STEP_RESIDENT: "MACROEXPAND-1",
            FULL_RESIDENT: "MACROEXPAND",
        },
        "relation_type": "ITERATION-CLOSURE",
        "carrier_domain": "outer-macro-rewrite/v1",
        "semantic_equations": {
            "step": "STEP(f)=one admitted outer rewrite if available, else f",
            "full": "FULL(f)=least reached fixed point of repeated STEP(f), when reached within resource policy",
            "fixed_point": "STEP(FULL(f))=FULL(f) for completed terminating runs",
            "ancestry": "every FULL edge replays exactly through STEP",
        },
        "termination_policy": {
            "completed": "FIXED-POINT",
            "resource_exhaustion": "INCOMPLETE/RESOURCE-BOUND",
            "false_result_on_exhaustion": False,
        },
        "witness": {
            "zero_step": zero,
            "one_step": one,
            "multi_step": multi,
            "resource_bound": bounded,
        },
        "negative_controls": [false],
        "scope_policy": {
            "hygiene_claim": "NONE",
            "lexical_scope_claim": "NONE",
            "reader/compiler_claim": "NONE",
        },
        "geometry": {
            "classification": "RELATION-ONLY",
            "fixes_absolute_coordinates": False,
            "fixes_adjacency": False,
            "fixes_orientation": False,
            "coordinate_theorem_status": "UNKNOWN",
            "current_adjacency_authority": 0,
            "solver_bonus_allowed_now": False,
        },
        "status": "BOUNDED-CONFIRMED",
        "non_conclusions": [
            "iteration/closure relation does not imply one-bit adjacency",
            "resource-bounded INCOMPLETE is not semantic failure",
            "no hygiene or scope semantics are inferred",
            "CURRENT placement is not evidence",
            "no production remap is proposed",
        ],
    }

    (args.out / "relation.json").write_text(
        json.dumps(relation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows = [
        {
            "stable_resident_id": STEP_RESIDENT,
            "role": "STEP",
            "zero_step_case": "UNCHANGED",
            "one_step_case_steps": 1,
            "multi_step_case_result": json.dumps(multi["step_result"]),
            "resource_bound_status": "N/A",
            "geometry_status": "RELATION-ONLY",
        },
        {
            "stable_resident_id": FULL_RESIDENT,
            "role": "FIXED-POINT-CLOSURE",
            "zero_step_case": "FIXED-POINT",
            "one_step_case_steps": 1,
            "multi_step_case_result": json.dumps(multi["full_result"]),
            "resource_bound_status": bounded["status"],
            "geometry_status": "RELATION-ONLY",
        },
    ]

    with (args.out / "relation.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    report = [
        "# D6 macro expansion closure — #3083",
        "",
        f"Stable STEP resident: `{STEP_RESIDENT}`",
        f"Stable FULL resident: `{FULL_RESIDENT}`",
        "",
        "Confirmed relation:",
        "- STEP applies at most one outer rewrite;",
        "- FULL replays STEP until a fixed point;",
        "- every FULL ancestry edge independently replays through STEP;",
        "- completed FULL output is a STEP fixed point.",
        "",
        "Controls:",
        "- non-macro: 0 steps;",
        "- one-step macro: STEP == FULL;",
        "- multi-step macro: STEP != FULL, FULL reaches fixed point in 2 steps;",
        "- cyclic macro: INCOMPLETE/RESOURCE-BOUND, no false fixed point.",
        "",
        "Falsifier: universal STEP == FULL is refuted by the multi-step case.",
        "",
        "Geometry status: **RELATION-ONLY**.",
        "No adjacency/orientation/absolute-coordinate theorem is claimed.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
