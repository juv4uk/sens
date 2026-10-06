#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
fill=json.loads((root/"knowledge/d9-final-semantic-fill-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d9-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d8-foundation.json").read_text(encoding="utf-8"))

assert fill["schema"]=="d9-final-semantic-fill-v1/v1"
assert fill["status"]=="RESEARCH-UNRATIFIED"
assert fill["authority"]=="#3995"
assert fill["accounting"]=={
    "selected_d9_candidates":137,
    "forward_tms_jtms":51,
    "lisp_fs":30,
    "clips_import":20,
    "canon":19,
    "linter":10,
    "process_adapters":3,
    "tcp_adapters":4,
    "d9_selected_before_fill":375,
    "d9_selected_after_fill":512,
    "d9_remaining_after_fill":0,
    "ratified_d9_residents":0,
}

rows=fill["rows"]
assert len(rows)==137
assert len({row["stable_id"] for row in rows})==137
assert len({row["semantic_name"] for row in rows})==137
assert all(row["decision"]=="SELECT-D9-CANDIDATE" for row in rows)
assert all(row["selected_d9_candidate"] is True for row in rows)
assert all(row["coordinate"] is None for row in rows)
assert all(row["coordinate_basis"]=="UNPLACED" for row in rows)
assert all(row["ratified_resident"] is False for row in rows)

expected_sources={
    "lib/forward.lisp":51,
    "lib/lisp-fs.lisp":30,
    "lib/clips-import.lisp":20,
    "lib/canon.lisp":19,
    "lib/linter.lisp":10,
    "lib/process.lisp":3,
    "lib/tcp.lisp":4,
}
actual={}
for row in rows:
    actual[row["source_file"]]=actual.get(row["source_file"],0)+1
assert actual==expected_sources

for source_file,count in expected_sources.items():
    text=(root/source_file).read_text(encoding="utf-8")
    defs={m.group(1) for m in re.finditer(r'^\([01]{8}\s+([^\s()]+)\s+', text, re.MULTILINE)}
    claimed={row["source_name"] for row in rows if row["source_file"]==source_file}
    assert len(claimed)==count
    assert claimed <= defs

lower_names=set()
for domain in foundation["domains"].values():
    lower_names.update(str(name).lower() for name in domain.get("residents",{}).values())
assert not (lower_names & {row["source_name"].lower() for row in rows})

for row in rows:
    assert "legacy_code" not in row
    assert "legacy_coordinate" not in row
    assert "sid" not in row
assert "zero D9 placement authority" in fill["coordinate_policy"]

inventory_by_id={row["stable_id"]:row for row in inventory["rows"]}
for row in rows:
    candidate=inventory_by_id[row["stable_id"]]
    assert candidate["semantic_name"]==row["semantic_name"]
    assert candidate["source_class"]=="FINAL-SEMANTIC-FILL"
    assert candidate["source_name"]==row["source_name"]
    assert candidate["coordinate"] is None
    assert candidate["coordinate_basis"]=="UNPLACED"
    assert candidate["ratified_resident"] is False

assert inventory["status"]=="RESEARCH-UNRATIFIED-COMPLETE"
assert len(inventory["rows"])==512
assert len({row["stable_id"] for row in inventory["rows"]})==512
assert len({row["semantic_name"] for row in inventory["rows"]})==512
assert inventory["accounting"]=={
    "selected_semantic_candidates":512,
    "law_forced_coordinates":128,
    "unplaced_selected_candidates":384,
    "remaining_semantic_inventory":0,
    "ratified_d9_residents":0,
}

placed=[row for row in inventory["rows"] if row["coordinate"] is not None]
unplaced=[row for row in inventory["rows"] if row["coordinate"] is None]
assert len(placed)==128
assert len(unplaced)==384
assert len({row["coordinate"] for row in placed})==128
assert all(len(row["coordinate"])==9 and set(row["coordinate"])<=set("01") for row in placed)
assert all(row["coordinate_basis"]=="PROVED-SELECTOR-GENERATOR" for row in placed)
assert all(row["coordinate_basis"]=="UNPLACED" for row in unplaced)

assert state["target"]=={
    "domain":"D9",
    "width":9,
    "capacity":512,
    "dense_target":512,
    "selected_semantic_candidates":512,
    "remaining_semantic_candidates":0,
    "ratified_residents":0,
}
assert state["final_semantic_fill"]=={
    "artifact":"knowledge/d9-final-semantic-fill-v1.json",
    "selected":137,
    "coordinates_assigned":0,
    "semantic_inventory_complete":True,
}
assert state["semantic_inventory"]=={
    "artifact":"knowledge/d9-v1-semantic-inventory.json",
    "selected":512,
    "law_forced_coordinates":128,
    "unplaced_selected":384,
    "remaining":0,
    "complete":True,
}

print("D9-FINAL-SEMANTIC-FILL-1=PASS")
print("semantic-inventory=512/512 placed=128 unplaced=384 remaining=0 ratified=0")
