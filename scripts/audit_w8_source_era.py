#!/usr/bin/env python3
"""Auditable pre-D8 Git provenance for original W8-blocked Lisp sources.

This NEVER chooses --source-era=legacy/current, converts .lisp, writes .sens
or claims an old/new semantic identity. SHA equality proves only that the
identical Git blob existed at the pinned pre-ratification snapshot.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "3bde35c014a565e1b15999fc3da79a9be8623ea1"
BEFORE = datetime(2026, 10, 1, tzinfo=timezone.utc)
SCHEMA = "sens-w8-pre-d8-blob-provenance/v1"

class EvidenceError(ValueError):
    pass


def git(repo: Path, *args: str, binary: bool = False):
    p = subprocess.run(
        ["git", *args], cwd=repo, check=False, capture_output=True,
        timeout=45,
    )
    if p.returncode:
        raise EvidenceError("Git provenance unavailable: " +
                            p.stderr.decode("utf-8", errors="replace")[-500:])
    return p.stdout if binary else p.stdout.decode("utf-8", errors="strict").strip()


def tree_blobs(repo: Path, commit: str) -> dict[str, str]:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise EvidenceError("baseline must be a full immutable Git SHA")
    if git(repo, "cat-file", "-t", commit) != "commit":
        raise EvidenceError("baseline is not a commit")
    stamp = datetime.fromisoformat(git(repo, "show", "-s", "--format=%cI", commit))
    if stamp.tzinfo is None or stamp >= BEFORE:
        raise EvidenceError("baseline was not committed before the pre-D8 cutoff")
    records = git(repo, "ls-tree", "-r", "-z", "--full-tree", commit, binary=True)
    result: dict[str, str] = {}
    for record in records.split(b"\x00"):
        if not record:
            continue
        try:
            meta, name = record.split(b"\t", 1)
            mode, kind, sha = meta.decode("ascii").split()
            path = name.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise EvidenceError("malformed historical Git tree") from exc
        if mode != "100644" or kind != "blob" or not path.endswith(".lisp"):
            continue
        if path in result:
            raise EvidenceError("duplicate historical path")
        result[path] = sha
    return result


def current_tracked_blobs(repo: Path) -> dict[str, str]:
    records = git(repo, "ls-files", "--stage", "-z", binary=True)
    out: dict[str, str] = {}
    for record in records.split(b"\x00"):
        if not record:
            continue
        try:
            info, name = record.split(b"\t", 1)
            mode, sha, stage = info.decode("ascii").split()
            path = name.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise EvidenceError("malformed current Git index") from exc
        if mode != "100644" or stage != "0" or not path.endswith(".lisp"):
            continue
        if path in out:
            raise EvidenceError("duplicate indexed source")
        out[path] = sha
    return out


def original_census(repo: Path) -> dict:
    path = repo / "scripts/report_original_migration_candidates.py"
    spec = importlib.util.spec_from_file_location("sens_original_census_for_w8", path)
    if spec is None or spec.loader is None:
        raise EvidenceError("original corpus reporter is missing")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.build_report(repo)


def report(repo: Path, census: dict, historical: dict[str, str], current: dict[str, str],
           baseline: str = BASELINE) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", baseline):
        raise EvidenceError("invalid baseline SHA")
    groups = census.get("exact_blocker_cohorts")
    if not isinstance(groups, list):
        raise EvidenceError("current canonical W8 blocker census unavailable")
    items = []
    seen: set[str] = set()
    for group in groups:
        if group.get("family") != "w8-provenance":
            continue
        word = group.get("coordinate")
        if not isinstance(word, str) or re.fullmatch(r"[01]{8}", word) is None:
            raise EvidenceError("W8 cohort does not have one exact binary word")
        for member in group.get("original_sources", []):
            path = member.get("path")
            source_sha = member.get("source_git_blob_sha")
            if not isinstance(path, str) or Path(path).is_absolute() or ".." in Path(path).parts or not path.endswith(".lisp"):
                raise EvidenceError("untrusted W8 source path")
            if path in seen:
                raise EvidenceError("duplicate W8 source membership")
            seen.add(path)
            if (not isinstance(source_sha, str)
                    or not re.fullmatch(r"[0-9a-f]{40}", source_sha)
                    or current.get(path) != source_sha):
                raise EvidenceError("W8 source SHA does not match tracked stage-0 Git blob")
            old = historical.get(path)
            if old is None:
                verdict = "NOT_PRESENT_IN_PRE_D8_SNAPSHOT"
            elif old != source_sha:
                verdict = "CHANGED_SINCE_PRE_D8_SNAPSHOT"
            else:
                verdict = "SAME_BLOB_BEFORE_D8_RATIFICATION"
            items.append({
                "path": path, "w8_first_blocker": word,
                "source_git_blob_sha": source_sha,
                "pre_d8_blob_sha": old, "provenance": verdict,
                "historical_legacy_semantics": "NOT_PROVEN",
                "executable_semantics": "NOT_PROVEN",
                "permission_to_choose_legacy": False,
            })
    items.sort(key=lambda r: (r["w8_first_blocker"], r["path"]))
    counts = {v: sum(x["provenance"] == v for x in items) for v in (
        "SAME_BLOB_BEFORE_D8_RATIFICATION",
        "CHANGED_SINCE_PRE_D8_SNAPSHOT",
        "NOT_PRESENT_IN_PRE_D8_SNAPSHOT",
    )}
    per_w8 = {}
    for row in items:
        word = row["w8_first_blocker"]
        per_w8.setdefault(word, {"total": 0, "same_blob": 0})
        per_w8[word]["total"] += 1
        per_w8[word]["same_blob"] += int(row["provenance"] == "SAME_BLOB_BEFORE_D8_RATIFICATION")
    if sum(counts.values()) != len(items):
        raise EvidenceError("non-exhaustive source provenance ledger")
    return {
        "schema": SCHEMA,
        "mode": "READ_ONLY_GIT_PROVENANCE_NOT_SEMANTIC_ADMISSION",
        "baseline_pre_d8_commit": baseline,
        "baseline_before_utc": BEFORE.isoformat(),
        "summary": {"w8_first_blocked_originals": len(items),
                    **counts, "current_semantic_admissions": 0, "published_sens": 0},
        "by_w8_first_blocker": dict(sorted(per_w8.items())),
        "sources": items,
        "interpretation": (
            "Same Git blob at pre-D8 snapshot is chronological evidence only. "
            "No automatic legacy/source-era decision, opcode semantics, "
            "numeric/Text7/host behavior, or release approval is inferred."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=ROOT)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    root = args.repo.resolve(strict=True)
    out = args.out.resolve(strict=False)
    if out.is_relative_to(root) or out.is_symlink():
        print("BLOCKED: report must be outside source repository", file=sys.stderr)
        return 2
    try:
        snapshot = tree_blobs(root, BASELINE)
        census = original_census(root)
        ledger = report(root, census, snapshot, current_tracked_blobs(root))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (EvidenceError, OSError, subprocess.SubprocessError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(ledger["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
