#!/usr/bin/env python3
"""Validate the D5 multilaw atlas against #3051 stable residents.

This is evidence ingestion, not a new semantic model.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "knowledge" / "d5-multilaw-atlas.json"
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

    assert atlas["schema"] == "d5-multilaw-atlas/v1"
    assert atlas["policy"]["human_names_in_objective"] is False
    assert atlas["policy"]["current_bits_in_objective"] is False
    assert atlas["policy"]["stable_resident_ids_are_research_handles"] is True
    assert atlas["policy"]["relation_type_is_explicit"] is True
    assert atlas["policy"]["geometry_preference_is_separate_from_semantic_law"] is True
    assert atlas["policy"]["no_global_d5_suffix_theorem"] is True
    assert atlas["production_map_mutation"] == "NONE"

    stable = {row["stable_resident_id"]: row for row in corpus["rows"]}
    d5_ids = {
        row["stable_resident_id"]
        for row in corpus["rows"]
        if row["current_domain"] == "D5"
    }
    d4_ids = {
        row["stable_resident_id"]
        for row in corpus["rows"]
        if row["current_domain"] == "D4"
    }
    assert len(d5_ids) == 32

    seen = []
    for pair in atlas["pairs"]:
        assert len(pair["residents"]) == 2
        assert len(pair["current_bits"]) == 2
        assert pair["relation_type"]
        assert pair["law_status"]
        assert pair["geometry_preference"]
        assert pair["evidence_refs"]
        assert "human_name" not in pair
        assert "names" not in pair

        for stable_id, bits in zip(pair["residents"], pair["current_bits"], strict=True):
            assert stable_id in d5_ids
            row = stable[stable_id]
            assert row["current_domain"] == "D5"
            assert row["current_bits"] == bits
            assert row["semantic_status"] == "RECOVERED"
            seen.append(stable_id)

        if pair["relation_type"] == "GENERATOR":
            parent = pair["parent_resident"]
            assert parent in d4_ids
            parent_row = stable[parent]
            assert pair["coordinate_equation"] == "child_bits=parent_bits||delta"
            assert pair["orientation_forced"] is True
            assert pair["geometry_preference"] == "PREFIX-GENERATOR"
            assert pair["current_bits"][0] == parent_row["current_bits"] + "0"
            assert pair["current_bits"][1] == parent_row["current_bits"] + "1"
        else:
            # No non-selector relation gets implicit prefix parenthood.
            assert "parent_resident" not in pair
            assert "coordinate_equation" not in pair
            assert pair["orientation_forced"] is False

    assert len(seen) == 32
    assert len(set(seen)) == 32
    assert set(seen) == d5_ids

    relation_counts = Counter(pair["relation_type"] for pair in atlas["pairs"])
    expected_counts = {
        "HISTORICAL-PAIRING": 4,
        "PRODUCT-AXIS": 2,
        "ENTAILMENT": 1,
        "INVERSE": 2,
        "DUALITY": 1,
        "ANTI-HOMOMORPHISM": 1,
        "GENERATOR": 4,
        "SEMANTIC-FAMILY": 1,
    }
    assert dict(relation_counts) == expected_counts

    selector_pairs = [p for p in atlas["pairs"] if p["relation_type"] == "GENERATOR"]
    local_pairs = [p for p in atlas["pairs"] if p["local_one_bit_law"]]
    forced_orientation = [p for p in atlas["pairs"] if p["orientation_forced"]]
    negative_or_no_bonus = [
        p for p in atlas["pairs"]
        if p["geometry_preference"] in {
            "PENALIZE-ONE-BIT-ADJACENCY",
            "NO-ADJACENCY-BONUS",
        }
    ]

    assert len(selector_pairs) == 4
    assert len(local_pairs) == 8
    assert len(forced_orientation) == 4
    assert len(negative_or_no_bonus) == 5

    # Same local adjacency must not be globally interpreted as one suffix law.
    non_generator_one_bit = [
        p for p in local_pairs if p["relation_type"] != "GENERATOR"
    ]
    assert all("parent_resident" not in p for p in non_generator_one_bit)

    audit = {
        "schema": "d5-multilaw-atlas-audit/v1",
        "status": "PASS",
        "pair_count": 16,
        "resident_coverage": 32,
        "relation_type_counts": dict(relation_counts),
        "selector_generator_pairs": len(selector_pairs),
        "local_one_bit_law_pairs": len(local_pairs),
        "orientation_forced_pairs": len(forced_orientation),
        "negative_or_no_bonus_pairs": len(negative_or_no_bonus),
        "all_rows_keyed_by_3051_stable_ids": True,
        "non_selector_prefix_parenthood_inferred": False,
        "production_map_mutation": False,
    }
    (args.out / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D5 stable-ID multilaw atlas — #3039",
        "",
        "Pairs: **16 / 16**",
        "D5 residents covered exactly once: **32 / 32**",
        f"Selector generator pairs: **{len(selector_pairs)}**",
        f"Pairs with a scoped local one-bit law: **{len(local_pairs)}**",
        f"Pairs whose exact bit orientation is forced by current evidence: **{len(forced_orientation)}**",
        f"Pairs with explicit one-bit-adjacency penalty/no bonus: **{len(negative_or_no_bonus)}**",
        "",
        "Relation types:",
    ]
    for kind, count in sorted(relation_counts.items()):
        report.append(f"- {kind}: {count}")

    report += [
        "",
        "Guards:",
        "- all semantic residents are keyed by #3051 stable handles;",
        "- human names do not enter the atlas objective;",
        "- non-selector local laws do not infer D4 prefix parenthood;",
        "- semantic-law validity and preferred SHADOW geometry are separate fields;",
        "- no global D5 suffix theorem is introduced;",
        "- CURRENT production placement is unchanged.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
