#!/usr/bin/env python3
"""Validate the research-only DOMAIN-ALTITUDE-ECONOMY corpus manifest."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "benchmarks" / "domain-altitude-economy" / "corpus-v1.json"


def main() -> None:
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert doc["schema"] == "domain-altitude-economy/d8-research-corpus/v1"
    assert doc["status"] == "research-only"
    assert doc["authority"]["contract"] == "Contract 11.8 / #4008"
    assert doc["authority"]["d8"] == "owner-ratified-256/256"
    assert doc["selection_policy"]["total"] == 20
    assert doc["equivalence_law"] == (
        "digest(execute(candidate_d8)) == digest(execute(candidate_d3_expansion))"
    )

    candidates = doc["candidates"]
    assert len(candidates) == 20
    ids = [row["id"] for row in candidates]
    coords = [row["exact_d8_coordinate"] for row in candidates]
    residents = [row["resident"] for row in candidates]
    assert len(set(ids)) == len(ids)
    assert len(set(coords)) == len(coords)
    assert len(set(residents)) == len(residents)

    required = {
        "recovery": 12,
        "selector_law": 4,
        "product_family": 4,
    }
    assert doc["selection_policy"]["recovery"] == required["recovery"]
    assert doc["selection_policy"]["selector_law"] == required["selector_law"]
    assert doc["selection_policy"]["product_family"] == required["product_family"]

    for row in candidates:
        assert row["benchmark_status"] == "candidate"
        assert row["equivalence_status"] == "required"
        assert row["d3_expansion_status"] in {
            "required",
            "derivation-family-known; executable witness required",
        }
        assert row["provenance_evidence"]
        assert row["exact_d8_coordinate"] and len(row["exact_d8_coordinate"]) == 8
        assert set(row["exact_d8_coordinate"]) <= {"0", "1"}

    print(
        f"OK: {len(candidates)} provenance-bound research candidates; "
        "no semantic authority is changed by this manifest."
    )


if __name__ == "__main__":
    main()
