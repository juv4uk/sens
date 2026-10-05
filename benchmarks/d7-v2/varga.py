#!/usr/bin/env python3
"""#3101 S1 — D7 varga phonology product geometry.

Research-only.  This slice covers the 25 recovered varga residents and asks:

1. do their source semantics form a complete place × manner product?
2. does CURRENT 7-bit placement expose that structure as simple bit geometry?
3. can one explicit 7-bit product embedding represent the same semantics?
4. how much coordinate gauge freedom remains?

Human renderings (SLP1/IAST/Devanagari/Ukrainian) are never read as evidence.
CURRENT bits are baseline diagnostics only, never semantic authority.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import random
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
STABLE = ROOT / "knowledge" / "d7-v2-stable-residents.json"
D7_MAP = ROOT / "knowledge" / "d7-full-map.json"

PLACES = ("K", "C", "T-retroflex", "T-dental", "P")
MANNERS = (
    "voiceless",
    "voiceless-aspirated",
    "voiced",
    "voiced-aspirated",
    "nasal",
)

# One explicit product witness, not a claimed canonical coordinate.
PLACE_CODE = {
    "K": "000",
    "C": "001",
    "T-retroflex": "010",
    "T-dental": "011",
    "P": "100",
}
MANNER_CODE = {
    "voiceless": "000",
    "voiceless-aspirated": "001",
    "voiced": "010",
    "voiced-aspirated": "011",
    "nasal": "100",
}


def hamming(a: str, b: str) -> int:
    assert len(a) == len(b)
    return sum(x != y for x, y in zip(a, b))


def parse_semantic_name(name: str) -> tuple[str, str]:
    parts = name.split(".")
    if len(parts) != 3 or parts[0] != "varga":
        raise ValueError(f"not an assigned varga semantic descriptor: {name}")
    return parts[1], parts[2]


def load_rows() -> list[dict]:
    stable = json.loads(STABLE.read_text(encoding="utf-8"))
    d7 = json.loads(D7_MAP.read_text(encoding="utf-8"))

    stable_by_bits = {
        row["current_bits"]: row
        for row in stable["rows"]
        if row["current_domain"] == "D7"
    }
    assert len(stable_by_bits) == 128

    out: list[dict] = []
    for cell in d7["coordinates"]:
        if cell["class"] != "varga" or cell["residency"] != "assigned":
            continue
        place, manner = parse_semantic_name(cell["name"])
        stable_row = stable_by_bits[cell["coordinate"]]
        assert stable_row["semantic_status"] == "RECOVERED"
        assert stable_row["semantic_class"] == "varga"
        out.append(
            {
                "stable_resident_id": stable_row["stable_resident_id"],
                "place": place,
                "manner": manner,
                "current_bits": cell["coordinate"],
            }
        )

    assert len(out) == 25
    assert {row["place"] for row in out} == set(PLACES)
    assert {row["manner"] for row in out} == set(MANNERS)

    combos = {(row["place"], row["manner"]) for row in out}
    expected = set(itertools.product(PLACES, MANNERS))
    assert combos == expected
    assert len(combos) == 25
    return sorted(out, key=lambda row: (PLACES.index(row["place"]), MANNERS.index(row["manner"])))


def relation_pairs(rows: list[dict], key: str) -> list[tuple[str, str]]:
    ids = [row["stable_resident_id"] for row in rows]
    by_id = {row["stable_resident_id"]: row for row in rows}
    pairs: list[tuple[str, str]] = []
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            if by_id[a][key] == by_id[b][key]:
                pairs.append((a, b))
    return pairs


def edge_score(
    mapping: dict[str, str],
    place_pairs: list[tuple[str, str]],
    manner_pairs: list[tuple[str, str]],
) -> dict[str, int]:
    place_h1 = sum(hamming(mapping[a], mapping[b]) == 1 for a, b in place_pairs)
    manner_h1 = sum(hamming(mapping[a], mapping[b]) == 1 for a, b in manner_pairs)
    return {
        "same_place_hamming1": place_h1,
        "same_manner_hamming1": manner_h1,
        "total_hamming1": place_h1 + manner_h1,
    }


def min_projection_bits(
    mapping: dict[str, str],
    labels: dict[str, object],
    eligible: Iterable[str],
) -> dict:
    ids = list(eligible)
    for width in range(0, 8):
        valid: list[tuple[int, ...]] = []
        for positions in itertools.combinations(range(7), width):
            seen: dict[str, object] = {}
            ok = True
            for rid in ids:
                projection = "".join(mapping[rid][p] for p in positions)
                label = labels[rid]
                if projection in seen and seen[projection] != label:
                    ok = False
                    break
                seen[projection] = label
            if ok:
                valid.append(positions)
        if valid:
            return {
                "min_bits": width,
                "example_positions": list(valid[0]),
                "equivalent_subsets_at_min_width": len(valid),
            }
    raise AssertionError("full 7-bit coordinate must decode labels")


def exact_single_bit_axes(
    mapping: dict[str, str],
    labels: dict[str, int],
    eligible: Iterable[str],
) -> list[dict]:
    ids = list(eligible)
    out: list[dict] = []
    for pos in range(7):
        bits = [int(mapping[rid][pos]) for rid in ids]
        target = [labels[rid] for rid in ids]
        if bits == target:
            out.append({"bit_position": pos, "polarity": "direct"})
        elif [1 - bit for bit in bits] == target:
            out.append({"bit_position": pos, "polarity": "complement"})
    return out


def percentile(sorted_values: list[int], q: float) -> int:
    idx = min(len(sorted_values) - 1, max(0, round(q * (len(sorted_values) - 1))))
    return sorted_values[idx]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--null-samples", type=int, default=4096)
    args = ap.parse_args()
    if args.null_samples < 100:
        ap.error("--null-samples must be >= 100")
    args.out.mkdir(parents=True, exist_ok=True)

    rows = load_rows()
    by_id = {row["stable_resident_id"]: row for row in rows}
    ids = [row["stable_resident_id"] for row in rows]

    place_pairs = relation_pairs(rows, "place")
    manner_pairs = relation_pairs(rows, "manner")
    assert len(place_pairs) == 50
    assert len(manner_pairs) == 50
    assert set(place_pairs).isdisjoint(set(manner_pairs))

    current = {rid: by_id[rid]["current_bits"] for rid in ids}
    product = {
        rid: "0" + PLACE_CODE[by_id[rid]["place"]] + MANNER_CODE[by_id[rid]["manner"]]
        for rid in ids
    }
    assert len(set(product.values())) == 25
    assert all(len(bits) == 7 for bits in product.values())

    current_score = edge_score(current, place_pairs, manner_pairs)
    product_score = edge_score(product, place_pairs, manner_pairs)

    rng = random.Random(3101)
    current_cells = [current[rid] for rid in ids]
    null_totals: list[int] = []
    null_place: list[int] = []
    null_manner: list[int] = []
    for _ in range(args.null_samples):
        shuffled = current_cells[:]
        rng.shuffle(shuffled)
        mapping = dict(zip(ids, shuffled, strict=True))
        score = edge_score(mapping, place_pairs, manner_pairs)
        null_place.append(score["same_place_hamming1"])
        null_manner.append(score["same_manner_hamming1"])
        null_totals.append(score["total_hamming1"])

    null_totals.sort()
    null_place.sort()
    null_manner.sort()
    p_ge = (1 + sum(x >= current_score["total_hamming1"] for x in null_totals)) / (
        args.null_samples + 1
    )

    labels_place = {rid: by_id[rid]["place"] for rid in ids}
    labels_manner = {rid: by_id[rid]["manner"] for rid in ids}
    labels_asp = {
        rid: int("aspirated" in by_id[rid]["manner"])
        for rid in ids
    }
    labels_nasal = {
        rid: int(by_id[rid]["manner"] == "nasal")
        for rid in ids
    }
    oral_ids = [rid for rid in ids if by_id[rid]["manner"] != "nasal"]
    labels_oral_voiced = {
        rid: int(by_id[rid]["manner"].startswith("voiced"))
        for rid in oral_ids
    }

    decode = {}
    for name, mapping in [("CURRENT", current), ("PRODUCT-WITNESS", product)]:
        decode[name] = {
            "place": min_projection_bits(mapping, labels_place, ids),
            "manner": min_projection_bits(mapping, labels_manner, ids),
            "aspirated": min_projection_bits(mapping, labels_asp, ids),
            "nasal": min_projection_bits(mapping, labels_nasal, ids),
            "oral_voiced": min_projection_bits(mapping, labels_oral_voiced, oral_ids),
            "single_bit_axes": {
                "aspirated": exact_single_bit_axes(mapping, labels_asp, ids),
                "nasal": exact_single_bit_axes(mapping, labels_nasal, ids),
                "oral_voiced": exact_single_bit_axes(mapping, labels_oral_voiced, oral_ids),
            },
        }

    # Deliberately false semantic grouping: duplicate C.voiceless and erase K.voiceless.
    corrupted = [(row["place"], row["manner"]) for row in rows]
    corrupted[0] = ("C", "voiceless")
    false_grouping_is_complete_product = set(corrupted) == set(itertools.product(PLACES, MANNERS))
    assert not false_grouping_is_complete_product

    current_matches_product = sum(current[rid] == product[rid] for rid in ids)
    rediscovered_current = current_matches_product == 25
    assert not rediscovered_current

    # Even with fixed 1-bit class prefix, any injective assignment of 5 place
    # categories to 3-bit codes and independently 5 manners to 3-bit codes
    # preserves exact product decodability.
    code_assignments_per_factor = math.perm(8, 5)
    product_embedding_gauge_lower_bound = code_assignments_per_factor ** 2
    assert product_embedding_gauge_lower_bound == 45_158_400

    resident_rows = []
    for row in rows:
        rid = row["stable_resident_id"]
        resident_rows.append(
            {
                **row,
                "product_witness_bits": product[rid],
                "current_diff": current[rid] != product[rid],
            }
        )
    with (args.out / "varga-residents.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(resident_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(resident_rows)

    score_rows = [
        {"model": "CURRENT", **current_score},
        {"model": "PRODUCT-WITNESS", **product_score},
    ]
    with (args.out / "geometry-scores.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(score_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(score_rows)

    artifact = {
        "schema": "d7-varga-product-geometry/s1-v1",
        "authority": "research-only",
        "scope": {
            "d7_total_residents": 128,
            "slice_residents": 25,
            "slice": "assigned varga only",
            "full_issue_acceptance_complete": False,
        },
        "semantic_source": {
            "stable_ids": "knowledge/d7-v2-stable-residents.json",
            "feature_descriptor": "knowledge/d7-full-map.json:name",
            "render_fields_used_as_evidence": [],
        },
        "product_law": {
            "places": list(PLACES),
            "manners": list(MANNERS),
            "complete_cartesian_product": True,
            "place_equivalence_pairs": len(place_pairs),
            "manner_equivalence_pairs": len(manner_pairs),
            "pair_relation_intersection": 0,
            "classification": "PRODUCT-STRUCTURE-WITNESSED",
        },
        "geometry": {
            "current": current_score,
            "product_witness": product_score,
            "current_null": {
                "samples": args.null_samples,
                "total_hamming1_p_ge": p_ge,
                "total_q05": percentile(null_totals, 0.05),
                "total_q50": percentile(null_totals, 0.50),
                "total_q95": percentile(null_totals, 0.95),
                "place_q50": percentile(null_place, 0.50),
                "manner_q50": percentile(null_manner, 0.50),
            },
            "decode_cost": decode,
            "current_exactly_rediscovered_by_product_witness": rediscovered_current,
            "current_product_exact_matches": current_matches_product,
            "product_embedding_gauge_lower_bound": product_embedding_gauge_lower_bound,
            "geometry_status": "PRODUCT-WITNESS-NOT-FORCED",
            "solver_credit": 0,
        },
        "falsifiers": {
            "false_grouping_complete_product": false_grouping_is_complete_product,
            "label_erased_absolute_embedding_unique": False,
            "reason": "at least 45,158,400 injective factor-code embeddings preserve the same 5x5 product under fixed class prefix",
        },
        "non_conclusions": [
            "the product witness is not a production D7 remap",
            "CURRENT Hamming adjacency is diagnostic only",
            "a 5x5 semantic product does not force any one absolute 7-bit embedding",
            "non-varga, vowel, sign/operator and 21 provenance-missing residents remain outside S1",
            "rendering spellings are not semantic evidence",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D7 varga product geometry — #3101 S1",
        "",
        "Scope: **25 / 128 D7 residents** (assigned varga slice only).",
        "",
        "Semantic result:",
        "- 5 places × 5 manners = complete Cartesian product;",
        "- 50 same-place pairs + 50 same-manner pairs;",
        "- relation intersection = 0;",
        "- classification = **PRODUCT-STRUCTURE-WITNESSED**.",
        "",
        "Geometry result:",
        f"- CURRENT Hamming-1 semantic edges: **{current_score['total_hamming1']} / 100**;",
        f"- matched-permutation p(null >= CURRENT): **{p_ge:.6f}**;",
        f"- explicit 7-bit product witness Hamming-1 edges: **{product_score['total_hamming1']} / 100**;",
        f"- CURRENT cells exactly reproduced by that witness: **{current_matches_product} / 25**;",
        f"- injective product-embedding gauge lower bound: **{product_embedding_gauge_lower_bound:,}**.",
        "",
        "Decode cost (minimum raw coordinate bits whose projection determines the feature on this slice):",
        f"- CURRENT place/manner = {decode['CURRENT']['place']['min_bits']} / {decode['CURRENT']['manner']['min_bits']};",
        f"- PRODUCT place/manner = {decode['PRODUCT-WITNESS']['place']['min_bits']} / {decode['PRODUCT-WITNESS']['manner']['min_bits']};",
        f"- CURRENT aspiration/nasal/oral-voice = {decode['CURRENT']['aspirated']['min_bits']} / {decode['CURRENT']['nasal']['min_bits']} / {decode['CURRENT']['oral_voiced']['min_bits']};",
        f"- PRODUCT aspiration/nasal/oral-voice = {decode['PRODUCT-WITNESS']['aspirated']['min_bits']} / {decode['PRODUCT-WITNESS']['nasal']['min_bits']} / {decode['PRODUCT-WITNESS']['oral_voiced']['min_bits']}.",
        "",
        "Verdict: **PRODUCT-WITNESS-NOT-FORCED**.",
        "The phonological product is real; the absolute 7-bit coordinate is still underdetermined.",
        "",
        "This is S1 only; it does not satisfy the full 128/128 D7 acceptance yet.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
