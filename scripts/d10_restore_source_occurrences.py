#!/usr/bin/env python3
"""Losslessly expand every SHA-pinned D10 catalog provenance occurrence.

Source record identity (candidate_id) is NOT a semantic equivalence proof.
Historical inventories can refer to the same semantic candidate repeatedly.
This program does not allocate coordinates, run oracles, or ratify D10.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path

SOURCE_COLUMNS = (
    "candidate_id", "semantic_name", "source_record_count",
    "current_d10_selected", "canonical_coordinate",
    "provisional_coordinate_claims", "semantic_law_variants",
    "donor_provenance_claims", "positive_witness_claims",
    "falsifier_claims", "source_records_sha_pinned",
    "historical_status_claims", "semantic_dedup_state",
    "witness_execution_state", "filter_state", "ratified",
)
OUTPUT_COLUMNS = (
    "candidate_id", "semantic_name", "source_ordinal",
    "source_path", "source_git_blob", "source_locator", "source_ref",
)
PIN = re.compile(r"^(.+?)@([0-9a-f]{40}):(.+)$")


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def expand(raw: str):
    reader = csv.DictReader(io.StringIO(raw, newline=""), delimiter="\t", strict=True)
    if tuple(reader.fieldnames or ()) != SOURCE_COLUMNS:
        raise ValueError("SOURCE_COLUMNS_MISMATCH")
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=OUTPUT_COLUMNS, delimiter="\t",
                            lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    ids, names, refs, paths, pairs = set(), set(), set(), Counter(), set()
    occurrences = 0
    for source in reader:
        if None in source or any(v is None for v in source.values()):
            raise ValueError("MALFORMED_SOURCE_ROW")
        cid, name = source["candidate_id"], source["semantic_name"]
        if not cid.strip() or not name.strip() or cid in ids:
            raise ValueError("DUPLICATE_OR_EMPTY_CANDIDATE_ID")
        if source["ratified"] != "0":
            raise ValueError("UNEXPECTED_RATIFICATION_CLAIM")
        ids.add(cid)
        names.add(name.casefold())
        try:
            pinrefs = json.loads(source["source_records_sha_pinned"])
            count = int(source["source_record_count"])
        except (TypeError, ValueError) as error:
            raise ValueError("INVALID_SOURCE_REFERENCE_ARRAY") from error
        if not isinstance(pinrefs, list) or len(pinrefs) != count:
            raise ValueError("SOURCE_RECORD_COUNT_LOSS")
        for ordinal, ref in enumerate(pinrefs, 1):
            if not isinstance(ref, str):
                raise ValueError("INVALID_REFERENCE_TYPE")
            match = PIN.fullmatch(ref)
            if match is None:
                raise ValueError("SOURCE_REF_NOT_SHA_PINNED")
            path, blob, locator = match.groups()
            if not path or not locator or any(c in ref for c in "\t\r\n"):
                raise ValueError("INVALID_SOURCE_LOCATOR")
            writer.writerow({
                "candidate_id": cid, "semantic_name": name,
                "source_ordinal": ordinal,
                "source_path": path, "source_git_blob": blob,
                "source_locator": locator, "source_ref": ref,
            })
            occurrences += 1
            refs.add(ref)
            paths[path] += 1
            pairs.add((path, blob))
    counts = {
        "candidate_identities": len(ids),
        "semantic_name_spellings": len(names),
        "pinned_source_occurrences": occurrences,
        "distinct_reference_strings": len(refs),
        "distinct_source_paths": len(paths),
        "source_path_blob_pairs": len(pairs),
    }
    return out.getvalue(), counts, dict(sorted(paths.items()))


def validate(root: Path, manifest_file: Path, check: bool = True):
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    source = root / manifest["input"]["path"]
    output = root / manifest["output"]["path"]
    source_bytes = source.read_bytes()
    if git_blob(source_bytes) != manifest["input"]["git_blob"]:
        raise ValueError("SOURCE_INDEX_GIT_BLOB_DRIFT")
    generated, counts, by_path = expand(source_bytes.decode("utf-8"))
    if counts != manifest["counts"]:
        raise ValueError(f"RECOVERY_COUNT_DRIFT:{counts}")
    if by_path != manifest["by_source_path"]:
        raise ValueError("RECOVERY_SOURCE_PATH_DRIFT")
    result_bytes = generated.encode("utf-8")
    if git_blob(result_bytes) != manifest["output"]["git_blob"]:
        raise ValueError("RECOVERY_OUTPUT_GIT_BLOB_DRIFT")
    if check:
        if output.read_bytes() != result_bytes:
            raise ValueError("RECOVERY_OUTPUT_ROWS_DRIFT")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result_bytes)
    claims = manifest["claims"]
    if (claims["historical_branch_coverage_complete"] or
            claims["deduplicated_independent_laws"] or
            claims["executed_oracles"] or
            claims["semantic_distinctness_proven"] or
            claims["d10_ratified_added"] != 0 or
            claims["d10_coordinates_added"] != 0):
        raise ValueError("UNSUPPORTED_ADMISSION_CLAIM")
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = args.manifest or root / "knowledge/d10-filter/source-occurrence-manifest.json"
    print(json.dumps(validate(root, manifest, not args.write), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
