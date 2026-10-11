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

from d10_prepare_filter_input import INDEX_FIELDS, json_list, find_name_line
from d10_mechanical_filter import git_blob, safe_file

HISTORICAL_COMMIT = "17ab25d65346a6a1bfc71f0ed6d64ee75fc6f22f"
HISTORICAL_BLOB = "4afd4c6292db8c93b001cae3162a85bc4307cf41"
ARRAY_FIELDS = (
    "provisional_coordinate_claims", "semantic_law_variants", "donor_provenance_claims",
    "positive_witness_claims", "falsifier_claims", "source_records_sha_pinned",
    "historical_status_claims",
)


def literal_tsv(path):
    # The original frozen 1495-record blob used literal tabs but malformed
    # RFC4180 quoting. Parse only that exact immutable blob in literal mode;
    # newer indexes use strict CSV quoting. Candidate identity is the immutable
    # candidate_id, not a human-readable semantic_name.
    rows = {}

    def add_record(record, number):
        ident = record.get("candidate_id", "").strip()
        if not ident:
            raise ValueError(f"EMPTY_CANDIDATE_ID:{number}")
        if record.get("ratified") != "0":
            raise ValueError(f"UNEXPECTED_RATIFICATION:{number}")
        if not record.get("semantic_name", "").strip():
            raise ValueError(f"EMPTY_SEMANTIC_NAME:{number}")
        for column in ARRAY_FIELDS:
            parse_array(record[column])
        previous = rows.get(ident)
        if previous is not None:
            previous_name = previous.get("semantic_name", "").strip()
            current_name = record.get("semantic_name", "").strip()
            if previous_name.casefold() != current_name.casefold():
                raise ValueError(
                    f"DUPLICATE_CANDIDATE_ID_CONFLICT:{number}:{ident}:"
                    f"{previous_name!r}!={current_name!r}"
                )
            raise ValueError(f"DUPLICATE_OR_EMPTY_SOURCE_IDENTITY:{number}:{ident}")
        rows[ident] = record

    if git_blob(path.read_bytes()) == HISTORICAL_BLOB:
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or tuple(lines[0].split("\t")) != INDEX_FIELDS:
            raise ValueError("INVALID_SOURCE_CATALOG_HEADER")
        for number, line in enumerate(lines[1:], 2):
            parts = line.split("\t")
            if len(parts) != len(INDEX_FIELDS):
                raise ValueError(f"INVALID_SOURCE_CATALOG_LINE:{number}")
            add_record(dict(zip(INDEX_FIELDS, parts)), number)
        return rows

    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, delimiter="\t", strict=True)
        try:
            if tuple(next(reader, ())) != INDEX_FIELDS:
                raise ValueError("INVALID_SOURCE_CATALOG_HEADER")
            for parts in reader:
                number = reader.line_num
                if not parts or (len(parts) == 1 and not parts[0]):
                    continue
                if len(parts) != len(INDEX_FIELDS):
                    raise ValueError(f"INVALID_SOURCE_CATALOG_LINE:{number}")
                add_record(dict(zip(INDEX_FIELDS, parts)), number)
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



def find_name_line(canonical_text, name, case_sensitive=True):
    """Return the exact 1-based line of a canonical JSON semantic_name field.

    Searching only the JSON key/value line prevents a spelling that occurs in
    provenance, an example, or a witness from masquerading as the inventory row.
    No match returns None; multiple matching rows fail closed rather than
    fabricating a unique source pin.
    """
    target = name if case_sensitive else name.casefold()
    found = []
    for line_number, raw_line in enumerate(canonical_text.splitlines(), 1):
        line = raw_line.strip()
        if not line.startswith('"semantic_name"'):
            continue
        key, separator, raw_value = line.partition(":")
        if not separator or key.strip() != '"semantic_name"':
            continue
        raw_value = raw_value.strip()
        if raw_value.endswith(","):
            raw_value = raw_value[:-1].rstrip()
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"INVALID_CANONICAL_SEMANTIC_NAME_LINE:{line_number}") from exc
        if not isinstance(value, str):
            raise ValueError(f"INVALID_CANONICAL_SEMANTIC_NAME_TYPE:{line_number}")
        comparable = value if case_sensitive else value.casefold()
        if comparable == target:
            found.append(line_number)
    if len(found) > 1:
        raise ValueError(f"AMBIGUOUS_CANONICAL_SEMANTIC_NAME:{name}")
    return found[0] if found else None


