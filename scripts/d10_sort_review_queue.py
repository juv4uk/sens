#!/usr/bin/env python3
"""Deterministic, non-destructive D10 review queue from frozen source claims.

Tiers are WORK ORDER, never proof of semantic independence or D10 admission.
Each candidate_id is conserved; the 7396-row provenance table stays unchanged.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

from d10_restore_source_occurrences import SOURCE_COLUMNS, git_blob

COLUMNS = (
    "candidate_id", "semantic_name", "review_tier", "next_action",
    "source_occurrences", "distinct_source_paths", "same_spelling_records",
    "same_spelling_as_other_selected", "law_claims", "donor_claims",
    "positive_witness_claims", "negative_witness_claims",
    "canonical_selection", "canonical_coordinate", "witness_status",
    "semantic_distinctness_status",
)
PRIORITIES = (
    "P0_REPLAY_BOTH_WITNESSES",
    "P1_ADD_NEGATIVE_WITNESSES",
    "P1_ADD_POSITIVE_WITNESSES",
    "P2_SPECIFY_BOTH_WITNESSES",
    "P3_VERIFY_DONOR_AND_WRITE_TESTS",
    "P3_SPECIFY_OBSERVABLE_LAW",
    "P4_RESEARCH_MISSING_LAW_AND_DONOR",
    "ARCHIVE_ALREADY_RESEARCH_SELECTED",
)


def parse_source(text):
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter="\t", strict=True)
    if tuple(reader.fieldnames or ()) != SOURCE_COLUMNS:
        raise ValueError("SOURCE_SCHEMA_MISMATCH")
    rows, ids = [], set()
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("RAGGED_SOURCE_ROW")
        cid = row["candidate_id"]
        if not cid or cid in ids:
            raise ValueError("DUPLICATE_OR_EMPTY_CANDIDATE_ID")
        ids.add(cid)
        if row["current_d10_selected"] not in ("NOT_SELECTED", "RESEARCH_SELECTED_UNRATIFIED"):
            raise ValueError("UNKNOWN_SOURCE_SELECTION_STATUS")
        if row["ratified"] != "0":
            raise ValueError("UNEXPECTED_RATIFICATION")
        for key in ("semantic_law_variants", "donor_provenance_claims",
                    "positive_witness_claims", "falsifier_claims",
                    "source_records_sha_pinned"):
            try:
                val = json.loads(row[key])
            except (TypeError, ValueError) as exc:
                raise ValueError("INVALID_SOURCE_CLAIMS:" + cid) from exc
            if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
                raise ValueError("INVALID_SOURCE_CLAIMS:" + cid)
            row[key] = val
        if len(row["source_records_sha_pinned"]) != int(row["source_record_count"]):
            raise ValueError("SOURCE_OCCURRENCES_LOST")
        rows.append(row)
    return rows


def category(row):
    if row["current_d10_selected"] == "RESEARCH_SELECTED_UNRATIFIED":
        return "ARCHIVE_ALREADY_RESEARCH_SELECTED", "KEEP_EXISTING_RESEARCH_INVENTORY"
    law = bool(row["semantic_law_variants"])
    donor = bool(row["donor_provenance_claims"])
    positive = bool(row["positive_witness_claims"])
    negative = bool(row["falsifier_claims"])
    if law and donor and positive and negative:
        return "P0_REPLAY_BOTH_WITNESSES", "REPLAY_DONOR_POSITIVE_NEGATIVE_THEN_COMPARE_D1_D9_D10"
    if law and donor and positive:
        return "P1_ADD_NEGATIVE_WITNESSES", "ADD_FALSIFIERS_THEN_REPLAY_BOTH"
    if law and donor and negative:
        return "P1_ADD_POSITIVE_WITNESSES", "ADD_POSITIVE_CASES_THEN_REPLAY_BOTH"
    if law and donor:
        return "P2_SPECIFY_BOTH_WITNESSES", "WRITE_BOTH_CASES_THEN_REPLAY_DONOR"
    if law:
        return "P3_VERIFY_DONOR_AND_WRITE_TESTS", "TRACE_PINNED_DONOR_AND_WRITE_BOTH_CASES"
    if donor:
        return "P3_SPECIFY_OBSERVABLE_LAW", "SPECIFY_TYPES_LAW_EFFECTS_AND_BOTH_CASES"
    return "P4_RESEARCH_MISSING_LAW_AND_DONOR", "RECOVER_DONOR_AND_BEHAVIOR_BEFORE_TESTING"


def make_queue(rows):
    spelling = Counter(x["semantic_name"].casefold() for x in rows)
    selected_names = {}
    for row in rows:
        if row["current_d10_selected"] == "RESEARCH_SELECTED_UNRATIFIED":
            selected_names.setdefault(row["semantic_name"].casefold(), set()).add(
                row["candidate_id"])
    queue = []
    for r in rows:
        name = r["semantic_name"]
        sources = r["source_records_sha_pinned"]
        tier, action = category(r)
        paths = {ref.split("@", 1)[0] for ref in sources}
        existing_name_ids = selected_names.get(name.casefold(), set())
        selected_elsewhere = bool(existing_name_ids - {r["candidate_id"]})
        coord = r["canonical_coordinate"]
        if r["current_d10_selected"] == "NOT_SELECTED" and coord != "NONE":
            raise ValueError("NONSELECTED_HAS_CANONICAL_COORDINATE")
        queue.append({
            "candidate_id": r["candidate_id"],
            "semantic_name": name,
            "review_tier": tier, "next_action": action,
            "source_occurrences": str(len(sources)),
            "distinct_source_paths": str(len(paths)),
            "same_spelling_records": str(spelling[name.casefold()]),
            "same_spelling_as_other_selected": "YES" if selected_elsewhere else "NO",
            "law_claims": str(len(r["semantic_law_variants"])),
            "donor_claims": str(len(r["donor_provenance_claims"])),
            "positive_witness_claims": str(len(r["positive_witness_claims"])),
            "negative_witness_claims": str(len(r["falsifier_claims"])),
            "canonical_selection": r["current_d10_selected"],
            "canonical_coordinate": coord,
            "witness_status": "NOT_ATTESTED_NO_F2_PASS",
            "semantic_distinctness_status": "UNPROVEN_NO_F3_PASS",
        })
    order = {key: i for i, key in enumerate(PRIORITIES)}
    queue.sort(key=lambda item: (order[item["review_tier"]],
                               -int(item["distinct_source_paths"]),
                               -int(item["source_occurrences"]),
                               item["semantic_name"].casefold(),
                               item["candidate_id"]))
    return queue


def render(queue):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=COLUMNS, delimiter="\t",
                            lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(queue)
    return output.getvalue().encode("utf-8")


def validate(root, manifest_path, write=False):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    archive = json.loads((root / "knowledge/d10-filter/source-occurrence-manifest.json")
                         .read_text(encoding="utf-8"))
    original = (root / manifest["input"]["path"]).read_bytes()
    if git_blob(original) != manifest["input"]["git_blob"]:
        raise ValueError("ORIGINAL_CATALOG_CHANGED")
    if archive["output"]["git_blob"] != manifest["preserved_archive_git_blob"]:
        raise ValueError("ARCHIVE_EXPECTATION_CHANGED")
    archive_path = root / archive["output"]["path"]
    if git_blob(archive_path.read_bytes()) != archive["output"]["git_blob"]:
        raise ValueError("PRESERVED_ARCHIVE_CHANGED")
    pointer = json.loads((root / "knowledge/d10-current-inventory.json")
                         .read_text(encoding="utf-8"))
    live = pointer["canonical_current"]
    pinned_original = pointer.get("historical_v9_research_inventory", live)
    if pinned_original["git_blob"] != manifest["canonical_inventory_git_blob"]:
        raise ValueError("FROZEN_TRIAGE_INVENTORY_PIN_MISMATCH")
    canonical_path = root / pinned_original["path"]
    if git_blob(canonical_path.read_bytes()) != pinned_original["git_blob"]:
        raise ValueError("ARCHIVED_INVENTORY_PIN_MISMATCH")
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    selected_by_id = {r["stable_id"]: r for r in canonical["rows"]}
    if len(selected_by_id) != pinned_original["selected"]:
        raise ValueError("ARCHIVED_CANONICAL_COUNT_MISMATCH")
    live_bytes = (root / live["path"]).read_bytes()
    if git_blob(live_bytes) != live["git_blob"]:
        raise ValueError("LIVE_INVENTORY_PIN_MISMATCH")
    current_rows = json.loads(live_bytes)["rows"]
    if (len(current_rows) < len(canonical["rows"]) or
            current_rows[:len(canonical["rows"])] != canonical["rows"]):
        raise ValueError("FROZEN_V9_PREFIX_REWRITTEN")
    rows = parse_source(original.decode("utf-8"))
    catalog_selected = {r["candidate_id"]: r for r in rows
                        if r["current_d10_selected"] == "RESEARCH_SELECTED_UNRATIFIED"}
    if set(catalog_selected) != set(selected_by_id):
        raise ValueError("SELECTED_CANDIDATE_ID_SET_DIFFERS_FROM_CANONICAL")
    for ident, row in catalog_selected.items():
        canonical_row = selected_by_id[ident]
        if (row["semantic_name"] != canonical_row["semantic_name"] or
                row["canonical_coordinate"] != (canonical_row.get("coordinate") or "NONE")):
            raise ValueError("CANONICAL_ID_NAME_COORDINATE_MISMATCH")
    queue = make_queue(rows)
    blob = render(queue)
    if git_blob(blob) != manifest["output"]["git_blob"]:
        raise ValueError("QUEUE_CONTENT_SHA_MISMATCH")
    if write:
        target = root / manifest["output"]["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
    elif (root / manifest["output"]["path"]).read_bytes() != blob:
        raise ValueError("COMMITTED_QUEUE_DIFFERS_FROM_REGENERATION")
    counts = dict(sorted(Counter(q["review_tier"] for q in queue).items()))
    if counts != manifest["tiers"] or len(queue) != manifest["total_candidate_identities"]:
        raise ValueError("QUEUE_COUNT_MISMATCH")
    if any(q["witness_status"] != "NOT_ATTESTED_NO_F2_PASS" or
           q["semantic_distinctness_status"] != "UNPROVEN_NO_F3_PASS" for q in queue):
        raise ValueError("UNSUPPORTED_SEMANTIC_PROOF_CLAIM")
    return {"total": len(queue), "tiers": counts,
            "archive_rows": archive["counts"]["pinned_source_occurrences"],
            "canonical_selected": len(selected_by_id)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = args.manifest or root / "knowledge/d10-filter/review-triage-manifest.json"
    print(json.dumps(validate(root, manifest, args.write), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
