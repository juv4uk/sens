#!/usr/bin/env python3
"""#3077 — validate the coordinate-independent D6 multilaw atlas.

This checker guards evidence separation:
semantic laws may be strong while geometry credit stays zero until a
coordinate theorem independently earns it.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "knowledge" / "d6-multilaw-atlas.json"
CORPUS = ROOT / "knowledge" / "d3-d8-stable-residents.json"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--atlas", type=Path, default=ATLAS)
    ap.add_argument("--corpus", type=Path, default=CORPUS)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    atlas = json.loads(args.atlas.read_text(encoding="utf-8"))
    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))

    assert atlas["schema"] == "d6-multilaw-atlas/v1"
    assert atlas["domain"] == "D6"
    assert atlas["occupancy"] == {"used": 64, "capacity": 64}
    assert atlas["production_map_mutation"] == "NONE"
    assert atlas["stable_corpus"]["schema"] == corpus["schema"]
    assert atlas["stable_corpus"]["corpus_hash"] == corpus["corpus_hash"]

    policy = atlas["policy"]
    assert policy["stable_resident_ids_are_research_handles"] is True
    assert policy["human_names_in_objective"] is False
    assert policy["current_bits_in_objective"] is False
    assert policy["semantic_law_separate_from_geometry"] is True
    assert policy["relation_only_has_zero_solver_credit"] is True
    assert policy["product_axis_candidate_has_zero_solver_credit"] is True
    assert policy["selector_prefix_generator_is_positive_control"] is True
    assert policy["no_global_d6_suffix_theorem"] is True

    stable = {row["stable_resident_id"]: row for row in corpus["rows"]}
    d6_ids = {
        row["stable_resident_id"]
        for row in corpus["rows"]
        if row["current_domain"] == "D6"
    }
    assert len(d6_ids) == 64

    relations = atlas["relations"]
    assert len(relations) == 8
    relation_ids = [row["relation_id"] for row in relations]
    assert len(set(relation_ids)) == len(relation_ids)

    coverage: set[str] = set()
    geometry_counts = Counter()
    type_counts = Counter()

    for relation in relations:
        assert relation["residents"]
        assert relation["relation_type"]
        assert relation["semantic_equation"]
        assert relation["carrier_scope"]
        assert relation["geometry_status"]
        assert relation["evidence_refs"]
        assert relation["negative_controls"]
        assert isinstance(relation["solver_credit"], int)
        assert "current_bits" not in relation
        assert "human_names" not in relation
        assert "label" not in relation

        for stable_id in relation["residents"]:
            assert stable_id in d6_ids, (relation["relation_id"], stable_id)
            assert stable[stable_id]["semantic_status"] == "RECOVERED"
            coverage.add(stable_id)

        geometry = relation["geometry_status"]
        credit = relation["solver_credit"]
        geometry_counts[geometry] += 1
        type_counts[relation["relation_type"]] += 1

        if geometry == "PREFIX-GENERATOR":
            assert relation["relation_type"] == "GENERATOR"
            assert credit == 1
            assert relation["orientation_status"] == "PROVED"
            assert len(relation["residents"]) == 16
        else:
            assert credit == 0, relation["relation_id"]

        if geometry in {"RELATION-ONLY", "PRODUCT-AXIS-CANDIDATE", "NEIGHBORHOOD-CANDIDATE"}:
            assert credit == 0

    selector = next(r for r in relations if r["relation_id"] == "D6-SELECTOR-PREFIX-GENERATOR")
    assert len(selector["residents"]) == 16
    assert len(set(selector["residents"])) == 16

    neg = next(r for r in relations if r["relation_id"] == "D6-ORDER-REVERSAL-BY-NEG")
    order = next(r for r in relations if r["relation_id"] == "D6-NUMERIC-ORDER-LATTICE")
    assert set(order["residents"]).issubset(set(neg["residents"]))
    assert len(set(neg["residents"]) - set(order["residents"])) == 1

    theorems = atlas["geometry_theorems"]
    assert len(theorems) == 1
    s1 = theorems[0]
    assert s1["theorem_id"] == "D6-SHARED-LSB-S1"
    assert s1["semantic_constraint_graph_components"] == 3
    assert s1["exact_axis_assignments"] == 216
    assert s1["common_axis_assignments"] == 6
    assert s1["shared_axis_forced"] is False
    assert s1["solver_credit"] == 0
    assert s1["status"] == "CURRENT-SHARED-AXIS-OBSERVED-BUT-NOT-FORCED"
    assert s1["d6_residents_unconstrained_by_slice"] == 42
    assert set(s1["relation_refs"]).issubset(set(relation_ids))

    # Current atlas touches 31 unique D6 residents. This is semantic-law
    # coverage, not occupancy coverage; all 64 residents remain occupied.
    assert len(coverage) == 31

    raw = args.atlas.read_text(encoding="utf-8")
    for forbidden in ("SID8", "Sens8", "Function8"):
        assert forbidden not in raw

    audit = {
        "schema": "d6-multilaw-atlas-audit/v1",
        "status": "PASS",
        "d6_occupancy": 64,
        "relation_records": len(relations),
        "unique_residents_touched_by_relations": len(coverage),
        "geometry_status_counts": dict(sorted(geometry_counts.items())),
        "relation_type_counts": dict(sorted(type_counts.items())),
        "positive_geometry_credit_records": sum(r["solver_credit"] > 0 for r in relations),
        "shared_lsb_forced": False,
        "production_map_mutation": False,
    }
    (args.out / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D6 stable-ID multilaw atlas — #3077",
        "",
        "D6 occupancy: **64 / 64**",
        f"Relation records: **{len(relations)}**",
        f"Residents touched by current proved/candidate relations: **{len(coverage)} / 64**",
        "",
        "Geometry status:",
    ]
    for kind, count in sorted(geometry_counts.items()):
        report.append(f"- {kind}: {count}")

    report += [
        "",
        "Guards:",
        "- only the selector PREFIX-GENERATOR has positive coordinate credit;",
        "- relation-only and candidate geometry records have solver credit 0;",
        "- the observed shared D6 LSB remains not forced;",
        "- semantic records are keyed only by stable resident IDs;",
        "- CURRENT bits and human names are excluded from the objective;",
        "- production placement is unchanged.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
