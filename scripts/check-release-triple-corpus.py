#!/usr/bin/env python3
"""Fail-closed: full-corpus T5 triple admission for the release tag path.

Mechanical gate only. Does not invent oracle evidence or admission ledger entries.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print(
            "usage: check-release-triple-corpus.py LEDGER.json STATUS_INT",
            file=sys.stderr,
        )
        return 2
    path = Path(argv[0])
    try:
        status = int(argv[1])
    except ValueError:
        print("RELEASE_BLOCKED: inventory exit status must be an integer", file=sys.stderr)
        return 1
    if not path.is_file() or path.is_symlink():
        print("RELEASE_BLOCKED: triple evidence ledger missing", file=sys.stderr)
        return 1
    try:
        r = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"RELEASE_BLOCKED: unreadable or invalid triple ledger: {type(exc).__name__}", file=sys.stderr)
        return 1
    if not isinstance(r, dict) or r.get("schema") != "sens-t5-triplet-inventory/v1":
        print("RELEASE_BLOCKED: unknown triple proof schema", file=sys.stderr)
        return 1
    s = r.get("summary")
    rows = r.get("files")
    failed = r.get("failed_required")
    keys = (
        "physical_pairs_seen", "physical_blocked", "view_missing",
        "view_invalid_or_unsafe", "view_present_valid",
        "uk_oracle_verified", "release_admitted",
    )
    if (
        not isinstance(s, dict)
        or not all(type(s.get(key)) is int and s[key] >= 0 for key in keys)
        or not isinstance(rows, list)
        or not isinstance(failed, list)
        or not all(isinstance(item, str) for item in failed)
        or len(rows) != s["physical_pairs_seen"]
        or not all(isinstance(row, dict) for row in rows)
    ):
        print("RELEASE_BLOCKED: malformed or inconsistent triple ledger", file=sys.stderr)
        return 1
    physical = s["physical_pairs_seen"]
    if (
        s["view_present_valid"] + s["view_missing"] + s["view_invalid_or_unsafe"] != physical
        or s["physical_blocked"] > s["view_invalid_or_unsafe"]
        or s["uk_oracle_verified"] > physical
        or s["release_admitted"] > physical
        or s["view_present_valid"] != sum(row.get("view_status") == "PHYSICAL_VIEW_PASS" for row in rows)
        or s["uk_oracle_verified"] != sum(row.get("uk_oracle") == "VERIFIED" for row in rows)
        or s["release_admitted"] != sum(row.get("release_admitted") is True for row in rows)
    ):
        print("RELEASE_BLOCKED: triple totals contradict per-file evidence", file=sys.stderr)
        return 1
    print("RELEASE_TRIPLE_DEBT", json.dumps(s, sort_keys=True))
    # Inventory cannot claim independent Ukrainian oracle for all canaries.
    # A ratified proof ledger must be consumed; never promote one D1 witness.
    blocked = (
        status != 0
        or bool(failed)
        or physical == 0
        or s["physical_blocked"] != 0
        or s["view_missing"] != 0
        or s["view_invalid_or_unsafe"] != 0
        or s["view_present_valid"] != physical
        or s["uk_oracle_verified"] != physical
        or s["release_admitted"] != physical
    )
    if blocked:
        print(
            "RELEASE_BLOCKED: some packed T5 views are absent/invalid, "
            "or canonical Ukrainian <-> current semantics and independent "
            "oracle admission for all release-scoped executables remain unproved",
            file=sys.stderr,
        )
        return 1
    print("RELEASE_TRIPLE_FULL_CORPUS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
