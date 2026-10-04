#!/usr/bin/env python3
"""#3082 — coordinate-independent D6 pair mutation duality witness.

Research-only. Stable resident IDs are semantic research handles.
CURRENT coordinates are deliberately absent from the proof.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FIRST = "FIRST"
REST = "REST"

RPLACA_RESIDENT = "sr-tdedcubrnwcy"
RPLACD_RESIDENT = "sr-gmqxwcmzqfnp"


class NonPairError(TypeError):
    pass


@dataclass
class Pair:
    first: Any
    rest: Any


def select(pair: Pair, field: str) -> Any:
    if not isinstance(pair, Pair):
        raise NonPairError("selector requires Pair")
    if field == FIRST:
        return pair.first
    if field == REST:
        return pair.rest
    raise ValueError("unknown field")


def update(pair: Pair, field: str, value: Any) -> Pair:
    if not isinstance(pair, Pair):
        raise NonPairError("mutation requires Pair")
    if field == FIRST:
        pair.first = value
    elif field == REST:
        pair.rest = value
    else:
        raise ValueError("unknown field")
    return pair


def snapshot(pair: Pair) -> tuple[Any, Any]:
    return (pair.first, pair.rest)


def corpus() -> list[tuple[Any, Any, Any]]:
    nested = Pair("n0", "n1")
    return [
        ("a", "b", "x"),
        (0, 1, 2),
        (None, "tail", "new"),
        (nested, Pair("r0", "r1"), Pair("v0", "v1")),
    ]


def run_operation(field: str) -> dict[str, Any]:
    cases = 0
    alias_cases = 0
    identity_cases = 0
    target_change_cases = 0
    other_preserved_cases = 0
    selector_axis_cases = 0

    for first, rest, new_value in corpus():
        pair = Pair(first, rest)
        alias = pair
        before = snapshot(pair)

        returned = update(pair, field, new_value)
        after = snapshot(pair)

        assert returned is pair
        assert alias is pair
        identity_cases += 1

        if field == FIRST:
            assert after[0] is new_value or after[0] == new_value
            assert after[1] is before[1] or after[1] == before[1]
            assert select(pair, FIRST) is new_value or select(pair, FIRST) == new_value
            assert select(pair, REST) is before[1] or select(pair, REST) == before[1]
        else:
            assert after[1] is new_value or after[1] == new_value
            assert after[0] is before[0] or after[0] == before[0]
            assert select(pair, REST) is new_value or select(pair, REST) == new_value
            assert select(pair, FIRST) is before[0] or select(pair, FIRST) == before[0]

        target_change_cases += 1
        other_preserved_cases += 1
        selector_axis_cases += 1

        # The alias observes the same in-place change.
        assert snapshot(alias) == after
        alias_cases += 1
        cases += 1

    return {
        "field": field,
        "cases": cases,
        "identity_cases": identity_cases,
        "alias_cases": alias_cases,
        "target_change_cases": target_change_cases,
        "other_preserved_cases": other_preserved_cases,
        "selector_axis_cases": selector_axis_cases,
    }


def failure_parity() -> list[dict[str, str]]:
    rows = []
    for field in (FIRST, REST):
        for bad in (None, 0, "not-a-pair", ("PAIR-LIKE",)):
            try:
                update(bad, field, "x")
            except NonPairError as exc:
                rows.append({
                    "field": field,
                    "input_type": type(bad).__name__,
                    "status": "FAIL-CLOSED",
                    "error_class": type(exc).__name__,
                })
            else:
                raise AssertionError("non-pair mutation unexpectedly succeeded")
    assert len(rows) == 8
    assert {row["error_class"] for row in rows} == {"NonPairError"}
    return rows


def extra_delta_falsifier() -> dict[str, Any]:
    """A deliberately bad update changes both fields; the axis model must reject it."""
    pair = Pair("a", "b")
    before = snapshot(pair)
    pair.first = "x"
    pair.rest = "x"
    after = snapshot(pair)

    changed = [
        field
        for field, old, new in (
            (FIRST, before[0], after[0]),
            (REST, before[1], after[1]),
        )
        if old != new
    ]
    assert changed == [FIRST, REST]
    return {
        "candidate": "update-both-fields",
        "status": "REFUTED-AS-ONE-AXIS",
        "changed_fields": changed,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    first_result = run_operation(FIRST)
    rest_result = run_operation(REST)
    failures = failure_parity()
    falsifier = extra_delta_falsifier()

    # Same generic mechanism, exactly one semantic field parameter.
    mechanism = {
        "operation": "destructive-pair-update(pair, field, value) -> same pair",
        "field_domain": [FIRST, REST],
        "observer_relation": "after[field]=value; after[other(field)]=before[other(field)]",
        "alias_relation": "all aliases observe the same updated pair identity",
    }

    relation = {
        "schema": "d6-multilaw-relation/v1",
        "authority": "research-only",
        "parent": "#3077",
        "issue": "#3082",
        "stable_resident_ids": [RPLACA_RESIDENT, RPLACD_RESIDENT],
        "diagnostic_projection": {
            RPLACA_RESIDENT: "RPLACA",
            RPLACD_RESIDENT: "RPLACD",
        },
        "relation_type": "SELECTOR-INDEXED-MUTATION-DUALITY",
        "carrier_domain": "mutable-pair/v1",
        "semantic_equation": mechanism["observer_relation"],
        "mechanism": mechanism,
        "partiality": "defined-on-Pair; non-Pair fails closed",
        "witness": {
            "first_field": first_result,
            "rest_field": rest_result,
            "failure_parity_cases": len(failures),
            "object_identity_preserved": True,
            "alias_visibility_preserved": True,
            "selector_axis_independently_checked": True,
        },
        "negative_controls": {
            "extra_semantic_delta": falsifier,
            "non_pair_failure_parity": failures,
        },
        "selector_connection": {
            "semantic_axis": [FIRST, REST],
            "relation": "mutation target field uses same independently stated first/rest distinction as selector observation",
            "borrowed_current_bits": False,
            "borrowed_d6_coordinates": False,
        },
        "geometry": {
            "classification": "PRODUCT-AXIS-CANDIDATE",
            "fixes_absolute_coordinates": False,
            "fixes_adjacency": False,
            "fixes_orientation": False,
            "coordinate_theorem_status": "UNKNOWN",
            "current_adjacency_authority": 0,
            "solver_bonus_allowed_now": False,
        },
        "status": "BOUNDED-CONFIRMED",
        "non_conclusions": [
            "field duality does not prove one-bit adjacency",
            "shared first/rest semantics does not copy selector coordinates into D6",
            "mutation mechanism does not imply pure selector semantics",
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
            "stable_resident_id": RPLACA_RESIDENT,
            "field": FIRST,
            "cases": first_result["cases"],
            "identity_preserved": True,
            "alias_visible": True,
            "other_field_preserved": True,
            "failure_parity": "NonPairError",
            "geometry_status": "PRODUCT-AXIS-CANDIDATE",
        },
        {
            "stable_resident_id": RPLACD_RESIDENT,
            "field": REST,
            "cases": rest_result["cases"],
            "identity_preserved": True,
            "alias_visible": True,
            "other_field_preserved": True,
            "failure_parity": "NonPairError",
            "geometry_status": "PRODUCT-AXIS-CANDIDATE",
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
        "# D6 pair-mutation axis — #3082",
        "",
        f"Stable resident A: `{RPLACA_RESIDENT}`",
        f"Stable resident B: `{RPLACD_RESIDENT}`",
        "",
        "One generic mutation mechanism is sufficient:",
        "",
        "    destructive-pair-update(pair, field, value) -> same pair",
        "",
        "Confirmed for both FIRST and REST:",
        "- exactly the selected field changes;",
        "- the other field is preserved;",
        "- returned object identity is unchanged;",
        "- aliases observe the in-place mutation;",
        "- selector observation of the target/non-target fields agrees;",
        "- non-Pair failure behavior is symmetric and fail-closed.",
        "",
        "Falsifier: a candidate that changes both fields is rejected as a one-axis model.",
        "",
        "Geometry status: **PRODUCT-AXIS-CANDIDATE** only.",
        "No adjacency, orientation or absolute coordinate theorem is claimed.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
