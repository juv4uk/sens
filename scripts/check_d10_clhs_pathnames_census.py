#!/usr/bin/env python3
"""Source-indexed CLHS §19.4 donor census; no automatic D10 admission.

Pinned historic D10/D1–D9 snapshot is evidence, not a growth ceiling.
Future appends cannot silently rewrite these source-index records.
"""
import argparse
import copy
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "knowledge/d10-clhs-pathnames-census-20261009.json"
INV = ROOT / "knowledge/d10-v1-semantic-inventory.json"
LOW = ROOT / "knowledge/d1-d9-foundation.json"
SECTIONS = [f"19.4.{n}" for n in range(1, 18)]
GROUPS = {
 "19.4.1":("PATHNAME",),"19.4.2":("LOGICAL-PATHNAME",),
 "19.4.3":("PATHNAME",),"19.4.4":("MAKE-PATHNAME",),
 "19.4.5":("PATHNAMEP",),
 "19.4.6":("PATHNAME-HOST","PATHNAME-DEVICE","PATHNAME-DIRECTORY","PATHNAME-NAME","PATHNAME-TYPE","PATHNAME-VERSION"),
 "19.4.7":("LOAD-LOGICAL-PATHNAME-TRANSLATIONS",),
 "19.4.8":("LOGICAL-PATHNAME-TRANSLATIONS",),
 "19.4.9":("LOGICAL-PATHNAME",),
 "19.4.10":("*DEFAULT-PATHNAME-DEFAULTS*",),
 "19.4.11":("NAMESTRING","FILE-NAMESTRING","DIRECTORY-NAMESTRING","HOST-NAMESTRING","ENOUGH-NAMESTRING"),
 "19.4.12":("PARSE-NAMESTRING",),"19.4.13":("WILD-PATHNAME-P",),
 "19.4.14":("PATHNAME-MATCH-P",),
 "19.4.15":("TRANSLATE-LOGICAL-PATHNAME",),
 "19.4.16":("TRANSLATE-PATHNAME",),
 "19.4.17":("MERGE-PATHNAMES",),
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify(corpus, inv, lower):
    assert corpus["schema"] == "d10-clhs-ch19-filenames-census/v1"
    assert corpus["status"] == "RESEARCH-CENSUS-NOT-SELECTED"
    assert corpus["source"]["dictionary_url"].startswith("https://franz.com/")
    assert corpus["source"]["merge_url"].startswith("https://franz.com/")
    assert corpus["source"]["match_url"].startswith("https://www.lispworks.com/")
    assert [f"{r['clhs_section']}:{r['source_name']}" for r in corpus["roles"]] == [
        f"{sec}:{name}" for sec in SECTIONS for name in GROUPS[sec]
    ], "19.4 order/role drift"
    assert corpus["counting"]["dictionary_positions"] == 17
    assert corpus["counting"]["name_kind_entries"] == len(corpus["roles"]) == 26
    assert corpus["counting"]["unique_source_names"] == 24
    assert corpus["counting"]["selected_additions"] == 0
    assert corpus["counting"]["ratified_additions"] == 0
    assert corpus["counting"]["assigned_coordinates"] == 0
    assert corpus["snapshot"]["D10_inventory_sha"] == "a55f307c27f17091795d75ebfcd7d051547d80bc"
    assert corpus["snapshot"]["D1_D9_foundation_sha"] == "09d1d71c39d1484dfd005a5068dbb18b76f0f0d4"
    assert corpus["snapshot"]["selected"] == 630 and corpus["snapshot"]["ratified"] == 0
    assert [r["source_kind"] for r in corpus["roles"] if r["clhs_section"] in ("19.4.1", "19.4.2")] == ["system-class","system-class"]
    assert [r["source_kind"] for r in corpus["roles"] if r["clhs_section"]=="19.4.10"] == ["special-variable"]
    assert all(r["source_kind"] in ("system-class","function","special-variable") for r in corpus["roles"])
    assert all(r["candidate_automatic"] is False for r in corpus["roles"])
    assert all(r["triage"].startswith(("REVIEW-", "HOLD-", "TYPE-")) for r in corpus["roles"])
    # Snapshot exact-name collisions are recorded as evidence; new appends
    # cannot change what the source corpus stated in the 630-row snapshot.
    assert all(r["exact_name_in_ratified_D1_D9"] is False and
               r["exact_name_in_selected_D10"] is False for r in corpus["roles"])
    assert corpus["counting"]["exact_D1_D9_matches"] == 0
    assert corpus["counting"]["exact_D10_matches"] == 0
    assert len(corpus["deep_review"]) == 3
    assert {x["name"] for x in corpus["deep_review"]} == {"MERGE-PATHNAMES","PATHNAME-MATCH-P","ENOUGH-NAMESTRING"}
    for x in corpus["deep_review"]:
        assert x["status"].startswith("HOLD-")
        assert len(x["tests"]) >= 2 and x["falsifier"] and x["dedup"]
    assert inv["domain"] == "D10" and inv["capacity"] == 1024
    assert inv["accounting"]["selected_semantic_candidates"] >= 630
    assert inv["accounting"]["ratified_d10_residents"] == 0
    assert len(inv["rows"]) == inv["accounting"]["selected_semantic_candidates"]
    assert lower["status"] == "owner-ratified"
    # If later selected, the source remains historical; requires an explicit
    # selected→ledger transition, never silently changes this census.
    new_selected = {r["semantic_name"] for r in inv["rows"]} & {
        x["source_name"] for x in corpus["roles"]
    }
    print(f"CLHS-PATHNAMES: PASS 17 dictionary entries, 26 name-role entries, "
          f"24 unique names, selected by THIS census=0, later exact-name overlaps={len(new_selected)}")


def negative_checks(corpus, inv, lower):
    changes = [
        lambda x: x["roles"].pop(),
        lambda x: x["roles"][1].update({"source_kind":"function"}),
        lambda x: x["roles"][0].update({"candidate_automatic": True}),
        lambda x: x["roles"][0].update({"exact_name_in_selected_D10":True}),
        lambda x: x["counting"].update({"selected_additions":1}),
        lambda x: x["source"].update({"dictionary_url":"https://example.invalid"}),
        lambda x: x["deep_review"][1].update({"status":"SELECTED"}),
        lambda x: x["snapshot"].update({"selected":625}),
    ]
    for n, mutate in enumerate(changes):
        other = copy.deepcopy(corpus)
        mutate(other)
        try:
            verify(other, inv, lower)
        except AssertionError:
            continue
        raise AssertionError(f"negative mutation #{n} escaped")
    print("CLHS-PATHNAMES: PASS 8/8 mutation controls rejected")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    corpus, inv, lower = read(CORPUS), read(INV), read(LOW)
    verify(corpus, inv, lower)
    if args.self_test:
        negative_checks(corpus, inv, lower)
