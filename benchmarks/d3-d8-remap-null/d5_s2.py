#!/usr/bin/env python3
"""#3049 D5 S2: matched null calibration for the #3068 multilaw scorer.

No semantic relation is defined here. The exact scorer is imported from
benchmarks/d3-d8-remap-solver/d5_s2.py.

All ensembles keep the eight selector-generated D5 residents at their
law-forced coordinates, matching the S2 search contract.
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import random
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
S2_PATH = ROOT / "benchmarks" / "d3-d8-remap-solver" / "d5_s2.py"
ATLAS_PATH = ROOT / "knowledge" / "d5-multilaw-atlas.json"
CORPUS_PATH = ROOT / "knowledge" / "d3-d8-stable-residents.json"


def load_s2():
    spec = importlib.util.spec_from_file_location("d5_s2_3049_null", S2_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def all_d5_coords() -> list[str]:
    return [format(i, "05b") for i in range(32)]


def hypercube_edges(coords: list[str], hamming) -> list[tuple[str, str]]:
    out = []
    for i, a in enumerate(coords):
        for b in coords[i + 1 :]:
            if hamming(a, b) == 1:
                out.append((a, b))
    return out


def prepare(s2, atlas_path: Path, corpus_path: Path):
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    rows = {row["stable_resident_id"]: row for row in corpus["rows"]}
    current = s2.current_map(atlas)
    generators = s2.generator_constraints(atlas, rows)
    axes = s2.local_axis_pairs(atlas)
    penalties = s2.penalty_pairs(atlas)

    forced_ids = {row["child_resident"] for row in generators}
    forced_coords = {row["expected_bits"] for row in generators}
    assert len(forced_ids) == 8
    assert len(forced_coords) == 8
    assert all(current[rid] in forced_coords for rid in forced_ids)

    free_ids = sorted(set(current) - forced_ids)
    free_coords = sorted(set(all_d5_coords()) - forced_coords)
    assert len(free_ids) == len(free_coords) == 24

    candidates, best, chosen = s2.exact_single_swap_search(
        current, generators, axes, penalties
    )
    current_score = s2.score_map(current, generators, axes, penalties)
    best_score = chosen["score"]
    assert s2.semantic_key(current_score) == (8, 4, -2)
    assert s2.semantic_key(best_score) == (8, 4, 0)
    assert len(best) == 4

    return {
        "atlas": atlas,
        "rows": rows,
        "current": current,
        "generators": generators,
        "axes": axes,
        "penalties": penalties,
        "forced_ids": forced_ids,
        "forced_coords": forced_coords,
        "free_ids": free_ids,
        "free_coords": free_coords,
        "radius_one_candidates": candidates,
        "current_score": current_score,
        "best_score": best_score,
        "chosen": chosen,
    }


def random_free_mapping(s2, ctx, rng: random.Random) -> dict[str, str]:
    mapping = {
        rid: bits
        for rid, bits in ctx["current"].items()
        if rid in ctx["forced_ids"]
    }
    slots = ctx["free_coords"][:]
    rng.shuffle(slots)
    mapping.update(dict(zip(ctx["free_ids"], slots, strict=True)))
    return mapping


def choose_disjoint_edges(
    free_coords: list[str],
    count: int,
    *,
    rng: random.Random,
    hamming,
) -> list[tuple[str, str]]:
    edges = hypercube_edges(free_coords, hamming)
    for _ in range(256):
        shuffled = edges[:]
        rng.shuffle(shuffled)
        selected = []
        used = set()
        for edge in shuffled:
            if edge[0] in used or edge[1] in used:
                continue
            selected.append(edge)
            used.update(edge)
            if len(selected) == count:
                return selected
    raise RuntimeError("unable to choose disjoint Hamming-1 edges")


def positive_family_preserving_mapping(s2, ctx, rng: random.Random) -> dict[str, str]:
    mapping = {
        rid: bits
        for rid, bits in ctx["current"].items()
        if rid in ctx["forced_ids"]
    }

    selected_edges = choose_disjoint_edges(
        ctx["free_coords"], len(ctx["axes"]), rng=rng, hamming=s2.hamming
    )
    rng.shuffle(selected_edges)
    used_coords = set()
    used_ids = set()

    axis_rows = list(ctx["axes"])
    rng.shuffle(axis_rows)
    for pair, edge in zip(axis_rows, selected_edges, strict=True):
        a, b = pair["residents"]
        x, y = edge
        if rng.choice([False, True]):
            x, y = y, x
        mapping[a] = x
        mapping[b] = y
        used_ids.update([a, b])
        used_coords.update([x, y])

    remaining_ids = [rid for rid in ctx["free_ids"] if rid not in used_ids]
    remaining_coords = [bits for bits in ctx["free_coords"] if bits not in used_coords]
    rng.shuffle(remaining_coords)
    mapping.update(dict(zip(remaining_ids, remaining_coords, strict=True)))
    return mapping


def map_hamming(s2, current: dict[str, str], candidate: dict[str, str]) -> int:
    return sum(
        s2.hamming(current[rid], candidate[rid])
        for rid in current
        if current[rid] != candidate[rid]
    )


def event_best(s2, score: dict[str, Any], best_score: dict[str, Any]) -> bool:
    return s2.semantic_key(score) >= s2.semantic_key(best_score)


def event_current_or_better(
    s2, score: dict[str, Any], current_score: dict[str, Any]
) -> bool:
    return s2.semantic_key(score) >= s2.semantic_key(current_score)


def summarize_scores(s2, scores, ctx):
    best_count = sum(event_best(s2, s, ctx["best_score"]) for s in scores)
    current_count = sum(
        event_current_or_better(s2, s, ctx["current_score"]) for s in scores
    )
    axis_values = [s["local_axis_pairs_hit"] for s in scores]
    penalty_values = [s["penalty_adjacency_violations"] for s in scores]
    n = len(scores)
    return {
        "samples": n,
        "best_or_better_count": best_count,
        "best_or_better_rate": best_count / n,
        "best_or_better_rate_plus1": (best_count + 1) / (n + 1),
        "current_or_better_count": current_count,
        "current_or_better_rate": current_count / n,
        "axis_hits_mean": statistics.fmean(axis_values),
        "axis_hits_histogram": {
            str(k): v for k, v in sorted(Counter(axis_values).items())
        },
        "penalty_violations_mean": statistics.fmean(penalty_values),
        "penalty_histogram": {
            str(k): v for k, v in sorted(Counter(penalty_values).items())
        },
    }


def random_ensemble(s2, ctx, *, mode: str, seed: int, samples: int):
    rng = random.Random(seed)
    scores = []
    hamming_values = []
    for _ in range(samples):
        if mode == "free-random":
            mapping = random_free_mapping(s2, ctx, rng)
        elif mode == "positive-family-preserving":
            mapping = positive_family_preserving_mapping(s2, ctx, rng)
        else:
            raise ValueError(mode)
        score = s2.score_map(
            mapping, ctx["generators"], ctx["axes"], ctx["penalties"]
        )
        assert score["generator_edges_hit"] == 8
        if mode == "positive-family-preserving":
            assert score["local_axis_pairs_hit"] == 4
        scores.append(score)
        hamming_values.append(map_hamming(s2, ctx["current"], mapping))

    summary = summarize_scores(s2, scores, ctx)
    summary.update({
        "ensemble": mode,
        "seed": seed,
        "hamming_min": min(hamming_values),
        "hamming_median": statistics.median(hamming_values),
        "hamming_max": max(hamming_values),
    })
    return summary


def exact_radius_one(s2, ctx):
    rows = ctx["radius_one_candidates"][1:]  # exclude CURRENT
    scores = [row["score"] for row in rows]
    summary = summarize_scores(s2, scores, ctx)
    h = [row["migration"]["total_bit_hamming"] for row in rows]
    summary.update({
        "ensemble": "exact-radius-one-all-swaps",
        "hamming_min": min(h),
        "hamming_median": statistics.median(h),
        "hamming_max": max(h),
    })
    return summary, rows


def exact_hamming_six(s2, ctx, rows):
    selected = [
        row for row in rows
        if row["migration"]["total_bit_hamming"] == 6
    ]
    assert selected
    scores = [row["score"] for row in selected]
    summary = summarize_scores(s2, scores, ctx)
    summary.update({
        "ensemble": "exact-radius-one-bit-hamming-6",
        "hamming_min": 6,
        "hamming_median": 6,
        "hamming_max": 6,
    })
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--atlas", type=Path, default=ATLAS_PATH)
    ap.add_argument("--corpus", type=Path, default=CORPUS_PATH)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--samples", type=int, default=4096)
    ap.add_argument("--seed", type=int, default=30495)
    args = ap.parse_args()
    if args.samples < 1000:
        ap.error("--samples must be >= 1000")
    args.out.mkdir(parents=True, exist_ok=True)

    s2 = load_s2()
    ctx = prepare(s2, args.atlas, args.corpus)

    ensembles = [
        random_ensemble(
            s2, ctx, mode="free-random",
            seed=args.seed, samples=args.samples
        ),
        random_ensemble(
            s2, ctx, mode="positive-family-preserving",
            seed=args.seed + 1009, samples=args.samples
        ),
    ]
    radius, radius_rows = exact_radius_one(s2, ctx)
    ensembles.append(radius)
    ensembles.append(exact_hamming_six(s2, ctx, radius_rows))

    # Exact radius-one must reproduce the four best #3068 swaps.
    assert radius["best_or_better_count"] == 4
    assert radius["samples"] == 276

    payload = {
        "schema": "d5-remap-null-s2/v1",
        "authority": "research-only",
        "candidate_scorer": "#3068 exact imported d5_s2.score_map",
        "stable_corpus_ref": "#3051/#3061",
        "atlas_ref": "#3039/#3065",
        "target_score": {
            "current": {
                "generator_edges_hit": 8,
                "local_axis_pairs_hit": 4,
                "penalty_adjacency_violations": 2,
            },
            "best_shadow": {
                "generator_edges_hit": 8,
                "local_axis_pairs_hit": 4,
                "penalty_adjacency_violations": 0,
            },
        },
        "ensembles": ensembles,
        "interpretation_rules": [
            "free-random asks how rare the full law score is without preserving non-generator family structure",
            "positive-family-preserving conditions on all four positive local one-bit laws and measures how hard it is to avoid penalty adjacencies",
            "exact-radius-one calibrates the local one-swap neighborhood with no Monte Carlo approximation",
            "fixed-Hamming-6 matches the migration distance of the deterministic #3068 chosen shadow",
        ],
        "multiple_testing": {
            "formal_significance_claim": False,
            "purpose": "adversarial calibration",
        },
        "non_conclusions": [
            "D5 null calibration does not select a production remap",
            "conditioning on positive families is not evidence that their coordinate geometry is globally optimal",
            "neutral atlas relations remain unscored",
            "global D3-D8 interactions remain for #3037/#3043",
        ],
    }
    (args.out / "d5-null.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "ensemble\tsamples\tbest_or_better_count\tbest_or_better_rate\tcurrent_or_better_rate\taxis_hits_mean\tpenalty_violations_mean\thamming_min\thamming_median\thamming_max"
    ]
    for row in ensembles:
        lines.append("\t".join(map(str, [
            row["ensemble"], row["samples"],
            row["best_or_better_count"], row["best_or_better_rate"],
            row["current_or_better_rate"], row["axis_hits_mean"],
            row["penalty_violations_mean"], row["hamming_min"],
            row["hamming_median"], row["hamming_max"],
        ])))
    (args.out / "d5-null.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = [
        "# D5 matched null calibration — #3049",
        "",
        "Target best score from #3068: **8/8 generators, 4/4 local axes, 0/2 penalty violations**.",
        "",
        "| ensemble | samples | best-or-better | rate | current-or-better | mean axis hits | mean penalties |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in ensembles:
        report.append(
            f"| {row['ensemble']} | {row['samples']:,} | "
            f"{row['best_or_better_count']} | {row['best_or_better_rate']:.6f} | "
            f"{row['current_or_better_rate']:.6f} | "
            f"{row['axis_hits_mean']:.4f} | {row['penalty_violations_mean']:.4f} |"
        )

    report += [
        "",
        "Interpretation:",
        "- free-random tests whether the complete D5 law score appears accidentally;",
        "- positive-family-preserving asks a different question: once the four positive local families are deliberately preserved, is avoiding the two bad adjacencies difficult?;",
        "- radius-one is exact, not sampled; it must contain exactly the four best swaps found by #3068;",
        "- migration distance remains separate from semantic score.",
        "",
        "No production remap is selected by this calibration.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
