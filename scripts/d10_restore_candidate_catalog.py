#!/usr/bin/env python3
"""Lossless D10 source-name catalog reconciliation: restore historical evidence.

Never equate spelling with independent D10 law; never ratify or allocate.
The older 1495-name index is SHA-pinned, not a second current authority.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

from d10_prepare_filter_input import INDEX_FIELDS, json_list
from d10_mechanical_filter import git_blob, safe_file

HISTORICAL_COMMIT = "17ab25d65346a6a1bfc71f0ed6d64ee75fc6f22f"
HISTORICAL_BLOB = "4afd4c6292db8c93b001cae3162a85bc4307cf41"
ARRAY_FIELDS = (
    "provisional_coordinate_claims", "semantic_law_variants", "donor_provenance_claims",
    "positive_witness_claims", "falsifier_claims", "source_records_sha_pinned",
    "historical_status_claims",
)


def literal_tsv(path):
    # The pinned original uses literal fields (including unmatched quote
    # characters). Only that exact Git blob is admitted through raw splitting.
    # All newer catalogs use strict RFC4180 TSV to preserve embedded JSON.
    frozen = git_blob(path.read_bytes()) == HISTORICAL_BLOB
    rows = {}
    if frozen:
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or tuple(lines[0].split("\t")) != INDEX_FIELDS:
            raise ValueError("INVALID_SOURCE_CATALOG_HEADER")
        parsed = [(i, line.split("\t")) for i, line in enumerate(lines[1:], 2)]
    else:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t", strict=True)
            try:
                if tuple(next(reader, ())) != INDEX_FIELDS:
                    raise ValueError("INVALID_SOURCE_CATALOG_HEADER")
                parsed = [(reader.line_num, cols) for cols in reader]
            except csv.Error as exc:
                raise ValueError(f"INVALID_CATALOG_QUOTING:{reader.line_num}") from exc
    for number, parts in parsed:
        if len(parts) != len(INDEX_FIELDS):
            raise ValueError(f"INVALID_SOURCE_CATALOG_LINE:{number}")
        record = dict(zip(INDEX_FIELDS, parts))
        ident = record["candidate_id"].strip()
        if not ident or not record["semantic_name"].strip() or ident in rows:
            raise ValueError(f"DUPLICATE_OR_EMPTY_SOURCE_IDENTITY:{number}:{ident}")
        if record["ratified"] != "0":
            raise ValueError("UNEXPECTED_RATIFICATION")
        rows[ident] = record
    return rows

def parse_array(raw):
    # Restore both frozen literal-TSV JSON arrays and RFC4180-escaped
    # JSON arrays emitted by the new unified index producer. Decode exactly,
    # never treat undecodable claims as provenance or executed witnesses.
    try:
        return json_list(raw)
    except (ValueError, TypeError) as exc:
        raise ValueError("INVALID_JSON_LIST") from exc


def merge_catalog(root, historical_path, current_path, output_path):
    # Confirm immutable 1495-row donor bytes before touching the current
    # source index. Candidate IDs, not human spellings, are source identities.
    if git_blob(historical_path.read_bytes()) != HISTORICAL_BLOB:
        raise ValueError("HISTORICAL_CATALOG_BLOB_CHANGED")
    historic = literal_tsv(historical_path)
    latest = literal_tsv(current_path)
    pointer = json.loads((root / "knowledge/d10-current-inventory.json").read_text())
    cur = pointer["canonical_current"]
    invpath = safe_file(root, cur["path"])
    if invpath is None or git_blob(invpath.read_bytes()) != cur["git_blob"]:
        raise ValueError("CANONICAL_POINTER_SHA_MISMATCH")
    inv = json.loads(invpath.read_text())
    selected = {r["semantic_name"].casefold(): r for r in inv["rows"]}
    if len(selected) != len(inv["rows"]) or len(selected) != cur["selected"]:
        raise ValueError("CANONICAL_SELECTED_DRIFT")
    combined = {}
    for ident in sorted(set(historic) | set(latest)):
        a, b = historic.get(ident), latest.get(ident)
        if a is not None and b is not None and a["semantic_name"] != b["semantic_name"]:
            raise ValueError("HISTORICAL_ID_NAME_CONFLICT:" + ident)
        primary = dict(b or a)
        for column in ARRAY_FIELDS:
            merged = []
            for record in (a, b):
                if record is None:
                    continue
                for value in parse_array(record[column]):
                    if value not in merged:
                        merged.append(value)
            if column == "historical_status_claims" and a is not None:
                tag = "HISTORIC_SOURCE_ID:" + ident
                if tag not in merged:
                    merged.append(tag)
                if b is None and "RESTORED_FROM_1495_NAME_FROZEN_INTAKE" not in merged:
                    merged.append("RESTORED_FROM_1495_NAME_FROZEN_INTAKE")
            primary[column] = json.dumps(merged, ensure_ascii=False, separators=(",", ":"))
        if primary["candidate_id"] != ident:
            raise ValueError("SOURCE_CANDIDATE_ID_CHANGED:" + ident)
        # Exact source identity, coordinate and selection claims are retained.
        # Matching human names never allocate, ratify or replace canonical IDs.
        primary["ratified"] = "0"
        counts = [int(x["source_record_count"]) for x in (a, b)
                  if x is not None and x["source_record_count"].isdigit()]
        primary["source_record_count"] = str(max([0, *counts,
            len(parse_array(primary["source_records_sha_pinned"]))]))
        combined[ident] = primary
    if not set(historic).issubset(combined) or not set(latest).issubset(combined):
        raise ValueError("SOURCE_CANDIDATE_ID_LOSS")
    name_counts = {}
    for row in combined.values():
        name = row["semantic_name"].strip().casefold()
        name_counts[name] = name_counts.get(name, 0) + 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=INDEX_FIELDS, delimiter="\t",
                                lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        for ident in sorted(combined):
            row = combined[ident]
            if any("\t" in row[c] or "\n" in row[c] or "\r" in row[c]
                   for c in INDEX_FIELDS):
                raise ValueError("INVALID_LITERAL_TSV_FIELD:" + ident)
            writer.writerow(row)
    return {
        # Retain workflow keys while reporting the actual ID-based contract.
        "source_historical_names": len(historic),
        "source_latest_names": len(latest),
        "restored_old_only_names": len(set(historic) - set(latest)),
        "new_names_beyond_historical": len(set(latest) - set(historic)),
        "full_union_names": len(combined),
        "source_historical_ids": len(historic),
        "source_latest_ids": len(latest),
        "restored_prior_only_ids": len(set(historic) - set(latest)),
        "new_ids_beyond_historical": len(set(latest) - set(historic)),
        "shared_candidate_ids": len(set(historic) & set(latest)),
        "full_union_ids": len(combined),
        "colliding_spelling_groups_not_deduped": sum(v > 1 for v in name_counts.values()),
        "current_canonical_selected": len(selected),
        "new_allocations": 0, "new_ratifications": 0,
        "historical_commit": HISTORICAL_COMMIT,
        "historical_git_blob": HISTORICAL_BLOB,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--historical", type=Path, required=True)
    parser.add_argument("--current", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    current = args.current or (root / "knowledge/d10-filter/all-candidates.tsv")
    output = args.output or current
    report = merge_catalog(root, args.historical, current, output)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
