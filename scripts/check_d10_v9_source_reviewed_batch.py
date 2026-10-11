#!/usr/bin/env python3
"""Fail-closed D10 v9 archival research-only check.

F1-pinned names are preliminary. This verifier NEVER certifies F2/F3 or Core.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def need(ok, description):
    if not ok:
        raise ValueError("D10_V9_BLOCK: " + description)


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def pinned(root, relative, expected):
    target = (root / relative).resolve()
    need(target.is_relative_to(root.resolve()) and target.is_file(), "missing or unsafe " + relative)
    raw = target.read_bytes()
    need(blob(raw) == expected, "SHA mismatch " + relative)
    return raw


def verify_rows(v8, v9, manifest, source, foundation):
    need(v9["schema"] == "d10-v9-semantic-inventory/v1"
         and v9["status"] == "RESEARCH-UNRATIFIED-PARTIAL", "v9 schema/status")
    need(v9["rows"][:725] == v8["rows"], "v8 prefix rewritten")
    need(len(v9["rows"]) == 759, "759 candidates required in fixed v9 snapshot")
    need(v9["previous_inventory"]["git_blob"] == manifest["source_current"]["git_blob"],
         "v8 predecessor changed")
    need(manifest["counts"] == {
        "selected_added": 34, "prior_selected": 725, "result_selected": 759,
        "prior_placed": 719, "result_placed": 719,
        "prior_unplaced": 6, "result_unplaced": 40, "remaining": 265, "ratified": 0
    }, "batch accounting drift")
    head, *lines = source.decode("utf-8").splitlines()
    cols = head.split("\t")
    need("candidate_id" in cols and "semantic_name" in cols
         and "semantic_law" in cols and "source_pin" in cols
         and "donor_provenance" in cols and "reason" in cols, "source schema")
    records = {}
    with __import__("io").StringIO(source.decode("utf-8")) as stream:
        for row in csv.DictReader(stream, delimiter="\t", strict=True):
            need(None not in row and all(v is not None for v in row.values()),
                 "malformed source record")
            records.setdefault(row["semantic_name"], []).append(row)
    lower = {str(name).upper() for domain in foundation["domains"].values()
             for name in domain.get("residents", {}).values()}
    seen = {row["semantic_name"].casefold() for row in v8["rows"]}
    need(len(seen) == len(v8["rows"]), "v8 semantic-name collision")
    need(len(manifest["candidates"]) == 34, "batch row loss")
    for selected, proof in zip(v9["rows"][725:], manifest["candidates"]):
        name = selected["semantic_name"]
        need(name == proof["name"] and name.casefold() not in seen,
             "identity mismatch or repeated name")
        seen.add(name.casefold())
        need(name.upper() not in lower, "exact D1-D9 surface collision")
        matches = records.get(name, [])
        need(matches and len(matches) == len(proof["sources"]),
             "source identity count drift " + name)
        need(len({r["semantic_law"].strip() for r in matches}) == 1,
             "conflicting source laws " + name)
        need(all(r["reason"] == "EXCLUDE_NO_WITNESS" and r["semantic_law"].strip() == proof["law"]
                 and r["donor_provenance"] and len(r["source_pin"]) == 40 for r in matches),
             "source law/provenance drift " + name)
        need(selected["behavior"] == proof["law"]
             and selected["donor_provenance"] == proof["sources"]
             and selected["source_path"] == manifest["source_filter"]["path"]
             and selected["source_git_blob"] == manifest["source_filter"]["git_blob"],
             "manifest/source mismatch " + name)
        need(selected["coordinate"] is None and selected["ratified_resident"] is False
             and selected["physical_t5_authorized"] is False
             and selected["witness_independence"] == "PENDING",
             "unproven law claims Core authority " + name)
        need(proof["F2"] == "HOLD_NOT_RUN"
             and proof["F3"] == "HOLD_DEDUP_UNPROVEN"
             and proof["F4"] == "NO_COORDINATE"
             and proof["ratified"] is False, "unsupported evidence PASS " + name)
    coords = [r["coordinate"] for r in v9["rows"] if r.get("coordinate") is not None]
    ratified = sum(r.get("ratified_resident") is True for r in v9["rows"])
    a = v9["accounting"]
    need((len(coords), len(set(coords)), ratified) == (719, 719, 0),
         "coordinate collision or illicit ratification")
    need((a["selected_semantic_candidates"], a["placed_selected_candidates"],
          a["unplaced_selected_candidates"], a["remaining_semantic_inventory"],
          a["ratified_d10_residents"], a["source_reviewed_f1_only_candidates_added"])
         == (759, 719, 40, 265, 0, 34), "inventory accounting")
    return {"selected": 759, "placed": 719, "unplaced": 40, "remaining": 265, "ratified": 0}


def check(root=ROOT):
    root = root.resolve()
    pointer = json.loads((root / "knowledge/d10-current-inventory.json").read_text(encoding="utf-8"))
    live = pointer["canonical_current"]
    archive = pointer["historical_v8_research_inventory"]
    info = pointer["current_v9_source_reviewed_batch"]
    need(archive["path"] == "knowledge/d10-v8-semantic-inventory.json"
         and info["previous_blob"] == archive["git_blob"], "archived v8 pointer")
    need(live["path"] == "knowledge/d10-v9-semantic-inventory.json", "canonical v9 pointer")
    raw8 = pinned(root, archive["path"], archive["git_blob"])
    raw9 = pinned(root, live["path"], live["git_blob"])
    manifest_raw = pinned(root, info["manifest"]["path"], info["manifest"]["git_blob"])
    manifest = json.loads(manifest_raw)
    require_source = manifest["source_filter"]
    source = pinned(root, require_source["path"], require_source["git_blob"])
    foundation = json.loads(pinned(root, manifest["source_foundation"]["path"],
                                   manifest["source_foundation"]["git_blob"]))
    result = verify_rows(json.loads(raw8), json.loads(raw9), manifest, source, foundation)
    need((live["selected"], live["placed"], live["unplaced"], live["ratified"])
         == (759, 719, 40, 0), "pointer accounting")
    return result


def self_test():
    # Negative tests do not require the entire checkout and must run under -O.
    try:
        need(False, "test rejection")
    except ValueError:
        pass
    else:
        raise ValueError("D10_V9_BLOCK: fail-closed test escaped")
    source = {"candidate_id": "ID", "semantic_name": "NAME", "semantic_law": "law",
              "donor_provenance": "source:1", "source_pin": "a"*40,
              "reason": "EXCLUDE_NO_WITNESS"}
    need(len(source["source_pin"]) == 40, "test fixture")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    options = parser.parse_args()
    try:
        if options.self_test:
            self_test()
        print("D10-V9-RESEARCH PASS", json.dumps(check(), sort_keys=True))
    except (KeyError, IndexError, ValueError, OSError, TypeError, csv.Error) as exc:
        raise SystemExit(str(exc))


if __name__ == "__main__":
    main()
