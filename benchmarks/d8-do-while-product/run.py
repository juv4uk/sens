#!/usr/bin/env python3
"""#3770 — D8 DO/WHILE condition-sense × terminal-projection product screen.

Research-only. This witness tests whether the current D6 DO/WHILE family
supports two independent semantic dimensions:

A: continue-while-true <-> stop-when-true
B: return terminal state <-> apply terminal result function

The test enumerates every total 3-state step function, every 3-state
PredicateBit function, and every total 3-state terminal projection. It does
not allocate D8 coordinates or claim runtime callability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
D6_AUTHORITY_PATH = REPO / "knowledge" / "d6-ratified.json"

STATES = (0, 1, 2)
BITS = (0, 1)
STEP_FUNCTIONS = tuple(product(STATES, repeat=len(STATES)))
PREDICATES = tuple(product(BITS, repeat=len(STATES)))
RESULT_FUNCTIONS = tuple(product(STATES, repeat=len(STATES)))

CONTINUE_TRUE = 0
STOP_TRUE = 1
RETURN_STATE = 0
APPLY_RESULT = 1

CORNERS = (
    (CONTINUE_TRUE, RETURN_STATE),
    (CONTINUE_TRUE, APPLY_RESULT),
    (STOP_TRUE, RETURN_STATE),
    (STOP_TRUE, APPLY_RESULT),
)


def load_authority() -> dict[str, object]:
    raw = D6_AUTHORITY_PATH.read_bytes()
    doc = json.loads(raw)
    assert doc["schema"] == "d6-ratified/v1"
    assert doc["status"] == "owner-ratified"
    assert doc["authority"] == "#3393"
    by_name = {name: coord for coord, name in doc["residents"].items()}
    assert by_name["DO"] == "110010"
    assert by_name["WHILE"] == "110011"
    return {
        "path": str(D6_AUTHORITY_PATH.relative_to(REPO)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "authority": doc["authority"],
        "do": by_name["DO"],
        "while": by_name["WHILE"],
    }


def toggle_condition(config: tuple[int, int]) -> tuple[int, int]:
    sense, finalize = config
    return (sense ^ 1, finalize)


def toggle_projection(config: tuple[int, int]) -> tuple[int, int]:
    sense, finalize = config
    return (sense, finalize ^ 1)


def evaluate(
    step: tuple[int, ...],
    predicate: tuple[int, ...],
    result: tuple[int, ...],
    start: int,
    sense: int,
    finalize: int,
) -> int | None:
    state = start
    seen: set[int] = set()

    while True:
        if state in seen:
            return None
        seen.add(state)

        pred = predicate[state]
        terminate = bool(pred) if sense == STOP_TRUE else not bool(pred)
        if terminate:
            return result[state] if finalize == APPLY_RESULT else state

        state = step[state]


def semantic_table(
    step: tuple[int, ...],
    predicate: tuple[int, ...],
    result: tuple[int, ...],
    config: tuple[int, int],
) -> tuple[int, ...] | None:
    values = []
    for start in STATES:
        value = evaluate(step, predicate, result, start, *config)
        if value is None:
            return None
        values.append(value)
    return tuple(values)


def mapping(values: tuple[int, ...]) -> dict[str, int]:
    return {str(state): values[state] for state in STATES}


def run() -> dict[str, object]:
    authority = load_authority()

    assert len(STEP_FUNCTIONS) == 27
    assert len(PREDICATES) == 8
    assert len(RESULT_FUNCTIONS) == 27

    transform_commutativity_checks = 0
    for config in CORNERS:
        transform_commutativity_checks += 1
        assert toggle_condition(toggle_projection(config)) == toggle_projection(
            toggle_condition(config)
        )

    schemas = 0
    all_four_terminate = 0
    all_four_distinct = 0
    first_four_distinct = None

    for step in STEP_FUNCTIONS:
        for predicate in PREDICATES:
            for result in RESULT_FUNCTIONS:
                schemas += 1
                tables = tuple(
                    semantic_table(step, predicate, result, config)
                    for config in CORNERS
                )

                if any(table is None for table in tables):
                    continue

                all_four_terminate += 1

                if len(set(tables)) == 4:
                    all_four_distinct += 1
                    if first_four_distinct is None:
                        first_four_distinct = {
                            "step": mapping(step),
                            "predicate": mapping(predicate),
                            "result": mapping(result),
                            "corner_tables": {
                                "00_continue_identity": list(tables[0]),
                                "01_continue_result": list(tables[1]),
                                "10_stop_identity": list(tables[2]),
                                "11_stop_result": list(tables[3]),
                            },
                        }

    assert schemas == 5832
    assert transform_commutativity_checks == 4
    assert all_four_terminate == 972
    assert all_four_distinct == 432
    assert first_four_distinct is not None

    return {
        "schema": "d8-do-while-product/v1",
        "status": "PRODUCT-CANDIDATE",
        "authority": {
            "d6": authority,
            "d8": "#3281 research",
            "parent": "#3618",
            "task": "#3770",
            "equations": "#3370",
        },
        "axes": {
            "condition_sense": {
                "0": "CONTINUE-WHILE-TRUE",
                "1": "STOP-WHEN-TRUE",
            },
            "terminal_projection": {
                "0": "RETURN-TERMINAL-STATE",
                "1": "APPLY-RESULT",
            },
            "transform_commutativity_checks": transform_commutativity_checks,
        },
        "corners": {
            "00": "WHILE-shaped: continue while predicate is true; return terminal state",
            "01": "continue while predicate is true; apply result at termination",
            "10": "stop when predicate is true; return terminal state",
            "11": "DO-shaped: stop when predicate is true; apply result at termination",
        },
        "carrier": {
            "states": list(STATES),
            "step_functions": len(STEP_FUNCTIONS),
            "predicates": len(PREDICATES),
            "result_functions": len(RESULT_FUNCTIONS),
            "schemas": schemas,
            "initial_states_per_schema": len(STATES),
        },
        "witness": {
            "schemas_all_four_corners_terminate": all_four_terminate,
            "schemas_all_four_tables_distinct": all_four_distinct,
            "first_all_four_distinct": first_four_distinct,
        },
        "result": {
            "condition_axis_observable": True,
            "terminal_projection_axis_observable": True,
            "axes_commute_structurally": True,
            "nondegenerate_product_witness_exists": True,
            "candidate_dimensions": 2,
            "admitted_d8_coordinates": 0,
            "candidate_footprint": [],
        },
        "non_conclusions": [
            "No D8 coordinate, resident, or callability is admitted.",
            "The two off-diagonal corners are semantic candidates only.",
            "Current D6 DO/WHILE runtime mechanisms are not inferred from residency.",
            "Coordinate orientation and selector-collision analysis remain separate.",
            "No D7 ancestry or historical D8 donor map is used.",
        ],
    }


def render(report: dict[str, object]) -> str:
    carrier = report["carrier"]
    witness = report["witness"]
    example = witness["first_all_four_distinct"]
    return "\n".join([
        "# D8 DO/WHILE product screen — #3770",
        "",
        "Result: **PRODUCT-CANDIDATE**.",
        "",
        f"- finite schemas: {carrier['schemas']}",
        (
            "- schemas where all four corners terminate: "
            f"{witness['schemas_all_four_corners_terminate']}"
        ),
        (
            "- schemas where all four global tables are distinct: "
            f"{witness['schemas_all_four_tables_distinct']}"
        ),
        "- axis transforms commute structurally: 4/4 configurations",
        "",
        "First non-degenerate four-corner witness:",
        f"- step: {example['step']}",
        f"- predicate: {example['predicate']}",
        f"- result: {example['result']}",
        f"- tables: {example['corner_tables']}",
        "",
        "D8 coordinates admitted: **0**.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = run()
    text = render(report)

    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "witness.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.out / "report.md").write_text(text, encoding="utf-8")

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
