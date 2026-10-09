#!/usr/bin/env python3
"""Перевірка D10: один математичний кандидат, без координати й ратифікації."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
DOSSIER="knowledge/d10-primitive-binary-word-root-v1.json"
INVENTORY="knowledge/d10-v1-semantic-inventory.json"
FOUNDATION="knowledge/d1-d9-foundation.json"
HISTORY="knowledge/d10-selection-transition-history.json"
LEDGER="knowledge/d10-proposal-ledger.tsv"
NAME="PRIMITIVE-BINARY-WORD-ROOT"
SID="d10.words.primitive-binary-root.v1"
PREVIOUS_SHA="34efd273000e3de8510441764cb59acbb5ab284b"

def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def check(dossier,inv,lower,history):
    assert dossier["schema"] == "d10-binary-word-primitive-root-selection/v1"
    assert dossier["baseline"]["previous_d10_blob"] == PREVIOUS_SHA
    assert dossier["baseline"]["previous_count"] == 631
    assert dossier["baseline"]["proposed_count"] == 632
    assert dossier["admission"]["selected_delta"] == 1
    assert dossier["admission"]["proposal_id"] == "D10P-0007"
    assert dossier["admission"]["coordinates_added"] == dossier["admission"]["ratified_added"] == 0
    assert len(dossier["selection"]) == 1
    target=dossier["selection"][0]
    assert target["semantic_name"] == NAME
    assert target["stable_id"] == SID
    assert target["status"] == "SELECTED-RESEARCH-CANDIDATE"
    assert target["source_class"] == "WORD-COMBINATORICS-PRIMARY-20261009"
    assert target["coordinate"] is None and target["coordinate_basis"] == "UNPLACED"
    assert target["ratified_resident"] is False and target["physical_t5_authorized"] is False
    assert target["proposal_status"] == "pending-owner-review"
    assert target["surface_uk"] and target["surface_ukr"] and target["behavior"]
    assert len(target["positive_witnesses"]) >= 5 and len(target["falsifiers"]) >= 2
    assert "minimal_period" in target["falsifiers"][0]
    assert target["primary_url"].startswith("https://doc.sagemath.org/")
    # The source's historic promotion was 631->632; future selected append
    # cannot rewrite its identity or keep it pinned to the physical last row.
    count = len(inv["rows"])
    assert count >= 632 and inv["accounting"]["selected_semantic_candidates"] == count
    assert inv["accounting"]["remaining_semantic_inventory"] == 1024-count
    assert inv["accounting"]["unplaced_selected_candidates"] == count-256
    assert inv["accounting"]["law_forced_coordinates"] == 256
    assert inv["accounting"]["ratified_d10_residents"] == 0
    matched=[(idx,r) for idx,r in enumerate(inv["rows"]) if r.get("stable_id") == SID]
    assert len(matched) == 1 and matched[0][0] == 631
    assert matched[0][1] == target, "selected identity must remain source-identical"
    assert matched[0][1]["coordinate"] is None
    prev=[r["semantic_name"].upper() for idx,r in enumerate(inv["rows"]) if idx != 631]
    assert NAME not in prev
    original={str(name).upper() for domain in lower["domains"].values()
                 for name in domain["residents"].values()}
    assert NAME not in original
    assert any("D8 ROTATE" in n for n in target["semantic_neighbors"])
    assert len(history["transitions"]) >= 3
    historical=[t for t in history["transitions"] if t.get("id") == "d10.word-primitive-full-repeat.20261009"]
    assert len(historical) == 1
    t=historical[0]
    assert t["id"] == "d10.word-primitive-full-repeat.20261009"
    assert t["previous_inventory_blob_sha"] == PREVIOUS_SHA
    assert t["previous_selected"] == 631 and t["resulting_selected"] == 632
    assert t["delta_selected"] == 1 and t["added_stable_ids"] == [SID]
    assert t["appended_sources"] == [DOSSIER]
    assert t["coordinates_added"] == t["ratified_added"] == 0
    assert history["status"] == "RESEARCH-ONLY-NO-RATIFICATION"
    assert DOSSIER in inv["sources"]
    ledger=(ROOT/LEDGER).read_text(encoding="utf-8")
    exact=[line.split("\t") for line in ledger.splitlines()[1:] if "\t"+NAME+"\t" in line]
    assert len(exact) == 1 and exact[0][0] == "D10P-0007"
    assert exact[0][-2:] == ["pending-review","0"]
    return True

def negative_controls(dossier,inv,lower,history):
    cases=[
      ("dossier forced coordinate",lambda d,i,h: d["selection"][0].__setitem__("coordinate","0000000000")),
      ("dossier false ratified",lambda d,i,h: d["selection"][0].__setitem__("ratified_resident",True)),
      ("dossier changed behavior",lambda d,i,h: d["selection"][0].__setitem__("behavior","")),
      ("new row changed",lambda d,i,h: next(r for r in i["rows"] if r.get("stable_id") == SID).__setitem__("behavior","invalid")),
      ("false count",lambda d,i,h: i["accounting"].__setitem__("selected_semantic_candidates",len(i["rows"])+1)),
      ("fake provenance",lambda d,i,h: d["selection"][0].__setitem__("primary_url","https://example.com")),
      ("transition incorrect",lambda d,i,h: next(t for t in h["transitions"] if t.get("id") == "d10.word-primitive-full-repeat.20261009").__setitem__("previous_selected",629)),
      ("transition hidden coordinate",lambda d,i,h: next(t for t in h["transitions"] if t.get("id") == "d10.word-primitive-full-repeat.20261009").__setitem__("coordinates_added",1)),
      ("missing selection",lambda d,i,h: i["rows"].pop(next(idx for idx,r in enumerate(i["rows"]) if r.get("stable_id") == SID))),
      ("replaced SID",lambda d,i,h: d["selection"][0].__setitem__("stable_id","other"))
    ]
    for label,mutate in cases:
        d,i,h=copy.deepcopy(dossier),copy.deepcopy(inv),copy.deepcopy(history)
        mutate(d,i,h)
        try:check(d,i,lower,h)
        except (AssertionError,IndexError):continue
        raise AssertionError("accepted tamper: "+label)
    print("D10 primitive-word 10 adversarial controls PASS")

def main():
    d,i,l,h=map(read,(DOSSIER,INVENTORY,FOUNDATION,HISTORY))
    check(d,i,l,h)
    if "--self-test" in sys.argv:negative_controls(d,i,l,h)
    print(f"D10 PRIMITIVE WORD historical identity PASS: selected={len(i['rows'])}/1024; original promotion 631->632 preserved; 0 coordinates; 0 ratified")
if __name__ == "__main__":main()
