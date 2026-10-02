#!/usr/bin/env python3
"""#2435 — generated Core-Math operation identity experiment.

Consumes the language-neutral #2433 exact-Q spec and its independently
cross-checked certificates. Compares four identity models:

A. allocated slot (order-sensitive control);
B. direct derivation tree;
C. recursively expanded canonical mathematical form;
D. bounded semantic signature (observational control, not authority).

Research only. No SENS function identity allocation and no Core admission.
"""

from __future__ import annotations

import argparse
import copy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "docs" / "research" / "2433-core-math-neutral-v1.json"
CERT_PATH = ROOT / "docs" / "research" / "2433-core-math-generation-certificates.json"
REPORT_PATH = ROOT / "docs" / "research" / "2435-core-math-generated-identity.json"

COMMUTATIVE_BASIS = {"add", "mul"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def substitute(node: dict[str, Any], mapping: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if "var" in node:
        return copy.deepcopy(mapping.get(node["var"], node))
    if "const" in node:
        return copy.deepcopy(node)
    if "call" in node:
        return {
            "call": node["call"],
            "args": [substitute(arg, mapping) for arg in node["args"]],
        }
    raise ValueError(f"unknown expression node: {node!r}")


def expand_generated(
    node: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    stack: tuple[str, ...] = (),
) -> dict[str, Any]:
    if "var" in node or "const" in node:
        return copy.deepcopy(node)
    if "call" not in node:
        raise ValueError(f"unknown expression node: {node!r}")

    call = node["call"]
    args = [expand_generated(arg, rules, stack) for arg in node["args"]]

    if call not in rules:
        return {"call": call, "args": args}

    if call in stack:
        raise ValueError("generated-operation cycle: " + " -> ".join(stack + (call,)))

    rule = rules[call]
    if len(args) != len(rule["inputs"]):
        raise ValueError(f"arity mismatch while expanding {call}")

    mapping = dict(zip(rule["inputs"], args, strict=True))
    replaced = substitute(rule["expression"], mapping)
    return expand_generated(replaced, rules, stack + (call,))


def canonicalize_expression(
    node: dict[str, Any],
    input_order: list[str],
) -> dict[str, Any]:
    if "var" in node:
        try:
            position = input_order.index(node["var"])
        except ValueError as exc:
            raise ValueError(f"unbound variable {node['var']}") from exc
        return {"var": f"v{position}"}

    if "const" in node:
        return {"const": node["const"]}

    if "call" in node:
        call = node["call"]
        args = [canonicalize_expression(arg, input_order) for arg in node["args"]]
        if call in COMMUTATIVE_BASIS:
            args.sort(key=canonical_json)
        return {"call": call, "args": args}

    raise ValueError(f"unknown expression node: {node!r}")


def identity_payload(
    spec: dict[str, Any],
    rule: dict[str, Any],
    expression: dict[str, Any],
) -> dict[str, Any]:
    carrier = spec["carrier"]["id"]
    return {
        "carrier": carrier,
        "arity": len(rule["inputs"]),
        "inputs": [carrier for _ in rule["inputs"]],
        "output": rule["output"],
        "partiality": rule["partiality"],
        "expression": canonicalize_expression(expression, rule["inputs"]),
    }


def direct_derivation_identity(spec: dict[str, Any], rule: dict[str, Any]) -> str:
    return "derivation-v1:" + digest(identity_payload(spec, rule, rule["expression"]))


def expanded_math_identity(
    spec: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    rule: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    expanded = expand_generated(rule["expression"], rules)
    payload = identity_payload(spec, rule, expanded)
    return "math-normal-v1:" + digest(payload), payload


def slot_map(spec: dict[str, Any]) -> dict[str, int]:
    return {
        rule["id"]: index
        for index, rule in enumerate(spec["generation_rules"])
    }


def semantic_signatures(certificates: dict[str, Any]) -> dict[str, str]:
    return {
        cert["operation"]: "bounded-semantic-v1:" + cert["semantic_signature_sha256"]
        for cert in certificates["certificates"]
    }


def equivalent_sub_expression() -> dict[str, Any]:
    return {
        "call": "add",
        "args": [
            {"var": "x"},
            {
                "call": "mul",
                "args": [
                    {"const": "neg_one"},
                    {"var": "y"},
                ],
            },
        ],
    }


def report(spec: dict[str, Any], certificates: dict[str, Any]) -> dict[str, Any]:
    rules = {rule["id"]: rule for rule in spec["generation_rules"]}
    semantic = semantic_signatures(certificates)

    operations: list[dict[str, Any]] = []
    for rule in spec["generation_rules"]:
        math_id, normal_payload = expanded_math_identity(spec, rules, rule)
        operations.append({
            "operation": rule["id"],
            "allocated_slot_control": slot_map(spec)[rule["id"]],
            "direct_derivation_identity": direct_derivation_identity(spec, rule),
            "expanded_math_identity": math_id,
            "expanded_math_normal_form": normal_payload,
            "bounded_semantic_signature_control": semantic[rule["id"]],
            "dedicated_semantic_registry_row": False,
        })

    sub_rule = rules["sub"]
    alternate = equivalent_sub_expression()

    direct_original = direct_derivation_identity(spec, sub_rule)
    direct_alternate = "derivation-v1:" + digest(
        identity_payload(spec, sub_rule, alternate)
    )

    expanded_original, original_payload = expanded_math_identity(spec, rules, sub_rule)
    alternate_payload = identity_payload(spec, sub_rule, alternate)
    expanded_alternate = "math-normal-v1:" + digest(alternate_payload)

    reordered = copy.deepcopy(spec)
    reordered["generation_rules"] = list(reversed(reordered["generation_rules"]))

    slot_original = slot_map(spec)
    slot_reordered = slot_map(reordered)

    return {
        "schema": "core-math-generated-identity-research/v1",
        "authority": "research-only",
        "source_spec": str(SPEC_PATH.relative_to(ROOT)),
        "source_certificates": str(CERT_PATH.relative_to(ROOT)),
        "identity_models": {
            "allocated_slot": {
                "role": "negative-control",
                "property": "order-sensitive allocation, not mathematical identity",
            },
            "direct_derivation_tree": {
                "role": "provenance-sensitive-candidate",
                "property": "preserves named generated dependencies; equivalent derivations may differ",
            },
            "expanded_math_normal_form": {
                "role": "positive-candidate",
                "property": "generated aliases expanded; variables alpha-normalized; commutative add/mul arguments sorted",
            },
            "bounded_semantic_signature": {
                "role": "observational-control",
                "property": "agrees across the two non-Lisp #2433 exact-Q models on the bounded corpus; insufficient as universal identity proof",
            },
        },
        "operations": operations,
        "equivalent_derivation_test": {
            "operation": "sub",
            "original": "add(x, neg(y))",
            "alternate": "add(x, mul(neg_one, y))",
            "direct_original": direct_original,
            "direct_alternate": direct_alternate,
            "direct_same": direct_original == direct_alternate,
            "expanded_original": expanded_original,
            "expanded_alternate": expanded_alternate,
            "expanded_same": expanded_original == expanded_alternate,
            "expanded_payload_same": original_payload == alternate_payload,
        },
        "allocation_order_attack": {
            "original_slots": slot_original,
            "reversed_rule_order_slots": slot_reordered,
            "stable": slot_original == slot_reordered,
        },
        "claims": {
            "sens_function_slot_required": False,
            "generated_registry_rows": 0,
            "serialization_replay_required": True,
            "executor_evidence": "#2433 / PR #2437 independently cross-checks bounded semantic signatures with Fraction and normalized-pair exact-Q models",
            "current_strongest_candidate": "expanded_math_normal_form",
            "current_status": "bounded-positive-candidate-not-ratified",
        },
        "non_conclusions": [
            "bounded semantic signatures are not universal semantic identity",
            "expanded normal form is not yet proved complete for all Core-Math operations",
            "commutativity normalization is admitted here only for the exact-Q add/mul witness",
            "no Core identity or SENS function coordinate is allocated",
            "no claim is made that all future residue operations have generated identities",
        ],
    }


def check_invariants(result: dict[str, Any]) -> None:
    eq = result["equivalent_derivation_test"]
    assert not eq["direct_same"], "direct derivation control unexpectedly collapsed provenance"
    assert eq["expanded_same"], "expanded mathematical form failed equivalent SUB derivation"
    assert eq["expanded_payload_same"]

    attack = result["allocation_order_attack"]
    assert not attack["stable"], "allocated-slot control unexpectedly survived reorder"

    assert result["claims"]["generated_registry_rows"] == 0
    assert result["claims"]["sens_function_slot_required"] is False

    for op in result["operations"]:
        assert op["expanded_math_identity"].startswith("math-normal-v1:")
        assert op["dedicated_semantic_registry_row"] is False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    spec = load_json(SPEC_PATH)
    certificates = load_json(CERT_PATH)

    assert spec["status"] == "research-only"
    assert certificates["authority"] == "research-only"

    result = report(spec, certificates)
    check_invariants(result)

    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    replay = json.loads(serialized)
    assert replay == result, "identity report failed serialization/reload replay"

    if args.check:
        committed = load_json(REPORT_PATH)
        assert committed == result, "generated identity report is stale"

    eq = result["equivalent_derivation_test"]
    attack = result["allocation_order_attack"]
    print("IDENTITY-MODELS=4")
    print("ALLOCATED-SLOT-ORDER-INVARIANT=" + str(attack["stable"]).upper())
    print("DIRECT-DERIVATION-EQUIVALENT-SUB=" + str(eq["direct_same"]).upper())
    print("EXPANDED-MATH-EQUIVALENT-SUB=" + str(eq["expanded_same"]).upper())
    print("SERIALIZATION-REPLAY=PASS")
    print("SENS-FUNCTION-SLOT-REQUIRED=0")
    print("GENERATED-REGISTRY-ROWS=0")
    print("STATUS=PASS-BOUNDED-GENERATED-IDENTITY-CANDIDATE")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
