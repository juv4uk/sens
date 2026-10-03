#!/usr/bin/env python3
"""#2425 — executable definition/accounting of Core-Math growth events.

Consumes the #2433 neutral exact-Q instance after #2427 validation.

This script distinguishes two claims:

1. recursive declared closure — WITNESSED:
   admitted basis + already-admitted generation rules produce operations by
   dependency closure, and generated NEG is reused by generated SUB.

2. autonomous/enumerative language growth — NOT YET PROVED:
   the current neutral spec still declares one generation rule per generated
   result (NEG/SUB/DIV). There are zero registry slots, but three declared
   result-producing rules. This script refuses to conflate those facts.

Research only.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs" / "research" / "2433-core-math-neutral-v1.json"
CERT_PATH = ROOT / "docs" / "research" / "2433-core-math-generation-certificates.json"


class GrowthError(RuntimeError):
    pass


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def calls(node: Any) -> set[str]:
    if not isinstance(node, dict):
        raise GrowthError("expression node must be object")
    if "call" not in node:
        return set()
    out = {node["call"]}
    for arg in node["args"]:
        out |= calls(arg)
    return out


def constants(node: Any) -> set[str]:
    if not isinstance(node, dict):
        raise GrowthError("expression node must be object")
    out: set[str] = set()
    if "const" in node:
        out.add(node["const"])
    if "call" in node:
        for arg in node["args"]:
            out |= constants(arg)
    return out


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def dependency_closure(spec: dict[str, Any]) -> tuple[list[dict[str, Any]], set[str]]:
    basis = {entry["id"] for entry in spec["basis_operations"]}
    consts = {entry["id"] for entry in spec["constants"]}
    rules = {entry["id"]: entry for entry in spec["generation_rules"]}

    admitted_ops = set(basis)
    admitted_generated: set[str] = set()
    events: list[dict[str, Any]] = []
    depth: dict[str, int] = {name: 0 for name in basis}

    round_index = 1
    unresolved = dict(rules)

    while unresolved:
        frontier: list[tuple[str, dict[str, Any], set[str], set[str]]] = []

        # Snapshot semantics: all rules in one round see the same prior state.
        prior_ops = set(admitted_ops)
        prior_generated = set(admitted_generated)

        for name, rule in unresolved.items():
            op_deps = calls(rule["expression"])
            const_deps = constants(rule["expression"])
            if op_deps <= prior_ops and const_deps <= consts:
                frontier.append((name, rule, op_deps, const_deps))

        if not frontier:
            break

        for name, rule, op_deps, const_deps in frontier:
            generated_deps = sorted(op_deps & prior_generated)
            basis_deps = sorted(op_deps & basis)
            event_depth = 1 + max((depth[d] for d in generated_deps), default=0)

            expression_digest = sha256(
                canonical_bytes(rule["expression"])
            ).hexdigest()

            events.append(
                {
                    "operation_ref": name,
                    "round": round_index,
                    "depth": event_depth,
                    "basis_dependencies": basis_deps,
                    "generated_dependencies": generated_deps,
                    "constant_dependencies": sorted(const_deps),
                    "expression_sha256": expression_digest,
                    "partiality": rule["partiality"],
                }
            )

        for name, _, _, _ in frontier:
            admitted_ops.add(name)
            admitted_generated.add(name)
            depth[name] = next(
                event["depth"]
                for event in events
                if event["operation_ref"] == name
            )
            del unresolved[name]

        round_index += 1

    return events, set(unresolved)


def certificate_metrics(certs: dict[str, Any]) -> dict[str, Any]:
    rows = certs["certificates"]
    encoded_rows = {
        row["operation"]: len(canonical_bytes(row))
        for row in rows
    }
    total = sum(encoded_rows.values())
    return {
        "per_operation_bytes": encoded_rows,
        "total_certificate_bytes": total,
    }


def invalid_controls(spec: dict[str, Any]) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []

    def run(label: str, edited: dict[str, Any], expected_unresolved: set[str]) -> None:
        _, unresolved = dependency_closure(edited)
        if unresolved != expected_unresolved:
            raise AssertionError(
                f"{label}: unresolved={sorted(unresolved)} "
                f"expected={sorted(expected_unresolved)}"
            )
        controls.append(
            {
                "label": label,
                "unresolved": sorted(unresolved),
            }
        )

    no_neg_one = json.loads(json.dumps(spec))
    no_neg_one["constants"] = []
    run("remove-neg_one", no_neg_one, {"neg", "sub"})

    no_mul = json.loads(json.dumps(spec))
    no_mul["basis_operations"] = [
        x for x in no_mul["basis_operations"] if x["id"] != "mul"
    ]
    run("remove-mul", no_mul, {"div", "neg", "sub"})

    no_add = json.loads(json.dumps(spec))
    no_add["basis_operations"] = [
        x for x in no_add["basis_operations"] if x["id"] != "add"
    ]
    run("remove-add", no_add, {"sub"})

    no_recip = json.loads(json.dumps(spec))
    no_recip["basis_operations"] = [
        x for x in no_recip["basis_operations"] if x["id"] != "recip"
    ]
    run("remove-recip", no_recip, {"div"})

    cyclic = json.loads(json.dumps(spec))
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
    run("dependency-cycle", cyclic, {"left", "right"})

    return controls


def main() -> None:
    spec = load(SPEC_PATH)
    certs = load(CERT_PATH)

    events, unresolved = dependency_closure(spec)
    if unresolved:
        raise GrowthError(f"positive control left unresolved: {sorted(unresolved)}")

    by_name = {event["operation_ref"]: event for event in events}
    assert by_name["neg"]["depth"] == 1
    assert by_name["div"]["depth"] == 1
    assert by_name["sub"]["depth"] == 2
    assert by_name["sub"]["generated_dependencies"] == ["neg"]

    depth_counts = Counter(event["depth"] for event in events)
    metrics = certificate_metrics(certs)
    negatives = invalid_controls(spec)

    basis_count = len(spec["basis_operations"])
    declared_rule_count = len(spec["generation_rules"])
    generated_count = len(events)
    closure_operation_count = basis_count + generated_count
    max_depth = max(event["depth"] for event in events)

    cert_ops = {c["operation"] for c in certs["certificates"]}
    event_ops = {e["operation_ref"] for e in events}
    assert cert_ops == event_ops

    report = {
        "growth_event_definition": {
            "prior_dependencies_admitted": True,
            "rule_already_admitted": True,
            "deterministic_result_construction": True,
            "replayable_certificate_required": True,
            "generated_result_reusable": True,
        },
        "metrics": {
            "initial_basis_operations": basis_count,
            "declared_generation_rules": declared_rule_count,
            "generated_operations": generated_count,
            "closure_operation_count": closure_operation_count,
            "max_generation_depth": max_depth,
            "generated_per_depth": {
                str(depth): depth_counts[depth]
                for depth in sorted(depth_counts)
            },
            "certificate_bytes_canonical_rows": metrics["total_certificate_bytes"],
            "registry_slots_required": 0,
            "autodiscovered_operation_rules": 0,
        },
        "events": events,
        "invalid_controls": negatives,
        "claim_status": {
            "recursive_declared_closure": "WITNESSED",
            "depth_at_least_2": "WITNESSED",
            "generated_result_reuse": "WITNESSED",
            "autonomous_enumerative_growth": "NOT-YET-PROVED",
            "minimal_basis": "OUT-OF-SCOPE-#2426",
            "growth_phase_semantics": "OUT-OF-SCOPE-#2431",
            "final_operation_identity": "OUT-OF-SCOPE-#2435",
        },
    }

    print("GROWTH-EVENT=dependency-closed-admitted-law-application")
    print(f"INITIAL-BASIS-OPS={basis_count}")
    print(f"DECLARED-GENERATION-RULES={declared_rule_count}")
    print(f"GENERATED-OPS={generated_count}")
    print(f"CLOSURE-OPS={closure_operation_count}")
    print(f"MAX-GENERATION-DEPTH={max_depth}")
    for depth in sorted(depth_counts):
        print(f"GENERATED-AT-DEPTH-{depth}={depth_counts[depth]}")
    print("CHAIN=neg->sub")
    print(f"CERTIFICATE-BYTES={metrics['total_certificate_bytes']}")
    print("REGISTRY-SLOTS-REQUIRED=0")
    print(f"INVALID-CONTROLS={len(negatives)}")
    print("RECURSIVE-DECLARED-CLOSURE=WITNESSED")
    print("AUTONOMOUS-ENUMERATIVE-GROWTH=NOT-YET-PROVED")
    print("CACHE-MATERIALIZATION-SEMANTICS=OUT-OF-SCOPE-#2431")
    print("STATUS=PASS-CORE-MATH-GROWTH-EVENT-ACCOUNTING")
    print("AUTHORITY=RESEARCH-ONLY")

    out = ROOT / "benchmarks" / "core-math-growth-law" / "report.json"
    expected = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if out.read_text(encoding="utf-8") != expected:
        raise SystemExit("STALE-GROWTH-REPORT")


if __name__ == "__main__":
    main()
