#!/usr/bin/env python3
"""#3081 — coordinate-independent D6 LET/LET* binding-order witness."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

PARALLEL_RESIDENT = "sr-bdhyqsyttxzy"
SEQUENTIAL_RESIDENT = "sr-npgqyeyykjdd"

PARALLEL = "PARALLEL"
SEQUENTIAL = "SEQUENTIAL"


class BindingError(ValueError):
    pass


def const(value: int) -> dict[str, Any]:
    return {"const": value}


def var(name: str) -> dict[str, Any]:
    return {"var": name}


def add(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {"add": [left, right]}


def pair(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {"pair": [left, right]}


def eval_expr(expr: dict[str, Any], env: dict[str, Any]) -> Any:
    if "const" in expr:
        return expr["const"]
    if "var" in expr:
        name = expr["var"]
        if name not in env:
            raise BindingError(f"unbound variable: {name}")
        return env[name]
    if "add" in expr:
        left, right = expr["add"]
        return eval_expr(left, env) + eval_expr(right, env)
    if "pair" in expr:
        left, right = expr["pair"]
        return (eval_expr(left, env), eval_expr(right, env))
    raise BindingError("malformed expression")


def validate_bindings(bindings: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for row in bindings:
        if set(row) != {"name", "init"}:
            raise BindingError("malformed binding")
        name = row["name"]
        if not isinstance(name, str) or not name:
            raise BindingError("invalid binding name")
        if name in seen:
            raise BindingError("duplicate binding name")
        seen.add(name)


def bind_eval(
    mode: str,
    incoming: dict[str, Any],
    bindings: list[dict[str, Any]],
    body: dict[str, Any],
) -> tuple[Any, dict[str, Any]]:
    validate_bindings(bindings)
    base = dict(incoming)

    if mode == PARALLEL:
        values = [(row["name"], eval_expr(row["init"], base)) for row in bindings]
        extended = dict(base)
        extended.update(values)
    elif mode == SEQUENTIAL:
        extended = dict(base)
        for row in bindings:
            value = eval_expr(row["init"], extended)
            extended[row["name"]] = value
    else:
        raise BindingError("unknown binding-order policy")

    # Incoming environment is not mutated by lexical extension.
    assert incoming == base
    return eval_expr(body, extended), extended


def dependent_control() -> dict[str, Any]:
    incoming = {"x": 10}
    bindings = [
        {"name": "x", "init": const(1)},
        {"name": "y", "init": add(var("x"), const(1))},
    ]
    body = pair(var("x"), var("y"))

    par_value, par_env = bind_eval(PARALLEL, incoming, bindings, body)
    seq_value, seq_env = bind_eval(SEQUENTIAL, incoming, bindings, body)

    assert par_value == (1, 11)
    assert seq_value == (1, 2)
    assert par_value != seq_value
    assert incoming == {"x": 10}

    return {
        "incoming": incoming,
        "parallel_result": list(par_value),
        "sequential_result": list(seq_value),
        "parallel_y": par_env["y"],
        "sequential_y": seq_env["y"],
        "status": "DISTINGUISHES-POLICY",
    }


def independent_control() -> dict[str, Any]:
    incoming = {"outer": 5}
    bindings = [
        {"name": "a", "init": add(var("outer"), const(1))},
        {"name": "b", "init": add(var("outer"), const(2))},
    ]
    body = add(var("a"), var("b"))

    par_value, _ = bind_eval(PARALLEL, incoming, bindings, body)
    seq_value, _ = bind_eval(SEQUENTIAL, incoming, bindings, body)
    assert par_value == seq_value == 13

    return {
        "parallel_result": par_value,
        "sequential_result": seq_value,
        "status": "AGREES-WHEN-INDEPENDENT",
    }


def alpha_renaming_control() -> dict[str, Any]:
    incoming = {"outer": 7}
    original = [
        {"name": "a", "init": add(var("outer"), const(1))},
        {"name": "b", "init": add(var("outer"), const(2))},
    ]
    renamed = [
        {"name": "p", "init": add(var("outer"), const(1))},
        {"name": "q", "init": add(var("outer"), const(2))},
    ]

    results = {}
    for mode in (PARALLEL, SEQUENTIAL):
        left, _ = bind_eval(mode, incoming, original, pair(var("a"), var("b")))
        right, _ = bind_eval(mode, incoming, renamed, pair(var("p"), var("q")))
        assert left == right == (8, 9)
        results[mode] = list(left)

    return {"status": "ALPHA-INVARIANT", "results": results}


def shadowing_control() -> dict[str, Any]:
    incoming = {"x": 10, "keep": 3}
    bindings = [{"name": "x", "init": const(1)}]

    rows = {}
    for mode in (PARALLEL, SEQUENTIAL):
        value, env = bind_eval(mode, incoming, bindings, pair(var("x"), var("keep")))
        assert value == (1, 3)
        assert env["x"] == 1
        assert incoming["x"] == 10
        rows[mode] = list(value)

    return {
        "status": "OUTER-BINDING-SHADOWED-WITHOUT-MUTATING-INCOMING",
        "results": rows,
    }


def malformed_controls() -> list[dict[str, str]]:
    cases = [
        (
            "duplicate-name",
            [
                {"name": "x", "init": const(1)},
                {"name": "x", "init": const(2)},
            ],
            const(0),
        ),
        (
            "missing-init",
            [{"name": "x"}],
            const(0),
        ),
        (
            "unbound-initializer",
            [{"name": "x", "init": var("missing")}],
            var("x"),
        ),
    ]

    rows = []
    for label, bindings, body in cases:
        for mode in (PARALLEL, SEQUENTIAL):
            try:
                bind_eval(mode, {}, bindings, body)
            except BindingError as exc:
                rows.append({
                    "control": label,
                    "mode": mode,
                    "status": "FAIL-CLOSED",
                    "error_class": type(exc).__name__,
                })
            else:
                raise AssertionError(f"{label}/{mode} unexpectedly succeeded")

    assert len(rows) == 6
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    dependent = dependent_control()
    independent = independent_control()
    alpha = alpha_renaming_control()
    shadowing = shadowing_control()
    malformed = malformed_controls()

    relation = {
        "schema": "d6-multilaw-relation/v1",
        "authority": "research-only",
        "parent": "#3077",
        "issue": "#3081",
        "stable_resident_ids": [PARALLEL_RESIDENT, SEQUENTIAL_RESIDENT],
        "diagnostic_projection": {
            PARALLEL_RESIDENT: "LET",
            SEQUENTIAL_RESIDENT: "LET*",
        },
        "relation_type": "BINDING-ORDER-POLICY",
        "carrier_domain": "lexical-environment-extension/v1",
        "semantic_equations": {
            "parallel": "v_i=eval(init_i,Gamma); Gamma'=extend_all(Gamma,(name_i,v_i))",
            "sequential": "Gamma_0=Gamma; v_i=eval(init_i,Gamma_{i-1}); Gamma_i=extend(Gamma_{i-1},name_i,v_i)",
        },
        "witness": {
            "dependent_initializer": dependent,
            "independent_initializers": independent,
            "alpha_renaming": alpha,
            "outer_shadowing": shadowing,
            "malformed_controls": malformed,
        },
        "semantic_delta": "initializer-environment policy only",
        "partiality": "malformed/duplicate/unbound input fails closed in research grammar",
        "geometry": {
            "classification": "PRODUCT-AXIS-CANDIDATE",
            "candidate_axis": "initializer-environment policy PARALLEL/SEQUENTIAL",
            "fixes_absolute_coordinates": False,
            "fixes_adjacency": False,
            "fixes_orientation": False,
            "coordinate_theorem_status": "UNKNOWN",
            "current_adjacency_authority": 0,
            "solver_bonus_allowed_now": False,
        },
        "status": "BOUNDED-CONFIRMED",
        "non_conclusions": [
            "semantic order policy does not prove one-bit adjacency",
            "no CURRENT coordinate is used as evidence",
            "research grammar does not claim every historical malformed-form detail",
            "no production remap is proposed",
        ],
    }

    (args.out / "relation.json").write_text(
        json.dumps(relation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows = [
        {
            "stable_resident_id": PARALLEL_RESIDENT,
            "policy": PARALLEL,
            "dependent_result": str(tuple(dependent["parallel_result"])),
            "independent_result": independent["parallel_result"],
            "alpha_invariant": True,
            "shadowing": True,
            "geometry_status": "PRODUCT-AXIS-CANDIDATE",
        },
        {
            "stable_resident_id": SEQUENTIAL_RESIDENT,
            "policy": SEQUENTIAL,
            "dependent_result": str(tuple(dependent["sequential_result"])),
            "independent_result": independent["sequential_result"],
            "alpha_invariant": True,
            "shadowing": True,
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
        "# D6 binding-order law — #3081",
        "",
        f"Stable resident A: `{PARALLEL_RESIDENT}`",
        f"Stable resident B: `{SEQUENTIAL_RESIDENT}`",
        "",
        "Dependent initializer control:",
        f"- PARALLEL result: **{tuple(dependent['parallel_result'])}**",
        f"- SEQUENTIAL result: **{tuple(dependent['sequential_result'])}**",
        "",
        "Independent initializer control:",
        f"- both policies: **{independent['parallel_result']}**",
        "",
        "Also confirmed:",
        "- alpha-renaming invariance;",
        "- outer-binding shadowing without mutating incoming environment;",
        "- malformed/duplicate/unbound forms fail closed in both policies.",
        "",
        "Semantic delta: initializer-environment policy only.",
        "",
        "Geometry status: **PRODUCT-AXIS-CANDIDATE** only.",
        "No adjacency/orientation/absolute-coordinate theorem is claimed.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
