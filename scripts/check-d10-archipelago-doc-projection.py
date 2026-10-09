#!/usr/bin/env python3
"""Ensure D10-facing Archipelago guidance mirrors OWNER-RATIFIED machine evidence.

Doc counts are a projection, never semantic authority. Fails closed on drift
between D10 inventory, source-donor matrix, and single-stream owner rule.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/architecture/ARCHIPELAGO-V1.uk.md"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
MATRIX = ROOT / "knowledge/d10-owner-repo-donor-matrix-v3.json"

BEGIN = "<!-- D10-INVENTORY-COUNTS:BEGIN -->"
END = "<!-- D10-INVENTORY-COUNTS:END -->"
COUNT_KEYS = {
    "D10 selected": "selected_semantic_candidates",
    "law-forced": "law_forced_coordinates",
    "unplaced": "unplaced_selected_candidates",
    "remaining": "remaining_semantic_inventory",
    "ratified": "ratified_d10_residents",
}
DONORS = (
    ("EVIDENCE-DONOR", "EVIDENCE-DONOR"),
    ("DIRECT-SEMANTIC-DONOR", "DIRECT-SEMANTIC-DONOR"),
    ("SEMANTIC-DONOR-WITH-MECHANISM-GATE", "SEMANTIC-DONOR-WITH-MECHANISM-GATE"),
)
BRIDGES = (
    "ISLAND-CALL", "EXECUTION-WITNESS", "NATIVE-OBSERVATION",
    "RESULT-COUNT", "BRIDGE", "MISSING-CAPABILITY",
)


def validate(document: str, inventory: dict, matrix: dict) -> dict:
    if document.count(BEGIN) != 1 or document.count(END) != 1:
        raise ValueError("D10 projection requires exactly one unique count block")
    start = document.index(BEGIN) + len(BEGIN)
    end = document.index(END)
    if start >= end:
        raise ValueError("misordered D10 count block")
    block = document[start:end]
    counts = inventory["accounting"]
    selected = counts["selected_semantic_candidates"]
    if inventory["status"] != "RESEARCH-UNRATIFIED-PARTIAL":
        raise ValueError("D10 inventory unexpectedly left research status")
    if (inventory["capacity"] != 1024 or inventory["width"] != 10
            or counts["ratified_d10_residents"] != 0
            or counts["remaining_semantic_inventory"] != 1024 - selected
            or counts["unplaced_selected_candidates"]
                != selected - counts["law_forced_coordinates"]
            or len(inventory["rows"]) != selected):
        raise ValueError("machine D10 accounting is inconsistent")
    for name, key in COUNT_KEYS.items():
        pattern = (rf"(?m)^{re.escape(name)}\s+"
                   + (rf"{counts[key]}/1024$" if name == "D10 selected"
                      else rf"{counts[key]}$"))
        if re.search(pattern, block) is None:
            raise ValueError(f"stale or missing D10 inventory projection: {name}")
    if "434/1024" in document or "selected              504/1024" in document:
        raise ValueError("historic D10 totals were mistaken for current authority")
    if "#4162" not in document or "єдиний" not in document:
        raise ValueError("missing global single-stream D10 owner correction")
    if "нечинне" not in document or "не є підставою відхиляти" not in document:
        raise ValueError("superseded package-exclusion rule remains ambiguous")
    if "ratified=false" not in document or "coordinate=null" not in document:
        raise ValueError("unratified D10 research admission boundary missing")
    for name in BRIDGES:
        if not re.search(rf"(?m)^{re.escape(name)}$", document):
            raise ValueError(f"missing required island border meaning: {name}")
    if matrix["scope"]["repositories_accounted"] != 87:
        raise ValueError("donor matrix repository-count authority drift")
    for label, key in DONORS:
        expected = matrix["policy_counts"][key]
        if re.search(rf"(?m)^{re.escape(label)}\s+{expected}$", document) is None:
            raise ValueError(f"stale donor-class breakdown: {label}")
    if sum(matrix["policy_counts"].values()) != 87:
        raise ValueError("donor-class sum differs from all owner repositories")
    return {
        "selected": selected,
        "remaining": counts["remaining_semantic_inventory"],
        "ratified": 0,
        "donor_repositories": 87,
        "semantic_namespace": "ONE-GLOBAL-D10-BITSTREAM",
    }


def main() -> None:
    document = DOC.read_text(encoding="utf-8")
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    result = validate(document, inventory, matrix)
    print("D10-ARCHIPELAGO-DOC-PROJECTION: PASS", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
