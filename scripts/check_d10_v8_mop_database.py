#!/usr/bin/env python3
"""Verify D10 v8 research-only intake from the frozen candidate database.

No witness is claimed executed; no D10 address or ratification is conferred.
All source pins are checked against bytes, not human-readable file names.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / "knowledge"
NAMES = (
    "CLASS-DIRECT-SLOTS",
    "CLASS-PRECEDENCE-LIST",
    "GENERIC-FUNCTION-METHODS",
    "GENERIC-FUNCTION-ARGUMENT-PRECEDENCE-ORDER",
)
FROZEN_V7 = "6a45275241717dafa6a6c9ccafae1e9ad819b306"


def need(condition, reason):
    if not condition:
        raise ValueError("D10_V8_BLOCK: " + reason)


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\\0" + data).hexdigest()


def read_pinned(relative, expected, root=ROOT):
    path = (root / relative).resolve()
    need(path.is_relative_to(root.resolve()) and path.is_file(), "unsafe or absent source: " + relative)
    raw = path.read_bytes()
    need(blob(raw) == expected, "source SHA drift: " + relative)
    return json.loads(raw)


def verify_payload(pointer, v7, v8, manifest, catalog, donor, ledger):
    need(pointer["canonical_current"]["path"] == "knowledge/d10-v8-semantic-inventory.json",
         "unexpected canonical research path")
    need(v8["schema"] == "d10-v8-semantic-inventory/v1", "v8 schema")
    need(v8["status"] == "RESEARCH-UNRATIFIED-PARTIAL", "research-only status")
    need(v8["previous_inventory"]["git_blob"] == FROZEN_V7, "v7 predecessor pin")
    need(v8["rows"][:721] == v7["rows"], "v7 archival prefix rewritten")
    need(len(v8["rows"]) == 725, "expected exactly four appended laws")
    need(manifest["resulting"] == {
        "selected": 725, "placed": 719, "unplaced": 6,
        "remaining": 299, "ratified": 0,
    }, "manifest accounting")
    suffix = v8["rows"][721:]
    need(tuple(row["semantic_name"] for row in suffix) == NAMES, "new semantic identities/order")
    need(len({row["stable_id"] for row in v8["rows"]}) == 725, "duplicate stable ID")
    need(len({row["semantic_name"].casefold() for row in v8["rows"]}) == 725, "duplicate semantic name")
    placed = [row["coordinate"] for row in v8["rows"] if row.get("coordinate") is not None]
    need(len(placed) == len(set(placed)) == 719
         and all(len(code) == 10 and set(code) <= {"0", "1"} for code in placed),
         "duplicate or malformed placed coordinate")
    a = v8["accounting"]
    need((a["selected_semantic_candidates"], a["placed_selected_candidates"],
          a["unplaced_selected_candidates"], a["remaining_semantic_inventory"],
          a["ratified_d10_residents"], a["mop_database_research_candidates_added"])
         == (725, 719, 6, 299, 0, 4), "current inventory accounting")
    found = {r["semantic_name"]: r for r in catalog["pending"]}
    evidence = {r["source_name"]: r for r in donor["entries"]}
    receipts = {r["semantic_name"]: r for r in manifest["selected"]}
    ledger_by_id = {r["proposal_id"]: r for r in ledger}
    need(len(receipts) == 4 and set(receipts) == set(NAMES), "manifest membership")
    for row in suffix:
        name = row["semantic_name"]
        need(name in found and name in evidence and name in receipts,
             "candidate absent from immutable database/source: " + name)
        candidate, source, receipt = found[name], evidence[name], receipts[name]
        need(candidate["selected"] is False and candidate["ratified"] is False
             and candidate["coordinate"] is None, "database source is not pending: " + name)
        need(source["selected"] is False and source["coordinate"] is None
             and source["ratified"] is False, "MOP source is not a research candidate: " + name)
        need(row["behavior"] == source["semantic_law"]
             and receipt["source_semantic_law"] == source["semantic_law"],
             "donor law drift: " + name)
        need(row["positive_witnesses"] == source["positive_witnesses"]
             and row["falsifier"] == source["falsifier"]
             and bool(source["positive_witnesses"]) and bool(source["falsifier"]),
             "positive/falsifier evidence missing: " + name)
        need(row["source_path"] == manifest["source_donor"]["path"]
             and row["source_git_blob"] == manifest["source_donor"]["git_blob"],
             "source provenance drift: " + name)
        need(row["stable_id"] == receipt["stable_id"]
             and row["proposal_id"] == receipt["proposal_id"],
             "candidate/ledger identity drift: " + name)
        proposal = ledger_by_id.get(row["proposal_id"])
        need(proposal is not None and proposal["semantic_name"] == name
             and proposal["semantic_law"] == candidate["observable_law"]
             and proposal["status"] == "pending-review" and proposal["ratified"] == "0",
             "ledger proposal drift: " + name)
        need(row["coordinate"] is None and row["ratified_resident"] is False
             and row["physical_t5_authorized"] is False,
             "new coordinate or authority claim: " + name)
        need(row["owner_core_vs_derived_review"] == "PENDING"
             and row["witness_independence"] == "PENDING"
             and receipt["F2"] == "HOLD_NOT_RUN"
             and receipt["F3"] == "HOLD_DEDUP_UNPROVEN"
             and receipt["F4"] == "NO_COORDINATE_PROPOSED",
             "unproven witness/dedup promoted to PASS: " + name)
    return {"selected": 725, "placed": 719, "unplaced": 6, "remaining": 299, "ratified": 0}


def check(root=ROOT, self_test=False):
    k = root / "knowledge"
    ptr = json.loads((k / "d10-current-inventory.json").read_text())
    frozen = ptr["historical_v7_research_inventory"]
    need(frozen["path"] == "knowledge/d10-v7-semantic-inventory.json"
         and frozen["git_blob"] == FROZEN_V7, "frozen v7 pointer changed")
    canonical = ptr["canonical_current"]
    v7 = read_pinned(frozen["path"], FROZEN_V7, root)
    v8 = read_pinned(canonical["path"], canonical["git_blob"], root)
    selection = ptr["current_v8_mop_database_selection"]
    manifest = read_pinned(selection["manifest"]["path"], selection["manifest"]["git_blob"], root)
    catalog = read_pinned(manifest["source_database"]["path"], manifest["source_database"]["git_blob"], root)
    donor = read_pinned(manifest["source_donor"]["path"], manifest["source_donor"]["git_blob"], root)
    need(manifest["source_database"] == selection["source_database"], "database provenance pointer")
    need((canonical["selected"], canonical["placed"], canonical["unplaced"], canonical["ratified"])
         == (725, 719, 6, 0), "canonical pointer accounting")
    with (k / "d10-proposal-ledger.tsv").open(newline="", encoding="utf-8") as f:
        ledger = list(csv.DictReader(f, delimiter="\\t"))
    result = verify_payload(ptr, v7, v8, manifest, catalog, donor, ledger)
    if self_test:
        for change in (
            lambda p, v, m: v["rows"][0].update(behavior="FORGED"),
            lambda p, v, m: v["rows"][-1].update(coordinate="0000000000"),
            lambda p, v, m: v["rows"][-1].update(ratified_resident=True),
            lambda p, v, m: v["rows"][-1].update(witness_independence="PASS"),
            lambda p, v, m: m["selected"][0].update(F3="PASS"),
            lambda p, v, m: v["rows"][-1].update(behavior="FORGED"),
        ):
            p, v, m = copy.deepcopy(ptr), copy.deepcopy(v8), copy.deepcopy(manifest)
            change(p, v, m)
            try:
                verify_payload(p, v7, v, m, catalog, donor, ledger)
            except ValueError:
                continue
            raise ValueError("D10_V8_BLOCK: negative mutation escaped")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        print("D10-V8-MOP PASS " + json.dumps(check(self_test=args.self_test), sort_keys=True))
    except (OSError, KeyError, TypeError, ValueError, IndexError) as error:
        raise SystemExit(str(error))


if __name__ == "__main__":
    main()
