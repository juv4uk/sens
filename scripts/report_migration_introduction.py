#!/usr/bin/env python3
"""Read-only Git pickaxe chronology for one exact SENS source fragment.

A pickaxe hit means the count of a literal string changed in a commit, NOT
that a domain law was ratified, a function admitted, or a form executed.
This is an optional archaeology tool, never a migration or CI gate.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HistoryError(ValueError):
    pass


def git(root: Path, *args: str) -> bytes:
    run = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45,
        check=False,
    )
    if run.returncode:
        detail = run.stderr.decode("utf-8", errors="replace").strip()
        raise HistoryError(f"git failed: {detail[:250]}")
    return run.stdout


def tracked_regular(root: Path, commit: str, path: str) -> bool:
    raw = git(root, "--literal-pathspecs", "ls-tree", "-z", "--full-tree",
              commit, "--", path)
    rows = [p for p in raw.split(b"\0") if p]
    if len(rows) != 1:
        return False
    header, tab, filename = rows[0].partition(b"\t")
    return (bool(tab) and filename.decode("utf-8") == path and
            header.split()[:2] in ([b"100644", b"blob"], [b"100755", b"blob"]))


def inspect(root: Path, path: str, needle: str, ref: str = "HEAD",
            limit: int = 50) -> dict:
    if not needle or "\0" in needle or "\n" in needle:
        raise HistoryError("a nonempty one-line literal --needle is required")
    if (not path or path.startswith("/") or "\\" in path or
            any(part in ("", ".", "..") for part in path.split("/"))):
        raise HistoryError("--path must be a repository-relative regular file")
    if not 1 <= limit <= 100:
        raise HistoryError("--max-events must be 1..100")
    if not ref or ref.startswith("-") or "\0" in ref:
        raise HistoryError("invalid --ref")
    commit = git(root, "rev-parse", "--verify",
                 f"{ref}^{{commit}}").decode().strip()
    if not tracked_regular(root, commit, path):
        raise HistoryError(f"not a regular file at {commit[:12]}: {path}")
    # Combining --reverse with --follow silently loses pre-rename history
    # on some Git versions. Get Git's default traversal and reverse in Python.
    lines = git(root, "--literal-pathspecs", "log", "--follow",
                "--topo-order", "--format=%H%x09%cI%x09%s", "--no-color",
                f"-S{needle}", commit, "--", path).decode("utf-8").splitlines()
    lines.reverse()
    events = []
    for line in lines:
        parts = line.split("\t", 2)
        if len(parts) != 3 or len(parts[0]) != 40:
            raise HistoryError("unexpected Git log format")
        sha, when, subject = parts
        events.append({"sha": sha, "committed_at": when, "subject": subject})
    return {
        "schema": "sens-migration-git-pickaxe/v1",
        "role": "READ_ONLY_PROVENANCE_NOT_SEMANTIC_AUTHORITY",
        "commit": commit,
        "path_at_commit": path,
        "needle_literal": needle,
        "method": "git log --follow -S (literal occurrence-count delta)",
        "event_count": len(events),
        "first_observed_delta": events[0] if events else None,
        "events": events[:limit],
        "truncated": len(events) > limit,
        "interpretation": (
            "A pickaxe delta is not ratification, SENS meaning, current "
            "callability or proof of first-ever syntax use. Compare the actual "
            "commit and contemporary owner authority before migrating. "
            "No source is changed."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True,
                        help="current tracked regular source file")
    parser.add_argument("--needle", required=True,
                        help="exact literal expression fragment")
    parser.add_argument("--ref", default="HEAD",
                        help="Git commit/ref at which the path exists")
    parser.add_argument("--max-events", type=int, default=50)
    parser.add_argument("--repo", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        report = inspect(args.repo, args.path, args.needle,
                         args.ref, args.max_events)
    except (HistoryError, OSError, subprocess.TimeoutExpired) as exc:
        parser.exit(2, f"MIGRATION_PROVENANCE_ERROR: {exc}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
