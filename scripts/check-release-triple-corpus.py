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
    status = int(argv[1])
    if not path.is_file():
        print("RELEASE_BLOCKED: triple evidence ledger missing", file=sys.stderr)
        return 1
    r = json.loads(path.read_text(encoding="utf-8"))
    if r.get("schema") != "sens-t5-triplet-inventory/v1":
        print("RELEASE_BLOCKED: unknown triple proof schema", file=sys.stderr)
        return 1
    s = r["summary"]
    print("RELEASE_TRIPLE_DEBT", json.dumps(s, sort_keys=True))
    physical = s["physical_pairs_seen"]
    # Inventory cannot claim independent Ukrainian oracle for all canaries.
    # A ratified proof ledger must be consumed; never promote one D1 witness.
    blocked = (
        status != 0
        or bool(r["failed_required"])
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
