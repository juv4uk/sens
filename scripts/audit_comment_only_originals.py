#!/usr/bin/env python3
"""Conservative read-only census of comment-only ORIGINAL unpaired Lisp sources.

This is a SOURCE REVIEW QUEUE, not a new SENS parser, converter, publisher,
or authorization to mark any original executable program as migrated.
Only blank lines and lines whose first non-whitespace character is ';' qualify.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "sens-original-comment-only-audit/v1"
CANDIDATE_SCHEMA = "sens-original-three-pass-eligibility/v1"
UNCLASSIFIED = "UNCLASSIFIED_NEEDS_SOURCE_PROOF"
NONEXEC = frozenset(("NONPROGRAM_DATA_REVIEWED", "ARCHIVED_BENCHMARK_NONPROGRAM"))


class AuditError(ValueError):
    pass


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def checked_path(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "//" in value:
        raise AuditError("invalid original source path")
    result = PurePosixPath(value)
    if (result.is_absolute() or result.as_posix() != value or
            result.suffix != ".lisp" or
            any(part in ("", ".", "..") for part in value.split("/"))):
        raise AuditError(f"unsafe original .lisp path: {value!r}")
    return result


def semantic_lines(raw: bytes) -> tuple[bool, int]:
    """Recognize only whole-line semicolon comments; no speculative Lisp reader."""
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise AuditError("source is not valid UTF-8") from exc
    lines = text.splitlines()
    return (all(not line.strip() or line.lstrip().startswith(";") for line in lines),
            len(lines))


def scan(repo: Path, candidate_report: dict) -> dict:
    if (not isinstance(candidate_report, dict) or
            candidate_report.get("schema") != CANDIDATE_SCHEMA or
            candidate_report.get("source_era") != "auto" or
            "read-only" not in str(candidate_report.get("mode", ""))):
        raise AuditError("canonical conservative source report required")
    summary = candidate_report.get("summary")
    if (not isinstance(summary, dict) or
            summary.get("physical_outputs_created") != 0 or
            summary.get("original_unpaired_executables_migrated_by_this_tool") != 0):
        raise AuditError("canonical report claimed physical/semantic publication")
    blocked = candidate_report.get("blocked_sources")
    pending = candidate_report.get("mechanical_candidates")
    if not isinstance(blocked, list) or not isinstance(pending, list):
        raise AuditError("original full source lists missing")
    if (len(blocked) != summary.get("blocked") or
            len(pending) != summary.get("mechanical_candidates") or
            len(blocked) + len(pending) != summary.get("scanned")):
        raise AuditError("source census is incomplete")
    repo = repo.resolve(strict=True)
    seen: set[str] = set()
    results: list[dict] = []
    active = 0
    for row in blocked + pending:
        if not isinstance(row, dict):
            raise AuditError("invalid canonical source row")
        rel = checked_path(row.get("path"))
        name = rel.as_posix()
        if name in seen:
            raise AuditError(f"duplicate original source: {name}")
        seen.add(name)
        if (row.get("same_stem_sens_already_exists") is not False or
                row.get("source_is_executable_proven") is not False or
                row.get("independent_semantic_oracle_passed") is not False):
            raise AuditError(f"unsafe source admission claim: {name}")
        if row.get("source_scope") in NONEXEC:
            continue
        if row.get("source_scope") != UNCLASSIFIED:
            raise AuditError(f"unknown source scope: {name}")
        active += 1
        path = repo
        for part in rel.parts:
            path = path / part
            if path.is_symlink():
                raise AuditError(f"source symlink forbidden: {name}")
        if not path.is_file() or path.with_suffix(".sens").exists():
            raise AuditError(f"original source missing or already paired: {name}")
        raw = path.read_bytes()
        sha = row.get("source_git_blob_sha")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise AuditError(f"invalid Git blob SHA: {name}")
        if git_blob_sha(raw) != sha:
            raise AuditError(f"source Git blob drift: {name}")
        comment_only, line_count = semantic_lines(raw)
        if not comment_only:
            continue
        results.append({
            "path": name,
            "source_git_blob_sha": sha,
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "lines": line_count,
            "classification": "COMMENT_ONLY_REVIEW_PENDING",
            "source_is_executable_proven": False,
            "independent_semantic_oracle_passed": False,
            "physical_sens_published": False,
        })
    if len(seen) != summary.get("original_unpaired_sources_scanned"):
        raise AuditError("missing canonical originals")
    return {
        "schema": SCHEMA,
        "mode": "READ_ONLY_SOURCE_KIND_REVIEW_NOT_MIGRATION",
        "summary": {
            "original_unpaired": len(seen),
            "active_or_unclassified_scanned": active,
            "strict_comment_only_review_candidates": len(results),
            "physical_outputs_created": 0,
            "executable_semantics_certified": 0,
        },
        "sources": sorted(results, key=lambda item: item["path"]),
        "note": (
            "Exact original-file SHA and semicolon-only syntax are evidence that "
            "the source text contains no active top-level forms. This audit does "
            "not automatically change reviewed source classification, corpus "
            "denominators, T5 admission, or release gates."
        ),
    }


def load_canonical(repo: Path) -> dict:
    path = repo / "scripts/report_original_migration_candidates.py"
    if not path.is_file() or path.is_symlink():
        raise AuditError("canonical migration reporter unavailable")
    spec = importlib.util.spec_from_file_location("comment_only_canonical_report", path)
    if spec is None or spec.loader is None:
        raise AuditError("canonical reporter could not be imported")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.build_report(repo)


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--repo", type=Path, default=ROOT)
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    try:
        repo = args.repo.resolve(strict=True)
        out = args.out.resolve(strict=False)
        if out.is_relative_to(repo) or out.is_symlink() or out.exists():
            raise AuditError("new evidence output must be outside repo, no overwrite")
        report = scan(repo, load_canonical(repo))
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
    except (OSError, AuditError, RuntimeError, UnicodeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
