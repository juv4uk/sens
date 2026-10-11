#!/usr/bin/env python3
"""Fail-closed research-only D10 intake of 23 pre-existing source-pinned proposals.

This does not prove Core primitiveness, native SENS execution, ratification,
or 10-bit placement. It rejects fabricated names, missing donor files,
source drift, absent ledger entries and unaccounted inventory growth.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF_PATH = "knowledge/d10-existing-ledger-semantic-tranche23-20261011.json"
SOURCE_INVENTORY = "4c803abf0f22582ef8234d9ba60ca4796d433eb5"
CURRENT_INVENTORY = "96f9a5e464c4a0f689065bf88b6d9aee48ad6d49"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def git_blob(path):
    raw = (ROOT / path).read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def verify(doc, inv, ledger, foundation, history, source_check=True):
    require(doc.get("schema") == "d10-existing-canonical-proposal-tranche23/v1",
            "proof document schema changed")
    require(doc.get("status") == "SELECTED-RESEARCH-NOT-RATIFIED",
            "proof document falsely claims ratification")
    require(doc.get("source_inventory_sha") == SOURCE_INVENTORY,
            "source 675-row inventory SHA changed")
    require(doc.get("selected_before") == 675 and doc.get("selected_after") == 698
            and doc.get("remaining_after") == 326
            and doc.get("forced_coordinates_unchanged") == 256
            and doc.get("ratified") == 0, "dossier accounting drift")
    require(len(doc["records"]) == 23 and len(doc["sources"]) == 18,
            "source batch size changed")
    names = [x["semantic_name"] for x in doc["records"]]
    require(len(set(names)) == 23, "duplicate identity in proposal tranche")
    require(len(inv["rows"]) == 698, "inventory length inconsistent")
    require([x["semantic_name"] for x in inv["rows"][-23:]] == names,
            "selection is not an append-only 23-meaning suffix")
    require(inv["accounting"] == {
        "selected_semantic_candidates": 698,
        "law_forced_coordinates": 256,
        "unplaced_selected_candidates": 442,
        "remaining_semantic_inventory": 326,
        "ratified_d10_residents": 0,
    }, "accounting mismatch")
    require(inv["sources"][-1] == PROOF_PATH,
            "source dossier not appended to canonical source list")
    require(len(set(x["semantic_name"] for x in inv["rows"])) == 698
            and len(set(x["stable_id"] for x in inv["rows"])) == 698,
            "duplicate full inventory identity")
    latest = history["transitions"][-1]
    require(latest["previous_inventory_blob_sha"] == SOURCE_INVENTORY
            and latest["resulting_inventory_blob_sha"] == CURRENT_INVENTORY
            and latest["previous_selected"] == 675
            and latest["resulting_selected"] == 698
            and latest["delta_selected"] == 23
            and latest["coordinates_added"] == 0
            and latest["ratified_added"] == 0
            and latest["appended_sources"] == [PROOF_PATH]
            and latest["added_stable_ids"] == [x["stable_id"] for x in doc["records"]],
            "machine append history drift")
    lower = {str(v).upper() for d in foundation["domains"].values()
             for v in d["residents"].values()}
    require(not (set(names) & lower), "D1-D9 exact-name collision")
    chosen = {x["semantic_name"]: x for x in inv["rows"][-23:]}
    records = {x["semantic_name"]: x for x in ledger if x["semantic_name"] in names}
    require(len(records) == 23, "missing proposal from source ledger")
    files = {(p["path"], p["sha"]) for p in doc["sources"]}
    require(len(files) == 18 and
            len({p["path"] for p in doc["sources"]}) == 18,
            "source files not unique")
    if source_check:
        for path, sha in files:
            require(git_blob(path) == sha, "original donor Git blob changed: " + path)
    for item in doc["records"]:
        name = item["semantic_name"]
        row, proposal = chosen[name], records[name]
        require(item["selected_research_only"] is not False if "selected_research_only" in item else True,
                "research-only flag false")
        require(item["research_selection"] is True
                and item["coordinate"] is None
                and item["ratified"] is False
                and item["physical_t5_authorized"] is False,
                "evidence falsely assigns authority")
        require((item["source_path"], item["source_git_blob"]) in files,
                "candidate donor outside pinned source manifest")
        require(row["historical_source_blob"] == item["source_git_blob"]
                and row["source_proposal_id"] == item["proposal_id"]
                and item["proposal_id"] == proposal["proposal_id"],
                "source ID mismatch")
        require(row["stable_id"] == item["stable_id"]
                and row["behavior"] == item["observable_law"]
                and proposal["semantic_law"] == item["observable_law"]
                and bool(item["observable_law"]), "semantic law mismatch")
        require(row["surface_uk"] == item["surface_uk"] == proposal["surface_uk"]
                and row["surface_ukr"] == item["surface_ukr"] ==
                proposal["surface_ukr"], "textual surface differs from proposal")
        require(row["status"] == "SELECTED-RESEARCH-CANDIDATE"
                and row["coordinate"] is None and row["coordinate_basis"] == "UNPLACED"
                and row["ratified_resident"] is False
                and row["physical_t5_authorized"] is False
                and row["native_sens_oracle_verified"] is False,
                "source research promoted to unauthorized Core/codec status")
        require(proposal["status"] == "pending-review" and
                proposal["ratified"] == "0", "research proposal falsely ratified")
        require(proposal["dedup_check"] ==
                f"D1-D9@{doc['foundation_sha']}=NO-MATCH;"
                f"D10@{SOURCE_INVENTORY}=NO-MATCH",
                "proposal dedup not keyed to exact previous inventory")
        require("CORE-VS-DERIVED-PENDING" == row["owner_review"],
                "Core-vs-library owner review erased")
    return {"selected": 698, "selected_added": 23, "sources_pinned": 18,
            "coordinates": 256, "unplaced": 442, "remaining": 326,
            "ratified": 0, "native_oracle_proved": False}


def adversarial(doc, inv, ledger, foundation, history):
    controls = [
        ("fake-name", lambda d, i, l, f, h:
         d["records"][0].__setitem__("semantic_name", "INVENTED-MEANING")),
        ("fake-law", lambda d, i, l, f, h:
         i["rows"][-1].__setitem__("behavior", "UNPROVED")),
        ("fake-code", lambda d, i, l, f, h:
         i["rows"][-1].__setitem__("coordinate", "0000000000")),
        ("fake-ratification", lambda d, i, l, f, h:
         i["rows"][-3].__setitem__("ratified_resident", True)),
        ("source-sha", lambda d, i, l, f, h:
         d["records"][2].__setitem__("source_git_blob", "0" * 40)),
        ("missing-source", lambda d, i, l, f, h: d["sources"].pop()),
        ("missing-ledger", lambda d, i, l, f, h: l.pop(
         next(j for j, p in enumerate(l) if p["semantic_name"] == d["records"][0]["semantic_name"]))),
        ("history-forgery", lambda d, i, l, f, h:
         h["transitions"][-1].__setitem__("resulting_selected", 1024)),
        ("native-oracle-lie", lambda d, i, l, f, h:
         i["rows"][-2].__setitem__("native_sens_oracle_verified", True)),
    ]
    for label, mutation in controls:
        d, i, l, f, h = [copy.deepcopy(o) for o in (doc, inv, ledger, foundation, history)]
        mutation(d, i, l, f, h)
        try:
            verify(d, i, l, f, h, source_check=False)
        except (KeyError, ValueError, IndexError, TypeError):
            continue
        raise RuntimeError("negative control accepted: " + label)
    return len(controls)


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--self-test", action="store_true")
    args = cli.parse_args()
    doc = read(PROOF_PATH)
    inv = read("knowledge/d10-v1-semantic-inventory.json")
    foundation = read("knowledge/d1-d9-foundation.json")
    history = read("knowledge/d10-selection-transition-history.json")
    with (ROOT / "knowledge/d10-proposal-ledger.tsv").open(
        encoding="utf-8", newline=""
    ) as f:
        ledger = list(csv.DictReader(f, delimiter="\t"))
    verdict = verify(doc, inv, ledger, foundation, history)
    if args.self_test:
        verdict["negative_mutations_rejected"] = adversarial(
            doc, inv, ledger, foundation, history)
    print(json.dumps(verdict, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
