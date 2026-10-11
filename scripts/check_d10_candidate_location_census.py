#!/usr/bin/env python3
"""Reconcile canonical D10 and every recorded proposal with archived intake slices.

Exact name matches are *not* behavioral equivalence; outputs are research indices,
not authority to assign a coordinate, select a Core resident or ratify D10.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ("existing_evidence_harvest", "research/d10/staging-20261011/d10-existing-evidence-harvest-20261011-a.json", "items"),
    ("existing_research_staging", "research/d10/staging-20261011/d10-existing-research-batch-replay-20261011.json", "entries"),
    ("historical_proposal_replay", "knowledge/d10-research-proposal-replay-20261011.json", "items"),
    ("next_tranche", "knowledge/d10-next-tranche-20261011.json", "proposals"),
)
LEDGER_FIELDS = (
    "proposal_id", "surface_uk", "surface_ukr", "semantic_name",
    "semantic_law", "width", "donor_provenance", "dedup_check",
    "ownership_test", "blocked_source", "status", "ratified",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def load(root, relative):
    return json.loads((root / relative).read_text(encoding="utf-8"))


def normalize_name(value):
    require(isinstance(value, str) and bool(value.strip()), "empty semantic name")
    return value.upper()


def report(root=ROOT):
    inv_path = "knowledge/d10-v1-semantic-inventory.json"
    inv = load(root, inv_path)
    foundation = load(root, "knowledge/d1-d9-foundation.json")
    with (root / "knowledge/d10-proposal-ledger.tsv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        require(tuple(reader.fieldnames or ()) == LEDGER_FIELDS, "ledger header drift")
        ledger = list(reader)
    selected = {}
    for item in inv["rows"]:
        name = normalize_name(item["semantic_name"])
        require(name not in selected, "duplicate selected D10 name " + name)
        selected[name] = item
    lower = defaultdict(list)
    for domain, data in foundation["domains"].items():
        for resident in data["residents"].values():
            lower[normalize_name(str(resident))].append(domain)
    requires = []
    proposal_names = set()
    proposal_ids = set()
    staging_index = defaultdict(list)
    source_sha = {}
    for label, path, key in SOURCES:
        data = load(root, path)
        source_sha[path] = source_blob(root / path)
        rows = data.get(key)
        require(isinstance(rows, list), "missing source array: " + path)
        for item in rows:
            name = normalize_name(item["semantic_name"])
            staging_index[name].append({
                "source": label, "path": path,
                "source_git_blob": source_sha[path],
                "original_donor_status": item.get("original_donor_status"),
            })
    for row in ledger:
        name = normalize_name(row["semantic_name"])
        require(row["proposal_id"] and row["proposal_id"] not in proposal_ids,
                "duplicate proposal id " + row["proposal_id"])
        require(name not in proposal_names, "duplicate proposal name " + name)
        require(row["status"] == "pending-review" and row["ratified"] == "0",
                "proposal is marked admitted or ratified: " + name)
        proposal_names.add(name)
        proposal_ids.add(row["proposal_id"])
        if name in selected:
            level = "ALREADY_SELECTED_D10"
        elif name in lower:
            level = "EXACT_NAME_MATCH_RATIFIED_D1_D9_REVIEW"
        else:
            level = "UNSELECTED_NO_EXACT_NAME_MATCH_REVIEW"
        requires.append({
            "proposal_id": row["proposal_id"],
            "semantic_name": row["semantic_name"],
            "surface_uk": row["surface_uk"],
            "surface_ukr": row["surface_ukr"],
            "classification": level,
            "d1_d9_exact_name_domains": lower.get(name, []),
            "selected_d10_stable_id": selected[name]["stable_id"] if name in selected else None,
            "semantic_law": row["semantic_law"],
            "donor_provenance": row["donor_provenance"],
            "dedup_check": row["dedup_check"],
            "original_ledger_status": row["status"],
            "supporting_staging": staging_index.get(name, []),
            "coordinate": None,
            "ratified": False,
        })
    classes = dict(Counter(p["classification"] for p in requires))
    require(len(requires) == len(proposal_names), "proposal name collision")
    require(inv["accounting"]["selected_semantic_candidates"] == len(selected), "canonical selected accounting drift")
    other_staged = sorted(set(staging_index) - proposal_names - set(selected))
    return {
        "schema": "d10-all-candidate-location-census/v1",
        "authority": "RESEARCH-INDEX-ONLY-NO-NEW-SELECTION",
        "inventory": {"path": inv_path, "git_blob": source_blob(root / inv_path),
                      "selected": len(selected), "capacity": inv["capacity"],
                      "placed": sum(x.get("coordinate") is not None for x in selected.values()),
                      "ratified": inv["accounting"]["ratified_d10_residents"]},
        "ledger": {"path": "knowledge/d10-proposal-ledger.tsv",
                   "git_blob": source_blob(root / "knowledge/d10-proposal-ledger.tsv"),
                   "proposals": len(requires)},
        "foundation": {"path": "knowledge/d1-d9-foundation.json",
                       "git_blob": source_blob(root / "knowledge/d1-d9-foundation.json")},
        "counts": {
            "selected_main": len(selected), "distinct_proposal_names": len(proposal_names),
            "proposal_already_selected_d10": classes.get("ALREADY_SELECTED_D10", 0),
            "proposal_exact_name_in_ratified_d1_d9": classes.get("EXACT_NAME_MATCH_RATIFIED_D1_D9_REVIEW", 0),
            "proposal_unselected_no_exact_name_match": classes.get("UNSELECTED_NO_EXACT_NAME_MATCH_REVIEW", 0),
            "selected_plus_proposal_unique_name_count": len(set(selected) | proposal_names),
            "archival_staging_distinct_names": len(staging_index),
            "staging_names_absent_from_both": len(other_staged),
            "remaining_d10_capacity_not_proven_laws": inv["capacity"] - len(selected),
        },
        "staging_source_git_blobs": source_sha,
        "staging_untracked_names": other_staged,
        "proposal_entries": requires,
        "caveats": [
            "Exact-name collision is not a behavioral duplicate proof.",
            "No-lexical-overlap is not a proof of distinct semantic law or Core ownership.",
            "19/10/32/8 staging items overlap canonical ledger; count distinct identities, not files.",
            "This census does not yet cover all historical PRs and 87 owner repositories exhaustively.",
            "Never create a D10 coordinate or ratification from this evidence index."
        ],
    }


def self_test(original):
    names = [x["semantic_name"].upper() for x in original["proposal_entries"]]
    require(len(names) == len(set(names)), "self-test proposal uniqueness")
    counter = original["counts"]
    require(counter["proposal_already_selected_d10"] +
            counter["proposal_exact_name_in_ratified_d1_d9"] +
            counter["proposal_unselected_no_exact_name_match"] ==
            counter["distinct_proposal_names"], "classification partition invalid")
    require(counter["selected_plus_proposal_unique_name_count"] ==
            counter["selected_main"] + counter["distinct_proposal_names"] -
            counter["proposal_already_selected_d10"], "union arithmetic invalid")
    require(counter["archival_staging_distinct_names"] -
            counter["staging_names_absent_from_both"] >= 0, "invalid staging census")
    return 4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    result = report(args.root)
    if args.self_test:
        result["self_test_checks_passed"] = self_test(result)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    print(json.dumps(result["counts"], sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
