#!/usr/bin/env python3
"""Fail-closed D10 history IDEAS guard. Not a domain allocator/admission tool."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = "knowledge/d10-flavors-restarts-research-v1.json"
INVENTORY = "knowledge/d10-v1-semantic-inventory.json"
FOUNDATION = "knowledge/d1-d9-foundation.json"


def verify_contract(ledger: dict, inventory: dict, foundation: dict) -> dict:
    assert ledger["schema"] == "d10-flavors-restarts-research-v1/v1"
    assert ledger["status"] == "RESEARCH-UNRATIFIED-NOT-IN-INVENTORY"
    assert ledger["snapshot"]["existing_semantic_inventory_mutated"] is False

    selected = inventory["accounting"]["selected_semantic_candidates"]
    assert len(inventory["rows"]) == selected
    assert selected >= ledger["snapshot"]["selected_main_at_authoring"]
    assert inventory["accounting"]["ratified_d10_residents"] == 0
    assert ledger["snapshot"]["ratified"] == 0

    existing = {row["semantic_name"].upper() for row in inventory["rows"]}
    assert len(existing) == len(inventory["rows"])
    lower = {
        str(name).upper()
        for domain in foundation["domains"].values()
        for name in domain.get("residents", {}).values()
    }
    rows = ledger["rows"]
    assert len(rows) == ledger["snapshot"]["proposed_rows"] == 8
    ids = {row["proposal_id"] for row in rows}
    names = {row["semantic_name"].upper() for row in rows}
    assert len(ids) == len(names) == len(rows), "duplicate proposal ID or name"
    assert not (names & existing), "already selected D10 resident/proposal"
    assert not (names & lower), "D1-D9 identity cannot be reused"

    urls = {source["url"] for source in ledger["sources"]}
    assert len(urls) >= 3
    assert all(url.startswith("https://") for url in urls)
    assert all(row["source_url"] in urls for row in rows)
    assert all(row["falsifier"] and row["semantic_law"]
               and row["distinct_from_existing"] for row in rows)
    assert all(row["surface_uk"] and row["surface_ukr"] for row in rows)
    assert all(row["ratified_resident"] is False
               and row["coordinate"] is None
               and row["physical_t5_authorized"] is False for row in rows)
    allowed = {"SEMANTIC-CANDIDATE", "HOLD-D2-CONTROL", "HOLD-ERROR-TAXONOMY"}
    assert all(row["triage_status"] in allowed for row in rows)
    assert sum(row["triage_status"] == "SEMANTIC-CANDIDATE" for row in rows) == 4
    assert sum(row["triage_status"] != "SEMANTIC-CANDIDATE" for row in rows) == 4
    assert {"DEFCLASS", "DEFMETHOD", "DEFGENERIC", "MAKE-INSTANCE", "UNDO"} <= {
        item["name"] for item in ledger["excluded"]
    }
    assert all(item["reason"] for item in ledger["excluded"])
    return {
        "newly_ratified": 0,
        "proposed_outside_inventory": len(rows),
        "candidates": 4,
        "hold": 4,
        "selected_actual_inventory": selected,
        "original_executable_t5_migrations": "NOT_ATTESTED_BY_RESEARCH",
    }


def main() -> None:
    read = lambda name: json.loads((ROOT / name).read_text(encoding="utf-8"))
    result = verify_contract(read(LEDGER), read(INVENTORY), read(FOUNDATION))
    print("D10-FLAVORS-RESTARTS-RESEARCH PASS", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
