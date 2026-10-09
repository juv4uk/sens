#!/usr/bin/env python3
"""#2463 — Core-Math autonomous closure scaling benchmark.

Stacked on #2462.  Sweeps depth 0..3 under three pruning regimes:

A. typed candidate expansion, no identity dedup;
B. construction identity dedup, no AC equivalence;
C. validated ADD/MUL AC normalization + identity dedup.

No operation-name whitelist participates in generation.
"""

from __future__ import annotations

import argparse
import copy
import csv
import importlib.util
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


def generated(ops):
    return [op for op in ops if op.depth > 0]


def cumulative_stats(auto, ops, depth: int) -> dict[str, int]:
    subset = [op for op in ops if 0 < op.depth <= depth]
    signatures = {op.signature_sha256 for op in subset}
    provenance_bytes = sum(
        len(auto.canonical_json(op.provenance).encode("utf-8"))
        for op in subset
    )
    verification_cases = sum(
        2 * (len(auto.CORPUS) ** op.arity)
        for op in subset
    )
    return {
        "cumulative_generated": len(subset),
        "semantic_signature_classes": len(signatures),
        "observational_duplicates": len(subset) - len(signatures),
        "provenance_bytes": provenance_bytes,
        "two_model_final_verification_cases": verification_cases,
    }


def run_no_dedup(auto, spec: dict[str, Any], donor):
    laws = list(spec["normalization_laws"])
    schemas = {x["id"] for x in spec["constructor_schemas"]}
    ops = auto.basis_operations(spec, laws)
    for op in ops:
        auto.attach_signature(donor, op, spec["constants"])

    metrics = []
    max_depth = int(spec["max_depth"])
    for depth in range(1, max_depth + 1):
        snapshot = list(ops)
        bind_raw = bind_reject = bind_valid = 0
        map_raw = map_reject = map_valid = 0
        new_ops = []

        if "bind-left-constant" in schemas:
            for dep in snapshot:
                if dep.depth + 1 != depth:
                    continue
                for constant in spec["constants"]:
                    bind_raw += 1
                    if dep.arity != 2:
                        bind_reject += 1
                        continue
                    candidate = auto.bind_left(dep, constant["id"], laws)
                    auto.attach_signature(donor, candidate, spec["constants"])
                    new_ops.append(candidate)
                    bind_valid += 1

        ops.extend(new_ops)
        snapshot = list(ops)
        map_new = []

        if "map-right" in schemas:
            for left in snapshot:
                for right in snapshot:
                    if max(left.depth, right.depth) + 1 != depth:
                        continue
                    map_raw += 1
                    if left.arity != 2 or right.arity != 1:
                        map_reject += 1
                        continue
                    candidate = auto.map_right(left, right, laws)
                    auto.attach_signature(donor, candidate, spec["constants"])
                    map_new.append(candidate)
                    map_valid += 1

        ops.extend(map_new)
        at_depth = [op for op in ops if op.depth == depth]
        metrics.append({
            "depth": depth,
            "raw_candidates": bind_raw + map_raw,
            "type_rejected": bind_reject + map_reject,
            "identity_dedup": 0,
            "new_unique_identities": len(at_depth),
            "bind_raw": bind_raw,
            "bind_valid": bind_valid,
            "map_right_raw": map_raw,
            "map_right_valid": map_valid,
        })

    return ops, metrics


def run_dedup(auto, spec: dict[str, Any], donor, *, ac: bool):
    old_ac = set(auto.AC_OPS)
    try:
        auto.AC_OPS = {"add", "mul"} if ac else set()
        local = copy.deepcopy(spec)
        if not ac:
            local["normalization_laws"] = []
        return auto.run_closure(local, donor)
    finally:
        auto.AC_OPS = old_ac


