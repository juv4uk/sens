#!/usr/bin/env python3
"""Expose actual old-source candidates from the existing fail-closed T5 census.

Read-only. A parse/codec-admissible dry-run is NOT semantic admission:
only independent source-law and Rust oracle parity can authorize publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts/migrate-three-pass.py"
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
from migration_source_scope import scope
ARGS = [
    "--foundation", "knowledge/d1-d9-foundation.json",
    "--domain-surfaces", "crates/sens/src/domain_surface_registry_generated.rs",
    "--semantic-generated", "crates/sens/src/semantic_registry_generated.rs",
    "--semantic-registry", "crates/sens/src/semantic_registry.rs",
    "--necessary-forms", "crates/sens/src/eval/necessary_forms_generated.rs",
    "--historical-map", "contracts/core1-historical-sid-map.lisp",
    "--text7", "crates/sens/src/text7_projection_generated.rs",
]

# First blocking symptom only. This is scheduling metadata, NEVER evidence that
# a Lisp record is an executable, or that a domain law has been admitted.
BLOCKER_ACTIONS = {
    "w8-provenance": "Pin original source Git blob and prove legacy SID8 vs ratified current D8 before an explicit --source-era retry.",
    "host-effect": "Prove host I/O/effect semantics and independent old/current observable parity; do not guess PRINT mappings.",
    "unmapped-function": "Resolve function identity against owner-ratified D1-D9 and historical successor ledger; unknown stays BLOCKED.",
    "d2-or-domain-data": "Inspect non-binary token and classify executable vs schema/archive/typed D2-as-data before any conversion.",
    "lexical-binding": "Prove lambda/define variable binding and call-head scope; keep symbolic locals blocked without a law.",
    "numeric-law": "Prove exact-width numeric representation and operations before emitting any words.",
    "text-or-quote": "Prove D7 Text7/quoted-data handling and code/data boundaries; no raw text masquerading as a program.",
    "other-unproved": "Review exact source/reason and request one authoritative law plus Rust D2 and independent oracle proof.",
}


def blocker_family(reason: str) -> str:
    """Stable first-symptom classification; does NOT attest executable meaning."""
    if not isinstance(reason, str):
        raise ValueError("blocker reason must be text")
    r = reason.casefold()
    if ("ambiguous" in r or "ambiguity" in r or "двознач" in r) and any(
        marker in r for marker in ("w8", "d8", "8-bit", "eight-bit", "8 bit")
    ):
        return "w8-provenance"
    if any(marker in r for marker in ("print", "host-effect", "host effect", "unproven io", "host io")):
        return "host-effect"
    if any(marker in r for marker in ("binding", "bound", "lambda", "local variable", "dynamic call", "lexical")):
        return "lexical-binding"
    if any(marker in r for marker in ("numeric", "number-width", "integer literal", "number-law")):
        return "numeric-law"
    if any(marker in r for marker in ("text7", "quoted", "quote datum", "string literal", "text law")):
        return "text-or-quote"
    if (r.startswith("word ") or "non-bit" in r or "not a binary" in r
            or "structural d2" in r or "d2-as-data" in r):
        return "d2-or-domain-data"
    if any(marker in r for marker in ("unmapped", "unknown function", "unratified function",
                                       "function head", "missing successor")):
        return "unmapped-function"
    return "other-unproved"


def blocker_cohorts(blocked_sources: list[dict]) -> list[dict]:
    """Build exhaustive disjoint source-blob-locked cohorts in stable order."""
    by_family: dict[str, list[dict]] = {}
    seen: set[str] = set()
    for row in blocked_sources:
        path = row["path"]
        if path in seen:
            raise ValueError(f"duplicate unpaired original source in ledger: {path}")
        seen.add(path)
        if row["status"] != "BLOCKED" or row["same_stem_sens_already_exists"]:
            raise ValueError(f"not an unpaired BLOCKED source: {path}")
        family = blocker_family(row["reason"])
        by_family.setdefault(family, []).append({
            "path": path,
            "source_git_blob_sha": row["source_git_blob_sha"],
            "first_blocker": row["reason"],
        })
    return [
        {
            "family": family,
            "count": len(rows),
            "next_action": BLOCKER_ACTIONS[family],
            "original_sources": sorted(rows, key=lambda row: row["path"]),
            "status": "BLOCKED_NOT_ORACLE_ADMITTED",
        }
        for family, rows in sorted(by_family.items(),
                                   key=lambda item: (-len(item[1]), item[0]))
    ]


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def categorize(row: dict, root: Path) -> dict:
    rel = Path(row["path"])
    if rel.is_absolute() or ".." in rel.parts or rel.suffix != ".lisp":
        raise ValueError("untrusted migrator path")
    source = root / rel
    if not source.is_file() or source.is_symlink():
        raise ValueError("source is not a regular tracked file")
    pair = source.with_suffix(".sens")
    result = {
        "path": rel.as_posix(),
        "source_git_blob_sha": git_blob_sha(source),
        "same_stem_sens_already_exists": pair.exists() or pair.is_symlink(),
        "source_is_executable_proven": False,
        "source_scope": scope(rel.as_posix()),
        "independent_semantic_oracle_passed": False,
    }
    if row["status"] == "would-write":
        result.update(
            status="CANDIDATE_NOT_ADMITTED",
            destination=rel.with_suffix(".sens").as_posix(),
            proposed_physical_sha256=row["physical_sha256"],
            proposed_typed_word_sha256=row["typed_word_sha256"],
            proposed_bytes=row["bytes"],
            proposed_words=row["semantic_word_count"],
            passes=row["passes"],
        )
    elif row["status"] == "blocked":
        result.update(status="BLOCKED", reason=row.get("reason", "unknown"))
    else:
        raise ValueError(f"unexpected dry-run status {row['status']!r}")
    return result


def build_report(root: Path = ROOT) -> dict:
    with tempfile.TemporaryDirectory(prefix="sens-original-candidate-") as td:
        report_path = Path(td) / "migration.json"
        output_dir = Path(td) / "no-physical-output"
        proc = subprocess.run(
            [sys.executable, str(root / "scripts/migrate-three-pass.py"),
             str(root), "--out", str(output_dir), *ARGS,
             "--report", str(report_path), "--dry-run",
             "--unpaired-only", "--source-era", "auto"],
            cwd=root, capture_output=True, text=True, timeout=210
        )
        if not report_path.exists():
            raise RuntimeError(f"no dry-run report: {proc.stderr[-2000:]}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if proc.returncode not in (0, 2):
            raise RuntimeError(f"dry-run crashed ({proc.returncode}): {proc.stderr[-2000:]}")
        if report["mode"] != "dry-run" or report["summary"]["files_written"] != 0:
            raise RuntimeError("unexpected write-capable migration report")
        if list(output_dir.rglob("*.sens")) if output_dir.exists() else []:
            raise RuntimeError("dry-run emitted physical output")
        rows = [categorize(row, root) for row in report["files"]]
        # The migrator's --unpaired-only contract must be enforced in BOTH
        # producer and consumer; counting a new paired canary as old progress is
        # a factual error, even if the physical bytes round-trip.
        if any(row["same_stem_sens_already_exists"] for row in rows):
            raise RuntimeError("unpaired original census included already paired .lisp")
        excluded = report.get("skipped_paired_paths", [])
        if len(excluded) != report["summary"].get("files_skipped_paired"):
            raise RuntimeError("paired-source exclusion count mismatch")
        if len(set(excluded)) != len(excluded):
            raise RuntimeError("duplicate paired-source exclusion")
        for excluded_path in excluded:
            rel = Path(excluded_path)
            if rel.is_absolute() or ".." in rel.parts or rel.suffix != ".lisp":
                raise RuntimeError("unsafe paired-source exclusion path")
            if not (root / rel.with_suffix(".sens")).is_file():
                raise RuntimeError("excluded pair is missing")
        candidates = [r for r in rows if r["status"] == "CANDIDATE_NOT_ADMITTED"]
        unpaired = [r for r in candidates if not r["same_stem_sens_already_exists"]]
        archived = [r for r in unpaired if r["source_scope"] == "ARCHIVED_BENCHMARK_NONPROGRAM"]
        actionable = [r for r in unpaired if r["source_scope"] != "ARCHIVED_BENCHMARK_NONPROGRAM"]
        blocked = len(rows) - len(candidates)
        if len(rows) != report["summary"]["files_seen"] or blocked != report["summary"]["files_blocked"]:
            raise RuntimeError("migrator report totals inconsistent")
        blocked_sources = sorted(
            (row for row in rows if row["status"] == "BLOCKED"),
            key=lambda row: row["path"],
        )
        cohorts = blocker_cohorts(blocked_sources)
        active_blocked_sources = [
            row for row in blocked_sources
            if row["source_scope"] != "ARCHIVED_BENCHMARK_NONPROGRAM"
        ]
        active_cohorts = blocker_cohorts(active_blocked_sources)
        if sum(cohort["count"] for cohort in cohorts) != blocked:
            raise RuntimeError("source blocker cohort totals inconsistent")
        if len({row["path"] for row in rows}) != len(rows):
            raise RuntimeError("duplicate original source in migration ledger")
        return {
            "schema": "sens-original-three-pass-eligibility/v1",
            "authority": "candidate discovery only; parser/codec parity is NOT oracle parity",
            "mode": "read-only canonical migrator dry-run",
            "summary": {
                "scanned": len(rows),
                "original_unpaired_sources_scanned": len(rows),
                "already_paired_sources_excluded": len(excluded),
                "blocked": blocked,
                "blocker_family_counts": {cohort["family"]: cohort["count"] for cohort in cohorts},
                "mechanical_candidates": len(candidates),
                "already_paired_candidates": len(candidates)-len(unpaired),
                "unpaired_candidates_needing_original_oracle": len(actionable),
                "archived_nonprogram_mechanical_candidates": len(archived),
                "active_or_unclassified_mechanical_candidates": len(actionable),
                "active_or_unclassified_blocked": len(active_blocked_sources),
                "original_unpaired_executables_migrated_by_this_tool": 0,
                "physical_outputs_created": 0,
            },
            "source_era": "auto",
            "authority": "original unpaired current D1-D9 source; candidate only; no oracle admission",
            "already_paired_sources_excluded": excluded,
            "mechanical_candidates": candidates,
            "archived_nonprogram_candidates": archived,
            "actionable_not_yet_oracle_proven_candidates": actionable,
            "blocked_sources": blocked_sources,
            "blocker_cohorts": cohorts,
            "active_or_unclassified_blocker_cohorts": active_cohorts,
            "unpaired_blocker_sample": blocked_sources[:20],
            "required_evidence": [
                "prove original file is an executable SENS program, not an archive/catalogue",
                "prove exact historical function successor, D1/D2/w8 era and no host/IO effects",
                "run actual three-pass CLI to same-stem packed T5 without overwriting source",
                "Rust exact-domain oracle parity including wrong-domain negatives and digest",
                "merge only after focused and independent physical+syntax CI green",
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary":result["summary"],"candidates":result["mechanical_candidates"]},ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
