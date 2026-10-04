#!/usr/bin/env python3
"""#3043 S0/S1: objective D3/D4 shadow remap solver.

This bounded research harness proves the solver contract before scaling to all
504 D3-D8 residents.

Scoring consumes only:
- opaque stable resident IDs;
- typed semantic relation records;
- candidate exact-width coordinates.

Human labels are report-only. CURRENT coordinates are baseline inputs only and
never receive objective weight.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import itertools
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = ROOT / "benchmarks" / "d3-d8-remap-solver" / "d3-d4-fixture.json"

D3 = "D3"
D4 = "D4"
SELECTOR_LAW = "selector-append/v1"
FALSE_LAW = "false-prefix-coincidence/v1"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def coords(width: int) -> list[str]:
    return [format(i, f"0{width}b") for i in range(1 << width)]


def current_map(fixture: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for domain in fixture["domains"].values():
        for row in domain["residents"]:
            out[row["id"]] = row["current_bits"]
    return out


def labels(fixture: dict[str, Any]) -> dict[str, str]:
    out = {}
    for domain in fixture["domains"].values():
        for row in domain["residents"]:
            out[row["id"]] = row.get("report_label", "")
    return out


def relation_by_id(fixture: dict[str, Any], law_id: str) -> dict[str, Any]:
    return next(row for row in fixture["semantic_relations"] if row["law_id"] == law_id)


def numeric_hits(mapping: dict[str, str], relation: dict[str, Any]) -> int:
    hits = 0
    for edge in relation["edges"]:
        parent = mapping[edge["parent"]]
        child = mapping[edge["child"]]
        expected = parent + edge["delta"]
        if child == expected:
            hits += 1
    return hits


def accepted_hits(mapping: dict[str, str], relation: dict[str, Any]) -> int:
    if not relation["semantic_valid"]:
        return 0
    return numeric_hits(mapping, relation)


def selector_score(mapping: dict[str, str], fixture: dict[str, Any]) -> dict[str, Any]:
    relation = relation_by_id(fixture, SELECTOR_LAW)
    hits = accepted_hits(mapping, relation)
    covered_ids = set()
    for edge in relation["edges"]:
        if mapping[edge["child"]] == mapping[edge["parent"]] + edge["delta"]:
            covered_ids.add(edge["parent"])
            covered_ids.add(edge["child"])
    total = sum(len(domain["residents"]) for domain in fixture["domains"].values())
    roots = len({edge["parent"] for edge in relation["edges"]})
    return {
        "law_edges_hit": hits,
        "law_edges_total": len(relation["edges"]),
        "covered_residents": len(covered_ids),
        "independent_roots": roots,
        "exception_facts": len(relation["edges"]) - hits,
        "certificate_bits": roots * 3 + hits,
        "derivation_depth_max": 1 if hits else 0,
        "unexplained_residents": total - len(covered_ids),
    }


def d3_exhaustive(fixture: dict[str, Any]) -> dict[str, Any]:
    cmap = current_map(fixture)
    d3_ids = [row["id"] for row in fixture["domains"][D3]["residents"]]
    d3_coords = coords(3)

    best_hits = -1
    best_maps: list[dict[str, str]] = []
    histogram: Counter[int] = Counter()

    for perm in itertools.permutations(d3_coords):
        candidate = dict(cmap)
        candidate.update(dict(zip(d3_ids, perm, strict=True)))
        hits = accepted_hits(candidate, relation_by_id(fixture, SELECTOR_LAW))
        histogram[hits] += 1
        if hits > best_hits:
            best_hits = hits
            best_maps = [{rid: candidate[rid] for rid in d3_ids}]
        elif hits == best_hits:
            best_maps.append({rid: candidate[rid] for rid in d3_ids})

    forced = {}
    for rid in d3_ids:
        values = sorted({m[rid] for m in best_maps})
        forced[rid] = values[0] if len(values) == 1 else None

    return {
        "search_space": 40320,
        "best_edge_hits": best_hits,
        "best_map_count": len(best_maps),
        "forced_coordinates": forced,
        "histogram": {str(k): v for k, v in sorted(histogram.items())},
        "current_is_best": accepted_hits(cmap, relation_by_id(fixture, SELECTOR_LAW)) == best_hits,
        "best_maps_hash": sha(sorted(
            [sorted(m.items()) for m in best_maps],
            key=canonical_json,
        )),
    }


def d4_selector_search(fixture: dict[str, Any]) -> dict[str, Any]:
    cmap = current_map(fixture)
    relation = relation_by_id(fixture, SELECTOR_LAW)
    child_ids = sorted({edge["child"] for edge in relation["edges"]})
    all_coords = coords(4)

    best_hits = -1
    best: list[dict[str, str]] = []
    histogram: Counter[int] = Counter()

    for perm in itertools.permutations(all_coords, len(child_ids)):
        candidate = dict(cmap)
        candidate.update(dict(zip(child_ids, perm, strict=True)))
        hits = accepted_hits(candidate, relation)
        histogram[hits] += 1
        if hits > best_hits:
            best_hits = hits
            best = [{rid: candidate[rid] for rid in child_ids}]
        elif hits == best_hits:
            best.append({rid: candidate[rid] for rid in child_ids})

    forced = {}
    for rid in child_ids:
        values = sorted({m[rid] for m in best})
        forced[rid] = values[0] if len(values) == 1 else None

    return {
        "search_space": 43680,
        "best_edge_hits": best_hits,
        "best_map_count": len(best),
        "forced_coordinates": forced,
        "histogram": {str(k): v for k, v in sorted(histogram.items())},
        "current_is_best": accepted_hits(cmap, relation) == best_hits,
        "best_maps_hash": sha(sorted(
            [sorted(m.items()) for m in best],
            key=canonical_json,
        )),
    }


def random_baseline(fixture: dict[str, Any], *, seed: int, samples: int) -> dict[str, Any]:
    rng = random.Random(seed)
    cmap = current_map(fixture)
    d3_ids = [row["id"] for row in fixture["domains"][D3]["residents"]]
    base_coords = coords(3)
    relation = relation_by_id(fixture, SELECTOR_LAW)
    hist: Counter[int] = Counter()
    values = []

    for _ in range(samples):
        shuffled = base_coords[:]
        rng.shuffle(shuffled)
        candidate = dict(cmap)
        candidate.update(dict(zip(d3_ids, shuffled, strict=True)))
        hits = accepted_hits(candidate, relation)
        values.append(hits)
        hist[hits] += 1

    mean = sum(values) / len(values)
    return {
        "seed": seed,
        "samples": samples,
        "mean_edge_hits": mean,
        "max_edge_hits": max(values),
        "histogram": {str(k): v for k, v in sorted(hist.items())},
    }


def objective_input(fixture: dict[str, Any]) -> dict[str, Any]:
    """Return exactly the fields allowed to influence optimization."""
    return {
        "domains": {
            name: {
                "width": domain["width"],
                "capacity": domain["capacity"],
                "resident_ids": sorted(row["id"] for row in domain["residents"]),
            }
            for name, domain in fixture["domains"].items()
        },
        "semantic_relations": [
            {
                "law_id": row["law_id"],
                "relation_type": row["relation_type"],
                "semantic_equation": row["semantic_equation"],
                "semantic_valid": row["semantic_valid"],
                "edges": row["edges"],
            }
            for row in fixture["semantic_relations"]
        ],
    }


def run_solver(fixture: dict[str, Any], *, seed: int, samples: int) -> dict[str, Any]:
    cmap = current_map(fixture)
    selector = relation_by_id(fixture, SELECTOR_LAW)
    false_law = relation_by_id(fixture, FALSE_LAW)

    d3 = d3_exhaustive(fixture)
    d4 = d4_selector_search(fixture)
    baseline = random_baseline(fixture, seed=seed, samples=samples)
    score = selector_score(cmap, fixture)
    score["randomized_hit_surplus"] = score["law_edges_hit"] - baseline["mean_edge_hits"]

    false_numeric = numeric_hits(cmap, false_law)
    false_accepted = accepted_hits(cmap, false_law)

    assert d3["search_space"] == 40320
    assert d4["search_space"] == 43680
    assert d3["best_edge_hits"] == 4
    assert d4["best_edge_hits"] == 4
    assert d3["best_map_count"] == 720
    assert d4["best_map_count"] == 1
    assert d3["forced_coordinates"]["r3-omicron"] == "101"
    assert d3["forced_coordinates"]["r3-pi"] == "110"
    assert d4["forced_coordinates"] == {
        "r4-lambda": "1010",
        "r4-mu": "1011",
        "r4-nu": "1100",
        "r4-xi": "1101",
    }
    assert false_numeric == 2
    assert false_accepted == 0

    return {
        "schema": "d3-d8-remap-solver-s1/v1",
        "authority": "research-only",
        "objective_input_sha256": sha(objective_input(fixture)),
        "current_score": score,
        "d3_exhaustive": d3,
        "d4_selector_bounded": d4,
        "random_baseline": baseline,
        "negative_control": {
            "law_id": FALSE_LAW,
            "numeric_hits_on_current": false_numeric,
            "accepted_semantic_hits": false_accepted,
            "status": "REJECTED-BY-SEMANTIC-ORACLE",
        },
        "interpretation": {
            "selector_family_current_geometry_rediscovered": True,
            "d3_forced_residents": 2,
            "d3_unconstrained_residents": 6,
            "d4_selector_forced_residents": 4,
            "d4_nonselector_residents_unconstrained_by_this_law": 12,
            "production_mutation": False,
        },
    }


def write_artifacts(out: Path, fixture: dict[str, Any], result: dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    run_hash = sha(result)[:16]
    cmap = current_map(fixture)
    label = labels(fixture)

    forced = {
        **{
            rid: bits
            for rid, bits in result["d3_exhaustive"]["forced_coordinates"].items()
            if bits is not None
        },
        **{
            rid: bits
            for rid, bits in result["d4_selector_bounded"]["forced_coordinates"].items()
            if bits is not None
        },
    }

    shadow_rows = []
    for domain_name, domain in fixture["domains"].items():
        for row in domain["residents"]:
            rid = row["id"]
            shadow_rows.append({
                "resident_id": rid,
                "domain": domain_name,
                "representative_bits": cmap[rid],
                "forced_by_active_laws": rid in forced,
                "forced_bits": forced.get(rid),
                "placement_status": (
                    "LAW-FORCED"
                    if rid in forced
                    else "UNCONSTRAINED-BY-S1-LAWS"
                ),
                "report_label": label[rid],
            })

    shadow = {
        "schema": "shadow-map/v1",
        "run_hash": run_hash,
        "research_only": True,
        "representative": "CURRENT used only as representative for unconstrained ties",
        "d3_best_equivalence_class_size": result["d3_exhaustive"]["best_map_count"],
        "rows": shadow_rows,
    }
    (out / f"shadow-map-{run_hash}.json").write_text(
        json.dumps(shadow, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    atlas = {
        "schema": "law-atlas/v1",
        "run_hash": run_hash,
        "laws": [
            {
                "law_id": SELECTOR_LAW,
                "relation_type": "GENERATOR",
                "semantic_valid": True,
                "coordinate_equation": "child_bits = parent_bits || delta_bit",
                "covered_edges": result["current_score"]["law_edges_hit"],
                "covered_residents": result["current_score"]["covered_residents"],
                "exceptions": result["current_score"]["exception_facts"],
                "certificate_bits": result["current_score"]["certificate_bits"],
                "status": "BOUNDED-CONFIRMED",
            },
            {
                "law_id": FALSE_LAW,
                "relation_type": "NEGATIVE-CONTROL",
                "semantic_valid": False,
                "coordinate_equation": "child_bits = parent_bits || delta_bit",
                "numeric_hits": result["negative_control"]["numeric_hits_on_current"],
                "accepted_hits": 0,
                "status": "REJECTED",
            },
        ],
    }
    (out / f"law-atlas-{run_hash}.json").write_text(
        json.dumps(atlas, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    score = {
        "schema": "remap-score/v1",
        "run_hash": run_hash,
        "score_vector": result["current_score"],
        "migration_distance": 0,
        "migration_distance_is_objective": False,
    }
    (out / f"score-{run_hash}.json").write_text(
        json.dumps(score, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    counter = {
        "schema": "remap-counterexamples/v1",
        "run_hash": run_hash,
        "controls": [
            result["negative_control"],
            {
                "control": "label-erasure",
                "status": "PASS",
                "claim": "report labels never enter objective_input",
            },
            {
                "control": "legacy-erasure",
                "status": "PASS",
                "claim": "fixture/objective contains no SID8/Sens8/Function8 fields",
            },
        ],
    }
    (out / "counterexamples.json").write_text(
        json.dumps(counter, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    frontier = {
        "schema": "remap-pareto-frontier/v1",
        "run_hash": run_hash,
        "entries": [
            {
                "candidate": "CURRENT",
                "score": result["current_score"],
                "migration_distance": 0,
                "note": "baseline",
            },
            {
                "candidate": "S1-selector-equivalence-class",
                "score": result["current_score"],
                "migration_distance": "varies across 720 D3 ties; excluded from objective",
                "note": "selector law fixes 2 D3 roots and 4 D4 descendants only",
            },
        ],
        "winner": None,
        "reason": "S1 law set does not explain enough residents to choose a new complete map",
    }
    (out / "pareto-frontier.json").write_text(
        json.dumps(frontier, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows = []
    for rid, bits in sorted(cmap.items()):
        domain = D3 if len(bits) == 3 else D4
        rows.append({
            "resident_id": rid,
            "domain": domain,
            "current_bits": bits,
            "forced_by_selector_law": rid in forced,
            "forced_bits": forced.get(rid, ""),
            "report_label": label[rid],
        })
    with (out / "placement-status.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    diff = [
        "# D3/D4 S1 remap diff vs CURRENT — #3043",
        "",
        "No production remap is proposed.",
        "",
        "Selector law independently rediscovers the CURRENT coordinates of:",
        "- both D3 selector roots;",
        "- all four D4 selector descendants.",
        "",
        f"D3 exhaustive search: **{result['d3_exhaustive']['search_space']:,}** maps.",
        f"Best selector score: **{result['d3_exhaustive']['best_edge_hits']}/4** edges.",
        f"Number of equally best D3 maps: **{result['d3_exhaustive']['best_map_count']:,}**.",
        "",
        "Therefore the selector law forces exactly two D3 placements but does not",
        "justify coordinates for the other six D3 residents.",
        "",
        f"D4 bounded selector search: **{result['d4_selector_bounded']['search_space']:,}** placements.",
        f"Best full selector-edge placement count: **{result['d4_selector_bounded']['best_map_count']}**.",
        "",
        "The four selector descendants are uniquely forced once the D3 roots are fixed.",
        "The other twelve D4 residents remain unexplained by this S1 law set.",
        "",
        "A false semantic relation has two perfect numeric prefix coincidences on CURRENT",
        "but receives zero score because the semantic oracle rejects the relation.",
        "",
    ]
    (out / "diff-vs-current.md").write_text("\n".join(diff), encoding="utf-8")

    report = [
        "# D3/D4 remap solver S1 — #3043",
        "",
        f"Run hash: `{run_hash}`",
        "",
        "| search | states | best selector edges | best-map count |",
        "|---|---:|---:|---:|",
        f"| D3 exhaustive | {result['d3_exhaustive']['search_space']:,} | {result['d3_exhaustive']['best_edge_hits']}/4 | {result['d3_exhaustive']['best_map_count']:,} |",
        f"| D4 selector bounded | {result['d4_selector_bounded']['search_space']:,} | {result['d4_selector_bounded']['best_edge_hits']}/4 | {result['d4_selector_bounded']['best_map_count']:,} |",
        "",
        "Findings:",
        "- CURRENT selector geometry is independently rediscovered;",
        "- D3 selector roots are forced to 101 and 110 by the selector generator law;",
        "- D4 selector descendants are uniquely forced to 1010/1011/1100/1101;",
        "- six other D3 residents and twelve other D4 residents remain unconstrained by this law;",
        "- false semantic law: 2 numeric prefix hits, 0 accepted score;",
        f"- randomized D3 mean selector-edge hits: **{result['random_baseline']['mean_edge_hits']:.4f}**;",
        f"- CURRENT/random surplus: **{result['current_score']['randomized_hit_surplus']:.4f}** edges.",
        "",
        "No new map is ratified or recommended by this S1 slice.",
        "The solver has proved only what the active semantic law actually constrains.",
        "",
    ]
    (out / "report.md").write_text("\n".join(report), encoding="utf-8")

    result_with_hash = {**result, "run_hash": run_hash}
    (out / "result.json").write_text(
        json.dumps(result_with_hash, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--random-seed", type=int, default=3043)
    ap.add_argument("--random-samples", type=int, default=4096)
    args = ap.parse_args()

    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))

    # Hard invariants.
    assert fixture["domains"][D3]["capacity"] == 8
    assert fixture["domains"][D4]["capacity"] == 16
    assert len(fixture["domains"][D3]["residents"]) == 8
    assert len(fixture["domains"][D4]["residents"]) == 16
    cmap = current_map(fixture)
    assert len(cmap) == 24
    assert len(set(cmap.values())) == 24  # widths differ, so strings remain unique here.
    assert all(len(bits) in {3, 4} for bits in cmap.values())

    # Objective must be exactly label-free and legacy-free.
    objective_text = canonical_json(objective_input(fixture)).lower()
    for forbidden in ["report_label", "sid8", "sens8", "function8", "english", "ukrainian"]:
        assert forbidden not in objective_text

    result1 = run_solver(fixture, seed=args.random_seed, samples=args.random_samples)
    result2 = run_solver(fixture, seed=args.random_seed, samples=args.random_samples)
    assert sha(result1) == sha(result2)

    # Label erasure must not change the result.
    erased = copy.deepcopy(fixture)
    for domain in erased["domains"].values():
        for row in domain["residents"]:
            row["report_label"] = ""
    result_erased = run_solver(erased, seed=args.random_seed, samples=args.random_samples)
    assert sha(result1) == sha(result_erased)

    write_artifacts(args.out, fixture, result1)
    print((args.out / "report.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
