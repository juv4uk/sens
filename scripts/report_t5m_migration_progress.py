#!/usr/bin/env python3
"""Read-only cross-check of two *independent* existing SENS migration audits.

Inputs are reports from:
  scripts/audit_t5_t5m_file_pairs.py
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
VALID_SOURCE_STATES = {"blocked", "would-write", "not-program"}


def _source_name(path: object, *, allow_bits: bool = False) -> str:
    endings = (".lisp", ".bits") if allow_bits else (".lisp",)
    if not isinstance(path, str) or not path.endswith(endings):
        raise ValueError(f"invalid source path: {path!r}")
    # PurePosixPath silently normalizes embedded "//" and "/./"; an audit
    # must reject such aliases rather than treating them as new Git paths.
    if ("\x00" in path or "\\" in path or
            any(part in ("", ".", "..") for part in path.split("/"))):
        raise ValueError(f"noncanonical source path: {path!r}")
    p = PurePosixPath(path)
    if p.is_absolute() or p.as_posix() != path:
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
    # Вилучені конкурсні варіанти збережені для історії, але не є
    # активними джерелами та не повинні створювати фальшиві RED.
    return {name for name in validated if "superseded" not in PurePosixPath(name).parts}


def combine(pairs: dict, readiness: dict, tracked_sources: set[str]) -> dict:
    if pairs.get("schema") != PAIRS_SCHEMA:
        raise ValueError("expected canonical T5 physical pair audit v1")
    if readiness.get("schema") != READINESS_SCHEMA:
        raise ValueError("expected canonical T5 readiness census v2")
    if pairs.get("mode") != "tracked-only":
        raise ValueError("cannot combine untracked or generated .sens output")
    if readiness.get("mode") != "original unpaired .lisp only; one physical-free dry-run (SID8/Sens8 eras retired)":
        raise ValueError("unexpected corpus interpretation in readiness input")

    pair_entries: dict[str, dict] = {}
    for row in pairs.get("files", []):
        source = _source_name(row.get("source"), allow_bits=True)
        if source in pair_entries:
            raise ValueError(f"duplicate physical source pair: {source}")
        expected = str(PurePosixPath(source).with_suffix(".sens"))
        if row.get("sens") != expected:
            raise ValueError(f"not a same-stem physical .sens: {source} -> {row.get('sens')}")
        if row.get("physical_status") not in ("PASS", "BLOCKED"):
            raise ValueError(f"unrecognized T5 audit status: {source}")
        if row["physical_status"] == "PASS" and row.get("physical_codec") not in ("t5m", "t5"):
            raise ValueError(f"physical PASS without identified T5M/T5 codec: {source}")
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

    # The physical auditor includes .bits-backed SENS fixtures. They have
    # exact binary sources, but are NOT untranslated executable .lisp files.
    # Keep their physical evidence visible without contaminating the Lisp
    # migration denominator or the migrator's skipped .lisp source set.
    lisp_pairs = {s: row for s, row in pair_entries.items() if s.endswith(".lisp")}
    binary_pairs = {s: row for s, row in pair_entries.items() if s.endswith(".bits")}

    queue: dict[str, dict] = {}
    for row in readiness.get("candidate_rows", []):
        source = _source_name(row.get("path"))
        if source in queue:
            raise ValueError(f"duplicate unpaired source: {source}")
        statuses = row.get("status")
        if not isinstance(statuses, dict) or set(statuses) != {"auto"}:
            raise ValueError(f"incomplete source-era evidence: {source}")
        if any(v not in VALID_SOURCE_STATES for v in statuses.values()):
            raise ValueError(f"unexpected source-era state: {source}")
        if statuses["auto"] == "not-program" and row.get("source_scope") not in (
            "NONPROGRAM_DATA_REVIEWED", "NONPROGRAM_COMMENT_ONLY",
            "ARCHIVED_BENCHMARK_NONPROGRAM",
        ):
            raise ValueError(f"unreviewed not-program in source ledger: {source}")
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
    if skipped != set(lisp_pairs):
        raise ValueError("the two existing audits disagree about paired .lisp paths")
    if set(lisp_pairs) & set(queue):
        raise ValueError("an original source cannot be paired AND unpaired")

    # A .sens without a tracked same-stem .lisp is an orphan physical
    # artifact, not evidence of migrated source or runtime semantics.
    for tracked in tracked_sources:
        _source_name(tracked)
    orphan_physical_sens = sorted(
        row["sens"] for source, row in lisp_pairs.items()
        if source not in tracked_sources
    )
    represented = set(lisp_pairs) | set(queue)
    missing = sorted(tracked_sources - represented)
    unknown = sorted(represented - tracked_sources)

    ledger = []
    for source in sorted(represented):
        if source in lisp_pairs:
            p = lisp_pairs[source]
            # Legacy T5 can roundtrip physically but is NOT current T5M.
            # Keep it visible as migration work, never promote it as a
            # canonical current carrier or as native semantic proof.
            condition = ("PHYSICAL_T5_PAIR_BLOCKED" if p["physical_status"] != "PASS"
                         else "PHYSICAL_LEGACY_T5_PAIR_REQUIRES_T5M"
                         if p["physical_codec"] == "t5"
                         else "PHYSICAL_T5M_PAIR_PENDING_INDEPENDENT_ORACLE")
            ledger.append({
                "source": source, "sens": p["sens"],
                "source_category": "paired",
                "status": condition,
                "physical_codec": p.get("physical_codec"),
                "source_sha256": p.get("source_sha256"),
                "physical_sha256": p.get("physical_sha256"),
                "typed_word_sha256": p.get("typed_word_sha256"),
                "source_view_status": p.get("source_status"),
                "semantic_admitted": False,
                "oracle_witness": None,
                "first_empty": (p.get("error") if condition == "PHYSICAL_T5_PAIR_BLOCKED"
                                else "legacy T5 must be converted to current T5M"
                                if p["physical_codec"] == "t5"
                                else "needs independent source/oracle witness"),
            })
        else:
            u = queue[source]
            archived = u.get("source_scope") == "ARCHIVED_BENCHMARK_NONPROGRAM"
            reviewed = u.get("source_scope") == "NONPROGRAM_DATA_REVIEWED"
            comment_only = u.get("source_scope") == "NONPROGRAM_COMMENT_ONLY"
            condition = ("NONPROGRAM_ARCHIVED_NO_EXECUTABLE_T5"
                         if archived else
                         "NONPROGRAM_REVIEWED_NO_EXECUTABLE_T5"
                         if reviewed else
                         "NONPROGRAM_COMMENT_ONLY_NO_EXECUTABLE_T5"
                         if comment_only else
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
                "first_empty": u.get("empty")
                                 or "mechanical candidate still needs oracle",
            })

    counts = Counter(row["status"] for row in ledger)
    # Mechanical inventory is not proof that all executable Lisp reverses to SENS.
    # Non-program DATA and archives are deliberately not executable targets.
    nonprogram = {"NONPROGRAM_ARCHIVED_NO_EXECUTABLE_T5",
                  "NONPROGRAM_REVIEWED_NO_EXECUTABLE_T5",
                  "NONPROGRAM_COMMENT_ONLY_NO_EXECUTABLE_T5"}
    executable_rows = [row for row in ledger if row["status"] not in nonprogram]
    semantic_proved = sum(
        row["semantic_admitted"] is True and row["oracle_witness"] is not None
        for row in executable_rows
    )
    all_executable_roundtrip_verified = (
        not missing and not unknown and not orphan_physical_sens
        and bool(executable_rows) and semantic_proved == len(executable_rows)
    )
    discrepancy = bool(missing or unknown or any(
        r["status"] == "PHYSICAL_T5_PAIR_BLOCKED" for r in ledger
    ) or any(r["physical_status"] == "BLOCKED" for r in binary_pairs.values()))
    return {
        "schema": SCHEMA,
        "status": "BLOCKED_DISCREPANCY" if discrepancy else "COMPLETE_MECHANICAL_INVENTORY_ONLY",
        "source_complete": not missing and not unknown,
        "semantic_certification": "NOT_ATTESTED_BY_THESE_AUDITS",
        "all_executable_lisp_roundtrip_verified": all_executable_roundtrip_verified,
        "executable_roundtrip_coverage": {
            "executable_or_unclassified_sources": len(executable_rows),
            "independent_runtime_oracle_verified": semantic_proved,
            "blocked_or_unverified": len(executable_rows) - semantic_proved,
            "nonprogram_excluded_from_executable_target": len(ledger) - len(executable_rows),
        },
        "summary": {
            "tracked_lisp_sources": len(tracked_sources),
            "tracked_physical_sens_pairs": len(lisp_pairs),
            "tracked_binary_source_fixture_pairs": len(binary_pairs),
            "binary_source_fixture_physical_blocked": sum(
                r["physical_status"] == "BLOCKED" for r in binary_pairs.values()
            ),
            "unpaired_source_rows": len(queue),
            "mechanically_canonical_physical_pairs": sum(
                r["physical_status"] == "PASS" for r in lisp_pairs.values()
            ),
            "mechanically_canonical_current_t5m_pairs": sum(
                r["physical_status"] == "PASS" and r.get("physical_codec") == "t5m"
                for r in lisp_pairs.values()
            ),
            "legacy_t5_pairs_requiring_t5m": sum(
                r["physical_status"] == "PASS" and r.get("physical_codec") == "t5"
                for r in lisp_pairs.values()
            ),
            "independently_oracle_certified_from_these_inputs": 0,
            "status_counts": dict(sorted(counts.items())),
            "missing_from_both_audits": len(missing),
            "unexpected_untracked_paths": len(unknown),
            "orphan_physical_sens_without_tracked_lisp": len(orphan_physical_sens),
        },
        "orphan_physical_sens_paths": orphan_physical_sens,
        "missing_source_paths": missing,
        "untracked_or_stale_source_paths": unknown,
        "files": ledger,
        "warning": (
            "A physical T5M pair is not an executable-semantic admission; "
            "legacy T5 physical success does not establish current T5M. "
            ".bits-backed fixtures are counted separately from executable Lisp. "
            "The original .lisp requires an independent canonical D2 parser "
            "and observer/oracle proof, never a filename-only or codec-only pass."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=Path, required=True,
                        help="existing audit_t5_t5m_file_pairs.py --output JSON")
    parser.add_argument("--readiness", type=Path, required=True,
                        help="existing migration-readiness-census.py --out JSON")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-executable-roundtrip", action="store_true",
                        help="block without independent runtime-oracle proof for all executable Lisp")
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
        if args.require_executable_roundtrip and not report["all_executable_lisp_roundtrip_verified"]:
            print("LISP_TO_SENS_ROUNDTRIP_BLOCKED: native SENS/oracle parity unverified",
                  file=sys.stderr)
            return 2
        return 0 if report["status"] == "COMPLETE_MECHANICAL_INVENTORY_ONLY" else 2
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"MIGRATION PROGRESS LEDGER ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
