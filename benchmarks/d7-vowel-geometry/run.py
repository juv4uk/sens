#!/usr/bin/env python3
"""#3121 — D7 vowel product/affine geometry research.

Semantic features are parsed from the structured D7 donor before coordinate
scoring. CURRENT bits are baseline evidence only.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STABLE = ROOT / "knowledge" / "d3-d8-stable-residents.json"
FULL = ROOT / "knowledge" / "d7-full-map.json"
SEED = 3121
SAMPLES = 4096

QUALITIES = ("a", "i", "u", "r-vocalic", "l-vocalic", "e", "o")
ORALITY = ("oral", "nasal")
LENGTH = ("short", "long")


def parse_name(name: str) -> dict:
    parts = name.split(".")
    if len(parts) == 3 and parts[:2] == ["vowel", "uk-ext"]:
        return {
            "family": "uk-ext",
            "quality": None,
            "orality": None,
            "length": None,
            "local_role": parts[2],
        }
    if len(parts) != 4 or parts[0] != "vowel":
        raise ValueError(f"unexpected vowel descriptor: {name}")
    quality, orality, length = parts[1:]
    if quality not in QUALITIES or orality not in ORALITY or length not in LENGTH:
        raise ValueError(f"unsupported vowel feature tuple: {name}")
    return {
        "family": "product-core",
        "quality": quality,
        "orality": orality,
        "length": length,
        "local_role": None,
    }


def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def xor_bits(a: str, b: str) -> str:
    return format(int(a, 2) ^ int(b, 2), f"0{len(a)}b")


def percentile(values: list[int], q: float) -> int:
    s = sorted(values)
    return s[min(len(s) - 1, int((len(s) - 1) * q))]


def modifier_pairs(rows: list[dict]) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    by_key = {
        (r["quality"], r["orality"], r["length"]): r["id"]
        for r in rows
    }
    length_pairs = []
    nasal_pairs = []
    for q in QUALITIES:
        for o in ORALITY:
            length_pairs.append((by_key[(q, o, "short")], by_key[(q, o, "long")]))
        for length in LENGTH:
            nasal_pairs.append((by_key[(q, "oral", length)], by_key[(q, "nasal", length)]))
    assert len(length_pairs) == 14
    assert len(nasal_pairs) == 14
    assert set(length_pairs).isdisjoint(set(nasal_pairs))
    return length_pairs, nasal_pairs


def axis_stats(mapping: dict[str, str], length_pairs, nasal_pairs) -> dict:
    length_xors = [xor_bits(mapping[a], mapping[b]) for a, b in length_pairs]
    nasal_xors = [xor_bits(mapping[a], mapping[b]) for a, b in nasal_pairs]
    lcount = Counter(length_xors)
    ncount = Counter(nasal_xors)
    lbest, lfreq = lcount.most_common(1)[0]
    nbest, nfreq = ncount.most_common(1)[0]
    all_pairs = length_pairs + nasal_pairs
    return {
        "modifier_hamming1": sum(hamming(mapping[a], mapping[b]) == 1 for a, b in all_pairs),
        "length_hamming1": sum(hamming(mapping[a], mapping[b]) == 1 for a, b in length_pairs),
        "nasal_hamming1": sum(hamming(mapping[a], mapping[b]) == 1 for a, b in nasal_pairs),
        "length_best_xor": lbest,
        "length_best_xor_frequency": lfreq,
        "nasal_best_xor": nbest,
        "nasal_best_xor_frequency": nfreq,
        "two_distinct_global_axes": (
            lfreq == len(length_pairs)
            and nfreq == len(nasal_pairs)
            and lbest != nbest
            and int(lbest, 2) != 0
            and int(nbest, 2) != 0
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    stable = json.loads(STABLE.read_text(encoding="utf-8"))
    full = json.loads(FULL.read_text(encoding="utf-8"))
    stable_by_bits = {
        r["current_bits"]: r
        for r in stable["rows"]
        if r["current_domain"] == "D7"
    }

    src = [
        r for r in full["coordinates"]
        if r["class"] == "vowel" and r["residency"] == "assigned"
    ]
    assert len(src) == 32

    rows = []
    for cell in src:
        s = stable_by_bits[cell["coordinate"]]
        assert s["semantic_class"] == "vowel"
        rows.append({
            "id": s["stable_resident_id"],
            "bits": cell["coordinate"],
            "name": cell["name"],
            **parse_name(cell["name"]),
        })

    core = [r for r in rows if r["family"] == "product-core"]
    local = [r for r in rows if r["family"] == "uk-ext"]
    assert len(core) == 28
    assert len(local) == 4

    combos = {(r["quality"], r["orality"], r["length"]) for r in core}
    expected = set(itertools.product(QUALITIES, ORALITY, LENGTH))
    assert combos == expected

    length_pairs, nasal_pairs = modifier_pairs(core)
    current_map = {r["id"]: r["bits"] for r in rows}
    current = axis_stats(current_map, length_pairs, nasal_pairs)
    assert current["two_distinct_global_axes"]

    # Corrupt one semantic feature: complete product must fail.
    corrupted = [dict(r) for r in core]
    victim = corrupted[0]
    victim["length"] = "long" if victim["length"] == "short" else "short"
    corrupted_combos = {(r["quality"], r["orality"], r["length"]) for r in corrupted}
    assert corrupted_combos != expected

    # Matched null: same 32 occupied vowel cells, semantic rows fixed, coordinates permuted.
    rng = random.Random(SEED)
    coords = [r["bits"] for r in rows]
    null_h1 = []
    null_lfreq = []
    null_nfreq = []
    null_axes = 0
    for _ in range(SAMPLES):
        perm = coords[:]
        rng.shuffle(perm)
        mapping = {r["id"]: b for r, b in zip(rows, perm, strict=True)}
        stats = axis_stats(mapping, length_pairs, nasal_pairs)
        null_h1.append(stats["modifier_hamming1"])
        null_lfreq.append(stats["length_best_xor_frequency"])
        null_nfreq.append(stats["nasal_best_xor_frequency"])
        null_axes += int(stats["two_distinct_global_axes"])

    null = {
        "modifier_hamming1": {
            "observed": current["modifier_hamming1"],
            "mean": sum(null_h1) / SAMPLES,
            "p95": percentile(null_h1, .95),
            "exceedance_rate": sum(x >= current["modifier_hamming1"] for x in null_h1) / SAMPLES,
        },
        "length_best_xor_frequency": {
            "observed": current["length_best_xor_frequency"],
            "mean": sum(null_lfreq) / SAMPLES,
            "p95": percentile(null_lfreq, .95),
            "exceedance_rate": sum(x >= current["length_best_xor_frequency"] for x in null_lfreq) / SAMPLES,
        },
        "nasal_best_xor_frequency": {
            "observed": current["nasal_best_xor_frequency"],
            "mean": sum(null_nfreq) / SAMPLES,
            "p95": percentile(null_nfreq, .95),
            "exceedance_rate": sum(x >= current["nasal_best_xor_frequency"] for x in null_nfreq) / SAMPLES,
        },
        "two_distinct_global_axes_rate": null_axes / SAMPLES,
    }

    # Even fixing the two modifier-axis polarities/positions, the product law
    # alone does not order the seven quality categories inside the 3-bit quality
    # coordinate. 8P7 * 2 * 2 is a conservative gauge lower bound.
    gauge_lower_bound = math.factorial(8) * 4
    assert gauge_lower_bound == 161280

    with (args.out / "vowel-residents.tsv").open("w", newline="", encoding="utf-8") as fh:
        fields = ["id", "name", "family", "quality", "orality", "length", "local_role", "bits"]
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    artifact = {
        "schema": "d7-vowel-product-geometry/s1-v1",
        "authority": "research-only",
        "scope": {
            "assigned_vowels": 32,
            "product_core": 28,
            "uk_ext_local": 4,
        },
        "semantic_product": {
            "qualities": list(QUALITIES),
            "orality": list(ORALITY),
            "length": list(LENGTH),
            "complete_7x2x2": True,
            "length_toggle_pairs": len(length_pairs),
            "nasal_toggle_pairs": len(nasal_pairs),
            "modifier_square_count": 7,
        },
        "current_geometry": current,
        "matched_null": null,
        "false_grouping_control": "PASS",
        "gauge": {
            "quality_code_and_polarity_lower_bound": gauge_lower_bound,
            "absolute_quality_order_forced": False,
        },
        "uk_ext_policy": {
            "count": 4,
            "status": "LOCAL-RESIDUE",
            "reason": "source descriptors do not admit oral/nasal x short/long product factors",
        },
        "geometry_status": "PRODUCT-AXES-WITNESSED-ABSOLUTE-QUALITY-CODE-UNDERDETERMINED",
        "non_conclusions": [
            "strong modifier axes do not force the absolute code of each vowel quality",
            "uk-ext vowels are not completed into invented nasal/length variants",
            "CURRENT class prefix receives no semantic credit from this slice",
            "no production D7/Text7 remap is performed",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D7 vowel product geometry — #3121",
        "",
        "Assigned vowel residents: **32**",
        "- source-supported 7×2×2 product core: **28**;",
        "- explicit uk-ext local rows: **4**.",
        "",
        "Semantic product core:",
        "- 7 qualities;",
        "- oral / nasal;",
        "- short / long;",
        "- 14 length-toggle pairs;",
        "- 14 nasal-toggle pairs;",
        "- 7 complete modifier squares.",
        "",
        "CURRENT affine controls:",
        f"- length global XOR delta: **{current['length_best_xor']}** on {current['length_best_xor_frequency']}/14 pairs;",
        f"- nasal global XOR delta: **{current['nasal_best_xor']}** on {current['nasal_best_xor_frequency']}/14 pairs;",
        f"- modifier Hamming-1 edges: **{current['modifier_hamming1']}/28**;",
        "",
        "4096 matched within-vowel permutations:",
        f"- modifier H1 observed={null['modifier_hamming1']['observed']}, null mean={null['modifier_hamming1']['mean']:.3f}, p95={null['modifier_hamming1']['p95']}, exceedance={null['modifier_hamming1']['exceedance_rate']:.4f};",
        f"- length-axis max-frequency observed={null['length_best_xor_frequency']['observed']}, null mean={null['length_best_xor_frequency']['mean']:.3f}, p95={null['length_best_xor_frequency']['p95']}, exceedance={null['length_best_xor_frequency']['exceedance_rate']:.4f};",
        f"- nasal-axis max-frequency observed={null['nasal_best_xor_frequency']['observed']}, null mean={null['nasal_best_xor_frequency']['mean']:.3f}, p95={null['nasal_best_xor_frequency']['p95']}, exceedance={null['nasal_best_xor_frequency']['exceedance_rate']:.4f};",
        f"- two distinct global axes null rate={null['two_distinct_global_axes_rate']:.6f}.",
        "",
        f"Gauge lower bound from free quality-code assignment + modifier polarity: **{gauge_lower_bound}**.",
        "",
        "Interpretation:",
        "the oral/nasal and short/long product axes are strongly witnessed on the 28-row core,",
        "but the semantic product alone does not choose one absolute 3-bit quality numbering.",
        "The four uk-ext vowels remain local residue rather than invented product completions.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
