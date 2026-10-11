#!/usr/bin/env python3
"""Fail-closed read-only reconciliation of the unified D10 candidate catalog."""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = "knowledge/d10-candidate-database-v1.json"

class InvalidCatalog(ValueError):
    pass

def require(ok, why):
    if not ok:
        raise InvalidCatalog(why)

def digest(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def name_set(items):
    names = [row["semantic_name"].upper() for row in items]
    require(len(names) == len(set(names)), "duplicate semantic names")
    return set(names)

def verify(document: dict, root: Path = ROOT) -> dict:
    require(document.get("schema") == "sens-d10-candidate-database/v1", "schema")
    pins = document.get("source_pins", [])
    expected_paths = (
        "knowledge/d10-v7-semantic-inventory.json",
        "knowledge/d10-provisional-candidate-coordinate-queue-v1.json",
        "knowledge/d10-historical-candidate-coordinate-queue-v1.json",
        "knowledge/d10-proposal-ledger.tsv",
        "knowledge/d10-source-universe-891-20261011.json",
        "knowledge/d1-d9-foundation.json",
    )
    require(tuple(p.get("path") for p in pins) == expected_paths, "source pin membership/order")
    raw = {}
    for pin in pins:
        path = pin["path"]
        source = (root / path).read_bytes()
        if path == "knowledge/d10-proposal-ledger.tsv":
            # The historical hash remains a real archival pin. Live ledger updates
            # are allowed only when every proposal identity and law is covered below.
            require(re.fullmatch(r"[0-9a-f]{40}", pin["git_blob"]), "archival ledger SHA")
        else:
            require(digest(source) == pin["git_blob"], "source changed: " + path)
        raw[path] = source
    current, initial, historical, foundation = [
        json.loads(raw[p]) for p in (expected_paths[0], expected_paths[1], expected_paths[2], expected_paths[5])
    ]
    pointer = json.loads((root / "knowledge/d10-current-inventory.json").read_text(encoding="utf-8"))
    # v1 is a frozen 721-selected catalog, not a mutable claim that no later
    # research candidates can be admitted from it. Current D10 must retain its
    # entire source inventory byte-exact as an append-only semantic prefix.
    archive = pointer.get("historical_v7_research_inventory", {})
    require(archive.get("path") == expected_paths[0]
            and archive.get("git_blob") == pins[0]["git_blob"], "frozen v7 catalog pin drift")
    live = pointer["canonical_current"]
    live_path = (root / live["path"]).resolve()
    require(live_path.is_relative_to(root.resolve()) and live_path.is_file(), "unsafe current inventory path")
    live_bytes = live_path.read_bytes()
    require(digest(live_bytes) == live["git_blob"], "current D10 SHA drift")
    live_rows = json.loads(live_bytes)["rows"]
    require(len(live_rows) >= len(current["rows"])
            and live_rows[:len(current["rows"])] == current["rows"], "current D10 broke archived v7 prefix")
    selected = document["selected"]
    pending = document["pending"]
    excluded = document["lower_domain_name_overlaps"]
    s_names, p_names, x_names = (name_set(items) for items in (selected, pending, excluded))
    require(not (s_names & p_names or s_names & x_names or p_names & x_names), "name sets overlap")
    require(len(selected) == len(current["rows"]), "selected count")
    for i, (row, original) in enumerate(zip(selected, current["rows"])):
        require(row["semantic_name"] == original["semantic_name"]
                and row["stable_id"] == original["stable_id"]
                and row["coordinate"] == original.get("coordinate")
                and row["observable_law"] == original.get("behavior"), "selected row drift " + str(i))
        require(row["selected"] is True and row["ratified"] is False, "selection/ratification claim")
        require(row["evidence_location"] == {
            "path": expected_paths[0], "git_blob": pins[0]["git_blob"], "row_index": i,
        }, "row source pointer")
    require(all(not r["selected"] and not r["ratified"] and r["coordinate"] is None
                for r in pending), "pending became resident")
    require(all(row["classification"] == "LOWER-DOMAIN-NAME-OVERLAP-NOT-D10"
                for row in excluded), "overlap status drift")
    current_names = {r["semantic_name"].upper() for r in current["rows"]}
    initial_names = {r["semantic_name"].upper() for r in initial["provisional_candidates"]}
    history_names = {r["semantic_name"].upper() for r in historical["candidates"]} - current_names
    lower_names = {r["semantic_name"].upper() for r in initial["lower_name_overlap_review"]}
    ledger = list(csv.DictReader(io.StringIO(raw[expected_paths[3]].decode("utf-8")), delimiter="\t"))
    ledger_names = {r["semantic_name"].upper() for r in ledger}
    require(len(ledger_names) == len(ledger), "duplicate live ledger names")
    by_name = {r["semantic_name"].upper(): r for r in selected + pending}
    overlap_by_name = {r["semantic_name"].upper(): r for r in excluded}
    for proposal in ledger:
        key = proposal["semantic_name"].upper()
        pid = proposal["proposal_id"]
        if key in by_name:
            record = by_name[key]
            require(pid in record.get("proposals", []), "missing proposal identity " + pid)
            if record.get("candidate_origin") == "LEDGER-ONLY-NO-QUEUE-COORDINATE":
                require(record["observable_law"] == proposal["semantic_law"],
                        "changed ledger-only law " + pid)
        elif key in overlap_by_name:
            source = overlap_by_name[key].get("source_provenance", [])
            require(any(p.get("id") == pid for p in source if isinstance(p, dict)),
                    "changed lower-domain proposal identity " + pid)
        else:
            raise InvalidCatalog("new unaccounted proposal " + pid)
        require(proposal["status"] == "pending-review" and proposal["ratified"] == "0",
                "ledger wrongly ratified " + pid)
    proposed_extra = ledger_names - current_names - initial_names - history_names - lower_names
    require({r["semantic_name"].upper() for r in pending
             if r["candidate_origin"] == "INITIAL-SOURCE-QUEUE"} == initial_names, "initial queue lost")
    require({r["semantic_name"].upper() for r in pending
             if r["candidate_origin"] == "HISTORICAL-LISP-RESEARCH-QUEUE"} == history_names, "history lost")
    require({r["semantic_name"].upper() for r in pending
             if r["candidate_origin"] == "LEDGER-ONLY-NO-QUEUE-COORDINATE"} == proposed_extra, "ledger orphan lost")
    require(x_names == lower_names, "lower overlaps lost")
    codes = [r["coordinate"] for r in selected if r["coordinate"] is not None]
    reserved = [r["provisional_coordinate"] for r in pending
                if r["candidate_origin"] != "LEDGER-ONLY-NO-QUEUE-COORDINATE"]
    require(all(re.fullmatch(r"[01]{10}", c) for c in codes + reserved), "invalid 10-bit word")
    require(len(codes + reserved) == len(set(codes + reserved)), "coordinate collision")
    lower_r = {str(name).upper() for domain in foundation["domains"].values()
               for name in domain["residents"].values()}
    require(x_names <= lower_r, "false lower-domain collision")
    require(len(s_names | p_names | x_names) == len(s_names) + len(p_names) + len(x_names),
            "aggregate overlap")
    a = document["accounting"]
    expected = {
        "capacity": 1024,
        "selected": len(selected),
        "placed_selected": len(codes),
        "selected_without_coordinate": len(selected) - len(codes),
        "ratified": 0,
        "pending_initial_queue": len(initial_names),
        "pending_historical_queue": len(history_names),
        "pending_ledger_only": len(proposed_extra),
        "pending_total": len(pending),
        "d10_unique_selected_or_pending": len(selected) + len(pending),
        "lower_domain_name_overlaps": len(excluded),
        "total_name_catalog": len(selected) + len(pending) + len(excluded),
        "provisional_reserved_not_selected": len(reserved),
        "unoccupied_codewords": 1024 - len(codes),
        "unreserved_codewords": 1024 - len(codes) - len(reserved),
        "historical_queue_rows_already_selected": len(
            {r["semantic_name"].upper() for r in historical["candidates"]} & current_names
        ),
    }
    require(a == expected, "incorrect catalog accounting")
    require(current["accounting"]["selected_semantic_candidates"] == len(selected)
            and current["accounting"]["ratified_d10_residents"] == 0, "canonical accounting drift")
    return expected

def main():
    arg = argparse.ArgumentParser()
    arg.add_argument("--self-test", action="store_true")
    args = arg.parse_args()
    catalog = json.loads((ROOT / CATALOG).read_text(encoding="utf-8"))
    result = verify(catalog)
    if args.self_test:
        for change in (
            lambda x: x["pending"].pop(),
            lambda x: x["selected"][0].update(coordinate="1111111111"),
            lambda x: x["selected"][0].update(ratified=True),
            lambda x: x["pending"][0].update(provisional_coordinate=x["selected"][0]["coordinate"]),
            lambda x: x["source_pins"][0].update(git_blob="0"*40),
            lambda x: x["accounting"].update(pending_total=0),
            lambda x: x["pending"][-1].update(observable_law="FORGED-LEDGER-LAW"),
        ):
            mutation = copy.deepcopy(catalog)
            change(mutation)
            try:
                verify(mutation)
            except InvalidCatalog:
                continue
            raise InvalidCatalog("negative mutation escaped")
    print("D10-CATALOG PASS " + json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    try:
        main()
    except (InvalidCatalog, AssertionError, ValueError, KeyError, TypeError, OSError) as e:
        raise SystemExit("D10-CATALOG BLOCK " + str(e))
