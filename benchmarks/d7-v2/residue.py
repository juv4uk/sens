#!/usr/bin/env python3
"""#3123 — D7 convention/residue firewall.

Consumes only the stable D3-D8 resident corpus from #3051/#3115.
No phonological class is inferred from CURRENT bits or human renderings.

Research-only output for #3101/#3043.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "knowledge" / "d7-v2-stable-residents.json"

PHONOLOGICAL_CLASSES = {"varga", "vowel", "non-varga"}
CONVENTION_CLASS = "sign/operator"


def classify(row: dict[str, Any]) -> tuple[str, bool, str]:
    status = row["semantic_status"]
    semantic_class = row.get("semantic_class")
    placement = row["placement_policy"]

    if status == "PROVENANCE-MISSING":
        if placement != "PINNED-UNTIL-PROVENANCE-RECOVERED":
            raise AssertionError(
                f"{row['stable_resident_id']}: missing provenance not pinned"
            )
        return (
            "PINNED-PROVENANCE-MISSING",
            False,
            "semantic provenance absent; geometry forbidden until evidence is recovered",
        )

    if status != "RECOVERED":
        raise AssertionError(
            f"{row['stable_resident_id']}: unexpected semantic status {status}"
        )

    if semantic_class == CONVENTION_CLASS:
        return (
            "NON-PHONOLOGICAL-CONVENTION",
            False,
            "recovered sign/operator semantics are not phonological geometry",
        )

    if semantic_class in PHONOLOGICAL_CLASSES:
        return (
            "PHONOLOGICAL-ELIGIBLE",
            True,
            "recovered sound class may participate in #3101 phonological geometry",
        )

    raise AssertionError(
        f"{row['stable_resident_id']}: recovered D7 row has unsupported class "
        f"{semantic_class!r}"
    )


def compact_refs(row: dict[str, Any]) -> list[Any]:
    refs: list[Any] = []
    refs.extend(row.get("historical_provenance_refs") or [])
    refs.extend(row.get("map_independent_witness_refs") or [])
    return refs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    rows = [row for row in data["rows"] if row["current_domain"] == "D7"]
    assert len(rows) == 128

    classified: list[dict[str, Any]] = []
    for row in rows:
        eligibility, phonology_score_eligible, reason = classify(row)
        classified.append(
            {
                "stable_resident_id": row["stable_resident_id"],
                "semantic_status": row["semantic_status"],
                "semantic_class": row.get("semantic_class"),
                "source_status": row.get("source_status"),
                "placement_policy": row["placement_policy"],
                "geometry_eligibility": eligibility,
                "phonology_score_eligible": phonology_score_eligible,
                "reason": reason,
                "evidence_refs": compact_refs(row),
                # Report-only projection. Never used by classify().
                "current_bits_report_only": row["current_bits"],
            }
        )

    phonology = [r for r in classified if r["phonology_score_eligible"]]
    convention = [
        r for r in classified
        if r["geometry_eligibility"] == "NON-PHONOLOGICAL-CONVENTION"
    ]
    pinned = [
        r for r in classified
        if r["geometry_eligibility"] == "PINNED-PROVENANCE-MISSING"
    ]

    by_class = {}
    for row in phonology:
        by_class[row["semantic_class"]] = by_class.get(row["semantic_class"], 0) + 1

    assert len(phonology) == 75
    assert by_class == {"varga": 25, "vowel": 32, "non-varga": 18}
    assert len(convention) == 32
    assert len(pinned) == 21
    assert len(phonology) + len(convention) + len(pinned) == 128

    # Firewall invariants.
    assert not any(r["phonology_score_eligible"] for r in convention)
    assert not any(r["phonology_score_eligible"] for r in pinned)
    assert all(
        r["placement_policy"] == "PINNED-UNTIL-PROVENANCE-RECOVERED"
        for r in pinned
    )
    assert all(r["semantic_status"] == "RECOVERED" for r in convention)
    assert all(r["semantic_class"] == CONVENTION_CLASS for r in convention)

    # CURRENT coordinate must not influence class. A synthetic permutation of
    # report-only bits leaves every classification unchanged.
    permuted_bits = list(reversed([r["current_bits_report_only"] for r in classified]))
    for row, replacement in zip(classified, permuted_bits, strict=True):
        shadow = dict(row)
        shadow["current_bits_report_only"] = replacement
        assert shadow["geometry_eligibility"] == row["geometry_eligibility"]
        assert shadow["phonology_score_eligible"] == row["phonology_score_eligible"]

    non_phonological = convention + pinned
    assert len(non_phonological) == 53

    tsv_fields = [
        "stable_resident_id",
        "semantic_status",
        "semantic_class",
        "source_status",
        "placement_policy",
        "geometry_eligibility",
        "phonology_score_eligible",
        "reason",
        "evidence_refs",
        "current_bits_report_only",
    ]
    with (args.out / "d7-convention-residue.tsv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(
            fh, fieldnames=tsv_fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row in non_phonological:
            writer.writerow(
                {
                    **row,
                    "evidence_refs": json.dumps(
                        row["evidence_refs"],
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                }
            )

    artifact = {
        "schema": "d7-convention-residue-firewall/v1",
        "authority": "research-only",
        "source": "knowledge/d7-v2-stable-residents.json",
        "source_corpus_hash": data.get("corpus_hash"),
        "accounting": {
            "D7_total": 128,
            "phonological_eligible": 75,
            "phonological_by_class": by_class,
            "non_phonological_convention": 32,
            "provenance_missing_pinned": 21,
            "geometry_ineligible_total": 53,
        },
        "firewall": {
            "classification_inputs": [
                "semantic_status",
                "semantic_class",
                "placement_policy",
                "preserved evidence refs",
            ],
            "classification_forbidden_inputs": [
                "CURRENT bits",
                "human renderings/labels",
                "adjacency",
            ],
            "current_bit_permutation_changes_classification": False,
        },
        "rows": classified,
        "non_conclusions": [
            "75 phonological-eligible rows do not imply their coordinates are correct",
            "32 convention rows may have separate typed laws, but receive zero phonology score",
            "21 provenance-missing rows remain semantically unknown and pinned",
            "complete 128-cell occupancy is not complete phonological recovery",
            "this artifact does not mutate production D7/Text7 placement",
        ],
    }
    result_path = args.out / "d7-accounting.json"
    result_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    assert json.loads(result_path.read_text(encoding="utf-8")) == artifact

    report = [
        "# D7 convention/residue firewall — #3123",
        "",
        "| class | rows | phonology score eligible? |",
        "|---|---:|---|",
        "| varga | 25 | yes |",
        "| vowel | 32 | yes |",
        "| non-varga | 18 | yes |",
        "| sign/operator | 32 | **no** |",
        "| provenance-missing | 21 | **no / pinned** |",
        "| **total** | **128** | |",
        "",
        "Accounting:",
        "- recovered phonological-eligible: **75**;",
        "- recovered convention rows excluded from phonology: **32**;",
        "- provenance-missing rows pinned: **21**;",
        "- full D7 accounted: **128/128**.",
        "",
        "Firewall controls:",
        "- CURRENT bits are report-only and never enter classification;",
        "- synthetic permutation of all report-only bit coordinates changes zero classifications;",
        "- sign/operator rows always receive phonology score 0;",
        "- provenance-missing rows remain PINNED-UNTIL-PROVENANCE-RECOVERED.",
        "",
        "Interpretation:",
        "D7 geometry research may fit sound laws only to the 75 recovered sound rows.",
        "The remaining 53 cells stay visible in full-domain accounting without fabricating phonology.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
