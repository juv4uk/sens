#!/usr/bin/env python3
"""#2452 — Core-Math equivalence-law gate for canonical identity.

Stacked on #2445/#2437.  The canonicalizer may only consume explicitly
validated mathematical equalities.  Candidate laws are tested on both exact-Q
models from #2437 before they are admitted to a normalization bundle.

Research only.  No Core/SENS coordinate or registry authority is touched.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
DONOR_PATH = ROOT / "scripts" / "research-2433-core-math-neutral-growth.py"

LAWSET_VERSION = "exact-q-equivalence-set/v1"


def load_donor():
    spec = importlib.util.spec_from_file_location("core_math_growth_2433_eq", DONOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def render(model, value: Any) -> str:
    return model.render(value)


@dataclass(frozen=True)
class LawResult:
    law_id: str
    equation: str
    model_a_pass: bool
    model_b_pass: bool
    counterexample: str
    status: str
    version: str
    identity_effect: str


def validate_commutativity(module, op_name: str) -> LawResult:
    models = [module.FractionModel(), module.PairModel()]
    passes = []
    first_ce = ""
    for model in models:
        op = getattr(model, op_name)
        ok = True
        for left_s in module.CORPUS:
            for right_s in module.CORPUS:
                left = model.parse(left_s)
                right = model.parse(right_s)
                a = render(model, op(left, right))
                b = render(model, op(right, left))
                if a != b:
                    ok = False
                    if not first_ce:
                        first_ce = f"{left_s},{right_s}: {a} != {b}"
                    break
            if not ok:
                break
        passes.append(ok)
    law_id = f"Q.{op_name}.commutative/v1"
    return LawResult(
        law_id,
        f"{op_name}(x,y) = {op_name}(y,x)",
        passes[0],
        passes[1],
        first_ce,
        "bounded-confirmed" if all(passes) else "falsified",
        "v1",
        "allows deterministic operand ordering",
    )


def validate_associativity(module, op_name: str) -> LawResult:
    models = [module.FractionModel(), module.PairModel()]
    passes = []
    first_ce = ""
    for model in models:
        op = getattr(model, op_name)
        ok = True
        for a_s in module.CORPUS:
            for b_s in module.CORPUS:
                for c_s in module.CORPUS:
                    a = model.parse(a_s)
                    b = model.parse(b_s)
                    c = model.parse(c_s)
                    left = render(model, op(op(a, b), c))
                    right = render(model, op(a, op(b, c)))
                    if left != right:
                        ok = False
                        if not first_ce:
                            first_ce = f"{a_s},{b_s},{c_s}: {left} != {right}"
                        break
                if not ok:
                    break
            if not ok:
                break
        passes.append(ok)
    law_id = f"Q.{op_name}.associative/v1"
    return LawResult(
        law_id,
        f"{op_name}({op_name}(x,y),z) = {op_name}(x,{op_name}(y,z))",
        passes[0],
        passes[1],
        first_ce,
        "bounded-confirmed" if all(passes) else "falsified",
        "v1",
        "allows flattening/regrouping of same-operation trees",
    )


def validate_idempotence(module, op_name: str) -> LawResult:
    models = [module.FractionModel(), module.PairModel()]
    passes = []
    first_ce = ""
    for model in models:
        op = getattr(model, op_name)
        ok = True
        for x_s in module.CORPUS:
            x = model.parse(x_s)
            left = render(model, op(x, x))
            right = render(model, x)
            if left != right:
                ok = False
                if not first_ce:
                    first_ce = f"{x_s}: {left} != {right}"
                break
        passes.append(ok)
    law_id = f"Q.{op_name}.idempotent/v1"
    return LawResult(
        law_id,
        f"{op_name}(x,x) = x",
        passes[0],
        passes[1],
        first_ce,
        "bounded-confirmed" if all(passes) else "falsified",
        "v1",
        "would collapse duplicate operands",
    )


def validate_recip_zero_total(module) -> LawResult:
    passes = []
    first_ce = ""
    for model in [module.FractionModel(), module.PairModel()]:
        zero = model.parse("0/1")
        result = model.recip(zero)
        ok = result is not module.UNDEFINED
        if not ok and not first_ce:
            first_ce = "0/1: recip is UNDEFINED"
        passes.append(ok)
    return LawResult(
        "Q.recip.total-at-zero/v1",
        "recip(0) is an ordinary Q value",
        passes[0],
        passes[1],
        first_ce,
        "bounded-confirmed" if all(passes) else "falsified",
        "v1",
        "would erase admitted partiality",
    )


def law_index(results: list[LawResult]) -> dict[str, LawResult]:
    return {row.law_id: row for row in results}


def require_validated(bundle: list[str], laws: dict[str, LawResult]) -> None:
    for law_id in bundle:
        if law_id not in laws:
            raise ValueError(f"unknown equivalence law: {law_id}")
        if laws[law_id].status != "bounded-confirmed":
            raise ValueError(f"non-validated equivalence law: {law_id}")


def canonicalize(
    node: dict[str, Any],
    *,
    arg_env: dict[str, int],
    bundle: set[str],
) -> dict[str, Any]:
    if "var" in node:
        return {"arg": arg_env[node["var"]]}
    if "const" in node:
        return {"const": node["const"]}

    op = node["call"]
    args = [
        canonicalize(arg, arg_env=arg_env, bundle=bundle)
        for arg in node["args"]
    ]

    assoc_id = f"Q.{op}.associative/v1"
    if assoc_id in bundle:
        flattened: list[dict[str, Any]] = []
        for arg in args:
            if arg.get("call") == op:
                flattened.extend(arg["args"])
            else:
                flattened.append(arg)
        args = flattened

    comm_id = f"Q.{op}.commutative/v1"
    if comm_id in bundle:
        args = sorted(args, key=canonical_json)

    return {"call": op, "args": args}


def canon(expr: dict[str, Any], inputs: list[str], bundle: list[str], laws) -> dict[str, Any]:
    require_validated(bundle, laws)
    return {
        "schema": "core-math-equivalence-normal-form/v1",
        "lawset_version": LAWSET_VERSION,
        "laws": sorted(bundle),
        "expression": canonicalize(
            expr,
            arg_env={name: i for i, name in enumerate(inputs)},
            bundle=set(bundle),
        ),
    }


def expr_call(op: str, *args: dict[str, Any]) -> dict[str, Any]:
    return {"call": op, "args": list(args)}


def var(name: str) -> dict[str, Any]:
    return {"var": name}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    module = load_donor()
    results = [
        validate_commutativity(module, "add"),
        validate_commutativity(module, "mul"),
        validate_associativity(module, "add"),
        validate_associativity(module, "mul"),
        validate_idempotence(module, "add"),
        validate_idempotence(module, "mul"),
        validate_recip_zero_total(module),
    ]
    laws = law_index(results)

    positives = [
        "Q.add.commutative/v1",
        "Q.mul.commutative/v1",
        "Q.add.associative/v1",
        "Q.mul.associative/v1",
    ]
    negatives = [
        "Q.add.idempotent/v1",
        "Q.mul.idempotent/v1",
        "Q.recip.total-at-zero/v1",
    ]
    assert all(laws[x].status == "bounded-confirmed" for x in positives)
    assert all(laws[x].status == "falsified" for x in negatives)

    # Commutativity control.
    xy = expr_call("add", var("x"), var("y"))
    yx = expr_call("add", var("y"), var("x"))
    no_comm_a = canon(xy, ["x", "y"], [], laws)
    no_comm_b = canon(yx, ["x", "y"], [], laws)
    with_comm_a = canon(xy, ["x", "y"], ["Q.add.commutative/v1"], laws)
    with_comm_b = canon(yx, ["x", "y"], ["Q.add.commutative/v1"], laws)
    assert no_comm_a != no_comm_b
    assert with_comm_a == with_comm_b

    # Associativity control.
    left_assoc = expr_call("add", expr_call("add", var("x"), var("y")), var("z"))
    right_assoc = expr_call("add", var("x"), expr_call("add", var("y"), var("z")))
    comm_only_left = canon(left_assoc, ["x", "y", "z"], ["Q.add.commutative/v1"], laws)
    comm_only_right = canon(right_assoc, ["x", "y", "z"], ["Q.add.commutative/v1"], laws)
    ac_bundle = ["Q.add.commutative/v1", "Q.add.associative/v1"]
    ac_left = canon(left_assoc, ["x", "y", "z"], ac_bundle, laws)
    ac_right = canon(right_assoc, ["x", "y", "z"], ac_bundle, laws)
    assert comm_only_left != comm_only_right
    assert ac_left == ac_right

    # Unknown/falsified law cannot enter a canonicalization bundle.
    rejected: list[str] = []
    for bad in ["Q.add.idempotent/v1", "Q.mul.idempotent/v1", "Q.unknown/v1"]:
        try:
            canon(xy, ["x", "y"], [bad], laws)
        except ValueError:
            rejected.append(bad)
    assert len(rejected) == 3

    # Demonstrate why the idempotence falsifier matters.
    # A forced bad rewrite add(x,x)->x would merge expressions that differ on Q.
    model = module.FractionModel()
    x = model.parse("1/1")
    bad_left = model.add(x, x)
    bad_right = x
    assert model.render(bad_left) == "2/1"
    assert model.render(bad_right) == "1/1"

    law_rows = []
    for row in results:
        law_rows.append({
            "law_id": row.law_id,
            "carrier": "Q",
            "equation": row.equation,
            "model_A_pass": row.model_a_pass,
            "model_B_pass": row.model_b_pass,
            "counterexample": row.counterexample,
            "status": row.status,
            "version": row.version,
            "identity_effect": row.identity_effect,
        })

    with (args.out / "law-results.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(law_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(law_rows)

    equivalence_rows = [
        {
            "control": "add-commutativity",
            "without_required_law_same": no_comm_a == no_comm_b,
            "with_validated_law_same": with_comm_a == with_comm_b,
            "required_laws": "Q.add.commutative/v1",
        },
        {
            "control": "add-associativity",
            "without_required_law_same": comm_only_left == comm_only_right,
            "with_validated_law_same": ac_left == ac_right,
            "required_laws": "Q.add.commutative/v1|Q.add.associative/v1",
        },
    ]
    with (args.out / "equivalence-results.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(equivalence_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(equivalence_rows)

    artifact = {
        "schema": "core-math-equivalence-law-gate/v1",
        "authority": "research-only",
        "lawset_version": LAWSET_VERSION,
        "validated_laws": [row for row in law_rows if row["status"] == "bounded-confirmed"],
        "falsified_laws": [row for row in law_rows if row["status"] == "falsified"],
        "canonicalization_controls": equivalence_rows,
        "rejected_bundle_members": rejected,
        "forced_false_law_counterexample": {
            "law": "Q.add.idempotent/v1",
            "input": "1/1",
            "left": "2/1",
            "right": "1/1",
        },
        "non_conclusions": [
            "bounded confirmation is not global theorem-prover authority",
            "the exact-Q law bundle is not automatically valid on another carrier",
            "canonical serialization is a mechanism, not mathematical semantics",
            "no operation registry slot or SENS coordinate is created",
        ],
    }
    artifact_path = args.out / "equivalence-law-gate.json"
    artifact_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    assert json.loads(artifact_path.read_text(encoding="utf-8")) == artifact

    report = [
        "# Core-Math equivalence-law gate — #2452",
        "",
        "| law | model A | model B | status |",
        "|---|---|---|---|",
    ]
    for row in law_rows:
        report.append(
            f"| {row['law_id']} | {row['model_A_pass']} | "
            f"{row['model_B_pass']} | {row['status']} |"
        )
    report += [
        "",
        "Canonicalization controls:",
        "- swapped ADD trees remain distinct without commutativity and converge only after validated commutativity;",
        "- regrouped ADD trees remain distinct with commutativity alone and converge only after validated associativity;",
        "- falsified/unknown law IDs are rejected before canonicalization;",
        "- forced ADD idempotence would collapse 2/1 and 1/1 at x=1, so the false law is demonstrably unsafe;",
        "- RECIP totalization at zero is falsified, preserving partiality.",
        "",
        "Interpretation:",
        "the canonicalizer is parameterized by a validated, versioned mathematical law set.",
        "It may apply admitted equalities; it is not allowed to create them.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
