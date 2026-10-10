#!/usr/bin/env python3
"""Перевірка бібліотечного добору Yantra для неретифікованого D10."""
import subprocess
import json
from pathlib import Path

# У режимі -O Python прибирає assert: provenance перевіряти небезпечно.
if not __debug__:
    raise SystemExit("D10-YANTRA-DONOR: BLOCKED — Python -O вимикає перевірки")

root = Path(__file__).resolve().parents[1]
read = lambda path: json.loads((root / path).read_text(encoding="utf-8"))
harvest = read("knowledge/d10-yantra-library-harvest-v1.json")
inv = read("knowledge/d10-v1-semantic-inventory.json")
state = read("knowledge/d10-fill-v1-state.json")
foundation = read("knowledge/d1-d9-foundation.json")
# Історичні рядки належать незмінному Git blob, а не поточній версії бібліотеки.
donor_path = root / "knowledge/archive/d10-yantra-donor-76460b72.lisp"
donor_bytes = donor_path.read_bytes()
# git hash-object рахує точний SHA фізичного Git blob без зміни репозиторію.
donor_git_sha = subprocess.run(
    ["git", "hash-object", "--stdin"],
    cwd=root,
    input=donor_bytes,
    capture_output=True,
    check=True,
).stdout.decode("ascii").strip()
assert donor_git_sha == harvest["donor"]["source_sha"], "Змінений історичний донор"
donor_source = donor_bytes.decode("utf-8").splitlines()
current_source = (root / "lib/yantra.lisp").read_text(encoding="utf-8").splitlines()

def definition_sites(lines, name):
    """Точно відокремлюємо ім'я визначення від його можливого префікса."""
    header = "(00001001 " + name
    return [
        line_number
        for line_number, line in enumerate(lines, 1)
        if line == header or line.startswith(header + " ")
    ]

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
    assert definition_sites(donor_source, row["source_name"]) == [row["source_line"]], (
        "Невірний рядок або повтор визначення в історичному донорі", row["stable_id"]
    )
    current_sites = definition_sites(current_source, row["source_name"])
    assert len(current_sites) == 1, (
        "Поточне визначення втрачено або дубльовано", row["source_name"], current_sites
    )
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
