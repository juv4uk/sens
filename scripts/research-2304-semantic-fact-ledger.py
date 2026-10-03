#!/usr/bin/env python3
"""#2304 — machine-check independent semantic fact accounting.

Research-only. The ledger compares candidate semantic architectures without
promoting any production identity or domain allocation.

Key discipline:
- facts are model-independent assertions;
- "root" vs "derived" is a role inside a model, not a fact kind;
- UNKNOWN contributes to an upper bound, never silently to zero;
- a derived fact must be reachable from declared independent/unknown facts;
- proof/certificate facts are reported separately from semantic-fact totals.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ALLOWED_KINDS = {
    "operation",
    "law",
    "carrier-premise",
    "constant-premise",
    "normalization",
    "equivalence",
    "partiality",
    "instance-map",
    "residue",
    "factor",
    "certificate",
}
ALLOWED_CLASSES = {"semantic", "proof", "mechanism"}
ALLOWED_BINARY_PARTICIPATION = {"B0", "B1", "B2", "B3"}

ALLOWED_STATUS = {
    "confirmed",
    "bounded-confirmed",
    "candidate",
    "bounded-negative",
    "falsified",
    "unknown",
}


def fail(message: str) -> None:
    raise SystemExit(f"SEMANTIC-FACT-LEDGER=FAIL\n{message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    require(data.get("version") == 1, "unsupported ledger version")
    classes = data.get("binary_participation_classes", {})
    require(set(classes) == ALLOWED_BINARY_PARTICIPATION, "binary participation class table must define exactly B0..B3")
    require(
        bool(data.get("binary_participation_accounting_rule", "").strip()),
        "missing binary participation accounting rule",
    )
    return data


def validate_fact(fact: dict[str, Any]) -> None:
    required = {
        "id",
        "kind",
        "accounting_class",
        "claim",
        "domain",
        "applies_to",
        "dependencies",
        "witness",
        "status",
        "provenance",
        "counterexample_class",
        "independence_evidence",
    }
    missing = sorted(required - fact.keys())
    require(not missing, f"{fact.get('id', '<unknown>')}: missing fields {missing}")
    require(fact["kind"] in ALLOWED_KINDS, f"{fact['id']}: invalid kind {fact['kind']}")
    require(
        fact["accounting_class"] in ALLOWED_CLASSES,
        f"{fact['id']}: invalid accounting_class {fact['accounting_class']}",
    )
    require(fact["status"] in ALLOWED_STATUS, f"{fact['id']}: invalid status {fact['status']}")
    require(isinstance(fact["dependencies"], list), f"{fact['id']}: dependencies must be a list")
    require(isinstance(fact["applies_to"], list), f"{fact['id']}: applies_to must be a list")
    require(bool(fact["claim"].strip()), f"{fact['id']}: empty claim")
    require(bool(fact["witness"].strip()), f"{fact['id']}: empty witness")
    require(
        bool(fact["independence_evidence"].strip()),
        f"{fact['id']}: missing independence evidence",
    )


def model_summary(
    model: dict[str, Any],
    facts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    binary_participation = model.get("binary_participation")
    require(
        binary_participation in ALLOWED_BINARY_PARTICIPATION,
        f"{model.get('id', '<unknown>')}: invalid/missing binary_participation",
    )
    independent = model.get("independent_facts", [])
    unknown = model.get("unknown_facts", [])
    derived = model.get("derived_facts", [])
    covers = model.get("covers", [])

    require(len(independent) == len(set(independent)), f"{model['id']}: duplicate independent fact")
    require(len(unknown) == len(set(unknown)), f"{model['id']}: duplicate unknown fact")
    require(not (set(independent) & set(unknown)), f"{model['id']}: fact both independent and unknown")

    referenced = set(independent) | set(unknown) | set(covers)
    for row in derived:
        require("target" in row and "via" in row, f"{model['id']}: malformed derivation row")
        require(isinstance(row["via"], list) and row["via"], f"{model['id']}: empty derivation path")
        referenced.add(row["target"])
        referenced.update(row["via"])

    missing = sorted(referenced - facts.keys())
    require(not missing, f"{model['id']}: references unknown facts {missing}")

    # A model must pay for all dependencies of any declared independent/unknown fact.
    paid_or_unknown = set(independent) | set(unknown)
    derived_targets = {row["target"] for row in derived}
    available_eventually = paid_or_unknown | derived_targets

    for fact_id in independent + unknown:
        missing_deps = sorted(set(facts[fact_id]["dependencies"]) - available_eventually)
        require(
            not missing_deps,
            f"{model['id']}: {fact_id} hides dependencies {missing_deps}",
        )

    # Resolve derivations as a small proof graph. UNKNOWN inputs are allowed but
    # they remain visible in the accounting interval.
    available = set(paid_or_unknown)
    remaining = list(derived)
    while remaining:
        progressed = False
        next_remaining = []
        for row in remaining:
            if set(row["via"]) <= available:
                available.add(row["target"])
                progressed = True
            else:
                next_remaining.append(row)
        if not progressed:
            blocked = [
                {
                    "target": row["target"],
                    "missing": sorted(set(row["via"]) - available),
                }
                for row in next_remaining
            ]
            fail(f"{model['id']}: unresolved derivations {blocked}")
        remaining = next_remaining

    missing_coverage = sorted(set(covers) - available)
    require(not missing_coverage, f"{model['id']}: uncovered semantic facts {missing_coverage}")

    semantic_independent = [
        fact_id
        for fact_id in independent
        if facts[fact_id]["accounting_class"] == "semantic"
    ]
    semantic_unknown = [
        fact_id
        for fact_id in unknown
        if facts[fact_id]["accounting_class"] == "semantic"
    ]

    by_kind = Counter(facts[fact_id]["kind"] for fact_id in semantic_independent)
    unknown_by_kind = Counter(facts[fact_id]["kind"] for fact_id in semantic_unknown)

    lower = len(semantic_independent)
    upper = lower + len(semantic_unknown)
    expected = model.get("expected_semantic_fact_interval")
    if expected is not None:
        require(
            expected == [lower, upper],
            f"{model['id']}: interval drift expected={expected} actual={[lower, upper]}",
        )

    return {
        "id": model["id"],
        "corpus": model.get("corpus", ""),
        "binary_participation": binary_participation,
        "semantic_fact_lower_bound": lower,
        "unknown_semantic_facts": len(semantic_unknown),
        "semantic_fact_upper_bound": upper,
        "independent_by_kind": dict(sorted(by_kind.items())),
        "unknown_by_kind": dict(sorted(unknown_by_kind.items())),
        "derived_fact_count": len(derived),
        "covered_fact_count": len(covers),
        "independent_fact_ids": semantic_independent,
        "unknown_fact_ids": semantic_unknown,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "ledger",
        nargs="?",
        default="benchmarks/generator-economy/semantic-fact-ledger.json",
    )
    parser.add_argument("--summary-json", default="")
    args = parser.parse_args()

    data = load(Path(args.ledger))
    facts_list = data.get("facts", [])
    models = data.get("models", [])
    require(facts_list, "no facts")
    require(models, "no models")

    ids = [fact.get("id") for fact in facts_list]
    require(len(ids) == len(set(ids)), "duplicate fact id")

    facts: dict[str, dict[str, Any]] = {}
    for fact in facts_list:
        validate_fact(fact)
        facts[fact["id"]] = fact

    model_ids = [model.get("id") for model in models]
    require(len(model_ids) == len(set(model_ids)), "duplicate model id")

    known_models = set(model_ids)
    for fact in facts_list:
        bad = sorted(set(fact["applies_to"]) - known_models)
        require(not bad, f"{fact['id']}: applies_to unknown models {bad}")
        for dep in fact["dependencies"]:
            require(dep in facts, f"{fact['id']}: dependency {dep} does not exist")

    summaries = [model_summary(model, facts) for model in models]

    proof_facts = [
        fact["id"] for fact in facts_list if fact["accounting_class"] == "proof"
    ]
    mechanism_facts = [
        fact["id"] for fact in facts_list if fact["accounting_class"] == "mechanism"
    ]

    output = {
        "ledger_version": data["version"],
        "accounting_unit": data["accounting_unit"],
        "models": summaries,
        "proof_fact_count": len(proof_facts),
        "proof_fact_ids": proof_facts,
        "mechanism_fact_count": len(mechanism_facts),
        "mechanism_fact_ids": mechanism_facts,
    }

    if args.summary_json:
        target = Path(args.summary_json)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    print("SEMANTIC-FACT-LEDGER=PASS")
    print("model\tbinary\tlower\tunknown\tupper\tderived")
    for row in summaries:
        print(
            f"{row['id']}\t{row['binary_participation']}\t"
            f"{row['semantic_fact_lower_bound']}\t{row['unknown_semantic_facts']}\t"
            f"{row['semantic_fact_upper_bound']}\t{row['derived_fact_count']}"
        )
    print(f"proof-facts\t{len(proof_facts)}")
    print("RULE=unknown-is-visible-not-zero")
    print("RULE=root-vs-derived-is-model-role-not-fact-kind")
    print("RULE=proof-facts-are-separate-from-semantic-facts")
    print("RULE=binary-participation-does-not-change-semantic-fact-count")


if __name__ == "__main__":
    main()
