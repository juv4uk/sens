#!/usr/bin/env python3
"""Lossless D10 source-name catalog reconciliation: restore historical evidence.

Never equate spelling with independent D10 law; never ratify or allocate.
The older 1495-name index is SHA-pinned, not a second current authority.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
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
    # The original frozen 1495-name blob used literal tabs but malformed
    # RFC4180 quoting. Parse that ONE exact immutable blob as originally
    # serialized; use strict csv.reader for every newer source.
    if git_blob(path.read_bytes()) == HISTORICAL_BLOB:
        rows = {}
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or tuple(lines[0].split("\t")) != INDEX_FIELDS:
            raise ValueError("INVALID_SOURCE_CATALOG_HEADER")
        for number, line in enumerate(lines[1:], 2):
            parts = line.split("\t")
            if len(parts) != len(INDEX_FIELDS):
                raise ValueError(f"INVALID_SOURCE_CATALOG_LINE:{number}")
            record = dict(zip(INDEX_FIELDS, parts))
            key = record["semantic_name"].strip().casefold()
            if not key or key in rows:
                raise ValueError(f"DUPLICATE_SOURCE_NAME:{number}:{key}")
            if record["ratified"] != "0":
                raise ValueError("UNEXPECTED_RATIFICATION")
            rows[key] = record
        return rows
    rows = {}
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, delimiter="\t", strict=True)
        try:
            if tuple(next(reader, ())) != INDEX_FIELDS:
                raise ValueError("INVALID_SOURCE_CATALOG_HEADER")
            for parts in reader:
                number = reader.line_num
                if len(parts) != len(INDEX_FIELDS):
                    raise ValueError(f"INVALID_SOURCE_CATALOG_LINE:{number}")
                record = dict(zip(INDEX_FIELDS, parts))
                key = record["semantic_name"].strip().casefold()
                if not key or key in rows:
                    raise ValueError(f"DUPLICATE_SOURCE_NAME:{number}:{key}")
                if record["ratified"] != "0":
                    raise ValueError("UNEXPECTED_RATIFICATION")
                rows[key] = record
        except csv.Error as exc:
            raise ValueError(f"INVALID_CATALOG_QUOTING:{reader.line_num}") from exc
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
    raw_old = historical_path.read_bytes()
    if git_blob(raw_old) != HISTORICAL_BLOB:
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
    for key in set(historic) | set(latest):
        a, b = historic.get(key), latest.get(key)
        primary = dict(b or a)
        ids = {x["candidate_id"] for x in (a, b) if x is not None}
        for column in ARRAY_FIELDS:
            merged = []
            for row in (a, b):
                if row is None:
                    continue
                for value in parse_array(row[column]):
                    if value not in merged:
                        merged.append(value)
            if column == "historical_status_claims":
                for original in sorted(ids):
                    tag = "HISTORIC_SOURCE_ID:" + original
                    if tag not in merged:
                        merged.append(tag)
                if a is not None and b is None:
                    merged.append("RESTORED_FROM_1495_NAME_FROZEN_INTAKE")
            primary[column] = json.dumps(merged, ensure_ascii=False, separators=(",", ":"))
        if not primary["semantic_name"]:
            raise ValueError("EMPTY_SEMANTIC_NAME")
        resident = selected.get(key)
        if resident:
            primary["candidate_id"] = resident["stable_id"]
            primary["canonical_coordinate"] = resident.get("coordinate") or "NONE"
            primary["current_d10_selected"] = "RESEARCH_SELECTED_UNRATIFIED"
        else:
            # Previous ordinal IDs collide after filtering; synthetic IDs are
            # stable *source indexes*, not binary SENS coordinates.
            digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]
            primary["candidate_id"] = "d10.source.name." + digest
            primary["canonical_coordinate"] = "NONE"
            primary["current_d10_selected"] = "NOT_SELECTED"
        primary["ratified"] = "0"
        counts = [int(x["source_record_count"]) for x in (a, b)
                  if x is not None and x["source_record_count"].isdigit()]
        primary["source_record_count"] = str(max([0, *counts,
                                     len(parse_array(primary["source_records_sha_pinned"]))]))
        combined[key] = primary
    if not set(historic).issubset(combined) or not set(latest).issubset(combined):
        raise ValueError("SOURCE_NAME_LOSS")
    ids = [r["candidate_id"] for r in combined.values()]
    if len(ids) != len(set(ids)):
        raise ValueError("SYNTHETIC_CANDIDATE_ID_COLLISION")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(INDEX_FIELDS) + "\n")
        for key in sorted(combined):
            rec = combined[key]
            values = [rec[c] for c in INDEX_FIELDS]
            if any("\t" in v or "\n" in v or "\r" in v for v in values):
                raise ValueError("INVALID_LITERAL_TSV_FIELD:" + key)
            fh.write("\t".join(values) + "\n")
    return {
        "source_historical_names": len(historic),
        "source_latest_names": len(latest),
        "restored_old_only_names": len(set(historic) - set(latest)),
        "new_names_beyond_historical": len(set(latest) - set(historic)),
        "full_union_names": len(combined),
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
