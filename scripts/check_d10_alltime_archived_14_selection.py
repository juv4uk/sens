#!/usr/bin/env python3
"""Source-pin 14 archived laws selected in D10 without coordinates or ratification.

Distinguish old research-HOLD snapshots from new research-only semantic selection.
Fail closed under normal Python and -O. Never grant runtime or Core authority.
"""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = "knowledge/d10-alltime-existing-research-selected-batch14-20261011.json"
ARCHIVE = "research/d10/staging-20261011/d10-existing-research-batch-replay-20261011.json"
PREVIOUS = "415f3516d599eb0aa6b3f50fb659a022ba0d758e"
FOUNDATION_BLOB = "09d1d71c39d1484dfd005a5068dbb18b76f0f0d4"

def require(ok, error):
    if not ok:
        raise ValueError(error)

def data(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def blob(path):
    raw = (ROOT / path).read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def verify(proof, archive, inv, foundation, ledger, history):
    require(proof.get("schema") == "sens-d10-archival-existing-evidence-selection-batch14/v1",
            "proof schema changed")
    require(proof.get("status") == "RESEARCH-SELECTED-OWNER-CORE-REVIEW-PENDING",
            "proof falsely ratified")
    require(proof.get("preselection_inventory_blob") == PREVIOUS and
            proof.get("source_archive_blob") == blob(ARCHIVE), "pinned source changed")
    require(proof.get("baseline") == 661 and proof.get("selected_after") == 675,
            "source projection mismatch")
    require(archive.get("verified_entry_count") == 19, "original archival corpus changed")
    src = {x["semantic_name"]: x for x in archive["entries"]}
    records = proof["records"]
    require(len(records) == 14, "exactly 14 archived names required")
    names = [x["semantic_name"] for x in records]
    require(len(set(names)) == 14, "duplicate historical name")
    require(len(inv["rows"]) == 675 and
            [x["semantic_name"] for x in inv["rows"][-14:]] == names,
            "canonical selected suffix not append-only")
    require(len({x["stable_id"] for x in inv["rows"]}) == 675 and
            len({x["semantic_name"] for x in inv["rows"]}) == 675,
            "duplicate canonical D10 identity")
    require(inv["sources"][-1] == DOSSIER, "proof not appended to inventory.sources")
    require(inv["accounting"] == {
        "selected_semantic_candidates": 675, "law_forced_coordinates": 256,
        "unplaced_selected_candidates": 419, "remaining_semantic_inventory": 349,
        "ratified_d10_residents": 0,
    }, "D10 accounting drift")
    prev = history["transitions"][-1]
    require(prev["previous_inventory_blob_sha"] == PREVIOUS
            and prev["resulting_selected"] == 675 and
            prev["delta_selected"] == 14
            and prev["added_stable_ids"] == [x["stable_id"] for x in records]
            and prev["appended_sources"] == [DOSSIER],
            "historical 14-law SHA transition mismatches")
    lower = {str(v).upper() for o in foundation["domains"].values()
             for v in o["residents"].values()}
    require(not (set(names) & lower), "ratified D1-D9 exact-name collision")
    proposals = {p["semantic_name"]: p for p in ledger if p["semantic_name"] in names}
    require(len(proposals) == 14, "missing/duplicate proposal for archived selection")
    donors = set()
    for record, resident in zip(records, inv["rows"][-14:]):
        name = record["semantic_name"]
        old = src.get(name)
        require(old is not None, "no historical source law for " + name)
        require(old["semantic_law"] == record["observable_law"] == resident["behavior"],
                "observable semantic law changed: " + name)
        require(old["falsifiers"] == record["falsifiers"] == resident["falsifiers"],
                "falsifier rewritten: " + name)
        require(old["positive_witnesses"] == record["positive_witnesses"]
                == resident["positive_witnesses"], "positive witness rewritten")
        require(record["historical_review_status"] == old["original_donor_status"]
                and record["owner_core_vs_derived"] == old["owner_core_library_review"],
                "archived HOLD or Core review changed")
        require(record["donor_path"] == old["source_path"]
                and record["donor_blob"] == old["donor_blob_sha"], "source path or Git SHA changed")
        if record["donor_path"] not in donors:
            require(blob(record["donor_path"]) == record["donor_blob"],
                    "source file changed after historical evidence")
            donors.add(record["donor_path"])
        require(resident["stable_id"] == record["stable_id"]
                and resident["status"] == "SELECTED-RESEARCH-CANDIDATE",
                "unapproved resident identity")
        require(resident["coordinate"] is None and
                resident["coordinate_basis"] == "UNPLACED" and
                resident["ratified_resident"] is False and
                resident["physical_t5_authorized"] is False,
                "proof invented code, ratification, or runtime authority")
        require(record["selected_research_only"] is True and
                record["coordinate"] is None and record["ratified"] is False,
                "proof changed approved scope")
        require(resident["surface_uk"] == record["surface_uk"] and
                resident["surface_ukr"] == record["surface_ukr"], "canonical surfaces changed")
        p = proposals[name]
        require(p["surface_uk"] == record["surface_uk"] and
                p["surface_ukr"] == record["surface_ukr"], "proposal surfaces changed")
        require(p["dedup_check"] ==
                f"D1-D9@{FOUNDATION_BLOB}=NO-MATCH;D10@{PREVIOUS}=NO-MATCH",
                "preselection ledger semantic check missing")
        require(p["status"] == "pending-review" and p["ratified"] == "0",
                "proposal unexpectedly ratified")
        require(bool(record["observable_law"]) and bool(record["positive_witnesses"])
                and len(record["falsifiers"]) >= 2, "unproved source candidate")
    require(len(donors) == 11, "not all independent archival files covered")
    return {"selected": 675, "new": 14, "sources_checked": len(donors),
            "placed": 256, "unplaced": 419, "missing": 349, "ratified": 0}

def verify_promoted(name, inventory):
    """Accept a formerly HOLD donor only after checking the entire subsequent
    source-pinned research admission. The historical donor stays unchanged."""
    proof, archive, foundation, history = (
        data(DOSSIER), data(ARCHIVE), data("knowledge/d1-d9-foundation.json"),
        data("knowledge/d10-selection-transition-history.json"))
    with (ROOT / "knowledge/d10-proposal-ledger.tsv").open(
        "r", encoding="utf-8", newline="") as f:
        ledger = list(csv.DictReader(f, delimiter="\t"))
    verdict = verify(proof, archive, inventory, foundation, ledger, history)
    require(verdict["new"] == 14, "full archive admission not proved")
    matches = [row for row in inventory["rows"] if row["semantic_name"] == name]
    require(len(matches) == 1 and name in {
        item["semantic_name"] for item in proof["records"]},
        "candidate lacks independent source-pinned selected evidence")
    return matches[0]


def negative_tests(proof, archive, inv, foundation, ledger, history):
    cases = [
        ("missing law", lambda p, a, i, f, l, h: p["records"][0].__setitem__("observable_law", "")),
        ("fake coordinate", lambda p, a, i, f, l, h: i["rows"][-1].__setitem__("coordinate", "1111111111")),
        ("ratification", lambda p, a, i, f, l, h: i["rows"][-2].__setitem__("ratified_resident", True)),
        ("historical source", lambda p, a, i, f, l, h: p["records"][2].__setitem__("donor_blob", "0"*40)),
        ("old HOLD erased", lambda p, a, i, f, l, h: p["records"][3].__setitem__("historical_review_status", "RATIFIED")),
        ("proposal false SHA", lambda p, a, i, f, l, h: next(x for x in l if x["semantic_name"]==p["records"][0]["semantic_name"]).__setitem__("dedup_check", "PENDING")),
        ("missing row", lambda p, a, i, f, l, h: i["rows"].pop()),
        ("history forged", lambda p, a, i, f, l, h: h["transitions"][-1].__setitem__("resulting_selected", 1024)),
    ]
    for name, edit in cases:
        p, a, i, f, l, h = copy.deepcopy(proof), copy.deepcopy(archive), copy.deepcopy(inv), copy.deepcopy(foundation), copy.deepcopy(ledger), copy.deepcopy(history)
        edit(p, a, i, f, l, h)
        try:
            verify(p, a, i, f, l, h)
        except (ValueError, KeyError, IndexError, TypeError):
            continue
        raise RuntimeError("unsafe mutation accepted: " + name)
    return len(cases)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    proof, archive, inv, foundation, history = map(data, (
        DOSSIER, ARCHIVE, "knowledge/d10-v1-semantic-inventory.json",
        "knowledge/d1-d9-foundation.json", "knowledge/d10-selection-transition-history.json"))
    with (ROOT / "knowledge/d10-proposal-ledger.tsv").open(
        "r", encoding="utf-8", newline="") as f:
        ledger = list(csv.DictReader(f, delimiter="\t"))
    outcome = verify(proof, archive, inv, foundation, ledger, history)
    if args.self_test:
        outcome["negative_mutations_rejected"] = negative_tests(
            proof, archive, inv, foundation, ledger, history)
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
