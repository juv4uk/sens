#!/usr/bin/env python3
"""#2433 — language-neutral Core-Math growth witness.

The semantic input is docs/research/2433-core-math-neutral-v1.json.
Two independent non-host-language exact-Q models consume the same spec:

A. fractions.Fraction
B. an independently normalized integer-pair rational model

Generated operations are compiled by dependency closure. In particular SUB
must consume already-generated NEG rather than hidden subtraction semantics.

Research only. No identity allocation and no Core admission.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import itertools
import json
from math import gcd
from pathlib import Path
import re
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "docs" / "research" / "2433-core-math-neutral-v1.json"
PROJECTION_PATH = ROOT / "docs" / "research" / "2433-core-math-research-projection.json"
CERT_PATH = ROOT / "docs" / "research" / "2433-core-math-generation-certificates.json"

CORPUS = ("-2/1", "-1/1", "-1/2", "0/1", "1/2", "1/1", "2/1")
UNDEFINED = object()

FORBIDDEN_NEUTRAL_TOKENS = {
    "lambda", "eval", "apply", "quote", "cons", "car", "cdr", "cond",
    "lisp", "registry", "sid", "reader",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def neutral_vocabulary_gate(spec: dict[str, Any]) -> None:
    text = json.dumps(spec, sort_keys=True).lower()
    tokens = set(re.findall(r"[a-z_]+", text))
    leaked = sorted(tokens & FORBIDDEN_NEUTRAL_TOKENS)
    assert not leaked, f"neutral spec leaked host/core vocabulary: {leaked}"
    assert "coordinate" not in tokens
    assert "identity" not in tokens


def called_operations(expr: dict[str, Any]) -> set[str]:
    result: set[str] = set()

    def walk(node: dict[str, Any]) -> None:
        if "call" in node:
            result.add(node["call"])
            for arg in node["args"]:
                walk(arg)

    walk(expr)
    return result


def used_constants(expr: dict[str, Any]) -> set[str]:
    result: set[str] = set()

    def walk(node: dict[str, Any]) -> None:
        if "const" in node:
            result.add(node["const"])
        if "call" in node:
            for arg in node["args"]:
                walk(arg)

    walk(expr)
    return result


class DependencyError(RuntimeError):
    pass


class Model:
    def parse(self, value: str) -> Any:
        raise NotImplementedError

    def render(self, value: Any) -> str:
        raise NotImplementedError

    def add(self, left: Any, right: Any) -> Any:
        raise NotImplementedError

    def mul(self, left: Any, right: Any) -> Any:
        raise NotImplementedError

    def recip(self, value: Any) -> Any:
        raise NotImplementedError


class FractionModel(Model):
    def parse(self, value: str) -> Fraction:
        return Fraction(value)

    def render(self, value: Any) -> str:
        if value is UNDEFINED:
            return "UNDEFINED"
        return f"{value.numerator}/{value.denominator}"

    def add(self, left: Fraction, right: Fraction) -> Fraction:
        return left + right

    def mul(self, left: Fraction, right: Fraction) -> Fraction:
        return left * right

    def recip(self, value: Fraction) -> Any:
        if value == 0:
            return UNDEFINED
        return Fraction(value.denominator, value.numerator)


@dataclass(frozen=True)
class PairQ:
    numerator: int
    denominator: int

    @staticmethod
    def normalized(numerator: int, denominator: int) -> "PairQ":
        if denominator == 0:
            raise ZeroDivisionError
        if denominator < 0:
            numerator = -numerator
            denominator = -denominator
        factor = gcd(abs(numerator), denominator)
        return PairQ(numerator // factor, denominator // factor)


class PairModel(Model):
    def parse(self, value: str) -> PairQ:
        numerator, denominator = value.split("/", 1)
        return PairQ.normalized(int(numerator), int(denominator))

    def render(self, value: Any) -> str:
        if value is UNDEFINED:
            return "UNDEFINED"
        return f"{value.numerator}/{value.denominator}"

    def add(self, left: PairQ, right: PairQ) -> PairQ:
        return PairQ.normalized(
            left.numerator * right.denominator
            + right.numerator * left.denominator,
            left.denominator * right.denominator,
        )

    def mul(self, left: PairQ, right: PairQ) -> PairQ:
        return PairQ.normalized(
            left.numerator * right.numerator,
            left.denominator * right.denominator,
        )

    def recip(self, value: PairQ) -> Any:
        if value.numerator == 0:
            return UNDEFINED
        return PairQ.normalized(value.denominator, value.numerator)


def eval_expression(
    expr: dict[str, Any],
    env: dict[str, Any],
    constants: dict[str, Any],
    operations: dict[str, Callable[..., Any]],
) -> Any:
    if "var" in expr:
        return env[expr["var"]]
    if "const" in expr:
        return constants[expr["const"]]
    op = operations[expr["call"]]
    values = [
        eval_expression(arg, env, constants, operations)
        for arg in expr["args"]
    ]
    if any(value is UNDEFINED for value in values):
        return UNDEFINED
    return op(*values)


def compile_spec(
    spec: dict[str, Any],
    model: Model,
) -> tuple[dict[str, Callable[..., Any]], list[str]]:
    constants = {
        entry["id"]: model.parse(entry["value"])
        for entry in spec["constants"]
    }

    basis: dict[str, Callable[..., Any]] = {
        "add": model.add,
        "mul": model.mul,
        "recip": model.recip,
    }

    declared_basis = {entry["id"] for entry in spec["basis_operations"]}
    assert declared_basis == set(basis)

    operations = dict(basis)
    rules = {entry["id"]: entry for entry in spec["generation_rules"]}
    generated_order: list[str] = []

    while rules:
        progress = False
        for name in sorted(list(rules)):
            rule = rules[name]
            calls = called_operations(rule["expression"])
            consts = used_constants(rule["expression"])

            if not consts <= constants.keys():
                continue
            if not calls <= operations.keys():
                continue

            inputs = tuple(rule["inputs"])
            expr = copy.deepcopy(rule["expression"])

            def generated(
                *args: Any,
                _inputs: tuple[str, ...] = inputs,
                _expr: dict[str, Any] = expr,
            ) -> Any:
                assert len(args) == len(_inputs)
                env = dict(zip(_inputs, args, strict=True))
                return eval_expression(_expr, env, constants, operations)

            operations[name] = generated
            generated_order.append(name)
            del rules[name]
            progress = True

        if not progress:
            unresolved = {
                name: {
                    "operations": sorted(called_operations(rule["expression"])),
                    "constants": sorted(used_constants(rule["expression"])),
                }
                for name, rule in sorted(rules.items())
            }
            raise DependencyError(json.dumps(unresolved, sort_keys=True))

    return operations, generated_order


def semantic_payload(
    rule: dict[str, Any],
    operation: Callable[..., Any],
    model: Model,
) -> tuple[dict[str, Any], int]:
    arity = len(rule["inputs"])
    combos = itertools.product(CORPUS, repeat=arity)
    inputs: list[list[str]] = []
    outputs: list[str] = []
    undefined = 0

    for combo in combos:
        values = tuple(model.parse(value) for value in combo)
        result = operation(*values)
        rendered = model.render(result)
        if rendered == "UNDEFINED":
            undefined += 1
        inputs.append(list(combo))
        outputs.append(rendered)

    return {
        "operation": rule["id"],
        "inputs": inputs,
        "outputs": outputs,
    }, undefined


def certificate_for(
    rule: dict[str, Any],
    operation: Callable[..., Any],
    model: Model,
) -> dict[str, Any]:
    payload, undefined = semantic_payload(rule, operation, model)
    digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return {
        "operation": rule["id"],
        "carrier": "Q",
        "dependencies": sorted(called_operations(rule["expression"])),
        "expression": rule["expression"],
        "partiality": rule["partiality"],
        "cases": str(len(payload["inputs"])),
        "undefined_cases": str(undefined),
        "semantic_signature_sha256": digest,
    }


def all_certificates(spec: dict[str, Any], model: Model) -> tuple[list[dict[str, Any]], list[str]]:
    operations, generated_order = compile_spec(spec, model)
    rules = {entry["id"]: entry for entry in spec["generation_rules"]}
    certs = [
        certificate_for(rules[name], operations[name], model)
        for name in generated_order
    ]
    certs.sort(key=lambda cert: cert["operation"])
    return certs, generated_order


def expected_artifact(spec: dict[str, Any], certs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "authority": "research-only",
        "certificates": certs,
        "corpus": list(CORPUS),
        "schema": "core-math-generation-certificates/v1",
        "spec": "docs/research/2433-core-math-neutral-v1.json",
    }


def negative_controls(spec: dict[str, Any]) -> None:
    def expect_unavailable(
        edited: dict[str, Any],
        unavailable: set[str],
    ) -> None:
        try:
            operations, _ = compile_spec(edited, FractionModel())
        except DependencyError:
            # A dependency failure is acceptable iff every claimed unavailable
            # operation is indeed blocked by the edited basis/constants.
            basis = {entry["id"] for entry in edited["basis_operations"]}
            consts = {entry["id"] for entry in edited["constants"]}
            rules = {entry["id"]: entry for entry in edited["generation_rules"]}

            available = set(basis)
            progress = True
            while progress:
                progress = False
                for name, rule in rules.items():
                    if name in available:
                        continue
                    if (
                        called_operations(rule["expression"]) <= available
                        and used_constants(rule["expression"]) <= consts
                    ):
                        available.add(name)
                        progress = True
            assert unavailable.isdisjoint(available)
            return
        assert unavailable.isdisjoint(operations)

    no_neg_one = copy.deepcopy(spec)
    no_neg_one["constants"] = []
    expect_unavailable(no_neg_one, {"neg", "sub"})

    no_mul = copy.deepcopy(spec)
    no_mul["basis_operations"] = [
        entry for entry in no_mul["basis_operations"] if entry["id"] != "mul"
    ]
    expect_unavailable(no_mul, {"neg", "sub", "div"})

    no_add = copy.deepcopy(spec)
    no_add["basis_operations"] = [
        entry for entry in no_add["basis_operations"] if entry["id"] != "add"
    ]
    expect_unavailable(no_add, {"sub"})

    no_recip = copy.deepcopy(spec)
    no_recip["basis_operations"] = [
        entry for entry in no_recip["basis_operations"] if entry["id"] != "recip"
    ]
    expect_unavailable(no_recip, {"div"})

    cyclic = copy.deepcopy(spec)
    cyclic["generation_rules"] = [
        {
            "id": "left",
            "inputs": ["x"],
            "output": "Q",
            "partiality": "total",
            "expression": {"call": "right", "args": [{"var": "x"}]},
        },
        {
            "id": "right",
            "inputs": ["x"],
            "output": "Q",
            "partiality": "total",
            "expression": {"call": "left", "args": [{"var": "x"}]},
        },
    ]
    try:
        compile_spec(cyclic, FractionModel())
    except DependencyError:
        pass
    else:
        raise AssertionError("dependency cycle was not rejected")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    spec = load_json(SPEC_PATH)
    neutral_vocabulary_gate(spec)

    projection = load_json(PROJECTION_PATH)
    assert projection["authority"] == "non-authoritative-projection"
    neutral_ops = {
        entry["id"] for entry in spec["basis_operations"]
    } | {
        entry["id"] for entry in spec["generation_rules"]
    }
    assert set(projection["current_research_labels"].values()) <= neutral_ops

    fraction_certs, fraction_order = all_certificates(spec, FractionModel())
    pair_certs, pair_order = all_certificates(spec, PairModel())

    assert fraction_order == pair_order
    assert fraction_certs == pair_certs

    # Generated closure must be real: SUB depends on generated NEG.
    sub = next(cert for cert in fraction_certs if cert["operation"] == "sub")
    assert "neg" in sub["dependencies"]
    assert fraction_order.index("neg") < fraction_order.index("sub")

    # Explicit partiality parity.
    fraction_ops, _ = compile_spec(spec, FractionModel())
    pair_ops, _ = compile_spec(spec, PairModel())
    assert fraction_ops["recip"](Fraction(0, 1)) is UNDEFINED
    assert pair_ops["recip"](PairQ.normalized(0, 1)) is UNDEFINED
    assert fraction_ops["div"](Fraction(1, 1), Fraction(0, 1)) is UNDEFINED
    assert pair_ops["div"](
        PairQ.normalized(1, 1), PairQ.normalized(0, 1)
    ) is UNDEFINED

    negative_controls(spec)

    artifact = expected_artifact(spec, fraction_certs)
    if args.check:
        committed = load_json(CERT_PATH)
        assert committed == artifact, "generation certificate artifact is stale"

    print("NEUTRAL-SPEC-VOCABULARY=PASS")
    print("MODEL-A=fractions.Fraction")
    print("MODEL-B=normalized-integer-pair-Q")
    print("MODEL-PARITY=PASS")
    print("GENERATED-ORDER=" + ",".join(fraction_order))
    print("CHAIN=neg->sub")
    print("ZERO-RECIPROCAL-PARTIALITY=PASS")
    print("ZERO-DIVISION-PARTIALITY=PASS")
    print("REMOVE-DEPENDENCY-CONTROLS=PASS")
    print("DEPENDENCY-CYCLE-REJECTED=1")
    print("REGISTRY-ROWS=0")
    for cert in fraction_certs:
        print(
            "CERT "
            + cert["operation"]
            + " cases="
            + cert["cases"]
            + " undefined="
            + cert["undefined_cases"]
            + " sha256="
            + cert["semantic_signature_sha256"]
        )
    print("STATUS=PASS-CORE-MATH-NEUTRAL-GROWTH")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
