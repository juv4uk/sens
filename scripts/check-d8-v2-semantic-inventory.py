#!/usr/bin/env python3
"""Guard #3953 для першого щільного semantic inventory D8 256/256.

Цей guard перевіряє склад residents, збереження попередньої роботи та чесну
межу координат. Він НЕ ратифікує D8 і НЕ вибирає остаточну геометрію.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "knowledge" / "d8-v2-semantic-inventory.json"
OVERFLOW = ROOT / "knowledge" / "d8-v2-overflow-ledger.json"
RECOVERY = ROOT / "knowledge" / "d8-recovery-candidate-map.json"
DONOR = ROOT / "knowledge" / "d8-donor-2934-historical-full-map.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def main() -> int:
    inv = load(INVENTORY)
    overflow = load(OVERFLOW)
    recovery = load(RECOVERY)
    donor = load(DONOR)

    require(inv["schema"] == "d8-v2-semantic-inventory/v1", "schema drift")
    require(inv["width"] == 8, "D8 width drift")
    require(inv["capacity"] == 256, "D8 capacity drift")
    require(inv["semantic_inventory_count"] == 256, "inventory accounting drift")

    rows = inv["rows"]
    require(len(rows) == 256, f"expected 256 meanings, got {len(rows)}")
    require(len({row["stable_id"] for row in rows}) == 256, "duplicate stable_id")
    require(len({row["semantic_name"] for row in rows}) == 256, "duplicate semantic_name")
    require(all(row["decision"] == "KEEP-IN-256" for row in rows), "non-keep row leaked into inventory")

    expected_sources = {
        "SELECTOR-LAW": 64,
        "RECOVERY": 12,
        "REOPENED-PRIOR-WORK": 11,
        "STRUCTURAL-GEOMETRIC": 15,
        "HISTORICAL-DONOR": 154,
    }
    require(inv["source_counts"] == expected_sources, f"source counts drift: {inv['source_counts']}")

    # Усі 64 selector-law residents мають зберігати попередню координатну evidence.
    selector_rows = [row for row in rows if row["source_class"] == "SELECTOR-LAW"]
    require(len(selector_rows) == 64, "selector count drift")
    current_selector_coords = set(recovery["selector_structural_lane"]["coordinates"])
    require(len(current_selector_coords) == 64, "current selector coordinate count drift")
    for row in selector_rows:
        require(
            len(row["coordinate_evidence"]) == 1
            and row["coordinate_evidence"][0] in current_selector_coords,
            f"current selector evidence lost: {row['semantic_name']}",
        )
        require(
            row.get("historical_donor_coordinate"),
            f"historical selector donor coordinate not preserved: {row['semantic_name']}",
        )
        require(
            row["coordinate_evidence"][0] != row["historical_donor_coordinate"],
            f"stale #2934 selector coordinate accidentally reused: {row['semantic_name']}",
        )

    # Жоден із чинних recovery candidates не може зникнути.
    current_recovery = {
        row["candidate"] for row in recovery["provisional_ladder_candidates"]
    }
    selected_names = {row["semantic_name"] for row in rows}
    require(current_recovery <= selected_names, "current recovery candidate lost")

    # Reopened prior work теж не можна знову тихо демотувати.
    reopened = {
        row["candidate"] for row in recovery.get("reopened_residency_candidates", [])
    }
    require(reopened <= selected_names, "reopened prior candidate lost")

    # Усі позитивні structural semantics з попередніх D8 досліджень мають бути всередині 256.
    structural = {
        name
        for family in recovery.get("structural_geometric_lane", [])
        for name in family.get("novel_semantics", [])
    }
    require(structural <= selected_names, "structural/product semantic lost")

    # Overflow — збережений корпус, а не видалення.
    require(overflow["overflow_count"] == 34, "overflow count drift")
    require(len(overflow["rows"]) == 34, "overflow rows drift")
    overflow_names = {row["semantic_name"] for row in overflow["rows"]}
    require(not (overflow_names & selected_names), "same semantic appears selected and overflow")

    # Повний корпус попередньої роботи не губиться: selected + overflow повинні
    # покривати кожен non-selector donor semantic, окрім тих, що злиті як
    # historical evidence в recovery/reopened row з тим самим ім'ям.
    donor_hist_names = {row["name"] for row in donor["unassigned_candidates"]}
    require(
        donor_hist_names <= (selected_names | overflow_names),
        "historical donor semantic silently lost",
    )

    # Старі #2934 координати для historical rows не можуть стати authority.
    historical = [row for row in rows if row["source_class"] == "HISTORICAL-DONOR"]
    require(
        all(row["coordinate_status"] == "DONOR-COORDINATE-NONAUTHORITATIVE" for row in historical),
        "historical donor coordinate accidentally promoted",
    )

    require(
        "derived/generated residents are allowed" in inv["doctrine"],
        "D3-D6 dense-domain doctrine lost",
    )

    print("D8-V2-SEMANTIC-INVENTORY=PASS")
    print("inventory=256/256")
    print("selector-law=64")
    print("recovery=12")
    print("reopened-prior=11")
    print("structural-product=15")
    print("historical-donor=154")
    print("overflow-preserved=34")
    print("ratified-residents=0")
    print("next=geometry/gauge phase after owner review of semantic inventory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
