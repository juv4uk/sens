#!/usr/bin/env python3
"""Fail-closed D10 source-proposal guard: zero semantic promotion or positions."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))

def verify(h, inv, st, f, source_bytes):
    assert h["schema"] == "d10-unify-lexical-harvest-v1/v1"
    assert h["status"] == "RESEARCH-UNRATIFIED-NOT-IN-INVENTORY"
    rows = h["rows"]
    a = h["accounting"]
    assert len(rows) == a["proposed"] == 9
    assert a["selected"] == 0 and a["ratified"] == 0
    assert a["before"] == a["after"] == 625
    assert len({r["stable_id"] for r in rows}) == len(rows)
    names = {r["semantic_name"].upper() for r in rows}
    assert len(names) == len(rows)
    lower = {str(name).upper() for d in f["domains"].values() for name in d.get("residents", {}).values()}
    existing = {r["semantic_name"].upper() for r in inv["rows"]}
    assert len(existing) == len(inv["rows"])
    assert not (names & existing), "proposal was improperly promoted to D10"
    assert not (names & lower), "D1-D9 resident cannot be added to D10"
    donors = {d["path"]: d for d in h["donors"]}
    assert set(donors) == {"lib/unify.lisp", "lib/linter.lisp"}
    assert set(source_bytes) == set(donors)
    sources = {}
    for path, donor in donors.items():
        raw = source_bytes[path]
        computed = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + bytes([0]) + raw).hexdigest()
        assert computed == donor["source_sha"], (path, computed)
        sources[path] = raw.decode("utf-8").splitlines()
    for r in rows:
        assert r["decision"].startswith("HOLD-")
        assert r["proposal_status"] == "pending-owner-review"
        assert r["coordinate"] is None and r["coordinate_basis"] == "UNPLACED"
        assert r["ratified_resident"] is False
        assert r["surface_uk"] and r["surface_ukr"] and r["behavior"]
        assert r["witness_positive"] and r["witness_falsifier"]
        donor = donors[r["source_file"]]
        assert r["source_sha"] == donor["source_sha"]
        assert r["definition_form"] == donor["definition_form"]
        prefix = "(" + r["definition_form"] + " " + r["source_name"]
        source_line = sources[r["source_file"]][r["source_line"] - 1]
        assert source_line.startswith(prefix), (r["source_file"], r["source_line"])
        assert source_line[len(prefix):][:1] in ("", " ", "\t", ")")
    selected = inv["accounting"]["selected_semantic_candidates"]
    assert selected >= a["before"] and len(inv["rows"]) == selected
    assert st["target"]["selected_semantic_candidates"] == selected
    assert st["target"]["remaining_semantic_candidates"] == 1024 - selected
    assert st["target"]["law_forced_coordinates"] == inv["accounting"]["law_forced_coordinates"] == 256
    assert st["target"]["unplaced_selected_candidates"] == selected - 256
    assert st["target"]["ratified_residents"] == inv["accounting"]["ratified_d10_residents"] == 0
    assert "knowledge/d10-unify-lexical-harvest-v1.json" not in inv["sources"]
    return {"proposals": len(rows), "promoted": 0, "selected": selected, "ratified": 0}

def main():
    h = read("knowledge/d10-unify-lexical-harvest-v1.json")
    inv = read("knowledge/d10-v1-semantic-inventory.json")
    st = read("knowledge/d10-fill-v1-state.json")
    f = read("knowledge/d1-d9-foundation.json")
    raw = {d["path"]: (ROOT / d["path"]).read_bytes() for d in h["donors"]}
    print("D10-UNIFY-LEXICAL-EVIDENCE PASS", json.dumps(verify(h, inv, st, f, raw), sort_keys=True))

if __name__ == "__main__":
    main()
