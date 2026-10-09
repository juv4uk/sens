#!/usr/bin/env python3
"""Read-only cross-check of two *independent* existing SENS migration audits.

Inputs are reports from:
  scripts/audit_t5_file_pairs.py
  scripts/migration-readiness-census.py

Do NOT encode Lisp, publish .sens, reinterpret DATA as programs, or award
semantic-oracle admission. This combines the physical *pairs* inventory and
the fail-closed *unpaired source* census into one complete source-path ledger.
It identifies missing, duplicate and stale rows. No fallback to fuzzy matching.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path, PurePosixPath

PAIRS_SCHEMA = "sens-t5-file-pair-audit/v1"
READINESS_SCHEMA = "sens-t5-migration-readiness/v2"
SCHEMA = "sens-t5-migration-progress/v1"
VALID_SOURCE_STATES = {"blocked", "would-write"}


def _source_name(path: object) -> str:
    if not isinstance(path, str) or not path.endswith(".lisp"):
        raise ValueError(f"invalid source path: {path!r}")
    p = PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts or "\\" in path or path.startswith("./"):
        raise ValueError(f"unsafe source path: {path!r}")
    return path


def tracked_lisp_paths(root: Path) -> set[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "*.lisp"],
        capture_output=True, check=True,
    )
    names = [os.fsdecode(x) for x in result.stdout.split(b"\0") if x]
    validated = [_source_name(name) for name in names]
    if len(validated) != len(set(validated)):
        raise ValueError("duplicate Git source paths")
    return set(validated)


def combine(pairs: dict, readiness: dict, tracked_sources: set[str]) -> dict:
    if pairs.get("schema") != PAIRS_SCHEMA:
        raise ValueError("expected canonical T5 physical pair audit v1")
    if readiness.get("schema") != READINESS_SCHEMA:
        raise ValueError("expected canonical T5 readiness census v2")
    if pairs.get("mode") != "tracked-only":
        raise ValueError("cannot combine untracked or generated .sens output")
    if readiness.get("mode") != "original unpaired .lisp only; three separate physical-free dry-runs":
        raise ValueError("unexpected corpus interpretation in readiness input")

    pair_entries: dict[str, dict] = {}
    for row in pairs.get("files", []):
        source = _source_name(row.get("source"))
        if source in pair_entries:
            raise ValueError(f"duplicate physical source pair: {source}")
        expected = str(PurePosixPath(source).with_suffix(".sens"))
        if row.get("sens") != expected:
            raise ValueError(f"not a same-stem physical .sens: {source} -> {row.get('sens')}")
        if row.get("physical_status") not in ("PASS", "BLOCKED"):
            raise ValueError(f"unrecognized T5 audit status: {source}")
        if row.get("source_status") not in (
            "EXACT_BINARY_SOURCE", "PENDING_ORACLE", "BLOCKED", "NOT_CHECKED",
        ):
            raise ValueError(f"unrecognized source-pair status: {source}")
        pair_entries[source] = row

    pair_summary = pairs.get("summary", {})
    if (pair_summary.get("sens_files") != len(pair_entries)
        or pair_summary.get("physical_pass") != sum(
            r["physical_status"] == "PASS" for r in pair_entries.values()
        )):
        raise ValueError("physical-pair source ledger disagrees with audit summary")

    queue: dict[str, dict] = {}
    for row in readiness.get("candidate_rows", []):
        source = _source_name(row.get("path"))
        if source in queue:
            raise ValueError(f"duplicate unpaired source: {source}")
        statuses = row.get("status")
        if not isinstance(statuses, dict) or set(statuses) != {"auto", "legacy", "current"}:
            raise ValueError(f"incomplete source-era evidence: {source}")
        if any(v not in VALID_SOURCE_STATES for v in statuses.values()):
            raise ValueError(f"unexpected source-era state: {source}")
        if row.get("physical_published") is not False or row.get("semantic_oracle_admitted") is not False:
            raise ValueError(f"unpaired report falsely claims published/admitted: {source}")
        if not isinstance(row.get("source_sha256"), str) or len(row["source_sha256"]) != 64:
            raise ValueError(f"missing SHA-pinned original: {source}")
        queue[source] = row

    if len(queue) != readiness.get("migrator_summary", {}).get("files_seen"):
        raise ValueError("unpaired census row count disagrees with migrator")
    skipped = {_source_name(s) for s in readiness.get("skipped_existing_sens_pairs", [])}
    if len(skipped) != len(readiness.get("skipped_existing_sens_pairs", [])):
        raise ValueError("duplicate skipped source in readiness")
    if skipped != set(pair_entries):
        raise ValueError("the two existing audits disagree about paired .lisp paths")
    if set(pair_entries) & set(queue):
        raise ValueError("an original source cannot be paired AND unpaired")

    represented = set(pair_entries) | set(queue)
    missing = sorted(tracked_sources - represented)
    unknown = sorted(represented - tracked_sources)

    ledger = []
    for source in sorted(represented):
        if source in pair_entries:
            p = pair_entries[source]
            condition = ("PHYSICAL_T5_PAIR_BLOCKED" if p["physical_status"] != "PASS"
                         else "PHYSICAL_T5_PAIR_PENDING_INDEPENDENT_ORACLE")
            ledger.append({
                "source": source, "sens": p["sens"],
                "source_category": "paired",
                "status": condition,
                "source_sha256": p.get("source_sha256"),
                "physical_sha256": p.get("physical_sha256"),
                "typed_word_sha256": p.get("typed_word_sha256"),
                "source_view_status": p.get("source_status"),
                "semantic_admitted": False,
                "oracle_witness": None,
                "first_blocker": p.get("error") if condition.endswith("BLOCKED")
                                    else "needs independent source/oracle witness",
            })
        else:
            u = queue[source]
            nonprogram = u.get("source_scope") == "ARCHIVED_BENCHMARK_NONPROGRAM"
            condition = ("NONPROGRAM_ARCHIVED_NO_EXECUTABLE_T5"
                         if nonprogram else
                         "MECHANICAL_CANDIDATE_NEEDS_ORACLE"
                         if any(v == "would-write" for v in u["status"].values()) else
                         "UNPAIRED_SOURCE_BLOCKED")
            ledger.append({
                "source": source, "sens": str(PurePosixPath(source).with_suffix(".sens")),
                "source_category": "unpaired",
                "status": condition, "source_sha256": u["source_sha256"],
                "source_era_states": u["status"],
                "semantic_admitted": False,
                "oracle_witness": None,
                "first_blocker": u.get("blocker_by_era", {}).get("auto")
                                 or "mechanical candidate still needs oracle",
            })

    counts = Counter(row["status"] for row in ledger)
    discrepancy = bool(missing or unknown or any(
        r["status"] == "PHYSICAL_T5_PAIR_BLOCKED" for r in ledger
    ))
    return {
        "schema": SCHEMA,
        "status": "BLOCKED_DISCREPANCY" if discrepancy else "COMPLETE_MECHANICAL_INVENTORY_ONLY",
        "source_complete": not missing and not unknown,
        "semantic_certification": "NOT_ATTESTED_BY_THESE_AUDITS",
        "summary": {
            "tracked_lisp_sources": len(tracked_sources),
            "tracked_physical_sens_pairs": len(pair_entries),
            "unpaired_source_rows": len(queue),
            "mechanically_canonical_physical_pairs": pair_summary["physical_pass"],
            "independently_oracle_certified_from_these_inputs": 0,
            "status_counts": dict(sorted(counts.items())),
            "missing_from_both_audits": len(missing),
            "unexpected_untracked_paths": len(unknown),
        },
        "missing_source_paths": missing,
        "untracked_or_stale_source_paths": unknown,
        "files": ledger,
        "warning": (
            "A physical T5 pair is not an executable-semantic admission. "
            "The original .lisp requires an independent canonical D2 parser "
            "and observer/oracle proof, never a filename-only or codec-only pass."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=Path, required=True,
                        help="existing audit_t5_file_pairs.py --output JSON")
    parser.add_argument("--readiness", type=Path, required=True,
                        help="existing migration-readiness-census.py --out JSON")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        pair_data = json.loads(args.pairs.read_text(encoding="utf-8"))
        readiness = json.loads(args.readiness.read_text(encoding="utf-8"))
        report = combine(pair_data, readiness, tracked_lisp_paths(args.root))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False)
                            + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], **report["summary"]},
                         ensure_ascii=False, sort_keys=True))
        return 0 if report["status"] == "COMPLETE_MECHANICAL_INVENTORY_ONLY" else 2
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"MIGRATION PROGRESS LEDGER ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
