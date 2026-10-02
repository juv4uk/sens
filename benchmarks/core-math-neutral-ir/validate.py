#!/usr/bin/env python3
"""#2427 — minimal language-neutral Core-Math IR contract.

This validator deliberately derives only the generic roles already exercised by
#2433. It does not define final Core-Math operation identity (#2435), syntax
(#2429), bridges (#2430), or execution semantics (#2428).

The current #2433 exact-Q JSON is treated as one IR instance.

Required generic roles:
- carrier/type
- constant
- basis operation signature
- generated operation rule
- expression AST
- dependency edge
- partiality declaration
- provenance envelope / source artifact
- canonical serialization

No Lisp/Core semantic vocabulary is admitted.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs" / "research" / "2433-core-math-neutral-v1.json"
PROJECTION = ROOT / "docs" / "research" / "2433-core-math-research-projection.json"
CERTIFICATES = ROOT / "docs" / "research" / "2433-core-math-generation-certificates.json"
CANONICAL = ROOT / "benchmarks" / "core-math-neutral-ir" / "canonical-2433.json"

FORBIDDEN = {
    "lambda", "eval", "apply", "quote", "cons", "car", "cdr", "cond",
    "lisp", "core", "registry", "sid", "reader",
}

PARTIALITY = {
    "total",
    "undefined-at-zero",
    "undefined-when-y-zero",
}


class IRValidationError(ValueError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def token_gate(value: Any) -> None:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
    tokens = set(re.findall(r"[a-z_]+", text))
    leaked = sorted(tokens & FORBIDDEN)
    if leaked:
        raise IRValidationError(f"forbidden semantic vocabulary: {leaked}")


def require_exact_keys(obj: dict[str, Any], required: set[str], optional: set[str] = set()) -> None:
    keys = set(obj)
    missing = required - keys
    unknown = keys - required - optional
    if missing:
        raise IRValidationError(f"missing keys: {sorted(missing)}")
    if unknown:
        raise IRValidationError(f"unknown keys: {sorted(unknown)}")


def validate_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", value):
        raise IRValidationError(f"invalid {label}: {value!r}")
    return value


def validate_type_id(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_^]*", value):
        raise IRValidationError(f"invalid carrier/type id: {value!r}")
    return value


def validate_expr(
    node: Any,
    variables: set[str],
    constants: set[str],
    operations: set[str],
) -> set[str]:
    if not isinstance(node, dict):
        raise IRValidationError("expression node must be object")

    kinds = [k for k in ("var", "const", "call") if k in node]
    if len(kinds) != 1:
        raise IRValidationError("expression node must have exactly one of var/const/call")

    if "var" in node:
        require_exact_keys(node, {"var"})
        name = validate_id(node["var"], "variable")
        if name not in variables:
            raise IRValidationError(f"unknown variable: {name}")
        return set()

    if "const" in node:
        require_exact_keys(node, {"const"})
        name = validate_id(node["const"], "constant")
        if name not in constants:
            raise IRValidationError(f"unknown constant: {name}")
        return set()

    require_exact_keys(node, {"call", "args"})
    op = validate_id(node["call"], "operation")
    if op not in operations:
        raise IRValidationError(f"unknown operation in expression: {op}")
    args = node["args"]
    if not isinstance(args, list):
        raise IRValidationError("call args must be list")
    deps = {op}
    for arg in args:
        deps |= validate_expr(arg, variables, constants, operations)
    return deps


def validate_spec(spec: dict[str, Any]) -> dict[str, Any]:
    require_exact_keys(
        spec,
        {
            "schema", "status", "carrier", "constants",
            "basis_operations", "generation_rules",
        },
    )
    if spec["schema"] != "core-math-neutral/v1":
        raise IRValidationError("unsupported neutral schema")
    if spec["status"] != "research-only":
        raise IRValidationError("neutral IR instance must remain research-only")

    token_gate(spec)

    carrier = spec["carrier"]
    require_exact_keys(carrier, {"id", "kind", "normalization", "partiality"})
    carrier_id = validate_type_id(carrier["id"])
    if carrier["partiality"] != "explicit":
        raise IRValidationError("carrier partiality must be explicit")

    constants: set[str] = set()
    for item in spec["constants"]:
        require_exact_keys(item, {"id", "carrier", "value"})
        ident = validate_id(item["id"], "constant")
        if ident in constants:
            raise IRValidationError(f"duplicate constant: {ident}")
        constants.add(ident)
        if item["carrier"] != carrier_id:
            raise IRValidationError("constant carrier mismatch")
        if not isinstance(item["value"], str):
            raise IRValidationError("constant value must be neutral serialized scalar")

    operation_arity: dict[str, int] = {}
    basis: set[str] = set()
    for item in spec["basis_operations"]:
        require_exact_keys(item, {"id", "inputs", "output", "partiality"})
        ident = validate_id(item["id"], "basis operation")
        if ident in operation_arity:
            raise IRValidationError(f"duplicate operation: {ident}")
        if not isinstance(item["inputs"], list):
            raise IRValidationError("operation inputs must be list")
        if any(t != carrier_id for t in item["inputs"]):
            raise IRValidationError("basis input carrier mismatch")
        if item["output"] != carrier_id:
            raise IRValidationError("basis output carrier mismatch")
        if item["partiality"] not in PARTIALITY:
            raise IRValidationError(f"unknown partiality: {item['partiality']}")
        operation_arity[ident] = len(item["inputs"])
        basis.add(ident)

    rules_by_id: dict[str, dict[str, Any]] = {}
    all_rule_ids: set[str] = set()
    for item in spec["generation_rules"]:
        require_exact_keys(
            item,
            {"id", "inputs", "output", "partiality", "expression"},
        )
        ident = validate_id(item["id"], "generated operation")
        if ident in operation_arity or ident in all_rule_ids:
            raise IRValidationError(f"duplicate operation: {ident}")
        all_rule_ids.add(ident)
        rules_by_id[ident] = item

    all_operations = basis | all_rule_ids

    dependency_graph: dict[str, set[str]] = {}
    for ident, item in rules_by_id.items():
        inputs = item["inputs"]
        if not isinstance(inputs, list) or len(set(inputs)) != len(inputs):
            raise IRValidationError(f"invalid inputs for {ident}")
        variables = {validate_id(x, "rule input") for x in inputs}
        if item["output"] != carrier_id:
            raise IRValidationError("generated output carrier mismatch")
        if item["partiality"] not in PARTIALITY:
            raise IRValidationError(f"unknown partiality: {item['partiality']}")

        deps = validate_expr(
            item["expression"],
            variables,
            constants,
            all_operations,
        )
        dependency_graph[ident] = {d for d in deps if d in all_rule_ids}
        operation_arity[ident] = len(inputs)

    # Arity validation after every operation is known.
    def check_arity(node: dict[str, Any]) -> None:
        if "call" in node:
            op = node["call"]
            if len(node["args"]) != operation_arity[op]:
                raise IRValidationError(
                    f"arity mismatch for {op}: expected {operation_arity[op]}"
                )
            for arg in node["args"]:
                check_arity(arg)

    for item in rules_by_id.values():
        check_arity(item["expression"])

    # Deterministic DAG check.
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise IRValidationError(f"generation cycle at {node}")
        if node in visited:
            return
        visiting.add(node)
        for dep in sorted(dependency_graph[node]):
            visit(dep)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(dependency_graph):
        visit(node)

    return {
        "carrier": carrier_id,
        "basis": sorted(basis),
        "generated": sorted(all_rule_ids),
        "dependencies": {
            node: sorted(deps)
            for node, deps in sorted(dependency_graph.items())
        },
    }


def validate_projection_roundtrip(
    spec: dict[str, Any],
    projection: dict[str, Any],
    certificates: dict[str, Any],
) -> dict[str, Any]:
    require_exact_keys(
        projection,
        {
            "schema", "authority", "neutral_spec",
            "current_research_labels", "refs", "note",
        },
    )
    if projection["authority"] != "non-authoritative-projection":
        raise IRValidationError("projection attempted upward authority")

    neutral_ops = {
        item["id"] for item in spec["basis_operations"]
    } | {
        item["id"] for item in spec["generation_rules"]
    }
    mapped = set(projection["current_research_labels"].values())
    if not mapped <= neutral_ops:
        raise IRValidationError("projection points at unknown neutral operation")

    cert_ops = {c["operation"] for c in certificates["certificates"]}
    generated_ops = {item["id"] for item in spec["generation_rules"]}
    if cert_ops != generated_ops:
        raise IRValidationError("certificate provenance does not cover generated operations exactly")

    # Canonical transport envelope. Local operation IDs/provenance are preserved
    # byte-for-byte after decode/encode; this is NOT final operation identity.
    envelope = {
        "neutral_spec": spec,
        "projection": projection,
        "generation_certificates": certificates,
    }
    encoded = canonical_json(envelope)
    decoded = json.loads(encoded)
    encoded_again = canonical_json(decoded)
    if encoded_again != encoded:
        raise IRValidationError("canonical round-trip instability")
    if decoded != envelope:
        raise IRValidationError("round-trip changed identity/provenance fields")
    return envelope


def negative_controls(spec: dict[str, Any]) -> int:
    rejected = 0

    def must_reject(mutator) -> None:
        nonlocal rejected
        candidate = copy.deepcopy(spec)
        mutator(candidate)
        try:
            validate_spec(candidate)
        except IRValidationError:
            rejected += 1
        else:
            raise AssertionError("malformed neutral IR was accepted")

    must_reject(lambda x: x.__setitem__("schema", "unknown/v9"))
    must_reject(lambda x: x["generation_rules"][0]["expression"].__setitem__("call", "mystery"))
    must_reject(lambda x: x["generation_rules"][0].__setitem__("partiality", "maybe"))
    must_reject(lambda x: x["generation_rules"][0]["expression"].__setitem__("args", []))
    must_reject(lambda x: x["generation_rules"][1]["expression"]["args"][1].__setitem__("call", "sub"))
    must_reject(lambda x: x.__setitem__("host", "lisp"))

    return rejected


def main() -> None:
    spec = load_json(SPEC)
    projection = load_json(PROJECTION)
    certificates = load_json(CERTIFICATES)

    summary = validate_spec(spec)
    envelope = validate_projection_roundtrip(spec, projection, certificates)
    negatives = negative_controls(spec)

    canonical = canonical_json(envelope)
    committed = CANONICAL.read_text(encoding="utf-8")
    if committed != canonical:
        raise SystemExit("STALE-CANONICAL-IR")

    print("SCHEMA=core-math-neutral/v1")
    print("CARRIER=" + summary["carrier"])
    print("BASIS=" + ",".join(summary["basis"]))
    print("GENERATED=" + ",".join(summary["generated"]))
    print("DEPENDENCY-sub=" + ",".join(summary["dependencies"]["sub"]))
    print("CANONICAL-ROUNDTRIP=PASS")
    print("IDENTITY-PROVENANCE-PRESERVED=PASS")
    print(f"MALFORMED-NEGATIVE-CASES={negatives}")
    print("UNKNOWN-LAW-FAIL-CLOSED=PASS")
    print("GENERATION-CYCLE-FAIL-CLOSED=PASS")
    print("HOST-PROJECTION-AUTHORITY=DOWNWARD-ONLY")
    print("FINAL-OPERATION-IDENTITY=OUT-OF-SCOPE-#2435")
    print("STATUS=PASS-CORE-MATH-NEUTRAL-IR")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