def rows_for_layer(auto, layer: str, ops, metrics, targets):
    rows = []
    matches = auto.find_matches(ops, targets)
    for depth in range(0, max([op.depth for op in ops]) + 1):
        if depth == 0:
            row = {
                "depth": 0,
                "raw_candidates": 0,
                "type_rejected": 0,
                "identity_dedup": 0,
                "new_unique_identities": 0,
            }
        else:
            row = metrics[depth - 1]
        cumulative = cumulative_stats(auto, ops, depth)
        target_hits = sum(
            1 for values in matches.values()
            if any(op.depth <= depth for op in values)
        )
        rows.append({
            "layer": layer,
            "depth": depth,
            "raw_candidates": row["raw_candidates"],
            "type_rejected": row["type_rejected"],
            "identity_dedup": row["identity_dedup"],
            "new_identities_or_occurrences": row["new_unique_identities"],
            **cumulative,
            "validation_target_classes_hit": target_hits,
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-depth", type=int, default=3)
    args = ap.parse_args()
    if not 1 <= args.max_depth <= 4:
        ap.error("--max-depth must be 1..4 for this bounded benchmark")
    args.out.mkdir(parents=True, exist_ok=True)

    auto = load_module(AUTO_PATH, "core_math_auto_2460_scaling")
    donor = load_module(DONOR_PATH, "core_math_growth_2433_scaling")
    base_spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    base_spec["max_depth"] = args.max_depth
    targets = auto.target_signatures(donor)

    # A: keep every valid constructor occurrence.
    ops_a, metrics_a = run_no_dedup(auto, copy.deepcopy(base_spec), donor)

    # B: construction identity dedup but no AC equality.
    ops_b, metrics_b = run_dedup(auto, copy.deepcopy(base_spec), donor, ac=False)

    # C: validated AC laws + identity dedup.
    ops_c, metrics_c = run_dedup(auto, copy.deepcopy(base_spec), donor, ac=True)

    rows = (
        rows_for_layer(auto, "A-type-only-no-dedup", ops_a, metrics_a, targets)
        + rows_for_layer(auto, "B-construction-identity", ops_b, metrics_b, targets)
        + rows_for_layer(auto, "C-validated-AC-identity", ops_c, metrics_c, targets)
    )

    # Enumeration-order independence for the strongest current layer.
    reversed_spec = copy.deepcopy(base_spec)
    reversed_spec["basis_operations"] = list(reversed(reversed_spec["basis_operations"]))
    reversed_spec["constants"] = list(reversed(reversed_spec["constants"]))
    reversed_spec["constructor_schemas"] = list(reversed(reversed_spec["constructor_schemas"]))
    rev_ops, _ = run_dedup(auto, reversed_spec, donor, ac=True)
    assert {op.identity for op in ops_c} == {op.identity for op in rev_ops}
    assert {op.signature_sha256 for op in ops_c} == {op.signature_sha256 for op in rev_ops}

    # Both models are checked inside attach_signature for every candidate.
    # All three layers must still discover the target validation classes.
    for label, ops in [("A", ops_a), ("B", ops_b), ("C", ops_c)]:
        matches = auto.find_matches(ops, targets)
        assert all(matches[name] for name in ("neg", "sub", "div")), label

    with (args.out / "scaling.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    # Per-constructor branching comes from the no-dedup layer, where no
    # canonicalization hides occurrences.
    branch_rows = []
    for row in metrics_a:
        branch_rows.append({
            "depth": row["depth"],
            "bind_left_raw": row["bind_raw"],
            "bind_left_valid": row["bind_valid"],
            "map_right_raw": row["map_right_raw"],
            "map_right_valid": row["map_right_valid"],
        })
    with (args.out / "branching.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(branch_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(branch_rows)

    final = {
        layer: next(
            row for row in rows
            if row["layer"] == layer and row["depth"] == args.max_depth
        )
        for layer in {
            "A-type-only-no-dedup",
            "B-construction-identity",
            "C-validated-AC-identity",
        }
    }

    artifact = {
        "schema": "core-math-closure-scaling/v1",
        "authority": "research-only",
        "max_depth": args.max_depth,
        "layers": final,
        "enumeration_order_independent_layer_C": True,
        "branching": branch_rows,
        "non_conclusions": [
            "depth-3 scaling does not establish asymptotic complexity",
            "bounded semantic signatures are observational evidence only",
            "non-target operations are not automatically useless or admissible",
            "no operation-name whitelist participates in pruning",
            "no new Core-Math law is admitted by this benchmark",
        ],
    }
    (args.out / "scaling.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Core-Math autonomous closure scaling — #2463",
        "",
        f"Depth sweep: 0..{args.max_depth}",
        "",
        "| layer | cumulative generated | signature classes | observational duplicates | target classes hit |",
        "|---|---:|---:|---:|---:|",
    ]
    for layer in [
        "A-type-only-no-dedup",
        "B-construction-identity",
        "C-validated-AC-identity",
    ]:
        row = final[layer]
        report.append(
            f"| {layer} | {row['cumulative_generated']} | "
            f"{row['semantic_signature_classes']} | "
            f"{row['observational_duplicates']} | "
            f"{row['validation_target_classes_hit']} |"
        )

    report += [
        "",
        "Per-depth strongest-layer growth:",
        "",
        "| depth | raw | type rejects | identity dedup | new identities | cumulative |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        if row["layer"] != "C-validated-AC-identity":
            continue
        report.append(
            f"| {row['depth']} | {row['raw_candidates']} | "
            f"{row['type_rejected']} | {row['identity_dedup']} | "
            f"{row['new_identities_or_occurrences']} | "
            f"{row['cumulative_generated']} |"
        )

    report += [
        "",
        "Layer C is enumeration-order independent on the bounded sweep.",
        "Every generated candidate was executed by both exact-Q models.",
        "No useful-name whitelist is used.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
