#!/usr/bin/env python3
"""#3051 — validate the coordinate-independent D3-D8 stable resident corpus.

The corpus is research infrastructure only. Stable IDs are opaque handles for
holding semantic residents fixed while CURRENT/SHADOW coordinates move.
They are not language-visible semantic identities.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "knowledge" / "d3-d8-stable-residents.json"


def compact_rows(rows) -> bytes:
    return json.dumps(
        rows,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def expected_coords(width: int) -> set[str]:
    return {format(i, f"0{width}b") for i in range(1 << width)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", type=Path, default=CORPUS)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    data = json.loads(args.corpus.read_text(encoding="utf-8"))
    rows = data["rows"]

    assert data["schema"] == "d3-d8-stable-resident-corpus/v1"
    assert data["owner_occupancy_authority"] == "#3029"
    assert data["stable_id_policy"]["language_visible"] is False
    assert data["stable_id_policy"]["semantic_identity"] is False
    assert data["stable_id_policy"]["derived_from_current_coordinate"] is False
    assert data["stable_id_policy"]["derived_from_human_name"] is False
    assert data["stable_id_policy"]["derived_from_legacy_id"] is False
    assert data["remap_policy"]["current_is_projection"] is True
    assert data["remap_policy"]["shadow_moves_coordinate_not_resident"] is True
    assert data["remap_policy"]["provenance_missing_rows_are_pinned"] is True

    assert len(rows) == 504
    ids = [row["stable_resident_id"] for row in rows]
    assert len(set(ids)) == 504
    assert all(re.fullmatch(r"sr-[a-z]{12}", stable_id) for stable_id in ids)

    by_domain = defaultdict(list)
    label_tokens = set()
    for row in rows:
        domain = row["current_domain"]
        width = int(domain[1:])
        bits = row["current_bits"]
        assert 3 <= width <= 8
        assert len(bits) == width
        assert set(bits) <= {"0", "1"}
        by_domain[domain].append(row)

        # Opaque handle cannot lexically encode the binary placement.
        assert bits not in row["stable_resident_id"]

        for label in row["human_labels_optional"]:
            token = re.sub(r"[^a-z]", "", str(label).lower())
            if token:
                label_tokens.add(token)

        if row["semantic_status"] == "PROVENANCE-MISSING":
            assert row["placement_policy"] == "PINNED-UNTIL-PROVENANCE-RECOVERED"
            assert not row["map_independent_witness_refs"]
        else:
            assert row["semantic_status"] == "RECOVERED"
            assert row["placement_policy"] == "SHADOW-ELIGIBLE"

    for stable_id in ids:
        opaque = stable_id.removeprefix("sr-")
        assert opaque not in label_tokens

    per_domain = {}
    for width in range(3, 9):
        domain = f"D{width}"
        domain_rows = by_domain[domain]
        assert len(domain_rows) == (1 << width)
        assert {row["current_bits"] for row in domain_rows} == expected_coords(width)
        counts = Counter(row["semantic_status"] for row in domain_rows)
        per_domain[domain] = {
            "total": len(domain_rows),
            "recovered": counts["RECOVERED"],
            "provenance_missing": counts["PROVENANCE-MISSING"],
        }

    expected = {
        "D3": {"total": 8, "recovered": 8, "provenance_missing": 0},
        "D4": {"total": 16, "recovered": 14, "provenance_missing": 2},
        "D5": {"total": 32, "recovered": 32, "provenance_missing": 0},
        "D6": {"total": 64, "recovered": 64, "provenance_missing": 0},
        "D7": {"total": 128, "recovered": 107, "provenance_missing": 21},
        "D8": {"total": 256, "recovered": 0, "provenance_missing": 256},
    }
    assert per_domain == expected

    recovered = sum(x["recovered"] for x in per_domain.values())
    missing = sum(x["provenance_missing"] for x in per_domain.values())
    assert recovered == 225
    assert missing == 279
    assert data["summary"]["resident_count"] == 504
    assert data["summary"]["recovered_semantics"] == recovered
    assert data["summary"]["provenance_missing"] == missing

    # #3060 guard: the D5 MEMBER operation is a D5 resident, but its
    # canonical yes/no result domain is D1.  The exact-D5 runtime boundary is
    # implemented; compatibility-only t/() output remains separate debt.
    member = next(
        row
        for row in rows
        if row["current_domain"] == "D5" and row["current_bits"] == "11101"
    )
    assert member["semantic_status"] == "RECOVERED"
    assert member["semantic_role"] == "predicate"
    # Domain and role stay separate: D1 is the domain; PredicateBit is the role.
    assert member["canonical_result_domain"] == "D1"
    assert member["canonical_result_values"] == {"NO": "0", "YES": "1"}
    assert member["canonical_result_law"] == {"no": "0", "yes": "1", "authority_refs": ["#3020", "#3029", "#3060"]}
    assert member["implementation_status"] == "IMPLEMENTED:#3060"
    assert "#3059" in member["map_independent_witness_refs"]
    assert "#3060" in member["semantic_law_refs"]

    digest = hashlib.sha256(compact_rows(rows)).hexdigest()
    assert data["corpus_hash"] == f"sha256:{digest}"

    # Demonstrate the semantic handle / map projection split without changing
    # the corpus: move one recovered resident in a synthetic SHADOW projection.
    sample = next(row for row in rows if row["current_domain"] == "D3")
    shadow = {
        "map_id": "SHADOW-VALIDATOR",
        "stable_resident_id": sample["stable_resident_id"],
        "candidate_domain": "D4",
        "candidate_bits": "1111",
    }
    assert shadow["stable_resident_id"] == sample["stable_resident_id"]
    assert (shadow["candidate_domain"], shadow["candidate_bits"]) != (
        sample["current_domain"],
        sample["current_bits"],
    )

    audit = {
        "schema": "d3-d8-stable-resident-corpus-audit/v1",
        "status": "PASS",
        "resident_count": len(rows),
        "unique_stable_ids": len(set(ids)),
        "corpus_hash": data["corpus_hash"],
        "per_domain": per_domain,
        "recovered_semantics": recovered,
        "provenance_missing": missing,
        "shadow_move_preserves_stable_id": True,
        "provenance_missing_rows_pinned": True,
        "stable_ids_encode_bits": False,
        "stable_ids_encode_human_names": False,
        "production_identity_type_added": False,
    }
    (args.out / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D3-D8 stable resident corpus — #3051",
        "",
        f"Rows: **{len(rows)} / 504**",
        f"Stable IDs: **{len(set(ids))} unique**",
        f"Corpus hash: `{data['corpus_hash']}`",
        "",
        "| domain | total | recovered semantics | provenance missing |",
        "|---|---:|---:|---:|",
    ]
    for domain in [f"D{i}" for i in range(3, 9)]:
        row = per_domain[domain]
        report.append(
            f"| {domain} | {row['total']} | {row['recovered']} | {row['provenance_missing']} |"
        )
    report += [
        "",
        "Policy:",
        "- stable IDs are opaque research handles, not language-visible identities;",
        "- CURRENT placement is a projection;",
        "- a SHADOW placement moves the coordinate, not the stable resident;",
        "- PROVENANCE-MISSING rows remain pinned until semantic provenance is recovered;",
        "- no missing role is guessed from current geometry, names or legacy rows.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
