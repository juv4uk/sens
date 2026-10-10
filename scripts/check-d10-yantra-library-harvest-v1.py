#!/usr/bin/env python3
"""Перевірка бібліотечного добору Yantra для неретифікованого D10."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
read = lambda path: json.loads((root / path).read_text(encoding="utf-8"))
harvest = read("knowledge/d10-yantra-library-harvest-v1.json")
inv = read("knowledge/d10-v1-semantic-inventory.json")
state = read("knowledge/d10-fill-v1-state.json")
foundation = read("knowledge/d1-d9-foundation.json")
source_path = root / "lib/yantra.lisp"
source = source_path.read_text(encoding="utf-8").splitlines()
# Перевіряємо чинний Git blob окремо від незмінного історичного донора.
actual_source_sha = subprocess.check_output(
    ["git", "hash-object", "--", str(source_path)], cwd=root, text=True
).strip()
observed = harvest["current_observation"]
assert observed["source_sha"] == actual_source_sha
assert observed["historical_donor_sha"] == harvest["donor"]["source_sha"]
assert observed["review_status"] == "SOURCE_POSITION_ONLY_BEHAVIOR_UNPROVEN"
rows = harvest["rows"]
assert harvest["schema"] == "d10-yantra-library-harvest-v1/v1"
assert harvest["status"] == "RESEARCH-UNRATIFIED"
assert len(rows) == 19
assert len({r["stable_id"] for r in rows}) == 19
assert len({r["semantic_name"] for r in rows}) == 19
existing = {r["semantic_name"] for r in inv["rows"] if r["source_class"] != "YANTRA-LIBRARY-SEMANTIC-HARVEST"}
lower = {str(name).upper() for d in foundation["domains"].values() for name in d.get("residents", {}).values()}
assert not ({r["semantic_name"] for r in rows} & (existing | lower))
lookup = {r["stable_id"]: r for r in inv["rows"]}
for row in rows:
    assert lookup[row["stable_id"]]["semantic_name"] == row["semantic_name"]
    assert row["proposal_status"] == "pending-owner-review"
    assert row["surface_uk"] and row["surface_ukr"]
    assert row["coordinate"] is None and row["coordinate_basis"] == "UNPLACED"
    assert row["ratified_resident"] is False
    assert row["source_sha"] == harvest["donor"]["source_sha"]
    # Історичний номер рядка та Git blob не змінюємо: він залишається
    # доказом походження, а не видається за поточний стан.
    assert row["source_line"] >= 1
    assert f'{row["source_file"]}:{row["source_line"]}' in row["provenance"]
    assert f'blob:{row["source_sha"]}' in row["provenance"]
    definition = "(00001001 " + row["source_name"]
    # Кожне чинне визначення має бути присутнє рівно один раз і саме
    # у спостереженому рядку; будь-який зсув знову блокує перевірку.
    positions = [
        i for i, line in enumerate(source, 1)
        if line == definition or line.startswith(definition + " ")
    ]
    assert positions == [row["current_source_line"]], (row["source_name"], positions)
selected = state["target"]["selected_semantic_candidates"]
assert len(inv["rows"]) == selected
assert len({r["semantic_name"] for r in inv["rows"]}) == selected
assert len({r["stable_id"] for r in inv["rows"]}) == selected
assert selected >= harvest["accounting"]["d10_after"]  # historical minimum, not ceiling
assert inv["accounting"] == {
    "selected_semantic_candidates": selected,
    "law_forced_coordinates": 256,
    "unplaced_selected_candidates": selected - 256,
    "remaining_semantic_inventory": 1024 - selected,
    "ratified_d10_residents": 0,
}
assert state["target"]["law_forced_coordinates"] == 256
assert state["target"]["unplaced_selected_candidates"] == selected - 256
assert state["target"]["remaining_semantic_candidates"] == 1024 - selected
assert state["target"]["ratified_residents"] == 0
print(f"D10-YANTRA-LIBRARY-HARVEST: PASS ({len(rows)} added; {selected}/1024; ratified 0)")
