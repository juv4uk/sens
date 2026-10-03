#!/usr/bin/env python3
"""#2470 — demand-derived Core-Math operations without eager closure.

Stacked on #2465.  Reuses the same neutral exact-Q basis, generic constructor
schemas, canonical identities and two-model semantic signatures.

Two demand modes are compared:
1. construction-directed recursive derivation;
2. bounded behavior-goal search by arity + exact-Q semantic signature.

Validation labels are attached only after derivation/search.  They never
participate in construction, identity, or search ordering.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AUTO_PATH = ROOT / "benchmarks" / "core-math-autonomous-closure" / "run.py"
DONOR_PATH = ROOT / "scripts" / "research-2433-core-math-neutral-growth.py"
SPEC_PATH = ROOT / "benchmarks" / "core-math-autonomous-closure" / "spec.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class DemandError(RuntimeError):
    pass


@dataclass
class DemandStats:
    constructor_visits: int = 0
    generated_materialized: int = 0
    identity_computations: int = 0
    semantic_signature_computations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    peak_cache_entries: int = 0

    def note_cache(self, cache: dict[str, Any]) -> None:
        self.peak_cache_entries = max(self.peak_cache_entries, len(cache))


def basis_by_id(auto, spec, laws):
    return {
        row["id"]: op
        for row, op in zip(
            spec["basis_operations"],
            auto.basis_operations(spec, laws),
            strict=True,
        )
    }


def constants_by_id(spec):
    return {row["id"]: row for row in spec["constants"]}


def schemas(spec):
    return {row["id"] for row in spec["constructor_schemas"]}


def target_basis(op_id: str) -> dict[str, Any]:
    return {"basis": op_id}


def target_bind_left(binary: dict[str, Any], constant_id: str) -> dict[str, Any]:
    return {
        "constructor": "bind-left-constant",
        "binary": binary,
        "constant": constant_id,
    }


def target_map_right(binary: dict[str, Any], unary: dict[str, Any]) -> dict[str, Any]:
    return {
        "constructor": "map-right",
        "binary": binary,
        "unary": unary,
    }


def derive_construction(
    target: dict[str, Any],
    *,
    auto,
    donor,
    spec: dict[str, Any],
    cache: dict[str, Any],
    stats: DemandStats,
):
    key = canonical_json(target)
    if key in cache:
        stats.cache_hits += 1
        return cache[key]
    stats.cache_misses += 1

    laws = list(spec["normalization_laws"])
    basis = basis_by_id(auto, spec, laws)
    consts = constants_by_id(spec)
    enabled = schemas(spec)

    if "basis" in target:
        op_id = target["basis"]
        if op_id not in basis:
            raise DemandError(f"missing-basis:{op_id}")
        op = basis[op_id]
        auto.attach_signature(donor, op, spec["constants"])
        cache[key] = op
        stats.semantic_signature_computations += 1
        stats.note_cache(cache)
        return op

    constructor = target.get("constructor")
    stats.constructor_visits += 1

    if constructor == "bind-left-constant":
        if constructor not in enabled:
            raise DemandError("schema-disabled:bind-left-constant")
        const_id = target.get("constant")
        if const_id not in consts:
            raise DemandError(f"missing-constant:{const_id}")
        dep = derive_construction(
            target["binary"],
            auto=auto,
            donor=donor,
            spec=spec,
            cache=cache,
            stats=stats,
        )
        if dep.arity != 2:
            raise DemandError("type-error:bind-left-requires-binary")
        op = auto.bind_left(dep, const_id, laws)

    elif constructor == "map-right":
        if constructor not in enabled:
            raise DemandError("schema-disabled:map-right")
        left = derive_construction(
            target["binary"],
            auto=auto,
            donor=donor,
            spec=spec,
            cache=cache,
            stats=stats,
        )
        right = derive_construction(
            target["unary"],
            auto=auto,
            donor=donor,
            spec=spec,
            cache=cache,
            stats=stats,
        )
        if left.arity != 2 or right.arity != 1:
            raise DemandError("type-error:map-right-requires-binary-and-unary")
        op = auto.map_right(left, right, laws)

    else:
        raise DemandError(f"unknown-constructor:{constructor}")

    stats.identity_computations += 1
    auto.attach_signature(donor, op, spec["constants"])
    stats.semantic_signature_computations += 1
    stats.generated_materialized += 1
    cache[key] = op
    stats.note_cache(cache)
    return op


@dataclass
class GoalSearchResult:
    status: str
    operation: Any | None
    candidates_considered: int
    generated_materialized: int
    type_rejected: int
    identity_dedup: int
    depth_reached: int


def goal_search(
    *,
    target_arity: int,
    target_signature: str,
    max_depth: int,
    visit_budget: int,
    auto,
    donor,
    spec: dict[str, Any],
) -> GoalSearchResult:
    """Lazy bounded search. Stop immediately when goal behavior is witnessed.

    The goal is arity + bounded exact-Q semantic signature.  That signature is
    observational search evidence only; generated identity remains construction-
    derived and must match the eager closure result independently.
    """
    laws = list(spec["normalization_laws"])
    enabled = schemas(spec)
    ops = auto.basis_operations(spec, laws)
    by_identity = {op.identity: op for op in ops}

    for op in ops:
        auto.attach_signature(donor, op, spec["constants"])

    considered = 0
    materialized = 0
    rejected = 0
    dedup = 0

    def accept(candidate, depth):
        nonlocal considered, materialized, dedup
        considered += 1
        if considered > visit_budget:
            return "BUDGET"
        auto.attach_signature(donor, candidate, spec["constants"])
        existing = by_identity.get(candidate.identity)
        if existing is not None:
            dedup += 1
            return None
        by_identity[candidate.identity] = candidate
        materialized += 1
        if candidate.arity == target_arity and candidate.signature_sha256 == target_signature:
            return candidate
        return None

    for depth in range(1, max_depth + 1):
        # Deterministic ordering is representation/mechanism only.
        snapshot = sorted(
            by_identity.values(),
            key=lambda op: (op.depth, op.arity, op.identity),
        )

        if "bind-left-constant" in enabled:
            for dep in snapshot:
                if dep.depth + 1 != depth:
                    continue
                for constant in sorted(spec["constants"], key=lambda x: x["id"]):
                    if dep.arity != 2:
                        rejected += 1
                        continue
                    candidate = auto.bind_left(dep, constant["id"], laws)
                    result = accept(candidate, depth)
                    if result == "BUDGET":
                        return GoalSearchResult(
                            "INCOMPLETE", None, considered - 1, materialized,
                            rejected, dedup, depth
                        )
                    if result is not None:
                        return GoalSearchResult(
                            "FOUND", result, considered, materialized,
                            rejected, dedup, depth
                        )

        snapshot = sorted(
            by_identity.values(),
            key=lambda op: (op.depth, op.arity, op.identity),
        )
        if "map-right" in enabled:
            for left in snapshot:
                for right in snapshot:
                    if max(left.depth, right.depth) + 1 != depth:
                        continue
                    if left.arity != 2 or right.arity != 1:
                        rejected += 1
                        continue
                    candidate = auto.map_right(left, right, laws)
                    result = accept(candidate, depth)
                    if result == "BUDGET":
                        return GoalSearchResult(
                            "INCOMPLETE", None, considered - 1, materialized,
                            rejected, dedup, depth
                        )
                    if result is not None:
                        return GoalSearchResult(
                            "FOUND", result, considered, materialized,
                            rejected, dedup, depth
                        )

    return GoalSearchResult(
        "NOT-DERIVABLE-WITHIN-BOUND", None, considered, materialized,
        rejected, dedup, max_depth
    )


def variant(
    spec: dict[str, Any],
    *,
    remove_basis: str | None = None,
    remove_constant: str | None = None,
    disable_schema: str | None = None,
) -> dict[str, Any]:
    out = copy.deepcopy(spec)
    if remove_basis:
        out["basis_operations"] = [
            row for row in out["basis_operations"] if row["id"] != remove_basis
        ]
    if remove_constant:
        out["constants"] = [
            row for row in out["constants"] if row["id"] != remove_constant
        ]
    if disable_schema:
        out["constructor_schemas"] = [
            row for row in out["constructor_schemas"]
            if row["id"] != disable_schema
        ]
    return out


def expect_demand_failure(target, spec, auto, donor) -> str:
    try:
        derive_construction(
            target,
            auto=auto,
            donor=donor,
            spec=spec,
            cache={},
            stats=DemandStats(),
        )
    except DemandError as exc:
        return str(exc)
    raise AssertionError("demand derivation unexpectedly succeeded")


def op_certificate(auto, op) -> dict[str, Any]:
    return {
        "identity": op.identity,
        "arity": op.arity,
        "depth": op.depth,
        "expression": auto.normalize_expr(op.expression),
        "partiality": auto.normalize_cond(op.partiality),
        "signature_sha256": op.signature_sha256,
        "undefined_cases": op.undefined_cases,
        "provenance": op.provenance,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    auto = load_module(AUTO_PATH, "core_math_auto_2470")
    donor = load_module(DONOR_PATH, "core_math_growth_2433_demand")
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))

    # Same mathematical basis/schemas as #2462/#2465.
    assert {x["id"] for x in spec["basis_operations"]} == {"add", "mul", "recip"}
    assert {x["id"] for x in spec["constructor_schemas"]} == {
        "bind-left-constant", "map-right"
    }
    assert {x["id"] for x in spec["constants"]} == {"neg_one"}

    t1 = target_bind_left(target_basis("mul"), "neg_one")
    t2 = target_map_right(target_basis("add"), t1)
    t3 = target_map_right(target_basis("mul"), target_basis("recip"))
    targets = [t1, t2, t3]

    validation_signatures = auto.target_signatures(donor)
    validation = [
        ("projection-neg", 1, validation_signatures["neg"]),
        ("projection-sub", 2, validation_signatures["sub"]),
        ("projection-div", 2, validation_signatures["div"]),
    ]

    # Eager depth-3 reference: same closure as #2465 strongest layer.
    eager_spec = copy.deepcopy(spec)
    eager_spec["max_depth"] = 3
    eager_ops, eager_metrics = auto.run_closure(eager_spec, donor)
    eager_generated = [op for op in eager_ops if op.depth > 0]
    eager_by_identity = {op.identity: op for op in eager_ops}
    eager_raw_candidates = sum(row["raw_candidates"] for row in eager_metrics)
    assert len(eager_generated) == 76

    # Construction-directed cold runs.
    construction_rows = []
    constructed = []
    for target, (label, arity, expected_sig) in zip(targets, validation, strict=True):
        cache: dict[str, Any] = {}
        stats = DemandStats()
        op = derive_construction(
            target, auto=auto, donor=donor, spec=spec, cache=cache, stats=stats
        )
        assert op.identity in eager_by_identity
        assert op.signature_sha256 == expected_sig
        assert op.arity == arity
        constructed.append(op)
        construction_rows.append({
            "validation_projection": label,
            "identity": op.identity,
            "signature_sha256": op.signature_sha256,
            "generated_materialized": stats.generated_materialized,
            "constructor_visits": stats.constructor_visits,
            "identity_computations": stats.identity_computations,
            "signature_computations": stats.semantic_signature_computations,
            "cache_hits": stats.cache_hits,
            "cache_misses": stats.cache_misses,
            "peak_cache_entries": stats.peak_cache_entries,
            "unrelated_generated_materialized": 0,
        })

    # Strong dependency control: target 2 has exactly generated target 1 + itself.
    assert construction_rows[1]["generated_materialized"] == 2
    assert constructed[0].identity in {
        dep
        for proof in constructed[1].provenance
        for dep in proof.get("dependencies", [])
    }

    # Cache invariance: cold -> warm -> clear gives same semantic object.
    shared_cache: dict[str, Any] = {}
    cold_stats = DemandStats()
    cold = derive_construction(
        t2, auto=auto, donor=donor, spec=spec, cache=shared_cache, stats=cold_stats
    )
    warm_stats = DemandStats()
    warm = derive_construction(
        t2, auto=auto, donor=donor, spec=spec, cache=shared_cache, stats=warm_stats
    )
    cleared_stats = DemandStats()
    cleared = derive_construction(
        t2, auto=auto, donor=donor, spec=spec, cache={}, stats=cleared_stats
    )
    assert cold.identity == warm.identity == cleared.identity
    assert cold.signature_sha256 == warm.signature_sha256 == cleared.signature_sha256
    assert op_certificate(auto, cold) == op_certificate(auto, cleared)
    assert warm_stats.cache_hits >= 1
    assert warm_stats.generated_materialized == 0

    # Request-order invariance with a shared mechanism cache.
    order_results = []
    for order in itertools.permutations(range(3)):
        cache = {}
        identities = {}
        signatures = {}
        stats = DemandStats()
        for index in order:
            op = derive_construction(
                targets[index],
                auto=auto,
                donor=donor,
                spec=spec,
                cache=cache,
                stats=stats,
            )
            identities[index] = op.identity
            signatures[index] = op.signature_sha256
        assert [identities[i] for i in range(3)] == [op.identity for op in constructed]
        assert [signatures[i] for i in range(3)] == [
            op.signature_sha256 for op in constructed
        ]
        order_results.append({
            "order": list(order),
            "generated_materialized": stats.generated_materialized,
            "cache_hits": stats.cache_hits,
            "cache_misses": stats.cache_misses,
        })

    # Goal-directed bounded search. No target names enter the search.
    goal_rows = []
    for label, arity, signature in validation:
        result = goal_search(
            target_arity=arity,
            target_signature=signature,
            max_depth=2,
            visit_budget=100,
            auto=auto,
            donor=donor,
            spec=spec,
        )
        assert result.status == "FOUND", (label, result)
        assert result.operation is not None
        assert result.operation.identity in eager_by_identity
        assert result.operation.signature_sha256 == signature
        goal_rows.append({
            "validation_projection": label,
            "status": result.status,
            "identity": result.operation.identity,
            "candidates_considered": result.candidates_considered,
            "generated_materialized": result.generated_materialized,
            "type_rejected": result.type_rejected,
            "identity_dedup": result.identity_dedup,
            "depth_reached": result.depth_reached,
        })

    # Search exhaustion is epistemic INCOMPLETE, never false.
    sub_signature = validation[1][2]
    exhausted = goal_search(
        target_arity=2,
        target_signature=sub_signature,
        max_depth=2,
        visit_budget=1,
        auto=auto,
        donor=donor,
        spec=spec,
    )
    assert exhausted.status == "INCOMPLETE"

    # Negative dependency/schema controls.
    negative_controls = [
        ("remove-neg-one/neg", t1, variant(spec, remove_constant="neg_one")),
        ("remove-neg-one/sub", t2, variant(spec, remove_constant="neg_one")),
        ("remove-mul/neg", t1, variant(spec, remove_basis="mul")),
        ("remove-mul/div", t3, variant(spec, remove_basis="mul")),
        ("remove-add/sub", t2, variant(spec, remove_basis="add")),
        ("remove-recip/div", t3, variant(spec, remove_basis="recip")),
        (
            "disable-bind-left/neg",
            t1,
            variant(spec, disable_schema="bind-left-constant"),
        ),
        (
            "disable-map-right/sub",
            t2,
            variant(spec, disable_schema="map-right"),
        ),
        (
            "disable-map-right/div",
            t3,
            variant(spec, disable_schema="map-right"),
        ),
    ]
    negative_rows = []
    for name, target, control_spec in negative_controls:
        reason = expect_demand_failure(target, control_spec, auto, donor)
        negative_rows.append({"control": name, "status": "REJECTED", "reason": reason})

    malformed = target_map_right(target_basis("recip"), target_basis("recip"))
    malformed_reason = expect_demand_failure(malformed, spec, auto, donor)
    assert malformed_reason.startswith("type-error:")
    negative_rows.append({
        "control": "malformed-map-right-type",
        "status": "REJECTED",
        "reason": malformed_reason,
    })

    # Demand should avoid unrelated eager materialization for all three controls.
    demand_unique_ids = {op.identity for op in constructed}
    assert demand_unique_ids <= {op.identity for op in eager_generated}
    assert len(demand_unique_ids) == 3
    assert len(eager_generated) == 76

    artifact = {
        "schema": "core-math-demand-derivation/v1",
        "authority": "research-only",
        "parent_eager_closure": "#2465",
        "eager_reference": {
            "depth": 3,
            "raw_candidates": eager_raw_candidates,
            "generated_identities_materialized": len(eager_generated),
            "bounded_semantic_classes": len(
                {op.signature_sha256 for op in eager_generated}
            ),
        },
        "construction_directed": construction_rows,
        "goal_directed": goal_rows,
        "cache_control": {
            "cold_identity": cold.identity,
            "warm_identity": warm.identity,
            "cleared_identity": cleared.identity,
            "warm_cache_hits": warm_stats.cache_hits,
            "warm_generated_materialized": warm_stats.generated_materialized,
            "semantics_invariant": True,
        },
        "request_order_controls": order_results,
        "search_exhaustion": {
            "status": exhausted.status,
            "visit_budget": 1,
            "claim": "INCOMPLETE/UNKNOWN, not false",
        },
        "negative_controls": negative_rows,
        "claims": {
            "full_eager_closure_required_for_requested_controls": False,
            "cache_is_semantic_authority": False,
            "result_name_whitelist_used": False,
            "sens_core_registry_rows_required": 0,
            "construction_directed_derivation": "WITNESSED",
            "bounded_behavior_goal_search": "WITNESSED",
            "generic_property_synthesis": "NOT-YET-PROVED",
        },
        "non_conclusions": [
            "bounded behavior signatures are search goals, not semantic identity authority",
            "construction-directed demand is not generic synthesis",
            "depth-2 goal search does not establish asymptotic search complexity",
            "static mathematical closure versus durable admitted vocabulary remains a separate policy question",
            "unrequested generated operations are not declared useless or invalid",
        ],
    }

    (args.out / "demand-derivation.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Core-Math demand-derived operation construction — #2470",
        "",
        f"Eager depth-3 reference: {len(eager_generated)} generated identities; "
        f"{eager_raw_candidates} raw constructor applications.",
        "",
        "| validation projection | construction materialized | goal candidates | goal materialized | identity matches eager |",
        "|---|---:|---:|---:|---|",
    ]
    for c_row, g_row in zip(construction_rows, goal_rows, strict=True):
        report.append(
            f"| {c_row['validation_projection']} | "
            f"{c_row['generated_materialized']} | "
            f"{g_row['candidates_considered']} | "
            f"{g_row['generated_materialized']} | yes |"
        )
    report += [
        "",
        "Key controls:",
        "- SUB construction-demand derives and reuses the generated NEG-like dependency;",
        "- cold/warm/cleared cache preserves identity, signature and certificate;",
        "- all six request orders converge to the same three identities;",
        "- missing basis/constants/schemas and malformed composition fail explicitly;",
        "- bounded goal-search exhaustion returns INCOMPLETE rather than false;",
        "- no result-name whitelist and no Core/SENS registry row participates.",
        "",
        "Interpretation:",
        "the mathematical closure can be treated as a possibility space while",
        "requested operations are materialized by certificate on demand.",
        "Cache changes work, not meaning.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
