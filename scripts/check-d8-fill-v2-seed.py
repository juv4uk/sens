#!/usr/bin/env python3
"""Guard #3951 D8 dense-fill seed.

This guard checks preservation and accounting only. It does not ratify D8.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "knowledge" / "d8-fill-v2-state.json"
DONOR = ROOT / "knowledge" / "d8-donor-2934-historical-full-map.json"
RECOVERY = ROOT / "knowledge" / "d8-recovery-candidate-map.json"
FOUNDATION = ROOT / "knowledge" / "d1-d7-foundation.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    state = load(STATE)
    donor = load(DONOR)
    recovery = load(RECOVERY)
    foundation = load(FOUNDATION)

    assert state["schema"] == "d8-fill-v2-state/v1"
    assert state["authority"] == "#3951"
    assert state["target"]["capacity"] == 256
    assert state["target"]["semantic_inventory_target"] == 256

    selectors = donor["coordinates"]
    historical = donor["unassigned_candidates"]
    assert len(selectors) == 64
    assert len(historical) == 192
    assert len(selectors) + len(historical) == 256

    # Preserve all old law-generated selector evidence.
    selector_lane = state["preserved_sources"]["selector_lane"]
    assert selector_lane["count"] == 64
    assert len(selector_lane["coordinates"]) == 64

    # Preserve every current recovery candidate.
    current = recovery["provisional_ladder_candidates"]
    saved = state["preserved_sources"]["current_recovery_lane"]["candidates"]
    assert {row["candidate"] for row in current} == {row["candidate"] for row in saved}

    # Preserve all structural/product families; do not demote them to discarded.
    current_families = recovery["structural_geometric_lane"]
    saved_families = state["preserved_sources"]["structural_product_lane"]["families"]
    assert {row["family"] for row in current_families} == {row["family"] for row in saved_families}

    # First-pass lower-domain name collision accounting is reproducible.
    lower_names = set()
    for domain in ("D1", "D2", "D3", "D4", "D5", "D6"):
        residents = foundation["domains"][domain].get("residents", {})
        lower_names.update(residents.values())

    lower_collisions = [row for row in historical if row["name"] in lower_names]
    assert len(lower_collisions) == state["first_pass_accounting"]["donor_historical_lower_name_collisions"]

    donor_names = {row["name"] for row in selectors + historical}
    extra_recovery = [row for row in current if row["candidate"] not in donor_names]
    raw_seed = len(selectors) + (len(historical) - len(lower_collisions)) + len(extra_recovery)

    assert raw_seed == state["first_pass_accounting"]["raw_distinct_name_seed_after_name_collision_filter"]
    assert raw_seed >= 256, "D8 seed lost enough semantics to fill the dense domain"

    # Critical doctrine: derivability alone is not exclusion.
    assert "DERIVABLE does not mean NO-SLOT" in state["invariants"]

    print("D8-FILL-V2-SEED=PASS")
    print(f"selector evidence={len(selectors)}")
    print(f"historical donor={len(historical)}")
    print(f"lower-name collisions={len(lower_collisions)}")
    print(f"additional current recovery names={len(extra_recovery)}")
    print(f"raw distinct-name seed={raw_seed}")
    print("target semantic inventory=256")
    print("NOTE: semantic duplicate review still required before final inventory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
