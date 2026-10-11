#!/usr/bin/env python3
"""Read-only, whole-history SENS branch source intake by immutable Git blobs.

Results are PROVENANCE / DEDUP candidates, not permission to merge historical
runtime semantics. Does not create, checkout, update or delete branches.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PART_ROOT = ROOT / "research/branch-history/20261011"
PARTS = ("01-08", "09-16", "17-24", "25-32", "33-40", "41-42")
ZERO_SHA = "0" * 40
SHA = re.compile(r"^[0-9a-f]{40}$")


def git(*args: str, allow_failure: bool = False) -> bytes:
    result = subprocess.run(("git", *args), cwd=ROOT, capture_output=True)
    if result.returncode and not allow_failure:
        raise RuntimeError("git " + " ".join(args[:5]) + ": "
                           + result.stderr.decode("utf-8", "replace")[:500])
    if result.returncode and allow_failure:
        return b""
    return result.stdout


def text(raw: bytes) -> str:
    return raw.decode("utf-8", "surrogateescape")


def snapshot() -> list[dict]:
    branches: list[dict] = []
    for part in PARTS:
        obj = json.loads((PART_ROOT / f"live-heads-pages-{part}.json")
                         .read_text(encoding="utf-8"))
        if obj["schema"] != "sens.git-branch-heads-part/v1":
            raise ValueError("Unexpected census part schema: " + part)
        if obj["count"] != len(obj["branches"]):
            raise ValueError("Census count mismatch: " + part)
        branches.extend(obj["branches"])
    index = json.loads((PART_ROOT / "index.json").read_text(encoding="utf-8"))
    if len(branches) != 4133 or index["total_live_branch_refs"] != len(branches):
        raise ValueError("Incomplete 4133-name snapshot")
    if len({b["name"] for b in branches}) != len(branches):
        raise ValueError("Duplicate branch names in census")
    if len({b["sha"] for b in branches}) != index["distinct_head_commits"]:
        raise ValueError("Distinct-head count mismatch")
    if any(not SHA.fullmatch(b["sha"]) for b in branches):
        raise ValueError("Invalid immutable source SHA")
    return branches


def tree() -> tuple[dict[str, str], set[str]]:
    same_path: dict[str, str] = {}
    blobs: set[str] = set()
    for part in git("ls-tree", "-r", "-z", "HEAD").split(b"\0"):
        if not part:
            continue
        metadata, pathname = part.split(b"\t", 1)
        mode, kind, sha = metadata.split(b" ", 2)
        if kind != b"blob":
            continue
        key = text(pathname)
        val = sha.decode("ascii")
        same_path[key] = val
        blobs.add(val)
    return same_path, blobs


def file_changes(base: str, head: str) -> list[tuple[str, str, str]]:
    chunks = git("diff", "--raw", "--no-renames", "-z", "--abbrev=40",
                 base, head, "--").split(b"\0")
    changes: list[tuple[str, str, str]] = []
    # With -z/--no-renames: raw header NUL path NUL for each entry.
    if chunks and chunks[-1] == b"":
        chunks.pop()
    if len(chunks) % 2:
        raise ValueError("Unexpected binary git --raw change framing")
    for i in range(0, len(chunks), 2):
        metadata, pathname = chunks[i], chunks[i + 1]
        cells = metadata.decode("ascii").split()
        if len(cells) != 5 or not cells[0].startswith(":"):
            raise ValueError("Unexpected Git raw diff metadata")
        source_blob = cells[3]
        status = cells[4]
        if not (source_blob == ZERO_SHA or SHA.fullmatch(source_blob)):
            raise ValueError("Invalid source blob SHA in raw diff")
        changes.append((text(pathname), status, source_blob))
    return changes


def categorize(path: str, status: str, blob: str,
               same_path: dict[str, str], blobs: set[str]) -> str:
    if status.startswith("D") or blob == ZERO_SHA:
        return "HISTORICAL_DELETION_REVIEW"
    if same_path.get(path) == blob:
        return "EXACT_BLOB_ALREADY_AT_SAME_PATH"
    if blob in blobs:
        return "EXACT_BLOB_PRESERVED_ELSEWHERE_IN_MAIN_TREE"
    return "ORIGINAL_BLOB_ABSENT_FROM_CURRENT_MAIN_TREE"


def produce(start: int, limit: int) -> dict:
    branches = snapshot()
    main_sha = text(git("rev-parse", "HEAD")).strip()
    if not SHA.fullmatch(main_sha):
        raise ValueError("Unexpected main SHA")
    branch_refs_by_sha: dict[str, list[str]] = collections.defaultdict(list)
    for branch in branches:
        branch_refs_by_sha[branch["sha"]].append(branch["name"])
    heads = list(branch_refs_by_sha.items())
    selected = heads[start:(start + limit if limit else None)]
    same_path, blobs = tree()
    report: list[dict] = []
    totals = collections.Counter()
    source_blobs = set()
    missing_blobs = set()
    for head_sha, names in selected:
        obj = git("cat-file", "-e", head_sha + "^{commit}", allow_failure=True)
        # git cat-file -e returns no stdout on BOTH success/failure, so check
        # with rev-parse -q --verify instead.
        obj = git("rev-parse", "-q", "--verify", head_sha + "^{commit}",
                  allow_failure=True).strip()
        if not obj:
            totals["MISSING_HEAD_OBJECT"] += len(names)
            report.append({"head": head_sha, "names": names,
                           "status": "MISSING_HEAD_OBJECT"})
            continue
        ancestry = subprocess.run(("git", "merge-base", "--is-ancestor",
                                  head_sha, main_sha), cwd=ROOT,
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
        if ancestry.returncode == 0:
            totals["HEAD_IS_MAIN_ANCESTOR"] += len(names)
            report.append({"head": head_sha, "names": names,
                           "status": "HEAD_IS_MAIN_ANCESTOR"})
            continue
        if ancestry.returncode != 1:
            raise RuntimeError("Cannot determine source ancestry " + head_sha)
        bases = text(git("merge-base", main_sha, head_sha,
                         allow_failure=True)).strip().splitlines()
        if not bases:
            totals["NO_COMMON_ANCESTOR"] += len(names)
            report.append({"head": head_sha, "names": names,
                           "status": "NO_COMMON_ANCESTOR"})
            continue
        merge_base = bases[0]
        changes = file_changes(merge_base, head_sha)
        changed: list[dict] = []
        for path, status, blob in changes:
            category = categorize(path, status, blob, same_path, blobs)
            totals[category] += 1
            if blob != ZERO_SHA:
                source_blobs.add(blob)
                if category == "ORIGINAL_BLOB_ABSENT_FROM_CURRENT_MAIN_TREE":
                    missing_blobs.add(blob)
            changed.append({"path": path, "kind": status,
                            "source_git_blob": blob, "verdict": category})
        totals["HEADS_NEED_SEMANTIC_REVIEW"] += len(names)
        report.append({"head": head_sha, "names": names,
                       "status": "HEADS_NEED_SEMANTIC_REVIEW",
                       "merge_base": merge_base,
                       "changed_files_against_merge_base": changed})
    return {
        "schema": "sens.branch-immutable-source-intake/v1",
        "basis": "2026-10-11 4133 current Git refs; deleted refs require PR history",
        "current_main_sha": main_sha,
        "total_source_heads": len(heads),
        "selected_source_heads": len(selected),
        "source_head_offset": start,
        "status": "CANDIDATE_SOURCE_RECONCILIATION_ONLY_NOT_MERGED",
        "branch_creation_count": 0,
        "per_file_counts": dict(totals),
        "distinct_changed_source_blobs": len(source_blobs),
        "distinct_blobs_absent_from_current_main_tree": len(missing_blobs),
        "warning": ("A source blob absent in current main is a candidate, NOT a "
                    "unique law or safe runtime patch. Exact existing blobs "
                    "may require preservation of source-era context. "
                    "Do not create branches or ratify D10 from this report."),
        "heads": report
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--limit", type=int, default=0,
                   help="0 = entire immutable 4034-head census")
    p.add_argument("--output", required=True)
    a = p.parse_args()
    if a.start < 0 or a.limit < 0:
        p.error("start and limit must be nonnegative")
    report = produce(a.start, a.limit)
    dest = Path(a.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=True,
                               separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "heads"},
                     ensure_ascii=True))
    if any(k in report["per_file_counts"]
           for k in ("MISSING_HEAD_OBJECT", "NO_COMMON_ANCESTOR")):
        print("BLOCKED: some immutable historical sources unavailable",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
