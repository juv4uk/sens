#!/usr/bin/env python3
"""Перевірка бібліотечного добору Yantra для неретифікованого D10."""
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
read = lambda path: json.loads((root / path).read_text(encoding="utf-8"))
harvest = read("knowledge/d10-yantra-library-harvest-v1.json")
inv = read("knowledge/d10-v1-semantic-inventory.json")
state = read("knowledge/d10-fill-v1-state.json")
foundation = read("knowledge/d1-d9-foundation.json")
# SHA Git-об'єкта залежить від точних байтів, а не від декодованих рядків.
source_bytes = (root / "lib/yantra.lisp").read_bytes()
source = source_bytes.decode("utf-8").splitlines()
source_sha = hashlib.sha1(
    b"blob " + str(len(source_bytes)).encode("ascii") + b"\0" + source_bytes
).hexdigest()
rows = harvest["rows"]
# Ця історична добірка v1 незмінна; вона не доводить, що
# донорна реалізація залишилась незмінною в актуальному джерелі.
assert harvest["donor"]["source_sha"] == "76460b72cccad6bc44b39e87372f37613735d7a1"
# Шукаємо лише верхньорівневі двійкові визначення. Коментарі, рядки
# та вкладені форми не можуть підтвердити поточну ідентичність.
current_locations = {}
for line_number, line in enumerate(source, start=1):
    found = re.match(r"^\(00001001[ \t]+([^\s()]+)(?=\s|\)|$)", line)
    if found:
        current_locations.setdefault(found.group(1), []).append(line_number)
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
    # Вихідна координата source_line належить закріпленому донорному об'єкту.
    # Після переходу на строгий COND номери рядків у файлі змінилися.
    # Не переписуємо історичні координати лише заради зеленого CI.
    assert isinstance(row["source_line"], int) and row["source_line"] > 0
    locations = current_locations.get(row["source_name"], [])
    assert len(locations) == 1, (
        f"{row['source_name']}: очікується рівно одне актуальне визначення D8, "
        f"знайдено {len(locations)} у рядках {locations}"
    )
    if source_sha == harvest["donor"]["source_sha"]:
        assert locations[0] == row["source_line"], (
            f"{row['source_name']}: source_line не відповідає закріпленому донору"
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
if source_sha != harvest["donor"]["source_sha"]:
    print(
        "D10-YANTRA-SOURCE-DRIFT: історичні координати збережено; "
        "імена поточних визначень унікальні; "
        "еквівалентність семантики НЕ ДОВЕДЕНО"
    )
print(f"D10-YANTRA-LIBRARY-HARVEST: PASS ({len(rows)} added; {selected}/1024; ratified 0)")