HISTORICAL_LEDGER_BLOB = "f10c545598b6aaf90f8f5caf8f49683448ff420f"
HISTORICAL_LEDGER_PATH = "knowledge/d10-proposal-ledger.tsv"
HISTORICAL_LEDGER_ARCHIVE = (
    "knowledge/d10-source-snapshots/d10-proposal-ledger-f10c545598b6aaf6.tsv"
)


def restore_historical_ledger_snapshot_locator(root, semantic_name, refs):
    """Add a verified archived locator for stale ledger pins without deleting the original claim."""
    result = list(refs)
    stale_prefix = f"{HISTORICAL_LEDGER_PATH}@{HISTORICAL_LEDGER_BLOB}:"
    if not any(ref.startswith(stale_prefix) for ref in result):
        return result

    snapshot = safe_file(root, HISTORICAL_LEDGER_ARCHIVE)
    if snapshot is None:
        raise ValueError("HISTORICAL_LEDGER_SNAPSHOT_MISSING")
    raw = snapshot.read_bytes()
    if git_blob(raw) != HISTORICAL_LEDGER_BLOB:
        raise ValueError("HISTORICAL_LEDGER_SNAPSHOT_BLOB_MISMATCH")

    try:
        reader = csv.reader(raw.decode("utf-8").splitlines(), delimiter="\t", strict=True)
        header = next(reader, None)
        if not header or "semantic_name" not in header:
            raise ValueError("HISTORICAL_LEDGER_SNAPSHOT_SCHEMA")
        name_column = header.index("semantic_name")
        matches = []
        for line_number, row in enumerate(reader, start=2):
            if len(row) != len(header):
                raise ValueError(f"HISTORICAL_LEDGER_SNAPSHOT_ROW:{line_number}")
            if row[name_column].strip().casefold() == semantic_name.strip().casefold():
                matches.append(line_number)
    except csv.Error as exc:
        raise ValueError("HISTORICAL_LEDGER_SNAPSHOT_TSV") from exc

    if len(matches) > 1:
        raise ValueError(f"HISTORICAL_LEDGER_NAME_AMBIGUOUS:{semantic_name}")
    if not matches:
        return result

    locator = (
        f"{HISTORICAL_LEDGER_ARCHIVE}@{HISTORICAL_LEDGER_BLOB}:source-record"
    )
    if locator not in result:
        result.append(locator)
    return result


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
    canonical_text = invpath.read_text(encoding="utf-8")
    inv = json.loads(canonical_text)
    selected_rows = inv.get("rows", [])
    selected = {row["stable_id"]: row for row in selected_rows}
    if len(selected) != len(selected_rows) or len(selected) != cur["selected"]:
        raise ValueError("CANONICAL_SELECTED_DRIFT")

    source_historical_ids = set(historic)
    source_latest_ids = set(latest)
    source_union_ids = source_historical_ids | source_latest_ids
    combined = {}

    for ident in sorted(source_union_ids):
        a, b = historic.get(ident), latest.get(ident)
        if (a is not None and b is not None and
                a["semantic_name"].strip().casefold() != b["semantic_name"].strip().casefold()):
            raise ValueError("HISTORICAL_ID_NAME_CONFLICT:" + ident)
        primary = dict(b or a)
        resident = selected.get(ident)

        # Merge evidence only for the same immutable candidate ID. A repeated
        # spelling under different IDs stays as separate rows for later
        # behavioral deduplication; it is never an equivalence proof.
        for column in ARRAY_FIELDS:
            merged = []
            for row in (a, b):
                if row is None:
                    continue
                for value in parse_array(row[column]):
                    if value not in merged:
                        merged.append(value)
            if column == "source_records_sha_pinned":
                merged = restore_historical_ledger_snapshot_locator(
                    root, primary.get("semantic_name", ""), merged
                )
            if column == "historical_status_claims":
                if a is not None:
                    tag = "HISTORIC_SOURCE_ID:" + ident
                    if tag not in merged:
                        merged.append(tag)
                    if b is None:
                        marker = "RESTORED_FROM_1495_NAME_FROZEN_INTAKE"
                        if marker not in merged:
                            merged.append(marker)
                for row in (a, b):
                    if row is None:
                        continue
                    source_status = row.get("current_d10_selected", "").strip()
                    if source_status:
                        tag = "SOURCE_SELECTION_CLAIM:" + source_status
                        if tag not in merged:
                            merged.append(tag)
                    source_name = row.get("semantic_name", "").strip()
                    if source_name and source_name.casefold() != primary.get("semantic_name", "").strip().casefold():
                        tag = "SOURCE_NAME_CLAIM:" + source_name
                        if tag not in merged:
                            merged.append(tag)
            if column == "provisional_coordinate_claims":
                canonical_coordinate = (
                    str(resident.get("coordinate") or "NONE") if resident else "NONE"
                )
                for row in (a, b):
                    if row is None:
                        continue
                    claim = row.get("canonical_coordinate", "").strip()
                    if claim and claim != "NONE" and claim != canonical_coordinate:
                        tag = "SOURCE_COORDINATE_CLAIM:" + ident + ":" + claim
                        if tag not in merged:
                            merged.append(tag)
            primary[column] = json.dumps(merged, ensure_ascii=False, separators=(",", ":"))

        if not primary["semantic_name"].strip():
            raise ValueError("EMPTY_SEMANTIC_NAME")

        if resident is not None:
            # Canonical status is attached by exact stable ID only. A historical
            # namesake with another ID is not renamed or promoted.
            canonical_name = resident["semantic_name"]
            if primary["semantic_name"].casefold() != canonical_name.casefold():
                claims = parse_array(primary["historical_status_claims"])
                tag = "SOURCE_NAME_CLAIM:" + primary["semantic_name"]
                if tag not in claims:
                    claims.append(tag)
                primary["historical_status_claims"] = json.dumps(
                    claims, ensure_ascii=False, separators=(",", ":")
                )
            primary["semantic_name"] = canonical_name
            primary["canonical_coordinate"] = resident.get("coordinate") or "NONE"
            primary["current_d10_selected"] = "RESEARCH_SELECTED_UNRATIFIED"
            behavior = resident.get("behavior") or resident.get("observable_law") or ""
            if behavior:
                laws = parse_array(primary["semantic_law_variants"])
                if behavior not in laws:
                    laws.append(behavior)
                primary["semantic_law_variants"] = json.dumps(
                    laws, ensure_ascii=False, separators=(",", ":")
                )
            line = find_name_line(canonical_text, canonical_name, False)
            if line is not None:
                locator = f"{cur['path']}@{cur['git_blob']}:{line}"
                pins = parse_array(primary["source_records_sha_pinned"])
                if locator not in pins:
                    pins.append(locator)
                primary["source_records_sha_pinned"] = json.dumps(
                    pins, ensure_ascii=False, separators=(",", ":")
                )
        else:
            primary["canonical_coordinate"] = "NONE"
            primary["current_d10_selected"] = "NOT_SELECTED"

        # Old coordinate/status strings are retained as claims only. They do
        # not assign a coordinate, authorize execution, or ratify a meaning.
        primary["ratified"] = "0"
        counts = [
            int(row["source_record_count"])
            for row in (a, b)
            if row is not None and row.get("source_record_count", "").isdigit()
        ]
        primary["source_record_count"] = str(max([
            0, *counts, len(parse_array(primary["source_records_sha_pinned"]))
        ]))
        combined[ident] = primary

    # Overlay selected D10 stable IDs only where the exact ID is absent. A
    # historical namesake never suppresses or inherits a canonical identity.
    canonical_overlay_ids_added = 0
    for ident, resident in sorted(selected.items()):
        if ident in combined:
            continue
        name = resident["semantic_name"]
        line = find_name_line(canonical_text, name, False)
        pins = [f"{cur['path']}@{cur['git_blob']}:{line}"] if line is not None else []
        row = {column: "" for column in INDEX_FIELDS}
        row.update(
            candidate_id=ident,
            semantic_name=name,
            source_record_count="1",
            current_d10_selected="RESEARCH_SELECTED_UNRATIFIED",
            canonical_coordinate=resident.get("coordinate") or "NONE",
            ratified="0",
        )
        for column in ARRAY_FIELDS:
            row[column] = "[]"
        law = resident.get("behavior") or resident.get("observable_law") or ""
        row["semantic_law_variants"] = json.dumps(
            [law] if law else [], ensure_ascii=False, separators=(",", ":")
        )
        row["source_records_sha_pinned"] = json.dumps(
            pins, ensure_ascii=False, separators=(",", ":")
        )
        row["historical_status_claims"] = json.dumps(
            ["CANONICAL_D10_SELECTED_OVERLAY"],
            ensure_ascii=False, separators=(",", ":")
        )
        combined[ident] = row
        canonical_overlay_ids_added += 1

    if not source_historical_ids.issubset(combined) or not source_latest_ids.issubset(combined):
        raise ValueError("SOURCE_ID_LOSS")
    ids = list(combined)
    if len(ids) != len(set(ids)):
        raise ValueError("DUPLICATE_CANDIDATE_ID_AFTER_MERGE")
    for ident, row in combined.items():
        if ident != row["candidate_id"]:
            raise ValueError("CANDIDATE_ID_RELABELED")
        if row["ratified"] != "0":
            raise ValueError("UNEXPECTED_RATIFICATION")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=INDEX_FIELDS, delimiter="\t",
            lineterminator="\n", extrasaction="raise",
        )
        writer.writeheader()
        for ident in sorted(combined):
            rec = combined[ident]
            values = [rec[column] for column in INDEX_FIELDS]
            if any("\t" in value or "\n" in value or "\r" in value for value in values):
                raise ValueError("INVALID_LITERAL_TSV_FIELD:" + ident)
            writer.writerow(rec)

    historic_names = {row["semantic_name"].strip().casefold() for row in historic.values()}
    latest_names = {row["semantic_name"].strip().casefold() for row in latest.values()}
    union_names = {row["semantic_name"].strip().casefold() for row in combined.values()}
    return {
        "source_historical_records": len(historic),
        "source_latest_records": len(latest),
        "source_historical_ids": len(source_historical_ids),
        "source_latest_ids": len(source_latest_ids),
        "source_id_overlap": len(source_historical_ids & source_latest_ids),
        "restored_old_only_candidate_ids": len(source_historical_ids - source_latest_ids),
        "restored_prior_only_ids": len(source_historical_ids - source_latest_ids),
        "new_candidate_ids_beyond_historical": len(source_latest_ids - source_historical_ids),
        "source_union_candidate_ids": len(source_union_ids),
        "canonical_overlay_ids_added": canonical_overlay_ids_added,
        "full_union_candidate_ids": len(combined),
        "full_union_ids": len(combined),
        "source_historical_names": len(historic_names),
        "source_latest_names": len(latest_names),
        "restored_old_only_names": len(historic_names - latest_names),
        "new_names_beyond_historical": len(latest_names - historic_names),
        "full_union_names": len(union_names),
        "colliding_spelling_groups_not_deduped": sum(
            1 for _name, group in
            __import__("itertools").groupby(
                sorted((row["semantic_name"].strip().casefold(), ident)
                       for ident, row in combined.items()),
                key=lambda item: item[0]
            )
            if len({item[1] for item in group}) > 1
        ),
        "current_canonical_selected": len(selected),
        "new_allocations": 0,
        "new_ratifications": 0,
        "historical_commit": HISTORICAL_COMMIT,
        "historical_git_blob": HISTORICAL_BLOB,
        "current_inventory_git_blob": cur["git_blob"],
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
