#!/usr/bin/env python3
"""Source/authority guard and independent finite-polynomial oracle for D10 Maling 1959.

The script validates a research dossier; it does not select or ratify a D10 resident.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import random
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-maling-symbolic-differentiation-1959-v1.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
PROPOSALS = ROOT / "knowledge/d10-proposal-ledger.tsv"
CANDIDATE = "FINITE-SYMBOLIC-DIFFERENTIATION"
KINDS = {"const", "var", "add", "mul"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _validate_expr(expr: Any, active: set[int] | None = None) -> None:
    if active is None:
        active = set()
    require(isinstance(expr, dict), "expression node must be a mapping")
    node_id = id(expr)
    require(node_id not in active, "cyclic expression objects are rejected")
    active.add(node_id)
    kind = expr.get("kind")
    require(kind in KINDS, f"unknown expression kind: {kind!r}")
    if kind == "const":
        require(set(expr) == {"kind", "value"}, "constant node shape must be exactly kind/value")
        require(type(expr["value"]) is int, "constant value must be an exact integer")
    elif kind == "var":
        require(set(expr) == {"kind", "name"}, "variable node shape must be exactly kind/name")
        require(isinstance(expr["name"], str) and bool(expr["name"]),
                "variable name must be a nonempty string")
    else:
        require(set(expr) == {"kind", "left", "right"},
                f"{kind} node shape must be exactly kind/left/right")
        _validate_expr(expr["left"], active)
        _validate_expr(expr["right"], active)
    active.remove(node_id)


def validate_expr(expr: Any) -> None:
    _validate_expr(expr)


def const(n: int) -> dict[str, Any]:
    return {"kind": "const", "value": n}


def var(name: str) -> dict[str, Any]:
    return {"kind": "var", "name": name}


def add(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return {"kind": "add", "left": a, "right": b}


def mul(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return {"kind": "mul", "left": a, "right": b}


def derivative(expr: dict[str, Any], target: str) -> dict[str, Any]:
    """Direct, unsimplified formal derivative by structural recursion."""
    validate_expr(expr)
    require(isinstance(target, str) and bool(target), "target variable must be a nonempty string")
    kind = expr["kind"]
    if kind == "const":
        return const(0)
    if kind == "var":
        return const(1 if expr["name"] == target else 0)
    left, right = expr["left"], expr["right"]
    if kind == "add":
        return add(derivative(left, target), derivative(right, target))
    return add(mul(derivative(left, target), copy.deepcopy(right)),
               mul(copy.deepcopy(left), derivative(right, target)))


# Independent polynomial coefficient oracle. A monomial is a sorted tuple
# ((variable, exponent), ...); the empty tuple denotes the constant monomial.
Monomial = tuple[tuple[str, int], ...]
Polynomial = dict[Monomial, int]


def normalize_poly(poly: Polynomial) -> Polynomial:
    return {m: c for m, c in poly.items() if c != 0}


def add_poly(a: Polynomial, b: Polynomial) -> Polynomial:
    out = dict(a)
    for monomial, coefficient in b.items():
        out[monomial] = out.get(monomial, 0) + coefficient
    return normalize_poly(out)


def multiply_monomials(a: Monomial, b: Monomial) -> Monomial:
    powers: dict[str, int] = {}
    for name, exponent in a + b:
        powers[name] = powers.get(name, 0) + exponent
    return tuple(sorted((name, exponent) for name, exponent in powers.items() if exponent))


def multiply_poly(a: Polynomial, b: Polynomial) -> Polynomial:
    out: Polynomial = {}
    for monomial_a, coefficient_a in a.items():
        for monomial_b, coefficient_b in b.items():
            monomial = multiply_monomials(monomial_a, monomial_b)
            out[monomial] = out.get(monomial, 0) + coefficient_a * coefficient_b
    return normalize_poly(out)


def expression_polynomial(expr: dict[str, Any]) -> Polynomial:
    """Translate an AST into canonical integer-polynomial coefficients."""
    validate_expr(expr)
    kind = expr["kind"]
    if kind == "const":
        value = expr["value"]
        return {} if value == 0 else {(): value}
    if kind == "var":
        return {((expr["name"], 1),): 1}
    left = expression_polynomial(expr["left"])
    right = expression_polynomial(expr["right"])
    if kind == "add":
        return add_poly(left, right)
    return multiply_poly(left, right)


def polynomial_derivative(poly: Polynomial, target: str) -> Polynomial:
    """Coefficient-space derivative, intentionally independent of AST rules."""
    out: Polynomial = {}
    for monomial, coefficient in poly.items():
        powers = dict(monomial)
        exponent = powers.get(target, 0)
        if exponent == 0:
            continue
        if exponent == 1:
            del powers[target]
        else:
            powers[target] = exponent - 1
        reduced = tuple(sorted(powers.items()))
        out[reduced] = out.get(reduced, 0) + coefficient * exponent
    return normalize_poly(out)


def assert_derivative_law(expr: dict[str, Any], target: str) -> None:
    actual = expression_polynomial(derivative(expr, target))
    expected = polynomial_derivative(expression_polynomial(expr), target)
    if actual != expected:
        raise AssertionError(
            f"derivative law mismatch for target={target}, expr={expr!r}: "
            f"actual polynomial={actual!r}, expected={expected!r}"
        )


def expression_height(expr: dict[str, Any]) -> int:
    if expr["kind"] in {"const", "var"}:
        return 0
    return 1 + max(expression_height(expr["left"]), expression_height(expr["right"]))


def exhaustive_small_expressions(max_height: int = 2) -> list[dict[str, Any]]:
    leaves = [const(-1), const(0), const(2), var("x"), var("y")]
    by_height: list[list[dict[str, Any]]] = [leaves]
    all_nodes = list(leaves)
    for height in range(1, max_height + 1):
        children = all_nodes
        exact: list[dict[str, Any]] = []
        for a in children:
            for b in children:
                if max(expression_height(a), expression_height(b)) == height - 1:
                    exact.extend((add(copy.deepcopy(a), copy.deepcopy(b)),
                                  mul(copy.deepcopy(a), copy.deepcopy(b))))
        by_height.append(exact)
        all_nodes.extend(exact)
    return all_nodes


def check_dossier_data(
    dossier: dict[str, Any], inventory: dict[str, Any], foundation: dict[str, Any], ledger: str
) -> dict[str, Any]:
    require(dossier.get("schema") == "d10-historical-symbolic-differentiation/v1",
            "wrong differentiation dossier schema")
    require(dossier.get("review_id") == "MALING-1959-DIFF-01", "wrong review id")
    require(dossier.get("proposed_semantic_name") == CANDIDATE, "candidate name drift")
    require(dossier.get("status") == "RESEARCH-ONLY-HOLD-CORE-VS-LIBRARY",
            "dossier must remain research-only")
    require(dossier.get("selected") is False, "research dossier must not select a resident")
    require(dossier.get("ratified") is False and dossier.get("coordinate") is None,
            "dossier may not ratify or assign coordinates")
    require(dossier.get("physical_t5_authorized") is False,
            "research dossier may not authorize physical T5")
    source = dossier.get("source", {})
    require(source.get("author") == "K. Maling", "historical author mismatch")
    require(source.get("title") == "The LISP Differentiation Demonstration Program",
            "historical title mismatch")
    require(source.get("source_kind") == "HISTORICAL-IMPLEMENTATION-MEMO",
            "source taxonomy missing")
    require(str(source.get("primary_pdf", "")).startswith("https://"),
            "historical primary PDF missing")
    require(str(source.get("archival_index", "")).startswith("https://"),
            "historical archive index missing")
    require("modern bounded formalization" in source.get("source_limit", ""),
            "historical-vs-modern contract boundary must be explicit")
    law = dossier.get("observable_law", {})
    require(law.get("expression_grammar") ==
            "Const(integer) | Var(name) | Add(expr,expr) | Mul(expr,expr)",
            "unexpected expression grammar")
    require("No simplification" in law.get("normalization", ""),
            "unsimplified output boundary missing")
    require(len(dossier.get("witnesses", [])) >= 5, "too few positive witnesses")
    require(len(dossier.get("falsifiers", [])) >= 5, "too few falsifiers")
    require(dossier.get("reviewer_state") == "PENDING-OWNER-AND-PEER-REVIEW",
            "owner/peer review must remain pending")

    selected_names = {str(r.get("semantic_name", "")).upper() for r in inventory.get("rows", [])}
    require(CANDIDATE not in selected_names, "candidate already exists in the live D10 inventory")
    lower_names = {
        str(name).upper()
        for domain in foundation.get("domains", {}).values()
        for name in domain.get("residents", {}).values()
    }
    require(CANDIDATE not in lower_names, "candidate exact name collides with D1-D9")
    ledger_rows = [line for line in ledger.splitlines()[1:] if line.strip()]
    require(not any(len(line.split("\t")) > 3 and line.split("\t")[3].upper() == CANDIDATE
                    for line in ledger_rows),
            "candidate exact name already exists in the canonical proposal ledger")
    require(len(inventory.get("rows", [])) == inventory.get("accounting", {}).get(
        "selected_semantic_candidates"), "inventory row/accounting mismatch")
    require(inventory.get("accounting", {}).get("ratified_d10_residents") == 0,
            "D10 authority unexpectedly changed")
    return {
        "candidate": CANDIDATE,
        "historical_source_pinned": True,
        "current_selected_count": len(inventory["rows"]),
        "exact_name_dedup": "NO-MATCH",
        "behavioral_minimality": "HOLD-CORE-VS-LIBRARY-REVIEW",
        "selected_added": 0,
        "coordinates_added": 0,
        "ratifications_added": 0,
    }


def self_test_authority(dossier: dict[str, Any], inventory: dict[str, Any],
                        foundation: dict[str, Any], ledger: str) -> int:
    check_dossier_data(dossier, inventory, foundation, ledger)
    attempts = 0
    for field, bad in (
        ("selected", True), ("ratified", True), ("coordinate", "0000000000"),
        ("physical_t5_authorized", True), ("status", "SELECTED-RESEARCH-CANDIDATE"),
    ):
        mutant = copy.deepcopy(dossier)
        mutant[field] = bad
        try:
            check_dossier_data(mutant, inventory, foundation, ledger)
        except ValueError:
            attempts += 1
        else:
            raise AssertionError(f"unsafe dossier mutation was not blocked: {field}={bad!r}")
    mutant_inventory = copy.deepcopy(inventory)
    mutant_inventory["rows"].append({
        "semantic_name": CANDIDATE,
        "stable_id": "test.fake",
        "coordinate": None,
        "ratified_resident": False,
    })
    mutant_inventory["accounting"]["selected_semantic_candidates"] += 1
    try:
        check_dossier_data(dossier, mutant_inventory, foundation, ledger)
    except ValueError:
        attempts += 1
    else:
        raise AssertionError("exact-name collision mutation was not blocked")
    return attempts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    dossier = json.loads(DOSSIER.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    ledger = PROPOSALS.read_text(encoding="utf-8")
    if args.self_test:
        authority_cases = self_test_authority(dossier, inventory, foundation, ledger)
        expressions = exhaustive_small_expressions(2)
        comparisons = 0
        for expression in expressions:
            for target in ("x", "y"):
                assert_derivative_law(expression, target)
                comparisons += 1
        # Independent deeper deterministic samples; seed is part of the test contract.
        rng = random.Random(1959)
        atoms = [const(-3), const(-1), const(0), const(2), var("x"), var("y")]

        def random_expr(depth: int) -> dict[str, Any]:
            if depth <= 0 or rng.random() < 0.28:
                return copy.deepcopy(rng.choice(atoms))
            left = random_expr(depth - 1)
            right = random_expr(depth - 1)
            return add(left, right) if rng.randrange(2) == 0 else mul(left, right)

        for _ in range(750):
            expression = random_expr(5)
            for target in ("x", "y"):
                assert_derivative_law(expression, target)
                comparisons += 1
        result = check_dossier_data(dossier, inventory, foundation, ledger)
        result.update({
            "authority_mutations_blocked": authority_cases,
            "python_exact_polynomial_crosschecks": comparisons,
            "seeded_deep_cases": 1500,
            "oracle": "AST rewrite versus exact integer coefficient-map differentiation",
        })
    else:
        result = check_dossier_data(dossier, inventory, foundation, ledger)
    print("D10-MALING-DIFFERENTIATION PASS", json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
