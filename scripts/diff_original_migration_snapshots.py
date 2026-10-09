#!/usr/bin/env python3
"""Compare TWO immutable read-only original-SENS migration censuses.

This is coordination evidence, NOT a converter or a semantic oracle.
A disappearing BLOCK is not a migrated program until same-stem physical .sens
plus source-specific independent old/current oracle witnesses are established.

Input: scripts/report_original_migration_candidates.py --out snapshots,
schema sens-original-three-pass-eligibility/v1.
Output: deterministic machine-readable change ledger. No files touched in repo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

SCHEMA = "sens-original-migration-delta/v1"
SOURCE_SCHEMA = "sens-original-three-pass-eligibility/v1"
STATES = {"BLOCKED", "CANDIDATE_NOT_ADMITTED"}
NONPROGRAM = {"NONPROGRAM_DATA_REVIEWED", "ARCHIVED_BENCHMARK_NONPROGRAM"}
SHA40 = re.compile(r"[0-9a-f]{40}\Z")


class SnapshotError(ValueError):
    pass


def checked_source(path: object) -> str:
    if not isinstance(path, str) or not path or "\\" in path or "//" in path:
        raise SnapshotError("unsafe source path")
    p = PurePosixPath(path)
    if (p.is_absolute() or p.as_posix() != path or p.suffix != ".lisp"
            or any(part in (".", "..", "") for part in path.split("/"))):
        raise SnapshotError(f"unsafe .lisp source path {path!r}")
    return path


def checked_snapshot(doc: object, label: str) -> tuple[dict[str, dict], set[str]]:
    if not isinstance(doc, dict) or doc.get("schema") != SOURCE_SCHEMA:
        raise SnapshotError(f"{label}: unrecognized source schema")
    summary = doc.get("summary")
    if (doc.get("source_era") != "auto" or
            doc.get("mode") != "read-only canonical migrator dry-run" or
            not isinstance(summary, dict) or summary.get("physical_outputs_created") != 0 or
            summary.get("original_unpaired_executables_migrated_by_this_tool") != 0):
        raise SnapshotError(f"{label}: only read-only original census admitted")
    blocked, candidates = doc.get("blocked_sources"), doc.get("mechanical_candidates")
    paired = doc.get("already_paired_sources_excluded")
    if not isinstance(blocked, list) or not isinstance(candidates, list) or not isinstance(paired, list):
        raise SnapshotError(f"{label}: missing complete source ledgers")
    rows: dict[str, dict] = {}
    for row in blocked + candidates:
        if not isinstance(row, dict):
            raise SnapshotError(f"{label}: invalid row")
        name = checked_source(row.get("path"))
        if name in rows:
            raise SnapshotError(f"{label}: duplicate original source {name}")
        sha = row.get("source_git_blob_sha")
        if not isinstance(sha, str) or not SHA40.fullmatch(sha):
            raise SnapshotError(f"{label}: no immutable source blob SHA for {name}")
        expected = "BLOCKED" if row in blocked else "CANDIDATE_NOT_ADMITTED"
        if row.get("status") != expected or row.get("same_stem_sens_already_exists") is not False:
            raise SnapshotError(f"{label}: invalid unpaired status for {name}")
        if row.get("source_is_executable_proven") is not False or row.get(
                "independent_semantic_oracle_passed") is not False:
            raise SnapshotError(f"{label}: source authority is misrepresented for {name}")
        if expected == "BLOCKED" and not isinstance(row.get("reason"), str):
            raise SnapshotError(f"{label}: blocked row missing reason for {name}")
        if not isinstance(row.get("source_scope"), str):
            raise SnapshotError(f"{label}: source scope missing for {name}")
        rows[name] = row
    paired_set: set[str] = set()
    for name in paired:
        checked_source(name)
        if name in paired_set or name in rows:
            raise SnapshotError(f"{label}: duplicate/overlapping already-paired path {name}")
        paired_set.add(name)
    if (summary.get("original_unpaired_sources_scanned") != len(rows) or
            summary.get("blocked") != len(blocked) or
            summary.get("mechanical_candidates") != len(candidates) or
            summary.get("already_paired_sources_excluded") != len(paired_set)):
        raise SnapshotError(f"{label}: census count mismatch")
    return rows, paired_set


def compare(before: dict, after: dict) -> dict:
    old, old_pairs = checked_snapshot(before, "before")
    new, new_pairs = checked_snapshot(after, "after")
    removed_pairs = old_pairs - new_pairs
    if removed_pairs:
        raise SnapshotError(f"existing .sens pair disappeared: {sorted(removed_pairs)[:3]}")
    # A source cannot simply vanish: deletion is not binary migration.
    disappeared = (old.keys() - new.keys()) - (new_pairs - old_pairs)
    if disappeared:
        raise SnapshotError(f"unpaired source vanished without same-stem .sens: {sorted(disappeared)[:3]}")
    created = new.keys() - old.keys()
    added_pairs = new_pairs - old_pairs
    # Newly named source is a fresh queue member, never a migration credit.
    if any(name in old_pairs for name in created):
        raise SnapshotError("already paired source was reintroduced as unpaired")
    changes: list[dict] = []
    for path in sorted(old.keys() | new.keys()):
        old_row, new_row = old.get(path), new.get(path)
        if path in added_pairs:
            if old_row is None:
                raise SnapshotError(f"new pair has no previous source record: {path}")
            changes.append({
                "path": path, "kind": "NEW_PAIR_REQUIRES_ORACLE_AND_SOURCE_RECHECK",
                "before_source_git_blob_sha": old_row["source_git_blob_sha"],
                "before_status": old_row["status"],
                "after_status": "EXCLUDED_SAME_STEM_PAIR_NOT_ORACLE_CERTIFIED",
                "claim": "physical pair census only; cannot prove source unchanged or semantics",
            })
            continue
        if old_row is None:
            changes.append({
                "path": path, "kind": "NEW_SOURCE_NEEDS_ADMISSION",
                "after_source_git_blob_sha": new_row["source_git_blob_sha"],
                "after_status": new_row["status"],
            })
            continue
        if new_row is None:
            raise SnapshotError(f"unaccounted source disappearance: {path}")
        before_sha, after_sha = old_row["source_git_blob_sha"], new_row["source_git_blob_sha"]
        if before_sha != after_sha:
            changes.append({
                "path": path, "kind": "SOURCE_BYTES_CHANGED_REVIEW_REQUIRED",
                "before_source_git_blob_sha": before_sha,
                "after_source_git_blob_sha": after_sha,
                "before_status": old_row["status"], "after_status": new_row["status"],
            })
            continue
        old_scope, new_scope = old_row["source_scope"], new_row["source_scope"]
        if old_scope != new_scope:
            kind = ("NEW_NONPROGRAM_CLASSIFICATION_NOT_MIGRATION"
                    if new_scope in NONPROGRAM else "SOURCE_KIND_CHANGED_REVIEW_REQUIRED")
            changes.append({"path": path, "kind": kind,
                            "source_git_blob_sha": before_sha,
                            "before_scope": old_scope, "after_scope": new_scope,
                            "before_status": old_row["status"], "after_status": new_row["status"]})
        if old_row["status"] != new_row["status"]:
            changes.append({
                "path": path,
                "kind": ("MECHANICAL_CANDIDATE_NOT_ORACLE_ADMITTED"
                         if new_row["status"] == "CANDIDATE_NOT_ADMITTED"
                         else "MECHANICAL_CANDIDATE_REGRESSED_TO_BLOCKED"),
                "source_git_blob_sha": before_sha,
                "before_status": old_row["status"], "after_status": new_row["status"],
            })
        elif old_row["status"] == "BLOCKED" and old_row["reason"] != new_row["reason"]:
            changes.append({
                "path": path, "kind": "FIRST_BLOCKER_CHANGED_NOT_MIGRATED",
                "source_git_blob_sha": before_sha,
                "before_reason": old_row["reason"], "after_reason": new_row["reason"],
                "before_scope": old_scope, "after_scope": new_scope,
            })
    from collections import Counter
    counts = dict(sorted(Counter(change["kind"] for change in changes).items()))
    return {
        "schema": SCHEMA,
        "authority": "READ_ONLY_PROGRESS_TRIAGE_NOT_ORACLE_OR_PROGRAM_ADMISSION",
        "before": {"unpaired": len(old), "paired": len(old_pairs)},
        "after": {"unpaired": len(new), "paired": len(new_pairs)},
        "summary": {
            "new_pairs_pending_proof": len(added_pairs),
            "new_sources_not_credit": len(created),
            "unchanged_unpaired_sources": len(set(old) & set(new)) -
                sum(1 for p in set(old) & set(new) if old[p]["source_git_blob_sha"] != new[p]["source_git_blob_sha"]),
            "change_events": len(changes),
            "kind_counts": counts,
            "semantically_admitted_by_this_tool": 0,
            "physical_outputs_created": 0,
        },
        "changes": sorted(changes, key=lambda row: (row["path"], row["kind"])),
        "required_gate": (
            "new .sens pair means only pairing; certify exact source Git blob, "
            "canonical T5, D2 parser, and independent source-specific "
            "historical+current semantic oracle witnesses before claiming migration"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--before", type=Path, required=True)
    cli.add_argument("--after", type=Path, required=True)
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args(argv)
    try:
        output = args.out.resolve(strict=False)
        inputs = [args.before.resolve(strict=True), args.after.resolve(strict=True)]
        # Never replace a pinned snapshot or an existing previous diff.
        if output in inputs or output.exists() or output.is_symlink():
            raise SnapshotError("output exists, collides with source, or is symlink")
        documents = [json.loads(x.read_text(encoding="utf-8")) for x in inputs]
        result = compare(documents[0], documents[1])
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=2, sort_keys=True)
            file.write("\n")
    except (OSError, ValueError, SnapshotError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
