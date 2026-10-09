#!/usr/bin/env python3
"""Read-only incremental Git-diff gate for physical SENS and its exact bit view.

Old unchanged physical files without views remain visible debt, but every
modified/new physical program or view must already roundtrip byte-for-byte.
Neither Ukrainian semantic parity nor release readiness is certified.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from report_t5_triplet_inventory import inspect as inspect_triplets
from verify_uk_t5_triplet import ProjectionBlocked, verify as verify_bounded_uk

SCHEMA = "sens-t5-triplet-delta-ratchet/v1"
COMMIT = re.compile(r"[0-9a-f]{40}\Z")


def git(root: Path, *args: str) -> bytes:
    proc = subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, check=False)
    if proc.returncode:
        raise ValueError("GIT: " + proc.stderr.decode("utf-8", "replace")[-450:])
    return proc.stdout


def safe_path(name: str) -> Path:
    path = Path(name)
    if (not name or "\\" in name or path.is_absolute()
            or path.as_posix() != name
            or any(piece in ("", ".", "..") for piece in name.split("/"))):
        raise ValueError("unsafe Git delta path")
    return path


def changed_paths(root: Path, base: str) -> list[tuple[str, str]]:
    if not COMMIT.fullmatch(base):
        raise ValueError("BASE: immutable 40-digit Git commit SHA required")
    git(root, "rev-parse", "--verify", base + "^{commit}")
    raw = git(root, "diff", "--name-status", "-z", "--no-renames",
              "--diff-filter=AMDRT", base, "HEAD")
    fields = raw.split(b"\0")
    if fields[-1] != b"":
        raise ValueError("GIT: malformed NUL-delimited status")
    fields.pop()
    if len(fields) % 2:
        raise ValueError("GIT: incomplete name-status pair")
    changed = []
    for i in range(0, len(fields), 2):
        status = fields[i].decode("ascii", "strict")
        name = os.fsdecode(fields[i + 1])
        safe_path(name)
        if status not in ("A", "M", "D", "T"):
            raise ValueError("GIT: unknown change " + status)
        changed.append((status, name))
    return changed


def inspect(root: Path, *, base: str) -> dict:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("not a repository directory")
    changes = changed_paths(root, base)
    tracked = {
        os.fsdecode(item) for item in git(root, "ls-files", "-z").split(b"\0") if item
    }
    census = inspect_triplets(root)
    by_sens = {row["sens"]: row for row in census["files"]}
    targets: set[str] = set()
    source_changed: set[str] = set()
    delta = []
    for status, name in changes:
        path = safe_path(name)
        if path.suffix == ".sens":
            targets.add(name)
            delta.append({"change": status, "path": name, "kind": "physical"})
        elif path.suffix == ".lisp" and name[:-5] + ".sens" in tracked:
            # A canonical Ukrainian source edit is a semantic delta even if
            # committed packed T5 and human bit-view are byte-for-byte stable.
            target = name[:-5] + ".sens"
            targets.add(target)
            source_changed.add(target)
            delta.append({"change": status, "path": name, "kind": "uk_source"})
        elif path.suffix == "" and name + ".sens" in tracked:
            # Deleting an existing extensionless view must be noticed too.
            targets.add(name + ".sens")
            delta.append({"change": status, "path": name, "kind": "view"})
    rows = []
    for name in sorted(targets):
        entry = by_sens.get(name)
        if name not in tracked:
            rows.append({"sens": name, "status": "BLOCKED",
                         "reason": "physical program deleted/not Git-tracked"})
        elif entry is None:
            rows.append({"sens": name, "status": "BLOCKED",
                         "reason": "no canonical physical/source pair"})
        elif entry["view_status"] != "PHYSICAL_VIEW_PASS":
            rows.append({"sens": name, "status": "BLOCKED",
                         "view_status": entry["view_status"],
                         "reason": entry.get("reason", "T5↔view check failed")})
        else:
            # Physical T5↔view is necessary but NOT sufficient when somebody
            # changes the actual human Ukrainian source of a paired program.
            # Reuse the EXISTING ratified bounded uk adapter. Unsupported
            # D4/Text7/binders/aliases or source drift must fail closed.
            if name in source_changed:
                stem = (root / name).with_suffix("")
                try:
                    proof = verify_bounded_uk(
                        stem.with_suffix(".lisp"),
                        stem.with_suffix(".sens"),
                        stem,
                    )
                except (ProjectionBlocked, OSError, ValueError) as exc:
                    rows.append({
                        "sens": name,
                        "status": "BLOCKED",
                        "reason": "UK_SOURCE_DELTA: " + str(exc)[:320],
                        "view_status": "PHYSICAL_VIEW_PASS",
                        "uk_oracle": "NOT_VERIFIED",
                    })
                    continue
                if not proof.get("canonical_uk_roundtrip"):
                    rows.append({
                        "sens": name, "status": "BLOCKED",
                        "reason": "UK_SOURCE_DELTA: bounded canonical witness missing",
                    })
                    continue
            rows.append({
                "sens": name, "status": "PHYSICAL_VIEW_PASS_UK_ORACLE_PENDING",
                "source_sha256": entry["source_sha256"],
                "physical_sha256": entry["physical_sha256"],
                "typed_word_sha256": entry["typed_word_sha256"],
                "view_sha256": entry["view_sha256"],
                "bounded_uk_source_roundtrip": (
                    "PASS_NOT_RUNTIME_ORACLE" if name in source_changed
                    else "NOT_CHECKED_SOURCE_UNCHANGED"
                ),
                "uk_oracle": "NOT_VERIFIED", "release_admitted": False,
            })
    blocked = sum(row["status"] == "BLOCKED" for row in rows)
    return {
        "schema": SCHEMA,
        "base_commit": base,
        "head_commit": git(root, "rev-parse", "HEAD").decode("ascii").strip(),
        "status": "BLOCKED" if blocked else "DELTA_PHYSICAL_VIEW_ONLY_UK_PENDING",
        "summary": {
            "changed_pairs": len(rows),
            "changed_verified_transport": len(rows) - blocked,
            "changed_blocked": blocked,
            "historical_missing_views_remain_release_debt": census["summary"]["view_missing"],
            "uk_oracle_verified": 0,
            "original_executable_migrations_certified": 0,
            "release_admitted": 0,
        },
        "changed_paths": delta,
        "files": rows,
        "warning": (
            "Mechanical T5↔view parity ONLY; independent canonical Ukrainian "
            "source oracle and full release coverage are NOT_VERIFIED."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--base-sha", required=True)
    args = parser.parse_args(argv)
    try:
        report = inspect(args.root, base=args.base_sha)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 2 if report["status"] == "BLOCKED" else 0
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        print("TRIPLET DELTA BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
