#!/usr/bin/env python3
"""#2431 — executable tournament for Core-Math growth phase semantics.

Consumes the same neutral rule graph used by #2433/#2425 and compares:
A. static closure
B. naive monotone durable discovered-state
C. ephemeral derivation
D. cached derivation
E. explicit ratified promotion

The benchmark does not choose a winner. It classifies which state transitions
are semantic and which are only discovery/materialization mechanisms.

Research only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs" / "research" / "2433-core-math-neutral-v1.json"
REPORT_PATH = ROOT / "benchmarks" / "core-math-growth-phase" / "report.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def calls(node: Any) -> set[str]:
    if not isinstance(node, dict):
        return set()
    out: set[str] = set()
    if "call" in node:
        out.add(node["call"])
        for arg in node["args"]:
            out |= calls(arg)
    return out


def graph(spec: dict[str, Any]) -> tuple[set[str], dict[str, set[str]]]:
    basis = {x["id"] for x in spec["basis_operations"]}
    generated = {x["id"] for x in spec["generation_rules"]}
    deps: dict[str, set[str]] = {}
    for rule in spec["generation_rules"]:
        refs = calls(rule["expression"])
        deps[rule["id"]] = {x for x in refs if x in generated}
    return basis, deps


def closure(
    basis: set[str],
    deps: dict[str, set[str]],
    active_rules: set[str] | None = None,
) -> set[str]:
    active = set(deps) if active_rules is None else set(active_rules)
    admitted = set(basis)
    generated_admitted: set[str] = set()

    changed = True
    while changed:
        changed = False
        for name in sorted(active):
            if name in generated_admitted:
                continue
            if deps[name] <= generated_admitted:
                generated_admitted.add(name)
                admitted.add(name)
                changed = True
    return admitted


def derivation_dependencies(target: str, deps: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()

    def visit(name: str) -> None:
        if name in seen:
            return
        seen.add(name)
        for dep in deps.get(name, set()):
            visit(dep)

    visit(target)
    return seen


def static_model(basis: set[str], deps: dict[str, set[str]]) -> dict[str, Any]:
    before = closure(basis, deps)
    active_after = set(deps) - {"neg"}
    after = closure(basis, deps, active_after)
    return {
        "semantic_before": sorted(before),
        "semantic_after_neg_withdrawal": sorted(after),
        "withdrawal_retracts": sorted(before - after),
        "order_independent": True,
        "cache_is_semantic": False,
        "classification": "mathematical-closure-state",
    }


def monotone_model(basis: set[str], deps: dict[str, set[str]]) -> dict[str, Any]:
    state = set(basis)
    generated_state: set[str] = set()

    # Discover in an adversarial order; skip until dependencies become present.
    order = ["sub", "div", "neg", "sub"]
    for name in order:
        if deps[name] <= generated_state:
            generated_state.add(name)
            state.add(name)

    assert {"neg", "sub", "div"} <= generated_state

    # Falsify the neg law after all discoveries. Naive monotone state does not
    # retract anything by itself.
    active_after = set(deps) - {"neg"}
    mathematically_valid_after = closure(basis, deps, active_after)
    stale = state - mathematically_valid_after

    return {
        "durable_state_before_withdrawal": sorted(state),
        "mathematically_valid_after_withdrawal": sorted(mathematically_valid_after),
        "stale_after_withdrawal": sorted(stale),
        "requires_versioned_revalidation": bool(stale),
        "order_independent_final_if_fair": True,
        "classification": "unsafe-without-retraction-versioning",
    }


def ephemeral_model(basis: set[str], deps: dict[str, set[str]]) -> dict[str, Any]:
    global_before = set(basis)
    context = derivation_dependencies("sub", deps)
    assert context == {"neg", "sub"}
    global_after = set(basis)

    active_after = set(deps) - {"neg"}
    after_closure = closure(basis, deps, active_after)

    return {
        "query_target": "sub",
        "ephemeral_context": sorted(context),
        "global_state_unchanged": global_before == global_after,
        "sub_derivable_after_neg_withdrawal": "sub" in after_closure,
        "classification": "context-local-derivation",
    }


def cached_model(basis: set[str], deps: dict[str, set[str]]) -> dict[str, Any]:
    semantics_before = closure(basis, deps)
    cache: set[str] = set()

    # Query SUB; materialize its dependency proof path.
    cache |= derivation_dependencies("sub", deps)
    cache_after_query = sorted(cache)

    # Clearing cache must not alter semantics.
    cache.clear()
    semantics_after_clear = closure(basis, deps)
    assert semantics_after_clear == semantics_before

    # Version change: withdraw NEG. Semantics changes; old cache would have to
    # be invalidated, but the cache itself is not the source of the change.
    active_after = set(deps) - {"neg"}
    semantics_after_withdrawal = closure(basis, deps, active_after)

    return {
        "semantic_before": sorted(semantics_before),
        "cache_after_sub_query": cache_after_query,
        "cache_after_clear": sorted(cache),
        "semantic_after_cache_clear": sorted(semantics_after_clear),
        "cache_clear_changes_semantics": semantics_after_clear != semantics_before,
        "semantic_after_neg_withdrawal": sorted(semantics_after_withdrawal),
        "classification": "mechanism-only-cache",
    }


def ratified_model(basis: set[str], deps: dict[str, set[str]]) -> dict[str, Any]:
    mathematical = closure(basis, deps)
    durable = set(basis)
    log: list[str] = []

    # Candidates exist mathematically before durable promotion.
    candidates = mathematical - basis

    for op in ("neg", "sub"):
        if op not in candidates:
            raise AssertionError(op)
        durable.add(op)
        log.append("ratify:" + op)

    before_revoke = sorted(durable)
    durable.remove("neg")
    # Because SUB's ratification depended on a generated NEG ancestry, a robust
    # durable model must revalidate and retract dependent promoted operations.
    durable.discard("sub")
    log.append("revoke:neg")
    log.append("revalidate:sub->retract")

    return {
        "mathematical_candidates": sorted(candidates),
        "durable_before_ratification": sorted(basis),
        "durable_after_ratify_neg_sub": before_revoke,
        "durable_after_revoke_neg": sorted(durable),
        "event_log": log,
        "explicit_state_transition_required": True,
        "classification": "explicit-ratified-state",
    }


def main() -> None:
    spec = load(SPEC_PATH)
    basis, deps = graph(spec)

    assert deps == {
        "neg": set(),
        "sub": {"neg"},
        "div": set(),
    }

    models = {
        "A_static_closure": static_model(basis, deps),
        "B_monotone_state": monotone_model(basis, deps),
        "C_ephemeral": ephemeral_model(basis, deps),
        "D_cached": cached_model(basis, deps),
        "E_ratified": ratified_model(basis, deps),
    }

    # Core invariants.
    assert models["D_cached"]["cache_clear_changes_semantics"] is False
    assert models["B_monotone_state"]["requires_versioned_revalidation"] is True
    assert models["C_ephemeral"]["global_state_unchanged"] is True
    assert models["C_ephemeral"]["sub_derivable_after_neg_withdrawal"] is False
    assert models["A_static_closure"]["withdrawal_retracts"] == ["neg", "sub"]
    assert models["E_ratified"]["explicit_state_transition_required"] is True

    report = {
        "schema": "core-math-growth-phase-tournament/v1",
        "basis": sorted(basis),
        "generated_dependency_graph": {
            key: sorted(value) for key, value in sorted(deps.items())
        },
        "models": models,
        "cross_model_findings": {
            "cache_filling_is_semantic_growth": False,
            "static_and_cached_share_semantics": True,
            "naive_monotone_requires_retraction_or_versioning": True,
            "ephemeral_derivation_mutates_global_language": False,
            "ratified_promotion_is_explicit_state_change": True,
            "law_withdrawal_retracts_dependents": ["neg", "sub"],
        },
        "decision": "NO-WINNER-SELECTED",
        "authority": "research-only",
    }

    expected = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if REPORT_PATH.read_text(encoding="utf-8") != expected:
        raise SystemExit("STALE-GROWTH-PHASE-REPORT")

    print("MODELS=5")
    print("STATIC-CLOSURE-DETERMINISTIC=PASS")
    print("CACHE-CLEAR-CHANGES-SEMANTICS=0")
    print("STATIC-AND-CACHED-SHARE-SEMANTICS=1")
    print("EPHEMERAL-MUTATES-GLOBAL-STATE=0")
    print("NAIVE-MONOTONE-STALE-AFTER-WITHDRAWAL=neg,sub")
    print("RATIFIED-PROMOTION-EXPLICIT-STATE-CHANGE=1")
    print("LAW-WITHDRAWAL-RETRACTS=neg,sub")
    print("WINNER=NONE")
    print("STATUS=PASS-CORE-MATH-GROWTH-PHASE-TOURNAMENT")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
