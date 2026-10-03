#!/usr/bin/env python3
"""#2420 — higher-order pair-eliminator lower-bound witness.

Research-only.

H0:
  whole-value identity/constants + ATOM/EQ + CONS/COND +
  LAMBDA/application + bounded iteration over public control state,
  with no pair-field observer.

H1:
  one explicit PAIR-CASE eliminator whose pair callback receives raw children.

H2:
  explicit UNCONS exposing both fields.

The H0 argument is a bounded executable equivariance witness: two opaque pair
worlds are related by whole-object renaming while their hidden children differ.
Every admitted H0 constructor preserves the relation. CAR/CDR targets do not.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Atom:
    name: str


@dataclass(frozen=True)
class PublicPair:
    left: Any
    right: Any


@dataclass(frozen=True)
class OpaquePair:
    token: str
    hidden_left: Any
    hidden_right: Any


FAIL = Atom("<FAIL>")
K = Atom("k")


@dataclass(frozen=True)
class Closure:
    param: str
    body: dict[str, Any]
    env: dict[str, Any]


def is_pair(value: Any) -> bool:
    return isinstance(value, (PublicPair, OpaquePair))


def atom_p(value: Any) -> bool:
    return not is_pair(value)


def visible_equal(left: Any, right: Any) -> bool:
    if isinstance(left, OpaquePair) or isinstance(right, OpaquePair):
        return (
            isinstance(left, OpaquePair)
            and isinstance(right, OpaquePair)
            and left.token == right.token
        )
    if isinstance(left, PublicPair) and isinstance(right, PublicPair):
        return visible_equal(left.left, right.left) and visible_equal(
            left.right, right.right
        )
    return left == right


def rename_world(value: Any) -> Any:
    if isinstance(value, OpaquePair):
        if value.token != "P0":
            raise ValueError(f"unexpected world-0 opaque token: {value.token}")
        # Hidden children deliberately do not participate in the public rename.
        return OpaquePair(
            "P1",
            Atom("hidden-c"),
            Atom("hidden-d"),
        )
    if isinstance(value, PublicPair):
        return PublicPair(rename_world(value.left), rename_world(value.right))
    if isinstance(value, Atom):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, Closure):
        return Closure(
            value.param,
            value.body,
            {key: rename_world(item) for key, item in value.env.items()},
        )
    raise TypeError(value)


def related(left: Any, right: Any) -> bool:
    if isinstance(left, OpaquePair):
        return (
            isinstance(right, OpaquePair)
            and left.token == "P0"
            and right.token == "P1"
        )
    if isinstance(left, PublicPair):
        return (
            isinstance(right, PublicPair)
            and related(left.left, right.left)
            and related(left.right, right.right)
        )
    if isinstance(left, Atom):
        return left == right
    if isinstance(left, bool):
        return left is right
    if isinstance(left, Closure):
        if not isinstance(right, Closure):
            return False
        if left.param != right.param or left.body != right.body:
            return False
        if left.env.keys() != right.env.keys():
            return False
        return all(related(left.env[k], right.env[k]) for k in left.env)
    return False


def var(name: str) -> dict[str, Any]:
    return {"var": name}


def const(name: str) -> dict[str, Any]:
    return {"const": name}


def cons(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {"cons": [left, right]}


def atom_expr(value: dict[str, Any]) -> dict[str, Any]:
    return {"atom": value}


def eq_expr(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {"eq": [left, right]}


def cond(
    predicate: dict[str, Any],
    yes: dict[str, Any],
    no: dict[str, Any],
) -> dict[str, Any]:
    return {"if": [predicate, yes, no]}


def lam(param: str, body: dict[str, Any]) -> dict[str, Any]:
    return {"lambda": {"param": param, "body": body}}


def app(fn: dict[str, Any], arg: dict[str, Any]) -> dict[str, Any]:
    return {"apply": [fn, arg]}


def iterate(
    count: int, fn: dict[str, Any], seed: dict[str, Any]
) -> dict[str, Any]:
    return {"iterate": {"count": count, "fn": fn, "seed": seed}}


def eval_expr(expr: dict[str, Any], env: dict[str, Any]) -> Any:
    if "var" in expr:
        return env[expr["var"]]
    if "const" in expr:
        return Atom(expr["const"])
    if "cons" in expr:
        left, right = expr["cons"]
        return PublicPair(eval_expr(left, env), eval_expr(right, env))
    if "atom" in expr:
        return atom_p(eval_expr(expr["atom"], env))
    if "eq" in expr:
        left, right = expr["eq"]
        return visible_equal(eval_expr(left, env), eval_expr(right, env))
    if "if" in expr:
        pred, yes, no = expr["if"]
        branch = yes if eval_expr(pred, env) else no
        return eval_expr(branch, env)
    if "lambda" in expr:
        payload = expr["lambda"]
        return Closure(payload["param"], payload["body"], dict(env))
    if "apply" in expr:
        fn_expr, arg_expr = expr["apply"]
        fn = eval_expr(fn_expr, env)
        arg_value = eval_expr(arg_expr, env)
        if not isinstance(fn, Closure):
            raise TypeError("application target is not a closure")
        call_env = dict(fn.env)
        call_env[fn.param] = arg_value
        return eval_expr(fn.body, call_env)
    if "iterate" in expr:
        payload = expr["iterate"]
        fn = eval_expr(payload["fn"], env)
        if not isinstance(fn, Closure):
            raise TypeError("iteration step is not a closure")
        state = eval_expr(payload["seed"], env)
        for _ in range(int(payload["count"])):
            call_env = dict(fn.env)
            call_env[fn.param] = state
            state = eval_expr(fn.body, call_env)
        return state
    raise ValueError(f"unknown expression: {expr}")


def prove_related(expr: dict[str, Any], env0: dict[str, Any], env1: dict[str, Any]):
    # Recursive executable relation-preservation check over the selected AST.
    # LAMBDA captures related environments; APPLY/ITERATE can therefore only
    # compose relation-preserving observations already present in the grammar.
    left = eval_expr(expr, env0)
    right = eval_expr(expr, env1)
    if not related(left, right):
        raise AssertionError(
            f"H0 relation broken by {json.dumps(expr, sort_keys=True)}: "
            f"{left!r} vs {right!r}"
        )
    return left, right


def h0_programs() -> list[tuple[str, dict[str, Any]]]:
    x = var("x")
    wrap = lam("y", cons(var("y"), const("k")))
    higher = app(
        lam("f", app(var("f"), x)),
        wrap,
    )
    composed = app(
        lam("z", app(wrap, var("z"))),
        x,
    )
    return [
        ("identity", x),
        ("constant", const("k")),
        ("construct", cons(x, const("k"))),
        (
            "whole-atom-control",
            cond(atom_expr(x), const("k"), x),
        ),
        (
            "whole-equality-control",
            cond(eq_expr(x, x), cons(x, const("k")), const("k")),
        ),
        ("lambda-application", app(wrap, x)),
        ("higher-order-application", higher),
        ("nested-composition", composed),
        ("public-state-iteration", iterate(4, wrap, x)),
        (
            "lambda-control",
            app(
                lam(
                    "z",
                    cond(
                        atom_expr(var("z")),
                        const("k"),
                        cons(var("z"), const("k")),
                    ),
                ),
                x,
            ),
        ),
    ]


def target_car(value: Any) -> Any:
    if isinstance(value, OpaquePair):
        return value.hidden_left
    if isinstance(value, PublicPair):
        return value.left
    return FAIL


def target_cdr(value: Any) -> Any:
    if isinstance(value, OpaquePair):
        return value.hidden_right
    if isinstance(value, PublicPair):
        return value.right
    return FAIL


def pair_case(value: Any, on_atom, on_pair):
    if isinstance(value, OpaquePair):
        return on_pair(value.hidden_left, value.hidden_right)
    if isinstance(value, PublicPair):
        return on_pair(value.left, value.right)
    return on_atom(value)


def pair_case_car(value: Any) -> Any:
    return pair_case(value, lambda _atom: FAIL, lambda left, _right: left)


def pair_case_cdr(value: Any) -> Any:
    return pair_case(value, lambda _atom: FAIL, lambda _left, right: right)


def uncons(value: Any):
    if isinstance(value, OpaquePair):
        return (value.hidden_left, value.hidden_right)
    if isinstance(value, PublicPair):
        return (value.left, value.right)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    p0 = OpaquePair("P0", Atom("hidden-a"), Atom("hidden-b"))
    p1 = OpaquePair("P1", Atom("hidden-c"), Atom("hidden-d"))
    assert related(p0, p1)

    env0 = {"x": p0}
    env1 = {"x": p1}

    h0_rows = []
    for name, expr in h0_programs():
        left, right = prove_related(expr, env0, env1)
        h0_rows.append(
            {
                "program": name,
                "relation_preserved": True,
                "left_result": repr(left),
                "right_result": repr(right),
            }
        )

    # The actual projections violate the H0 whole-object relation.
    car0, car1 = target_car(p0), target_car(p1)
    cdr0, cdr1 = target_cdr(p0), target_cdr(p1)
    assert not related(car0, car1)
    assert not related(cdr0, cdr1)

    # H1: as soon as PAIR-CASE explicitly hands raw children to a callback,
    # both projections are derivable and non-pair parity is explicit.
    sample_values = [
        p0,
        PublicPair(Atom("left"), Atom("right")),
        Atom("not-a-pair"),
    ]
    for value in sample_values:
        assert pair_case_car(value) == target_car(value)
        assert pair_case_cdr(value) == target_cdr(value)

    assert not related(pair_case_car(p0), pair_case_car(p1))
    assert not related(pair_case_cdr(p0), pair_case_cdr(p1))

    # H2: UNCONS is explicitly circular as a lower-bound derivation candidate:
    # its result interface already names/returns the two hidden fields.
    u0 = uncons(p0)
    assert u0 is not None
    assert u0[0] == target_car(p0)
    assert u0[1] == target_cdr(p0)
    assert uncons(Atom("not-a-pair")) is None

    capability_graph = {
        "nodes": [
            {
                "id": "whole-value",
                "kind": "observable",
                "authority": "opaque object identity only",
            },
            {"id": "ATOM", "kind": "predicate", "field_access": False},
            {"id": "EQ", "kind": "predicate", "field_access": False},
            {"id": "CONS", "kind": "constructor", "field_access": False},
            {"id": "COND", "kind": "control", "field_access": False},
            {
                "id": "LAMBDA/APPLY",
                "kind": "higher-order composition",
                "field_access": False,
            },
            {
                "id": "PUBLIC-ITERATION",
                "kind": "recursion/control",
                "field_access": False,
            },
            {
                "id": "PAIR-CASE",
                "kind": "eliminator",
                "field_access": True,
                "exposes": ["raw-left", "raw-right"],
            },
            {
                "id": "UNCONS",
                "kind": "eliminator",
                "field_access": True,
                "exposes": ["first", "rest"],
            },
            {"id": "CAR", "kind": "projection-target"},
            {"id": "CDR", "kind": "projection-target"},
        ],
        "edges": [
            {"from": "whole-value", "to": "ATOM", "kind": "whole-observation"},
            {"from": "whole-value", "to": "EQ", "kind": "whole-observation"},
            {"from": "whole-value", "to": "CONS", "kind": "construction"},
            {"from": "ATOM", "to": "COND", "kind": "control-input"},
            {"from": "EQ", "to": "COND", "kind": "control-input"},
            {
                "from": "LAMBDA/APPLY",
                "to": "PUBLIC-ITERATION",
                "kind": "composition-only",
            },
            {"from": "PAIR-CASE", "to": "CAR", "kind": "derives"},
            {"from": "PAIR-CASE", "to": "CDR", "kind": "derives"},
            {"from": "UNCONS", "to": "CAR", "kind": "explicit-field"},
            {"from": "UNCONS", "to": "CDR", "kind": "explicit-field"},
        ],
    }

    result = {
        "schema": "pair-eliminator-lower-bound/v1",
        "authority": "research-only",
        "H0": {
            "grammar": [
                "identity/constants",
                "ATOM",
                "EQ",
                "CONS",
                "COND",
                "LAMBDA/application",
                "bounded iteration over public control state",
            ],
            "pair_field_observer": False,
            "tested_programs": len(h0_rows),
            "equivariance": "PASS",
            "CAR_target_breaks_equivariance": True,
            "CDR_target_breaks_equivariance": True,
            "status": "BOUNDED-NONDERIVABLE-BY-OPAQUE-RELATION",
        },
        "H1": {
            "primitive": "PAIR-CASE",
            "callback_receives_raw_children": True,
            "CAR_derivable": True,
            "CDR_derivable": True,
            "malformed_nonpair_returns_FAIL": True,
            "authority_class": "PAIR-ELIMINATION",
            "economy": (
                "bundles both projection channels; row count alone cannot show "
                "it is weaker than CAR+CDR"
            ),
            "status": "EXPLICIT-NEW-ELIMINATOR-AUTHORITY",
        },
        "H2": {
            "primitive": "UNCONS",
            "output_signature": "Pair -> (first,rest) or failure",
            "CAR_certificate": "UNCONS.first",
            "CDR_certificate": "UNCONS.rest",
            "status": "CIRCULAR-EQUIVALENT-DESTRUCTURING-AUTHORITY",
        },
        "semantic_fact_accounting": {
            "H0_pair_field_channels": 0,
            "H1_new_eliminator_interfaces": 1,
            "H1_raw_child_channels": 2,
            "H2_explicit_child_channels": 2,
            "root_promotion": 0,
            "coordinate_allocation": 0,
            "economy_conclusion": "UNKNOWN-NOT-COMPARABLE-BY-COUNT",
        },
        "capability_graph": capability_graph,
        "non_conclusions": [
            "bounded executable equivariance is not a mechanized theorem over every possible host language",
            "PAIR-CASE may be an alternative basis candidate but is not proved smaller or preferable",
            "this does not prove D3 root uniqueness or coordinate placement",
            "higher-order composition is only field-neutral while its primitives are field-neutral",
        ],
    }

    with (args.out / "h0-programs.tsv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(h0_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(h0_rows)

    (args.out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Pair-eliminator lower bound — #2420",
        "",
        "H0 — no pair-field observer:",
        f"- tested higher-order/control programs: **{len(h0_rows)}**;",
        "- whole-object world-renaming equivariance: **PASS**;",
        "- CAR target violates the relation: **yes**;",
        "- CDR target violates the relation: **yes**.",
        "",
        "H1 — PAIR-CASE raw-child callback:",
        "- CAR derivable: **yes**;",
        "- CDR derivable: **yes**;",
        "- non-pair failure parity: **PASS**;",
        "- classification: **explicit pair-elimination authority**.",
        "",
        "H2 — UNCONS:",
        "- CAR certificate: `UNCONS.first`;",
        "- CDR certificate: `UNCONS.rest`;",
        "- classification: **circular/equivalent destructuring authority**.",
        "",
        "Interpretation:",
        "LAMBDA/application/ordinary control can compose available observations;",
        "they do not manufacture a hidden pair-field channel in this bounded model.",
        "A fold/case primitive that receives raw children succeeds precisely because",
        "that interface adds the missing eliminator authority.",
        "",
        "No D3 root promotion or coordinate allocation follows from this witness.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
