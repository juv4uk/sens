#!/usr/bin/env python3
"""A census, not a proof that 891 lexical names are 891 independent D10 laws."""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = "knowledge/d10-complete-existing-candidate-name-census-20261011.json"
SOURCE_FILES = (
    "knowledge/d10-v1-semantic-inventory.json",
    "knowledge/d10-proposal-ledger.tsv",
    "knowledge/d1-d9-foundation.json",
    "knowledge/d10-library-source-symbols-v1.json",
    "knowledge/d10-interest-proposal-v1.json",
)

def require(ok, message):
    if not ok:
        raise ValueError(message)

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def git_blob(path):
    raw = (ROOT / path).read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def verify(doc, inventory, ledger, foundation, library, interests):
    require(doc["schema"] == "d10-complete-candidate-source-census/v1"
            and doc["status"] == "SCOPE-LIMITED-NAME-CENSUS-NO-AUTHORITY",
            "census forged to grant authority")
    require([p["path"] for p in doc["pinned"]] == list(SOURCE_FILES),
            "source list changed")
    selected = {r["semantic_name"].upper() for r in inventory["rows"]}
    ratified = {str(x).upper() for d in foundation["domains"].values()
                for x in d["residents"].values()}
    require(len(selected) == len(inventory["rows"]) == 698,
            "selected inventory count unexpected")
    require(doc["selected"] == 698, "census selected count forged")
    ledger_names = [p["semantic_name"].upper() for p in ledger]
    library_names = [p["name"].upper() for p in library["candidates"]]
    interest_names = [x.upper() for grp in interests["families"].values()
                      for x in grp["candidate_functions"]]
    require(doc["source_counts"] == {"ledger": len(ledger_names),
            "library": len(library_names), "interest": len(interest_names)},
            "source counts tampered")
    require(len(ledger_names) == 130 and len(library_names) == 102
            and len(interest_names) == 52, "source counts drift")
    names = set(ledger_names) | set(library_names) | set(interest_names)
    require(len(doc["names"]) == len(names) == 284,
            "census omitted or doubled a recorded name")
    indexed = {n["semantic_name"]: n for n in doc["names"]}
    require(set(indexed) == names and len(indexed) == len(doc["names"]),
            "census missing or fabricated source name")
    for n, rec in indexed.items():
        require(rec["already_selected"] == (n in selected)
                and rec["ratified_d1_d9_name_match"] == (n in ratified),
                "name's authority classification forged")
        parents = set(x["source"] for x in rec["origins"])
        real_parents = set()
        if n in ledger_names: real_parents.add("PROPOSAL_LEDGER")
        if n in library_names: real_parents.add("LIBRARY_SOURCE_SYMBOL")
        if n in interest_names: real_parents.add("OWNER_INTEREST_FAMILY")
        require(parents == real_parents, "source claim drift")
    extras = names - selected
    require(doc["extra_unique_names"] == len(extras) == 193
            and doc["selected_plus_extra_name_union"] == len(selected | names) == 891,
            "name-union arithmetic forged")
    require(not any("coordinate" in x for x in doc["names"]),
            "census invented 10-bit positions")
    return {"selected": 698, "source_names": 284,
            "unselected_source_names": 193,
            "total_unique_names_not_verified_laws": 891}

def adversarial(doc, inv, led, found, library, interests):
    cases = [
        ("invented name", lambda d,i,l,f,b,p: d["names"][0].__setitem__("semantic_name","UNVERIFIED-NEW")),
        ("fake selected", lambda d,i,l,f,b,p: d.__setitem__("selected",1024)),
        ("false overlap", lambda d,i,l,f,b,p: d["names"][0].__setitem__("already_selected", not d["names"][0]["already_selected"])),
        ("remove source", lambda d,i,l,f,b,p: d["names"][1]["origins"].clear()),
        ("fake coordinate", lambda d,i,l,f,b,p: d["names"][1].__setitem__("coordinate","0000000000")),
        ("hide donor", lambda d,i,l,f,b,p: p["families"]["chess"]["candidate_functions"].pop()),
    ]
    for label, mutate in cases:
        a = [copy.deepcopy(x) for x in (doc,inv,led,found,library,interests)]
        mutate(*a)
        try:
            verify(*a)
        except (ValueError, KeyError, TypeError, IndexError):
            continue
        raise RuntimeError("unsafe source-census mutation passed: " + label)
    return len(cases)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    doc = read(ARTIFACT)
    inv = read(SOURCE_FILES[0])
    with (ROOT / SOURCE_FILES[1]).open(encoding="utf-8", newline="") as f:
        ledger = list(csv.DictReader(f, delimiter="\t"))
    foundation,library,interests = [read(x) for x in SOURCE_FILES[2:]]
    for pin in doc["pinned"]:
        require(git_blob(pin["path"]) == pin["git_blob"], "source snapshot changed: "+pin["path"])
    res = verify(doc,inv,ledger,foundation,library,interests)
    if args.self_test:
        res["negative_tests_rejected"] = adversarial(
            doc, inv, ledger, foundation, library, interests)
    print(json.dumps(res, sort_keys=True))

if __name__ == "__main__":
    main()
