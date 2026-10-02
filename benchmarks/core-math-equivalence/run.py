#!/usr/bin/env python3
"""#2450 — Core-Math operation equivalence beyond canonical syntax.

First bounded split:
- a decidable exact-Q polynomial fragment for ADD/MUL/NEG-like constructions;
- a proof-carrying guarded fragment for partial RECIP laws;
- bounded exact-Q counterexample search as a falsifier/control;
- UNKNOWN outside admitted fragments.

Research only. This does not ratify a universal equality theory.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs" / "research" / "2433-core-math-neutral-v1.json"

LAWSET_VERSION = "core-math-exact-q-equivalence/v1"
PROOF_VERSION = "core-math-equivalence-proof/v1"

CORPUS = (
    Fraction(-2, 1),
    Fraction(-1, 1),
    Fraction(-1, 2),
    Fraction(0, 1),
    Fraction(1, 2),
    Fraction(1, 1),
    Fraction(2, 1),
)


class OutOfCanonicalFragment(RuntimeError):
    pass


class Undefined:
    pass


UNDEFINED = Undefined()


def qtext(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def load_spec() -> dict[str, Any]:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def q(value: str) -> dict[str, str]:
    return {"q": value}


def var(name: str) -> dict[str, str]:
    return {"var": name}


def call(name: str, *args: dict[str, Any]) -> dict[str, Any]:
    return {"call": name, "args": list(args)}


def substitute(node: dict[str, Any], mapping: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if "var" in node:
        return mapping.get(node["var"], node)
    if "q" in node or "const" in node:
        return node
    if "call" in node:
        return {
            "call": node["call"],
            "args": [substitute(arg, mapping) for arg in node["args"]],
        }
    raise ValueError(node)


def expand_generated(
    node: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    stack: tuple[str, ...] = (),
) -> dict[str, Any]:
    if "var" in node or "q" in node or "const" in node:
        return node
    op = node["call"]
    args = [expand_generated(arg, rules, stack) for arg in node["args"]]
    if op not in rules:
        return {"call": op, "args": args}
    if op in stack:
        raise ValueError("generated-operation cycle")
    rule = rules[op]
    if len(rule["inputs"]) != len(args):
        raise ValueError(f"arity mismatch: {op}")
    mapping = dict(zip(rule["inputs"], args, strict=True))
    return expand_generated(
        substitute(rule["expression"], mapping),
        rules,
        stack + (op,),
    )


Polynomial = dict[tuple[str, ...], Fraction]


def poly_clean(poly: Polynomial) -> Polynomial:
    return {monomial: coeff for monomial, coeff in poly.items() if coeff != 0}


def poly_add(left: Polynomial, right: Polynomial) -> Polynomial:
    result = dict(left)
    for monomial, coeff in right.items():
        result[monomial] = result.get(monomial, Fraction(0)) + coeff
    return poly_clean(result)


def poly_mul(left: Polynomial, right: Polynomial) -> Polynomial:
    result: Polynomial = {}
    for lm, lc in left.items():
        for rm, rc in right.items():
            monomial = tuple(sorted(lm + rm))
            result[monomial] = result.get(monomial, Fraction(0)) + lc * rc
    return poly_clean(result)


def poly_of(
    node: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    constants: dict[str, Fraction],
) -> Polynomial:
    node = expand_generated(node, rules)
    if "var" in node:
        return {(node["var"],): Fraction(1)}
    if "q" in node:
        return {(): Fraction(node["q"])}
    if "const" in node:
        if node["const"] not in constants:
            raise OutOfCanonicalFragment(f"unknown constant {node['const']}")
        return {(): constants[node["const"]]}
    op = node["call"]
    args = node["args"]
    if op == "add" and len(args) == 2:
        return poly_add(
            poly_of(args[0], rules, constants),
            poly_of(args[1], rules, constants),
        )
    if op == "mul" and len(args) == 2:
        return poly_mul(
            poly_of(args[0], rules, constants),
            poly_of(args[1], rules, constants),
        )
    raise OutOfCanonicalFragment(op)


def poly_payload(poly: Polynomial) -> list[dict[str, Any]]:
    rows = []
    for monomial, coeff in sorted(poly.items()):
        rows.append({
            "monomial": list(monomial),
            "coefficient": qtext(coeff),
        })
    return rows


def canonical_equal(
    left: dict[str, Any],
    right: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    constants: dict[str, Fraction],
) -> tuple[str, dict[str, Any]]:
    try:
        lpoly = poly_of(left, rules, constants)
        rpoly = poly_of(right, rules, constants)
    except OutOfCanonicalFragment as exc:
        return "UNKNOWN", {"reason": f"outside-polynomial-fragment:{exc}"}
    same = lpoly == rpoly
    return (
        "EQUAL" if same else "NOT-EQUAL-IN-CANONICAL-FRAGMENT",
        {
            "left_normal_form": poly_payload(lpoly),
            "right_normal_form": poly_payload(rpoly),
        },
    )


def eval_expr(
    node: dict[str, Any],
    env: dict[str, Fraction],
    rules: dict[str, dict[str, Any]],
    constants: dict[str, Fraction],
) -> Fraction | Undefined:
    node = expand_generated(node, rules)
    if "var" in node:
        return env[node["var"]]
    if "q" in node:
        return Fraction(node["q"])
    if "const" in node:
        return constants[node["const"]]
    args = [eval_expr(arg, env, rules, constants) for arg in node["args"]]
    if any(arg is UNDEFINED for arg in args):
        return UNDEFINED
    op = node["call"]
    if op == "add":
        return args[0] + args[1]  # type: ignore[operator]
    if op == "mul":
        return args[0] * args[1]  # type: ignore[operator]
    if op == "recip":
        value = args[0]
        assert isinstance(value, Fraction)
        if value == 0:
            return UNDEFINED
        return Fraction(value.denominator, value.numerator)
    raise ValueError(op)


def variables(node: dict[str, Any]) -> set[str]:
    if "var" in node:
        return {node["var"]}
    if "q" in node or "const" in node:
        return set()
    result: set[str] = set()
    for arg in node["args"]:
        result |= variables(arg)
    return result


def counterexample(
    left: dict[str, Any],
    right: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    constants: dict[str, Fraction],
) -> dict[str, Any] | None:
    names = sorted(variables(left) | variables(right))
    if len(names) > 3:
        raise ValueError("bounded control supports at most 3 variables")

    import itertools

    for values in itertools.product(CORPUS, repeat=len(names)):
        env = dict(zip(names, values, strict=True))
        lv = eval_expr(left, env, rules, constants)
        rv = eval_expr(right, env, rules, constants)
        if lv is UNDEFINED or rv is UNDEFINED:
            if lv is not rv:
                return {
                    "env": {k: qtext(v) for k, v in env.items()},
                    "left": "UNDEFINED" if lv is UNDEFINED else qtext(lv),
                    "right": "UNDEFINED" if rv is UNDEFINED else qtext(rv),
                }
            continue
        assert isinstance(lv, Fraction) and isinstance(rv, Fraction)
        if lv != rv:
            return {
                "env": {k: qtext(v) for k, v in env.items()},
                "left": qtext(lv),
                "right": qtext(rv),
            }
    return None


@dataclass(frozen=True)
class GuardedProof:
    law: str
    variable: str
    assumptions: tuple[str, ...]
    provenance: str


def check_guarded_reciprocal_inverse(
    proof: GuardedProof,
    left: dict[str, Any],
    right: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    x = proof.variable
    expected_left = call("mul", var(x), call("recip", var(x)))
    expected_right = q("1/1")
    if proof.law != "mul-recip-nonzero":
        return "REJECTED", {"reason": "unknown-law"}
    if left != expected_left or right != expected_right:
        return "REJECTED", {"reason": "shape-mismatch"}
    guard = f"nonzero:{x}"
    if guard not in proof.assumptions:
        return "UNKNOWN", {"reason": "missing-nonzero-assumption"}
    return "PROVED-WITH-GUARD", {
        "law": proof.law,
        "assumptions": list(proof.assumptions),
        "proof_version": PROOF_VERSION,
        "provenance": proof.provenance,
    }


def run() -> dict[str, Any]:
    spec = load_spec()
    rules = {rule["id"]: rule for rule in spec["generation_rules"]}
    constants = {
        row["id"]: Fraction(row["value"])
        for row in spec["constants"]
    }

    x, y, z = var("x"), var("y"), var("z")
    zero, one = q("0/1"), q("1/1")

    controls: list[dict[str, Any]] = []

    pairs = [
        (
            "add-associativity",
            call("add", call("add", x, y), z),
            call("add", x, call("add", y, z)),
        ),
        ("add-zero", call("add", x, zero), x),
        ("mul-one", call("mul", x, one), x),
        ("double-negation", call("neg", call("neg", x)), x),
        (
            "distributivity",
            call("mul", x, call("add", y, z)),
            call("add", call("mul", x, y), call("mul", x, z)),
        ),
    ]

    for name, left, right in pairs:
        status, evidence = canonical_equal(left, right, rules, constants)
        assert status == "EQUAL", (name, status, evidence)
        controls.append({
            "case": name,
            "model": "exact-q-polynomial-normal-form",
            "status": status,
            "evidence": evidence,
        })

    false_left = call("add", x, y)
    false_right = call("mul", x, y)
    status, evidence = canonical_equal(false_left, false_right, rules, constants)
    assert status == "NOT-EQUAL-IN-CANONICAL-FRAGMENT"
    witness = counterexample(false_left, false_right, rules, constants)
    assert witness is not None
    controls.append({
        "case": "false-add-vs-mul",
        "model": "canonical+bounded-counterexample",
        "status": "REFUTED",
        "counterexample": witness,
        "canonical": evidence,
    })

    recip_left = call("mul", x, call("recip", x))
    recip_right = one

    poly_status, poly_evidence = canonical_equal(
        recip_left, recip_right, rules, constants
    )
    assert poly_status == "UNKNOWN"
    controls.append({
        "case": "reciprocal-inverse-polynomial-fragment",
        "model": "exact-q-polynomial-normal-form",
        "status": poly_status,
        "evidence": poly_evidence,
    })

    proof = GuardedProof(
        law="mul-recip-nonzero",
        variable="x",
        assumptions=("nonzero:x",),
        provenance="explicit-typed-proof-control",
    )
    proof_status, proof_evidence = check_guarded_reciprocal_inverse(
        proof, recip_left, recip_right
    )
    assert proof_status == "PROVED-WITH-GUARD"
    controls.append({
        "case": "reciprocal-inverse-nonzero",
        "model": "proof-carrying-guarded-equality",
        "status": proof_status,
        "evidence": proof_evidence,
    })

    missing_guard = GuardedProof(
        law="mul-recip-nonzero",
        variable="x",
        assumptions=(),
        provenance="missing-guard-negative-control",
    )
    no_guard_status, no_guard_evidence = check_guarded_reciprocal_inverse(
        missing_guard, recip_left, recip_right
    )
    assert no_guard_status == "UNKNOWN"
    controls.append({
        "case": "reciprocal-inverse-without-guard",
        "model": "proof-carrying-guarded-equality",
        "status": no_guard_status,
        "evidence": no_guard_evidence,
    })

    zero_eval = eval_expr(
        recip_left,
        {"x": Fraction(0)},
        rules,
        constants,
    )
    assert zero_eval is UNDEFINED
    controls.append({
        "case": "reciprocal-inverse-at-zero",
        "model": "exact-Q-evaluation-falsifier",
        "status": "NOT-EQUAL/UNDEFINED",
        "evidence": {
            "x": "0/1",
            "left": "UNDEFINED",
            "right": "1/1",
        },
    })

    assoc_left = pairs[0][1]
    assoc_right = pairs[0][2]
    left_poly = poly_payload(poly_of(assoc_left, rules, constants))
    right_poly = poly_payload(poly_of(assoc_right, rules, constants))
    assert left_poly == right_poly
    provenance_control = {
        "semantic_normal_form": left_poly,
        "proofs": [
            {"source": "left-associated-source", "expression": assoc_left},
            {"source": "right-associated-source", "expression": assoc_right},
        ],
    }

    artifact = {
        "schema": "core-math-equivalence-research/v1",
        "authority": "research-only",
        "law_set_version": LAWSET_VERSION,
        "proof_version": PROOF_VERSION,
        "parent_identity_tournament": "#2435 / PR #2445",
        "fragments": {
            "exact-q-polynomial": {
                "status": "DECIDABLE-CANONICAL-BOUNDED-LANGUAGE-FRAGMENT",
                "operations": ["add", "mul", "neg/sub via generated expansion"],
                "laws_realized_by_normal_form": [
                    "add-associative",
                    "add-commutative",
                    "add-zero",
                    "mul-associative",
                    "mul-commutative",
                    "mul-one",
                    "distributivity",
                    "double-negation",
                ],
            },
            "guarded-reciprocal": {
                "status": "PROOF-CARRYING-PARTIAL-FRAGMENT",
                "laws": ["mul-recip-nonzero"],
                "required_assumption": "nonzero:x",
            },
            "outside": {
                "status": "UNKNOWN",
                "rule": "no equality is invented outside admitted canonical/proof fragments",
            },
        },
        "controls": controls,
        "provenance_separation": provenance_control,
        "egraph": {
            "status": "DEFERRED-FIRST-SLICE",
            "reason": "first corpus is small enough to establish rewrite/proof boundary directly; equality saturation remains a comparison candidate as law interactions grow",
        },
        "claims": {
            "universal_normal_form": False,
            "unknown_is_valid": True,
            "sens_function_slot_required": False,
            "partiality_is_semantic": True,
            "provenance_is_identity": False,
        },
        "non_conclusions": [
            "polynomial canonicalization does not decide reciprocal/general partial equivalence",
            "guarded proof checker is intentionally tiny and not a universal theorem prover",
            "bounded counterexample search proves falsity only when it finds a witness",
            "future law sets may make the general word problem harder or undecidable",
            "this slice does not ratify final Core-Math equality semantics",
        ],
    }
    return artifact


def render_report(artifact: dict[str, Any]) -> str:
    lines = [
        "# Core-Math equivalence research — #2450",
        "",
        "| case | model | status |",
        "|---|---|---|",
    ]
    for row in artifact["controls"]:
        lines.append(f"| {row['case']} | {row['model']} | {row['status']} |")
    lines += [
        "",
        "Interpretation:",
        "- polynomial exact-Q ADD/MUL/NEG fragment gets a deterministic algebraic normal form;",
        "- reciprocal inverse is not forced into that fragment and needs an explicit nonzero proof;",
        "- x=0 remains undefined and cannot be simplified to 1;",
        "- false equality ADD(x,y)=MUL(x,y) has a concrete exact-Q counterexample;",
        "- outside admitted fragments the result is UNKNOWN;",
        "- provenance is preserved separately from semantic equality.",
        "",
        "E-graph/equality saturation is deliberately deferred from this first slice.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    artifact = run()
    out_json = args.out / "equivalence.json"
    out_json.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    assert json.loads(out_json.read_text(encoding="utf-8")) == artifact

    report = render_report(artifact)
    (args.out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
