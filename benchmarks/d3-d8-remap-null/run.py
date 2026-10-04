#!/usr/bin/env python3
"""#3049 S1: adversarial null ensembles for the merged #3043 D3/D4 scorer.

The scorer and semantic oracle are imported directly from
benchmarks/d3-d8-remap-solver/run.py. Candidate maps and null maps therefore
receive exactly the same semantic scoring code.

This is the bounded D3/D4 calibration layer. It is designed to extend to the
504-row #3051 corpus without changing the scoring contract.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import random
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
SOLVER_PATH = ROOT / "benchmarks" / "d3-d8-remap-solver" / "run.py"
FIXTURE_PATH = ROOT / "benchmarks" / "d3-d8-remap-solver" / "d3-d4-fixture.json"

METRIC_DIRECTION = {
    "law_edges_hit": "higher",
    "covered_residents": "higher",
    "independent_roots": "lower",
    "exception_facts": "lower",
    "certificate_bits": "lower",
    "derivation_depth_max": "lower",
    "unexplained_residents": "lower",
}


def load_solver():
    spec = importlib.util.spec_from_file_location("remap_solver_3043_null", SOLVER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("empty sample")
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def hamming(a: str, b: str) -> int:
    assert len(a) == len(b)
    return sum(x != y for x, y in zip(a, b, strict=True))


def map_bit_hamming(current: dict[str, str], candidate: dict[str, str]) -> int:
    total = 0
    for rid, bits in current.items():
        other = candidate[rid]
        if len(bits) != len(other):
            # Cross-width moves are intentionally much larger than a local
            # same-width perturbation; encode width change explicitly.
            total += max(len(bits), len(other)) + abs(len(bits) - len(other))
        else:
            total += hamming(bits, other)
    return total


def ids_by_domain(fixture: dict[str, Any], domain: str) -> list[str]:
    return [row["id"] for row in fixture["domains"][domain]["residents"]]


def assign(ids: list[str], slots: list[str], rng: random.Random) -> dict[str, str]:
    out = slots[:]
    rng.shuffle(out)
    return dict(zip(ids, out, strict=True))


def n0_global_capacity(
    solver, fixture: dict[str, Any], rng: random.Random
) -> dict[str, str]:
    """Shuffle residents across D3/D4 while preserving 8/16 coordinate capacity."""
    all_ids = ids_by_domain(fixture, solver.D3) + ids_by_domain(fixture, solver.D4)
    shuffled_ids = all_ids[:]
    rng.shuffle(shuffled_ids)
    d3_ids = shuffled_ids[:8]
    d4_ids = shuffled_ids[8:]
    return {
        **assign(d3_ids, solver.coords(3), rng),
        **assign(d4_ids, solver.coords(4), rng),
    }


def n1_within_domain(
    solver, fixture: dict[str, Any], rng: random.Random
) -> dict[str, str]:
    return {
        **assign(ids_by_domain(fixture, solver.D3), solver.coords(3), rng),
        **assign(ids_by_domain(fixture, solver.D4), solver.coords(4), rng),
    }


def selector_classes(solver, fixture: dict[str, Any]):
    relation = solver.relation_by_id(fixture, solver.SELECTOR_LAW)
    roots = sorted({edge["parent"] for edge in relation["edges"]})
    children = sorted({edge["child"] for edge in relation["edges"]})
    all_ids = ids_by_domain(fixture, solver.D3) + ids_by_domain(fixture, solver.D4)
    residue = [rid for rid in all_ids if rid not in set(roots + children)]
    return relation, roots, children, residue


def n2_family_preserving(
    solver, fixture: dict[str, Any], rng: random.Random
) -> dict[str, str]:
    """Preserve the selector generator shape but freely relocate the family."""
    relation, roots, children, residue = selector_classes(solver, fixture)
    d3_slots = solver.coords(3)
    chosen_roots = rng.sample(d3_slots, 2)
    rng.shuffle(chosen_roots)

    mapping: dict[str, str] = dict(zip(roots, chosen_roots, strict=True))
    edge_by_parent_delta = {
        (edge["parent"], edge["delta"]): edge["child"]
        for edge in relation["edges"]
    }

    # Global role-bit orientation may flip; this preserves the abstract
    # two-factor family law while testing that absolute polarity is not forced.
    flip = rng.choice([False, True])
    used_children: set[str] = set()
    for root_id in roots:
        root_bits = mapping[root_id]
        for delta in ["0", "1"]:
            child_id = edge_by_parent_delta[(root_id, delta)]
            placed_delta = str(1 - int(delta)) if flip else delta
            child_bits = root_bits + placed_delta
            mapping[child_id] = child_bits
            used_children.add(child_bits)

    current = solver.current_map(fixture)
    d3_residue = [rid for rid in residue if len(current[rid]) == 3]
    d4_residue = [rid for rid in residue if len(current[rid]) == 4]
    free_d3 = [x for x in solver.coords(3) if x not in set(chosen_roots)]
    free_d4 = [x for x in solver.coords(4) if x not in used_children]
    mapping.update(assign(d3_residue, free_d3, rng))
    mapping.update(assign(d4_residue, free_d4, rng))
    return mapping


def n3_root_preserving_suffix_scramble(
    solver, fixture: dict[str, Any], rng: random.Random
) -> dict[str, str]:
    current = solver.current_map(fixture)
    relation, roots, children, _ = selector_classes(solver, fixture)
    mapping = dict(current)

    # Keep semantic roots fixed at CURRENT coordinates, but randomly assign the
    # four semantic children to the four corresponding prefix slots.
    slots = sorted(
        current[edge["parent"]] + edge["delta"]
        for edge in relation["edges"]
    )
    shuffled = slots[:]
    rng.shuffle(shuffled)
    for rid, bits in zip(children, shuffled, strict=True):
        mapping[rid] = bits
    return mapping


def n4_degree_preserving_graph_relabel(
    solver, fixture: dict[str, Any], rng: random.Random
) -> dict[str, str]:
    """Relabel residents inside semantic graph degree classes."""
    current = solver.current_map(fixture)
    _, roots, children, residue = selector_classes(solver, fixture)
    mapping = dict(current)

    def permute_ids(ids: list[str]) -> None:
        slots = [current[rid] for rid in ids]
        rng.shuffle(slots)
        for rid, bits in zip(ids, slots, strict=True):
            mapping[rid] = bits

    permute_ids(roots)
    permute_ids(children)
    d3_residue = [rid for rid in residue if len(current[rid]) == 3]
    d4_residue = [rid for rid in residue if len(current[rid]) == 4]
    permute_ids(d3_residue)
    permute_ids(d4_residue)
    return mapping


def hypercube_edges(bits: list[str]) -> list[tuple[str, str]]:
    out = []
    for i, a in enumerate(bits):
        for b in bits[i + 1 :]:
            if hamming(a, b) == 1:
                out.append((a, b))
    return out


def n5_fixed_hamming(
    solver, fixture: dict[str, Any], rng: random.Random
) -> dict[str, str]:
    current = solver.current_map(fixture)
    mapping = dict(current)
    reverse = {bits: rid for rid, bits in current.items()}

    # One distance-1 coordinate transposition in each domain. Each swap moves
    # two residents by one bit => total map bit-Hamming distance exactly four.
    d3_edge = rng.choice(hypercube_edges(solver.coords(3)))
    d4_edge = rng.choice(hypercube_edges(solver.coords(4)))
    for a, b in [d3_edge, d4_edge]:
        ra, rb = reverse[a], reverse[b]
        mapping[ra], mapping[rb] = b, a

    assert map_bit_hamming(current, mapping) == 4
    return mapping


def score_mapping(solver, fixture: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    return solver.selector_score(mapping, fixture)


def summarize_metric(observed: float, values: list[float], direction: str) -> dict[str, Any]:
    mean = statistics.fmean(values)
    median = statistics.median(values)
    stdev = statistics.pstdev(values)
    if direction == "higher":
        favorable = sum(value >= observed for value in values)
    else:
        favorable = sum(value <= observed for value in values)
    # Plus-one empirical correction keeps zero-probability claims out of a
    # finite adversarial calibration.
    p_empirical = (favorable + 1) / (len(values) + 1)
    effect = None if stdev == 0 else (observed - mean) / stdev
    return {
        "observed": observed,
        "null_mean": mean,
        "null_median": median,
        "null_p95": percentile(values, 0.95),
        "null_p99": percentile(values, 0.99),
        "favorable_direction": direction,
        "favorable_or_better_count": favorable,
        "empirical_exceedance_rate_plus1": p_empirical,
        "standardized_effect_observed_minus_mean": effect,
    }


def run_ensemble(
    solver,
    fixture: dict[str, Any],
    name: str,
    generator: Callable,
    *,
    seed: int,
    samples: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    observed_map = solver.current_map(fixture)
    observed = score_mapping(solver, fixture, observed_map)
    false_law = solver.relation_by_id(fixture, solver.FALSE_LAW)

    score_rows: list[dict[str, Any]] = []
    hamming_values: list[int] = []
    false_accepted = 0

    for _ in range(samples):
        candidate = generator(solver, fixture, rng)
        assert len(candidate) == 24
        assert len(set(candidate.values())) == 24
        score = score_mapping(solver, fixture, candidate)
        score_rows.append(score)
        hamming_values.append(map_bit_hamming(observed_map, candidate))
        false_accepted += solver.accepted_hits(candidate, false_law)

    assert false_accepted == 0

    metrics = {}
    for metric, direction in METRIC_DIRECTION.items():
        values = [float(row[metric]) for row in score_rows]
        metrics[metric] = summarize_metric(float(observed[metric]), values, direction)

    hist = Counter(row["law_edges_hit"] for row in score_rows)
    return {
        "ensemble": name,
        "seed": seed,
        "samples": samples,
        "same_scorer": "benchmarks/d3-d8-remap-solver/run.py::selector_score",
        "metrics": metrics,
        "selector_hit_histogram": {str(k): v for k, v in sorted(hist.items())},
        "map_bit_hamming": {
            "min": min(hamming_values),
            "median": statistics.median(hamming_values),
            "max": max(hamming_values),
        },
        "false_semantic_law_accepted_hits": false_accepted,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--samples", type=int, default=4096)
    ap.add_argument("--seed", type=int, default=3049)
    args = ap.parse_args()
    if args.samples < 1000:
        ap.error("--samples must be >= 1000")
    args.out.mkdir(parents=True, exist_ok=True)

    solver = load_solver()
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    # Re-run the merged candidate scorer first. This prevents a null harness
    # from silently drifting away from the candidate implementation.
    merged_result = solver.run_solver(fixture, seed=3043, samples=4096)
    observed = merged_result["current_score"]
    assert observed["law_edges_hit"] == 4

    generators = [
        ("N0-global-capacity", n0_global_capacity),
        ("N1-within-domain", n1_within_domain),
        ("N2-family-preserving", n2_family_preserving),
        ("N3-root-preserving-suffix-scramble", n3_root_preserving_suffix_scramble),
        ("N4-degree-preserving-graph-relabel", n4_degree_preserving_graph_relabel),
        ("N5-fixed-bit-hamming-4", n5_fixed_hamming),
    ]

    ensembles = []
    for index, (name, generator) in enumerate(generators):
        ensembles.append(
            run_ensemble(
                solver,
                fixture,
                name,
                generator,
                seed=args.seed + index * 1009,
                samples=args.samples,
            )
        )

    # N5 is a strict construction invariant.
    n5 = next(x for x in ensembles if x["ensemble"] == "N5-fixed-bit-hamming-4")
    assert n5["map_bit_hamming"] == {"min": 4, "median": 4.0, "max": 4}

    # Family-preserving null intentionally preserves the abstract selector
    # family. Depending on global role polarity, raw append-bit orientation may
    # score either all 4 or 0; this is a conditional null, not a generic random map.
    n2_hist = next(x for x in ensembles if x["ensemble"] == "N2-family-preserving")[
        "selector_hit_histogram"
    ]
    assert set(n2_hist).issubset({"0", "4"})

    tested_hypotheses = len(ensembles) * len(METRIC_DIRECTION)

    artifact = {
        "schema": "d3-d8-remap-null-s1/v1",
        "authority": "research-only",
        "candidate_scorer": "merged #3056 / #3043 S1 scorer",
        "fixture": "D3/D4 24 resident S1 corpus",
        "observed_current_score": observed,
        "ensembles": ensembles,
        "multiple_testing": {
            "reported_metric_ensemble_comparisons": tested_hypotheses,
            "formal_significance_claim": False,
            "purpose": "adversarial calibration only",
        },
        "mandatory_controls": {
            "false_prefix_semantic_law": "accepted hits remain zero in every ensemble",
            "label_erasure": "inherited merged #3056 control",
            "domain_separation": "#2508 standing guard; no cross-domain semantic score without typed relation",
            "go_return_anti_law": {
                "ref": "#3042",
                "status": "DEFERRED-TO-FULL-ATLAS",
                "reason": "GO/RETURN are outside the current 24-row D3/D4 fixture; no synthetic resident is invented",
            },
        },
        "full_504_extension": {
            "stable_corpus": "#3051 / PR #3061",
            "policy": "same scorer/null contract; provenance-missing rows stay pinned",
        },
        "non_conclusions": [
            "S1 D3/D4 null statistics do not establish full D3-D8 significance",
            "family-preserving conditional nulls test coordinate polarity/absolute placement, not semantic-law existence",
            "empirical exceedance rates are bounded calibration, not formal p-values",
            "no production coordinate is changed",
        ],
    }

    (args.out / "null-ensembles.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # Compact TSV for the primary law-coverage metric.
    lines = [
        "ensemble\tsamples\tobserved_hits\tnull_mean\tnull_median\tnull_p95\tnull_p99\tempirical_exceedance_plus1\thamming_min\thamming_median\thamming_max"
    ]
    for row in ensembles:
        m = row["metrics"]["law_edges_hit"]
        h = row["map_bit_hamming"]
        lines.append(
            "\t".join(
                map(
                    str,
                    [
                        row["ensemble"],
                        row["samples"],
                        m["observed"],
                        m["null_mean"],
                        m["null_median"],
                        m["null_p95"],
                        m["null_p99"],
                        m["empirical_exceedance_rate_plus1"],
                        h["min"],
                        h["median"],
                        h["max"],
                    ],
                )
            )
        )
    (args.out / "selector-null.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = [
        "# D3/D4 remap null ensemble — #3049",
        "",
        f"Same merged scorer as #3056. Samples per ensemble: **{args.samples:,}**.",
        "",
        "| ensemble | observed selector hits | null mean | p95 | p99 | empirical >= observed |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in ensembles:
        m = row["metrics"]["law_edges_hit"]
        report.append(
            f"| {row['ensemble']} | {m['observed']:.0f} | {m['null_mean']:.4f} | "
            f"{m['null_p95']:.2f} | {m['null_p99']:.2f} | "
            f"{m['empirical_exceedance_rate_plus1']:.6f} |"
        )

    report += [
        "",
        f"Reported metric×ensemble comparisons: **{tested_hypotheses}**.",
        "No formal significance claim is made; this is adversarial calibration.",
        "",
        "Controls:",
        "- intentionally false semantic prefix law receives 0 accepted hits in every null map;",
        "- N5 maps are exactly bit-Hamming distance 4 from CURRENT;",
        "- #2508 domain firewall remains mandatory;",
        "- #3042 GO/RETURN anti-law is explicitly deferred until the full semantic corpus includes those residents; it is not fabricated into D3/D4.",
        "",
        "Interpretation:",
        "candidate and null maps now share one scorer. Coordinate laws must beat matched legal geometry,",
        "not merely look regular on CURRENT.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
