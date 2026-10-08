#!/usr/bin/env python3
"""Read-only inventory of same-stem SENS triples: Ukrainian source, T5 and view.

This does not translate Ukrainian, admit semantic parity, or publish programs.
It never creates or modifies source, packed T5 or extensionless view files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from audit_t5_file_pairs import inspect as inspect_pairs
from sens_t5_codec import decode_bytes, encode_words, typed_sha256

SCHEMA = "sens-t5-triplet-inventory/v1"
GOLDEN = "tests/fixtures/migration-d1-cond-cohort/branch.sens"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_view(words: list[str]) -> bytes:
    """Exactly ONE ASCII space between exact-width bit words and ONE last LF."""
    return (" ".join(words) + "\n").encode("ascii")


def tracked_paths(root: Path) -> set[str]:
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True, check=False,
    )
    if proc.returncode:
        raise ValueError("tracked Git inventory unavailable; use --include-untracked for temporary fixtures")
    return {os.fsdecode(x) for x in proc.stdout.split(b"\0") if x}


def safe_relative(name: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("invalid relative .sens path")
    path = Path(name)
    if (path.is_absolute() or path.suffix != ".sens" or
            path.as_posix() != name or
            any(x in ("", ".", "..") for x in name.split("/"))):
        raise ValueError("require a safe repo-relative .sens path")
    return path


def no_link_ancestors(root: Path, relative: Path) -> bool:
    """Avoid symlink escapes even where the final view is a regular file."""
    cur = root
    for part in relative.parts:
        cur = cur / part
        if cur.is_symlink():
            return False
    return True


def inspect(root: Path, *, include_untracked: bool = False,
            required: tuple[str, ...] = (), strict: bool = False) -> dict:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("not a directory")
    required_names = {safe_relative(p).as_posix() for p in required}
    # Existing canonical pair auditor supplies the complete physical inventory
    # and source provenance; this report adds VIEW only, not new semantics.
    pairs = inspect_pairs(root, include_untracked=include_untracked)
    tracked = None if include_untracked else tracked_paths(root)
    records: list[dict] = []
    statuses = {}
    for pair in pairs["files"]:
        name = pair["sens"]
        path = safe_relative(name)
        source_rel = path.with_suffix(".lisp")
        view_rel = path.with_suffix("")
        view_name = view_rel.as_posix()
        row = {
            "sens": name,
            "source": source_rel.as_posix(),
            "view": view_name,
            "physical_status": pair["physical_status"],
            "source_status": pair["source_status"],
            "view_status": "BLOCKED",
            "uk_oracle": "NOT_VERIFIED",
            "release_admitted": False,
            "original_executable_migration_credit": 0,
        }
        records.append(row)
        statuses[name] = row
        if (not no_link_ancestors(root, path) or
                not no_link_ancestors(root, source_rel) or
                not no_link_ancestors(root, view_rel)):
            row["view_status"] = "UNSAFE_LINK"
            row["reason"] = "source, physical binary or extensionless view has a symlink ancestor"
            continue
        if pair["physical_status"] != "PASS":
            row["view_status"] = "PHYSICAL_BLOCKED"
            row["reason"] = pair.get("error", "T5/source pair not validated")
            continue
        row["physical_sha256"] = pair["physical_sha256"]
        row["source_sha256"] = pair["source_sha256"]
        row["typed_word_sha256"] = pair["typed_word_sha256"]
        row["typed_word_count"] = pair["semantic_word_count"]
        try:
            payload = (root / path).read_bytes()
            words = decode_bytes(payload)
            # The base pair auditor has already checked this, but fail-closed
            # on changes to the physical file between its scan and our scan.
            if encode_words(words) != payload or sha(payload) != pair["physical_sha256"]:
                raise ValueError("T5 bytes drifted during inventory")
            expected = canonical_view(words)
            row["expected_view_sha256"] = sha(expected)
            file = root / view_rel
            if not file.is_file():
                row["view_status"] = "MISSING_VIEW"
                row["reason"] = "no extensionless text view beside verified .sens"
                continue
            if tracked is not None and view_name not in tracked:
                row["view_status"] = "UNTRACKED_VIEW"
                row["reason"] = "untracked extensionless view cannot prove a Git release candidate"
                continue
            actual = file.read_bytes()
            row["view_sha256"] = sha(actual)
            if actual != expected:
                row["view_status"] = "VIEW_MISMATCH"
                row["reason"] = (
                    "view must be canonical ASCII exact bits, one ordinary space "
                    "between words and one final LF; bytes differ from decoded T5"
                )
                continue
            if encode_words(actual[:-1].decode("ascii").split(" ")) != payload:
                raise ValueError("view to physical T5 byte-roundtrip failed")
            if typed_sha256(actual[:-1].decode("ascii").split(" ")) != pair["typed_word_sha256"]:
                raise ValueError("exact domain word widths drifted")
            row["view_status"] = "PHYSICAL_VIEW_PASS"
        except (OSError, UnicodeError, ValueError) as exc:
            row["view_status"] = "BLOCKED"
            row["reason"] = str(exc)[:320]

    failed_required = sorted(
        name for name in required_names
        if name not in statuses or statuses[name]["view_status"] != "PHYSICAL_VIEW_PASS"
    )
    blocked_physical = sum(r["physical_status"] != "PASS" for r in records)
    ready = sum(r["view_status"] == "PHYSICAL_VIEW_PASS" for r in records)
    missing = sum(r["view_status"] == "MISSING_VIEW" for r in records)
    invalid = sum(r["view_status"] not in ("PHYSICAL_VIEW_PASS", "MISSING_VIEW")
                  for r in records)
    # INCOMPLETE_VIEWS is a debt-bearing informational result, not release GREEN.
    status = ("NO_FILES" if not records else
              "BLOCKED" if blocked_physical or invalid or failed_required or
                          (strict and ready != len(records)) else
              "INCOMPLETE_VIEWS" if ready != len(records) else
              "PHYSICAL_VIEW_ONLY_UK_PENDING")
    return {
        "schema": SCHEMA,
        "status": status,
        "mode": pairs["mode"],
        "strict": strict,
        "required": sorted(required_names),
        "failed_required": failed_required,
        "summary": {
            "physical_pairs_seen": len(records),
            "physical_blocked": blocked_physical,
            "view_present_valid": ready,
            "view_missing": missing,
            "view_invalid_or_unsafe": invalid,
            "uk_oracle_verified": 0,
            "original_executable_migrations_certified": 0,
            "release_admitted": 0,
        },
        "files": records,
        "warning": (
            "T5↔ASCII view identity is mechanical ONLY. Ukrainian uk source "
            "roundtrip, independent runtime semantics and release are NOT_VERIFIED."
        ),
    }



def write_receipt_once(root: Path, destination: Path, report: dict) -> None:
    """Create an immutable JSON evidence file outside the source corpus.

    Hard-linking a flushed temporary file is exclusive; a concurrent write
    cannot replace a source .lisp, physical .sens, human view or earlier report.
    """
    source_root = root.resolve(strict=True)
    if not source_root.is_dir():
        raise ValueError("corpus root must be a directory")
    target = destination.absolute()
    if target.exists() or target.is_symlink():
        raise ValueError("report already exists; no overwrite")
    if target.resolve(strict=False).is_relative_to(source_root):
        raise ValueError("report must be outside original source repository")
    ancestor = target.parent
    while True:
        if ancestor.is_symlink():
            raise ValueError("report path has symlink ancestor")
        if ancestor == ancestor.parent:
            break
        ancestor = ancestor.parent
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.parent.is_symlink() or target.parent.resolve() != target.parent:
        raise ValueError("report parent changed to a symlink during staging")
    staged = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=target.parent,
            prefix=".sens-triplet-receipt-", suffix=".tmp", delete=False,
        ) as stream:
            staged = Path(stream.name)
            json.dump(report, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(staged, target)  # atomic create-if-absent
    except FileExistsError as error:
        raise ValueError("report already exists; no overwrite") from error
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--include-untracked", action="store_true",
                        help="test-only: scan an isolated temporary fixture directory")
    parser.add_argument("--require-view", action="append", default=[],
                        help="require exact physical/view parity for named .sens path")
    parser.add_argument("--strict", action="store_true",
                        help="BLOCK if ANY tracked physical pair lacks a canonical view")
    parser.add_argument("--report", type=Path,
                        help="write JSON audit receipt, never a program or view")
    args = parser.parse_args(argv)
    try:
        report = inspect(
            args.root, include_untracked=args.include_untracked,
            required=tuple(args.require_view), strict=args.strict,
        )
        if args.report:
            write_receipt_once(args.root, args.report, report)
        print(json.dumps({"status": report["status"], **report["summary"],
                          "failed_required": report["failed_required"]},
                         ensure_ascii=False, sort_keys=True))
        return 2 if report["status"] in ("BLOCKED", "NO_FILES") else 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("TRIPLE INVENTORY BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
