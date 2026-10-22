#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
harvest=json.loads((root/"knowledge/d9-library-harvest-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d9-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d8-foundation.json").read_text(encoding="utf-8"))

assert harvest["schema"]=="d9-library-harvest-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#3983"
assert harvest["accounting"]=={
    "selected_d9_candidates":51,
    "persistent_map":5,
    "persistent_vector":6,
    "reasoning":7,
    "unification":6,
    "epistemic":7,
    "knowledge":6,
    "time":14,
    "d9_selected_before_harvest":168,
    "d9_selected_after_harvest":219,
    "d9_remaining_after_harvest":293,
    "ratified_d9_residents":0,
}

rows=harvest["rows"]
assert len(rows)==51
assert len({row["stable_id"] for row in rows})==51
assert len({row["semantic_name"] for row in rows})==51
assert len({(row["source_file"],row["source_name"]) for row in rows})==51
assert all(row["decision"]=="SELECT-D9-CANDIDATE" for row in rows)
assert all(row["selected_d9_candidate"] is True for row in rows)
assert all(row["coordinate"] is None for row in rows)
assert all(row["coordinate_basis"]=="UNPLACED" for row in rows)
assert all(row["old_registry_coordinate_authority"]=="NONE" for row in rows)
assert all(row["ratified_resident"] is False for row in rows)

expected_sources={
    "lib/persistent-map.lisp":5,
    "lib/persistent-vector.lisp":6,
    "lib/reason.lisp":7,
    "lib/unify.lisp":6,
    "lib/epistemic.lisp":7,
    "lib/knowledge.lisp":6,
    "lib/core4.lisp":1,
    "lib/time.lisp":13,
}
actual_sources={}
for row in rows:
    actual_sources[row["source_file"]]=actual_sources.get(row["source_file"],0)+1
assert actual_sources==expected_sources

# Єдина чинна людська голова ратифікованого D4 DEFINE — «визначити».
# Історичні W8:00001001 і текстові бітові голови не є доказом
# сьогоднішньої виконуваної прив'язки, навіть коли збігаються назви.
TOP_LEVEL_DEFINE = re.compile(
    r'^[ \t]*\(визначити\s+([^\s()]+)\s+', re.MULTILINE
)


def top_level_definitions(text: str) -> set[str]:
    return {match.group(1) for match in TOP_LEVEL_DEFINE.finditer(text)}


# Чинні позитивні та історичні негативні свідки.
assert top_level_definitions("(визначити точне (функція (х) х))\n") == {"точне"}
assert top_level_definitions("(визначити багаторядкове\n  (функція (х) х))\n") == {"багаторядкове"}
for legacy in (
    "(0011 старе (0010 (х) х))\n",
    "(00001001 старе (00001000 (х) х))\n",
    "(00001010 макрос (х) х)\n",
    "(00000001 цитата ())\n",
    "(110011100 рядок ())\n",
):
    assert top_level_definitions(legacy) == set(), legacy
assert top_level_definitions("; (визначити коментар ())\n") == set()

# Історичні source_name повинні бути живими визначеннями, навіть після
# точнодоменного cutover вихідного .lisp.
for source_file,count in expected_sources.items():
    text=(root/source_file).read_text(encoding="utf-8")
    defs=top_level_definitions(text)
    claimed={row["source_name"] for row in rows if row["source_file"]==source_file}
    assert len(claimed)==count
    assert claimed <= defs

# Do not silently reintroduce exact resident names from D1-D8.
lower_names=set()
for domain in foundation["domains"].values():
    lower_names.update(str(name).lower() for name in domain.get("residents",{}).values())
assert not (lower_names & {row["source_name"].lower() for row in rows})

# Raw host mechanisms are explicitly outside this language-owned tranche.
excluded=set(harvest["host_boundary"]["excluded_raw_mechanisms"])
assert excluded=={"unix-time-now","ntp-query-raw","timezone-declarations-raw"}
assert not (excluded & {row["source_name"] for row in rows})

# Old semantic-registry coordinates must not be carried as placement facts.
for row in rows:
    assert "legacy_code" not in row
    assert "legacy_coordinate" not in row
    assert "sid" not in row
assert "zero D9 placement authority" in harvest["coordinate_policy"]

inventory_by_id={row["stable_id"]:row for row in inventory["rows"]}
for row in rows:
    candidate=inventory_by_id[row["stable_id"]]
    assert candidate["semantic_name"]==row["semantic_name"]
    assert candidate["source_class"]=="CANONICAL-LISP-LIBRARY-HARVEST"
    assert candidate["source_name"]==row["source_name"]
    assert candidate["coordinate"] is None
    assert candidate["coordinate_basis"]=="UNPLACED"
    assert candidate["ratified_resident"] is False

target=state["target"]
assert target["selected_semantic_candidates"]>=226
assert target["remaining_semantic_candidates"]==512-target["selected_semantic_candidates"]
assert target["ratified_residents"]==0

assert len(inventory["rows"])==target["selected_semantic_candidates"]
assert len({row["stable_id"] for row in inventory["rows"]})==target["selected_semantic_candidates"]
assert len({row["semantic_name"] for row in inventory["rows"]})==target["selected_semantic_candidates"]

assert state["library_harvest"]=={
    "artifact":"knowledge/d9-library-harvest-v1.json",
    "selected":58,
    "coordinates_assigned":0,
    "raw_host_mechanisms_excluded":3,
}

print("D9-LIBRARY-HARVEST-1=PASS")
selected_total=target["selected_semantic_candidates"]
remaining_total=target["remaining_semantic_candidates"]
print(f"selected=58 inventory={selected_total}/512 placed=128 unplaced={selected_total-128} remaining={remaining_total} ratified=0")
