#!/usr/bin/env python3
"""#3230 clean-room D4: finite D1-D3 composition vs unbounded re-entry.

Allowed semantic vocabulary in this witness is restricted to ratified D1-D3:
EMPTY, QUOTE, ATOM, CAR, CDR, EQ, COND, CONS.

No historical post-D3 resident table or coordinate is used.

The executable witness has three roles:
1. structural lower-bound accounting for finite expressions;
2. finite-unroll sharpness tests with held-out deeper inputs;
3. two explicit post-D3 positive controls:
   reusable semantic re-entry and opaque stage-enter.

Research only. No D4 coordinate is assigned.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

YES = 1
NO = 0


@dataclass(frozen=True)
class Empty:
    pass


EMPTY = Empty()


@dataclass(frozen=True)
class Atom:
    name: str


@dataclass(frozen=True)
class Pair:
    first: Any
    rest: Any


class SemanticError(RuntimeError):
    pass


# ---- Ratified D1-D3 value operations -------------------------------------

def atom_p(value: Any) -> int:
    return YES if not isinstance(value, Pair) else NO


def car(value: Any) -> Any:
    if not isinstance(value, Pair):
        raise SemanticError("CAR requires pair")
    return value.first


def cdr(value: Any) -> Any:
    if not isinstance(value, Pair):
        raise SemanticError("CDR requires pair")
    return value.rest


def eq_p(left: Any, right: Any) -> int:
    if isinstance(left, Pair) or isinstance(right, Pair):
        return NO
    return YES if left == right else NO


def cons(first: Any, rest: Any) -> Pair:
    return Pair(first, rest)


# ---- Finite D1-D3 expression language -----------------------------------

@dataclass(frozen=True)
class Expr:
    op: str
    args: tuple[Any, ...] = ()


def var() -> Expr:
    return Expr("INPUT")


def empty_expr() -> Expr:
    return Expr("EMPTY")


def quote(value: Any) -> Expr:
    return Expr("QUOTE", (value,))


def unary(op: str, arg: Expr) -> Expr:
    return Expr(op, (arg,))


def binary(op: str, left: Expr, right: Expr) -> Expr:
    return Expr(op, (left, right))


def cond(test: Expr, yes: Expr, no: Expr) -> Expr:
    return Expr("COND", (test, yes, no))


def eval_expr(expr: Expr, input_value: Any) -> Any:
    op = expr.op
    if op == "INPUT":
        return input_value
    if op == "EMPTY":
        return EMPTY
    if op == "QUOTE":
        return expr.args[0]
    if op == "ATOM":
        return atom_p(eval_expr(expr.args[0], input_value))
    if op == "CAR":
        return car(eval_expr(expr.args[0], input_value))
    if op == "CDR":
        return cdr(eval_expr(expr.args[0], input_value))
    if op == "EQ":
        return eq_p(
            eval_expr(expr.args[0], input_value),
            eval_expr(expr.args[1], input_value),
        )
    if op == "CONS":
        return cons(
            eval_expr(expr.args[0], input_value),
            eval_expr(expr.args[1], input_value),
        )
    if op == "COND":
        test = eval_expr(expr.args[0], input_value)
        return eval_expr(expr.args[1] if test == YES else expr.args[2], input_value)
    raise SemanticError(f"unknown D1-D3 op: {op}")


def selector_bound(expr: Expr) -> int:
    """Finite upper bound on nested input inspection for this finite AST.

    This intentionally over-approximates some constructed-value cases.
    Finiteness, rather than exact minimal depth, is the lower-bound invariant.
    """
    if expr.op in {"INPUT", "EMPTY", "QUOTE"}:
        return 0
    if expr.op in {"CAR", "CDR"}:
        return 1 + selector_bound(expr.args[0])
    child_exprs = [x for x in expr.args if isinstance(x, Expr)]
    return max((selector_bound(x) for x in child_exprs), default=0)


def ast_nodes(expr: Expr) -> int:
    return 1 + sum(ast_nodes(x) for x in expr.args if isinstance(x, Expr))


# Target transformation:
# [a,b,c] -> [(a), (b), (c)] where each source element is wrapped as Pair(a,EMPTY).
# This forces every source head to be individually reached; copying an untouched
# tail cannot satisfy the target.

def finite_wrap_program(depth: int, current: Expr | None = None) -> Expr:
    current = var() if current is None else current
    if depth == 0:
        return empty_expr()
    return cond(
        unary("ATOM", current),
        empty_expr(),
        binary(
            "CONS",
            binary("CONS", unary("CAR", current), empty_expr()),
            finite_wrap_program(depth - 1, unary("CDR", current)),
        ),
    )


def proper_chain(length: int) -> Any:
    out: Any = EMPTY
    for i in reversed(range(length)):
        out = Pair(Atom(f"a{i}"), out)
    return out


def recursive_target(value: Any, *, fuel: int = 10000) -> Any:
    if fuel <= 0:
        raise SemanticError("fuel exhausted")
    if value == EMPTY:
        return EMPTY
    if not isinstance(value, Pair):
        raise SemanticError("improper pair-chain")
    return Pair(Pair(value.first, EMPTY), recursive_target(value.rest, fuel=fuel - 1))


def recursive_duplicate_target(value: Any, *, fuel: int = 10000) -> Any:
    if fuel <= 0:
        raise SemanticError("fuel exhausted")
    if value == EMPTY:
        return EMPTY
    if not isinstance(value, Pair):
        raise SemanticError("improper pair-chain")
    return Pair(value.first, Pair(value.first, recursive_duplicate_target(value.rest, fuel=fuel - 1)))


# ---- Explicit new capability A: reusable semantic re-entry ---------------

@dataclass
class ReentryStats:
    calls: int = 0
    max_depth: int = 0


def semantic_reentry(
    step: Callable[[Any, Callable[[Any], Any]], Any],
    value: Any,
    *,
    fuel: int,
    stats: ReentryStats,
    depth: int = 0,
) -> Any:
    """Explicit new authority: behavior may call itself on a subobject.

    Host recursion is the mechanism witness for the NEW capability and is never
    counted as D1-D3 power.
    """
    if fuel <= 0:
        raise SemanticError("re-entry fuel exhausted")
    stats.calls += 1
    stats.max_depth = max(stats.max_depth, depth)

    def again(subvalue: Any) -> Any:
        return semantic_reentry(
            step,
            subvalue,
            fuel=fuel - 1,
            stats=stats,
            depth=depth + 1,
        )

    return step(value, again)


def wrap_step(value: Any, again: Callable[[Any], Any]) -> Any:
    if atom_p(value) == YES:
        if value == EMPTY:
            return EMPTY
        raise SemanticError("improper pair-chain")
    return cons(cons(car(value), EMPTY), again(cdr(value)))


def duplicate_step(value: Any, again: Callable[[Any], Any]) -> Any:
    if atom_p(value) == YES:
        if value == EMPTY:
            return EMPTY
        raise SemanticError("improper pair-chain")
    head = car(value)
    return cons(head, cons(head, again(cdr(value))))


# ---- Explicit new capability B: opaque stage-enter -----------------------

@dataclass
class StageStats:
    entries: int = 0
    recursive_entries: int = 0


def stage_enter(program_bits: str, value: Any, *, fuel: int, stats: StageStats) -> Any:
    """Opaque interpreter/transformer control.

    Program bits are mechanism-local for this experiment, not D4 coordinates.
    """
    if fuel <= 0:
        raise SemanticError("stage-enter fuel exhausted")
    stats.entries += 1
    if value == EMPTY:
        return EMPTY
    if not isinstance(value, Pair):
        raise SemanticError("improper pair-chain")

    stats.recursive_entries += 1
    head = value.first
    tail = value.rest

    if program_bits == "0":
        return Pair(Pair(head, EMPTY), stage_enter("0", tail, fuel=fuel - 1, stats=stats))
    if program_bits == "1":
        return Pair(head, Pair(head, stage_enter("1", tail, fuel=fuel - 1, stats=stats)))
    raise SemanticError("unknown represented behavior")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-unroll", type=int, default=8)
    ap.add_argument("--deep-length", type=int, default=256)
    args = ap.parse_args()

    if args.max_unroll < 1:
        ap.error("--max-unroll must be >= 1")
    if args.deep_length <= args.max_unroll + 1:
        ap.error("--deep-length must exceed finite unroll range")

    args.out.mkdir(parents=True, exist_ok=True)

    # Sharp finite-depth boundary: each unrolled D1-D3 program handles all
    # proper chains up to k and fails the held-out k+1 case.
    finite_rows = []
    for k in range(1, args.max_unroll + 1):
        program = finite_wrap_program(k)
        bound = selector_bound(program)
        nodes = ast_nodes(program)

        in_bound_ok = True
        for n in range(0, k + 1):
            value = proper_chain(n)
            if eval_expr(program, value) != recursive_target(value):
                in_bound_ok = False
                break

        held_out = proper_chain(k + 1)
        held_out_equal = eval_expr(program, held_out) == recursive_target(held_out)

        assert in_bound_ok
        assert not held_out_equal

        finite_rows.append({
            "unroll_depth": k,
            "ast_nodes": nodes,
            "finite_selector_bound": bound,
            "all_lengths_0_to_k_pass": in_bound_ok,
            "held_out_length": k + 1,
            "held_out_pass": held_out_equal,
        })

    # Structural theorem artifact:
    # Any finite AST has finite selector_bound. The target family requires
    # source paths CDR^i/CAR for unbounded i. Therefore choose i beyond the
    # finite bound; no one finite AST can realize the generic transform.
    theorem = {
        "premise": "every admitted D1-D3 program is a finite AST",
        "derived_invariant": "every such AST has finite input-selector nesting bound",
        "target_requirement": "wrap-all requires accessing source path CDR^i/CAR for arbitrary i",
        "separation": "for any finite bound k choose a proper chain longer than k",
        "conclusion": "no one finite D1-D3 AST implements generic wrap-all for unbounded proper chains",
    }

    # Positive control A: one reusable re-entry mechanism supports two distinct
    # recursive behaviors without adding a per-behavior recursive primitive.
    deep = proper_chain(args.deep_length)

    wrap_stats = ReentryStats()
    wrap_reentry = semantic_reentry(
        wrap_step, deep, fuel=args.deep_length + 2, stats=wrap_stats
    )
    assert wrap_reentry == recursive_target(deep, fuel=args.deep_length + 2)

    duplicate_stats = ReentryStats()
    dup_reentry = semantic_reentry(
        duplicate_step, deep, fuel=args.deep_length + 2, stats=duplicate_stats
    )
    assert dup_reentry == recursive_duplicate_target(deep, fuel=args.deep_length + 2)

    # Positive control B: opaque stage-enter can also cross the bound, but each
    # represented behavior is interpreted inside the stage-enter authority.
    stage_wrap_stats = StageStats()
    wrap_stage = stage_enter(
        "0", deep, fuel=args.deep_length + 2, stats=stage_wrap_stats
    )
    assert wrap_stage == recursive_target(deep, fuel=args.deep_length + 2)

    stage_dup_stats = StageStats()
    dup_stage = stage_enter(
        "1", deep, fuel=args.deep_length + 2, stats=stage_dup_stats
    )
    assert dup_stage == recursive_duplicate_target(deep, fuel=args.deep_length + 2)

    # Malformed/improper inputs fail closed for both explicit new mechanisms.
    improper = Pair(Atom("head"), Atom("bad-tail"))
    malformed = []
    for mechanism, fn in [
        (
            "re-entry",
            lambda: semantic_reentry(
                wrap_step, improper, fuel=8, stats=ReentryStats()
            ),
        ),
        (
            "stage-enter",
            lambda: stage_enter("0", improper, fuel=8, stats=StageStats()),
        ),
    ]:
        try:
            fn()
        except SemanticError as exc:
            malformed.append({
                "mechanism": mechanism,
                "status": "FAIL-CLOSED",
                "reason": str(exc),
            })
        else:
            raise AssertionError(f"{mechanism} accepted improper chain")

    # Fuel is explicit; an insufficient bound never silently produces a value.
    fuel_controls = []
    for mechanism, fn in [
        (
            "re-entry",
            lambda: semantic_reentry(
                wrap_step, deep, fuel=args.max_unroll, stats=ReentryStats()
            ),
        ),
        (
            "stage-enter",
            lambda: stage_enter(
                "0", deep, fuel=args.max_unroll, stats=StageStats()
            ),
        ),
    ]:
        try:
            fn()
        except SemanticError as exc:
            fuel_controls.append({
                "mechanism": mechanism,
                "status": "INCOMPLETE/FAIL-CLOSED",
                "reason": str(exc),
            })
        else:
            raise AssertionError(f"{mechanism} ignored insufficient fuel")

    with (args.out / "finite-bound.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(finite_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(finite_rows)

    mechanism_rows = [
        {
            "mechanism": "reusable-semantic-reentry",
            "new_core_capability_count": 1,
            "embedded_behavior_dispatch_rows": 0,
            "parameter_context_explicit": True,
            "same_mechanism_two_recursive_behaviors": True,
            "deep_length_passed": args.deep_length,
            "calls_wrap": wrap_stats.calls,
            "calls_second_behavior": duplicate_stats.calls,
            "coordinate_assigned": False,
        },
        {
            "mechanism": "opaque-stage-enter",
            "new_core_capability_count": 1,
            "embedded_behavior_dispatch_rows": 2,
            "parameter_context_explicit": False,
            "same_mechanism_two_recursive_behaviors": True,
            "deep_length_passed": args.deep_length,
            "calls_wrap": stage_wrap_stats.entries,
            "calls_second_behavior": stage_dup_stats.entries,
            "coordinate_assigned": False,
        },
    ]
    with (args.out / "mechanism-comparison.tsv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(mechanism_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(mechanism_rows)

    artifact = {
        "schema": "d4-cleanroom-reentry/v1",
        "authority": "research-only",
        "allowed_basis": [
            "D1 predicate bit",
            "D2 structural framing",
            "D3 EMPTY/QUOTE/ATOM/CAR/CDR/EQ/COND/CONS",
        ],
        "historical_post_d3_seed_rows": 0,
        "absolute_d4_coordinate_assignments": 0,
        "finite_lower_bound": theorem,
        "finite_unroll_rows": finite_rows,
        "positive_controls": mechanism_rows,
        "malformed_controls": malformed,
        "fuel_controls": fuel_controls,
        "scoped_interpretation": [
            "unbounded semantic re-entry is a missing capability relative to finite D1-D3 composition",
            "the witness does not prove a unique implementation of that capability",
            "the authority-count comparison is scoped mechanism accounting, not global minimality",
            "no absolute D4 coordinate is earned by this result",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D4 clean-room re-entry lower bound — #3230",
        "",
        "Input authority: ratified D1-D3 only. Historical post-D3 seed rows: **0**.",
        "Absolute D4 coordinates assigned: **0**.",
        "",
        "Finite D1-D3 unroll sharpness:",
        "",
        "| k | AST nodes | selector bound | 0..k | held-out k+1 |",
        "|---:|---:|---:|---|---|",
    ]
    for row in finite_rows:
        report.append(
            f"| {row['unroll_depth']} | {row['ast_nodes']} | "
            f"{row['finite_selector_bound']} | PASS | "
            f"{'PASS' if row['held_out_pass'] else 'FAIL as required'} |"
        )

    report += [
        "",
        "Structural lower bound:",
        "every finite D1-D3 AST has finite input-inspection depth, while the",
        "generic recursive transform requires CDR^i/CAR source access for unbounded i.",
        "",
        f"Positive control depth: **{args.deep_length}** pair cells.",
        "",
        "- reusable semantic re-entry: PASS on two distinct recursive behaviors;",
        "- opaque stage-enter: PASS on the same two behaviors;",
        "- malformed input: both fail closed;",
        "- insufficient fuel: both return explicit incomplete/failure.",
        "",
        "Current conclusion:",
        "**unbounded semantic re-entry is genuinely new power beyond finite D1-D3 composition.**",
        "The experiment does not yet assign a D4 coordinate or prove a unique mechanism.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
