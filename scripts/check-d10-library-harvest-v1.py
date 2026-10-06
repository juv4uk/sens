#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
harvest=json.loads((root/"knowledge/d10-library-harvest-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))

assert harvest["schema"]=="d10-library-harvest-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#4026"
assert harvest["accounting"]=={
    "selected_d10_candidates":39,
    "translation_protocol":11,
    "world_ancestry":6,
    "utf8_validation":7,
    "lisp_fs_recovery":7,
    "dimension_algebra":4,
    "prolog_datalog_projection":2,
    "structured_narration":2,
    "d10_selected_before_harvest":265,
    "d10_selected_after_harvest":304,
    "d10_remaining_after_harvest":720,
    "law_forced_coordinates":256,
    "unplaced_selected_after_harvest":48,
    "ratified_d10_residents":0,
}

rows=harvest["rows"]
assert len(rows)==39
assert len({r["stable_id"] for r in rows})==39
assert len({r["semantic_name"] for r in rows})==39
assert len({(r["source_file"],r["source_name"]) for r in rows})==39
assert all(r["decision"]=="SELECT-D10-CANDIDATE" for r in rows)
assert all(r["selected_d10_candidate"] is True for r in rows)
assert all(r["coordinate"] is None for r in rows)
assert all(r["coordinate_basis"]=="UNPLACED" for r in rows)
assert all(r["legacy_coordinate_authority"]=="NONE" for r in rows)
assert all(r["ratified_resident"] is False for r in rows)

expected_sources={
    "lib/translation.lisp":11,
    "lib/world.lisp":6,
    "lib/utf8.lisp":7,
    "lib/lisp-fs.lisp":7,
    "lib/quantity.lisp":4,
    "lib/bridge/prolog-to-datalog.lisp":2,
    "lib/narrate.lisp":2,
}
actual={}
for r in rows:
    actual[r["source_file"]]=actual.get(r["source_file"],0)+1
assert actual==expected_sources

# Every row must name an actual top-level semantic definition in its source file.
for source_file,count in expected_sources.items():
    text=(root/source_file).read_text(encoding="utf-8")
    defs={m.group(1) for m in re.finditer(r'^\([01]{8}\s+([^\s()]+)\s+',text,re.MULTILINE)}
    claimed={r["source_name"] for r in rows if r["source_file"]==source_file}
    assert len(claimed)==count
    assert claimed <= defs

lower=set()
for domain in foundation["domains"].values():
    lower.update(str(name).lower() for name in domain.get("residents",{}).values())
assert not (lower & {r["source_name"].lower() for r in rows})

inv_by_id={r["stable_id"]:r for r in inventory["rows"]}
for row in rows:
    got=inv_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["source_class"]=="CANONICAL-LISP-LIBRARY-HARVEST"
    assert got["source_name"]==row["source_name"]
    assert got["coordinate"] is None
    assert got["coordinate_basis"]=="UNPLACED"
    assert got["ratified_resident"] is False

assert len(inventory["rows"])==304
assert len({r["stable_id"] for r in inventory["rows"]})==304
assert len({r["semantic_name"] for r in inventory["rows"]})==304
assert inventory["accounting"]=={
    "selected_semantic_candidates":304,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":48,
    "remaining_semantic_inventory":720,
    "ratified_d10_residents":0,
}

assert state["target"]["selected_semantic_candidates"]==304
assert state["target"]["remaining_semantic_candidates"]==720
assert state["target"]["law_forced_coordinates"]==256
assert state["target"]["unplaced_selected_candidates"]==48
assert state["target"]["ratified_residents"]==0
assert state["library_harvest_v1"]=={
    "artifact":"knowledge/d10-library-harvest-v1.json",
    "selected":39,
    "coordinates_assigned":0,
    "excluded_classes":[
        "schema/version/global constants",
        "onto accumulators",
        "generic local helpers",
        "compatibility wrappers",
        "host mechanisms",
    ],
}

print("D10-LIBRARY-HARVEST-V1=PASS")
print("selected=39 inventory=304/1024 placed=256 unplaced=48 remaining=720 ratified=0")
