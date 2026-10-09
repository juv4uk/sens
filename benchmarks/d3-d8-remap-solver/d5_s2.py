#!/usr/bin/env python3
"""#3043 S2: consume the #3039 D5 multilaw atlas and score shadow geometry.

No new D5 semantic law is defined here.  The scorer consumes only explicit
geometry statements already present in knowledge/d5-multilaw-atlas.json.

Positive geometry:
- GENERATOR: exact parent||delta, with D4 parent coordinates already forced by
  the merged #3056 selector proof;
- non-generator local_one_bit_law: Hamming-1 neighborhood, orientation free.

Negative geometry:
- PENALIZE-ONE-BIT-ADJACENCY: Hamming-1 counts as a violation.

All other atlas relations remain geometry-neutral in S2.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ATLAS_PATH = ROOT / "knowledge" / "d5-multilaw-atlas.json"
CORPUS_PATH = ROOT / "knowledge" / "d3-d8-stable-residents.json"


def hamming(a: str, b: str) -> int:
    assert len(a) == len(b)
    return sum(x != y for x, y in zip(a, b, strict=True))


def load_inputs(atlas_path: Path, corpus_path: Path):
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    rows = {row["stable_resident_id"]: row for row in corpus["rows"]}
    return atlas, rows


def current_map(atlas: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in atlas["pairs"]:
        for resident, bits in zip(pair["residents"], pair["current_bits"], strict=True):
            assert resident not in out
            out[resident] = bits
    assert len(out) == 32
    assert len(set(out.values())) == 32
    assert all(len(bits) == 5 for bits in out.values())
    return out


def generator_constraints(atlas: dict[str, Any], corpus_rows: dict[str, dict[str, Any]]):
    constraints = []
    parent_bits_seen = set()
    for pair in atlas["pairs"]:
        if pair["relation_type"] != "GENERATOR":
            continue
        parent = pair["parent_resident"]
        parent_row = corpus_rows[parent]
        assert parent_row["current_domain"] == "D4"
        parent_bits = parent_row["current_bits"]
        # These exact D4 parent coordinates are independently forced by the
        # merged #3056 selector search. CURRENT is only their equal projection.
        assert parent_bits in {"1010", "1011", "1100", "1101"}
        parent_bits_seen.add(parent_bits)

        c0, c1 = pair["residents"]
        expected0, expected1 = parent_bits + "0", parent_bits + "1"
        # Atlas CURRENT is a sanity check only, never a score feature.
        assert pair["current_bits"] == [expected0, expected1]
        constraints.extend([
            {
                "parent_resident": parent,
                "parent_bits": parent_bits,
                "delta": "0",
                "child_resident": c0,
                "expected_bits": expected0,
            },
            {
                "parent_resident": parent,
                "parent_bits": parent_bits,
                "delta": "1",
                "child_resident": c1,
                "expected_bits": expected1,
            },
        ])
    assert parent_bits_seen == {"1010", "1011", "1100", "1101"}
    assert len(constraints) == 8
    return constraints


def local_axis_pairs(atlas: dict[str, Any]):
    out = []
    for pair in atlas["pairs"]:
        if pair["relation_type"] == "GENERATOR":
            continue
        if pair["local_one_bit_law"] and pair["law_status"].startswith("SEMANTIC"):
            out.append({
                "pair_id": pair["pair_id"],
                "residents": pair["residents"],
                "relation_type": pair["relation_type"],
                "geometry_preference": pair["geometry_preference"],
            })
    assert len(out) == 4
    return out


def penalty_pairs(atlas: dict[str, Any]):
    out = []
    for pair in atlas["pairs"]:
        if pair["geometry_preference"] == "PENALIZE-ONE-BIT-ADJACENCY":
            out.append({
                "pair_id": pair["pair_id"],
                "residents": pair["residents"],
                "relation_type": pair["relation_type"],
            })
    assert len(out) == 2
    return out


def neutral_pairs(atlas: dict[str, Any], axis_ids: set[str], penalty_ids: set[str]):
    return [
        pair["pair_id"]
        for pair in atlas["pairs"]
        if pair["relation_type"] != "GENERATOR"
        and pair["pair_id"] not in axis_ids
        and pair["pair_id"] not in penalty_ids
    ]


def score_map(
    mapping: dict[str, str],
    generators: list[dict[str, Any]],
    axes: list[dict[str, Any]],
    penalties: list[dict[str, Any]],
) -> dict[str, Any]:
    generator_hits = sum(
        mapping[row["child_resident"]] == row["expected_bits"]
        for row in generators
    )
    axis_hits = 0
    axis_detail = []
    for pair in axes:
        a, b = pair["residents"]
        distance = hamming(mapping[a], mapping[b])
        hit = distance == 1
        axis_hits += hit
        axis_detail.append({
            "pair_id": pair["pair_id"],
            "distance": distance,
            "hit": hit,
        })

    penalty_violations = 0
    penalty_detail = []
    for pair in penalties:
        a, b = pair["residents"]
        distance = hamming(mapping[a], mapping[b])
        violation = distance == 1
        penalty_violations += violation
        penalty_detail.append({
            "pair_id": pair["pair_id"],
            "distance": distance,
            "violation": violation,
        })

    covered = set()
    for row in generators:
        if mapping[row["child_resident"]] == row["expected_bits"]:
            covered.add(row["child_resident"])
    for pair in axes:
        a, b = pair["residents"]
        if hamming(mapping[a], mapping[b]) == 1:
            covered.update([a, b])

    return {
        "generator_edges_hit": int(generator_hits),
        "generator_edges_total": len(generators),
        "local_axis_pairs_hit": int(axis_hits),
        "local_axis_pairs_total": len(axes),
        "penalty_adjacency_violations": int(penalty_violations),
        "penalty_pair_total": len(penalties),
        "positive_geometry_covered_residents": len(covered),
        "unconstrained_or_relation_only_residents": 32 - len(covered),
        "axis_detail": axis_detail,
        "penalty_detail": penalty_detail,
    }


def semantic_key(score: dict[str, Any]):
    # Migration is intentionally excluded from semantic ranking.
    return (
        score["generator_edges_hit"],
        score["local_axis_pairs_hit"],
        -score["penalty_adjacency_violations"],
    )


def migration(current: dict[str, str], candidate: dict[str, str]):
    moved = [rid for rid in current if current[rid] != candidate[rid]]
    bit_hamming = sum(hamming(current[rid], candidate[rid]) for rid in moved)
    return {
        "moved_residents": len(moved),
        "total_bit_hamming": bit_hamming,
        "moved_ids": sorted(moved),
    }


def swap_candidate(mapping: dict[str, str], a: str, b: str):
    out = dict(mapping)
    out[a], out[b] = out[b], out[a]
    return out


def exact_single_swap_search(
    current: dict[str, str],
    generators: list[dict[str, Any]],
    axes: list[dict[str, Any]],
    penalties: list[dict[str, Any]],
):
    forced_children = {row["child_resident"] for row in generators}
    movable = sorted(set(current) - forced_children)
    assert len(movable) == 24

    candidates = []
    baseline_score = score_map(current, generators, axes, penalties)
    candidates.append({
        "kind": "CURRENT",
        "mapping": dict(current),
        "score": baseline_score,
        "migration": migration(current, current),
    })

    for a, b in itertools.combinations(movable, 2):
        mapping = swap_candidate(current, a, b)
        score = score_map(mapping, generators, axes, penalties)
        candidates.append({
            "kind": "ONE-SWAP",
            "swap": [a, b],
            "mapping": mapping,
            "score": score,
            "migration": migration(current, mapping),
        })

    assert len(candidates) == 277

    best_key = max(semantic_key(row["score"]) for row in candidates)
    best = [row for row in candidates if semantic_key(row["score"]) == best_key]
    chosen = min(
        best,
        key=lambda row: (
            row["migration"]["moved_residents"],
            row["migration"]["total_bit_hamming"],
            row.get("swap", []),
        ),
    )
    return candidates, best, chosen


def write_map(path: Path, mapping: dict[str, str], score: dict[str, Any], mig: dict[str, Any], *, note: str):
    rows = [
        {"stable_resident_id": rid, "candidate_domain": "D5", "candidate_bits": bits}
        for rid, bits in sorted(mapping.items())
    ]
    payload = {
        "schema": "d5-shadow-map-s2/v1",
        "authority": "research-only",
        "note": note,
        "score": score,
        "migration_vs_current": mig,
        "rows": rows,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--atlas", type=Path, default=ATLAS_PATH)
    ap.add_argument("--corpus", type=Path, default=CORPUS_PATH)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    atlas, corpus_rows = load_inputs(args.atlas, args.corpus)
    current = current_map(atlas)
    generators = generator_constraints(atlas, corpus_rows)
    axes = local_axis_pairs(atlas)
    penalties = penalty_pairs(atlas)
    axis_ids = {row["pair_id"] for row in axes}
    penalty_ids = {row["pair_id"] for row in penalties}
    neutral = neutral_pairs(atlas, axis_ids, penalty_ids)

    # Objective text is stable IDs / relation types / geometry rules only.
    objective_payload = {
        "generators": generators,
        "axes": axes,
        "penalties": penalties,
        "neutral_pair_ids": neutral,
    }
    objective_text = json.dumps(objective_payload, sort_keys=True).lower()
    for forbidden in ["human_labels", "sens8", "function8", "english", "ukrainian"]:
        assert forbidden not in objective_text

    current_score = score_map(current, generators, axes, penalties)
    candidates, best, chosen = exact_single_swap_search(
        current, generators, axes, penalties
    )
    chosen_score = chosen["score"]

    # The local theorem we are testing: a single transposition can strictly
    # improve known D5 geometry without touching selector-forced residents.
    assert current_score["generator_edges_hit"] == 8
    assert current_score["local_axis_pairs_hit"] == 4
    assert current_score["penalty_adjacency_violations"] == 2
    assert chosen_score["generator_edges_hit"] == 8
    assert chosen_score["local_axis_pairs_hit"] == 4
    assert chosen_score["penalty_adjacency_violations"] == 0
    assert chosen["migration"]["moved_residents"] == 2
    assert semantic_key(chosen_score) > semantic_key(current_score)

    write_map(
        args.out / "current-map.json",
        current,
        current_score,
        migration(current, current),
        note="CURRENT baseline; coordinates are not objective authority",
    )
    write_map(
        args.out / "best-one-swap-shadow.json",
        chosen["mapping"],
        chosen_score,
        chosen["migration"],
        note="best semantic score reachable by one transposition among 24 non-generator D5 residents",
    )

    score_rows = []
    for row in candidates:
        score_rows.append({
            "kind": row["kind"],
            "generator_edges_hit": row["score"]["generator_edges_hit"],
            "local_axis_pairs_hit": row["score"]["local_axis_pairs_hit"],
            "penalty_adjacency_violations": row["score"]["penalty_adjacency_violations"],
            "moved_residents": row["migration"]["moved_residents"],
            "total_bit_hamming": row["migration"]["total_bit_hamming"],
            "swap": "|".join(row.get("swap", [])),
        })
    with (args.out / "one-swap-search.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(score_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(score_rows)

    best_semantic_count = len(best)
    artifact = {
        "schema": "d5-remap-solver-s2/v1",
        "authority": "research-only",
        "atlas_ref": "#3039/#3065",
        "stable_corpus_ref": "#3051/#3061",
        "parent_coordinate_ref": "#3043/#3056 S1 law-forced D4 selector descendants",
        "null_calibration_ref": "#3049/#3063",
        "score_contract": {
            "positive": [
                "GENERATOR exact parent||delta",
                "non-generator semantic local_one_bit_law => Hamming-1, orientation free",
            ],
            "negative": [
                "PENALIZE-ONE-BIT-ADJACENCY => Hamming-1 violation",
            ],
            "neutral": [
                "ENTAILMENT",
                "LOCAL-ALGEBRA-NEIGHBORHOOD without coordinate theorem",
                "FAMILY-CLUSTER-WITH-EXPLICIT-AXES without coordinate theorem",
                "NO-ADJACENCY-BONUS",
            ],
        },
        "search": {
            "movable_residents": 24,
            "states": len(candidates),
            "one_swap_states": len(candidates) - 1,
            "best_semantic_state_count": best_semantic_count,
        },
        "current_score": current_score,
        "best_one_swap_score": chosen_score,
        "best_one_swap_migration": chosen["migration"],
        "best_one_swap": chosen.get("swap"),
        "semantic_dominates_current": True,
        "production_mutation": False,
        "non_conclusions": [
            "one-swap dominance does not prove a globally optimal D5 map",
            "neutral relation families receive no invented coordinate reward",
            "migration distance is reported separately and is not semantic score",
            "owner re-ratification is required before any production move",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D5 family-constrained remap S2 — #3043",
        "",
        "Consumes the complete stable-resident D5 atlas from #3065; adds no semantics.",
        "",
        "| map | generator edges | local one-bit axes | forbidden adjacencies | moved residents |",
        "|---|---:|---:|---:|---:|",
        f"| CURRENT | {current_score['generator_edges_hit']}/8 | {current_score['local_axis_pairs_hit']}/4 | {current_score['penalty_adjacency_violations']}/2 | 0 |",
        f"| best one-swap SHADOW | {chosen_score['generator_edges_hit']}/8 | {chosen_score['local_axis_pairs_hit']}/4 | {chosen_score['penalty_adjacency_violations']}/2 | {chosen['migration']['moved_residents']} |",
        "",
        f"Exact bounded search states: **{len(candidates)}** (CURRENT + all C(24,2)=276 single swaps).",
        f"Semantically best one-swap states: **{best_semantic_count}**.",
        f"Chosen migration bit-Hamming: **{chosen['migration']['total_bit_hamming']}**.",
        "",
        "Finding:",
        "a two-resident transposition preserves every currently explicit positive D5 geometry",
        "(8 selector generator edges + 4 non-generator local one-bit laws) while removing",
        "both current one-bit adjacencies that the atlas explicitly marks as penalties.",
        "",
        "Therefore CURRENT is **not Pareto-optimal under the current explicit D5 law atlas**.",
        "This is research evidence only; no production remap is proposed.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
