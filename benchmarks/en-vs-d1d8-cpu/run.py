#!/usr/bin/env python3
"""#3113 — orchestrate paired English/canonical-D1-D8 preflight.

No performance ratio is produced here. Timing stays blocked until every case
proves that both source projections lower to the same exact-domain trace.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path


FIELDS = [
    "case",
    "candidate",
    "mode",
    "status",
    "git_sha",
    "binary_sha",
    "corpus_sha",
    "english_sha",
    "canonical_sha",
    "oracle",
    "rep",
    "i_refs",
    "wall_s",
    "user_s",
    "sys_s",
    "maxrss_kb",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_sha(repo: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def read_manifest(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"case", "english_path", "canonical_path", "oracle"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise SystemExit(
                "manifest must contain: case, english_path, canonical_path, oracle"
            )
        rows = list(reader)
    if not rows:
        raise SystemExit("manifest is empty")
    return rows


def corpus_sha(rows, repo: Path) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(row["case"].encode())
        digest.update(b"\0")
        digest.update(row["oracle"].encode())
        digest.update(b"\0")
        for key in ("english_path", "canonical_path"):
            path = (repo / row[key]).resolve()
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def preflight_status(stdout: str, returncode: int) -> str:
    for line in stdout.splitlines():
        if line.startswith("status\t"):
            return line.split("\t", 1)[1].strip()
    return "PREFLIGHT_OK" if returncode == 0 else "BLOCKED_PARSE"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--preflight-bin", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument(
        "--require-ready",
        action="store_true",
        help="return nonzero when any case is blocked",
    )
    args = ap.parse_args()

    repo = args.repo.resolve()
    rows = read_manifest(args.manifest)
    corpus = corpus_sha(rows, repo)
    binary_hash = sha256_file(args.preflight_bin)
    commit = git_sha(repo)

    output = []
    blocked = 0
    for item in rows:
        english = repo / item["english_path"]
        canonical = repo / item["canonical_path"]
        proc = subprocess.run(
            [str(args.preflight_bin), str(english), str(canonical)],
            capture_output=True,
            text=True,
        )
        status = preflight_status(proc.stdout, proc.returncode)
        if status != "PREFLIGHT_OK":
            blocked += 1
        row = {
            "case": item["case"],
            "candidate": "paired",
            "mode": "preflight",
            "status": status,
            "git_sha": commit,
            "binary_sha": binary_hash,
            "corpus_sha": corpus,
            "english_sha": sha256_file(english),
            "canonical_sha": sha256_file(canonical),
            "oracle": item["oracle"],
            "rep": None,
            "i_refs": None,
            "wall_s": None,
            "user_s": None,
            "sys_s": None,
            "maxrss_kb": None,
        }
        output.append(row)
        print(f"[preflight] {item['case']}: {status}")
        if proc.stderr.strip():
            print(proc.stderr.rstrip())

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "preflight.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(output)

    with (args.out / "preflight.jsonl").open("w", encoding="utf-8") as handle:
        for row in output:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    environment = {
        "git_sha": commit,
        "binary_sha": binary_hash,
        "corpus_sha": corpus,
        "python": platform.python_version(),
        "kernel": platform.release(),
        "cpu_count": os.cpu_count(),
        "preflight_cases": len(output),
        "blocked_cases": blocked,
        "timing_enabled": False,
        "timing_blocker": "#3088 readiness spine",
    }
    (args.out / "environment.json").write_text(
        json.dumps(environment, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        f"[summary] cases={len(output)} blocked={blocked} "
        "timing=BLOCKED_RUNTIME_READINESS"
    )
    if args.require_ready and blocked:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
