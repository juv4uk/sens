#!/usr/bin/env python3
"""Read-only inventory: SAME-STEM .lisp + physical T5 .sens + ASCII bit-view.

This extends the canonical physical pair audit; it neither generates missing
extensionless files nor asserts Ukrainian Lisp ↔ SENS semantic equivalence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from audit_t5_file_pairs import inspect as inspect_pairs
from sens_t5_codec import SensT5Error, decode_bytes, encode_words, typed_sha256

SCHEMA = "sens-t5-same-stem-triplet-inventory/v1"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_ascii_view(words: list[str]) -> bytes:
    """Exactly one ASCII space between words and exactly one terminal LF."""
    if not words:
        raise SensT5Error("an empty program has no canonical view")
    return (" ".join(words) + "\n").encode("ascii")


def inspect(root: Path, *, include_untracked: bool = False) -> dict:
    root = root.resolve(strict=True)
    base = inspect_pairs(root, include_untracked=include_untracked)
    rows = []
    for pair in base["files"]:
        sens_rel = Path(pair["sens"])
        if sens_rel.suffix != ".sens":
            raise ValueError("non-.sens candidate in physical pair audit")
        view_rel = sens_rel.with_suffix("")
        src_rel = sens_rel.with_suffix(".lisp")
        row = {
            "stem": view_rel.as_posix(),
            "source": src_rel.as_posix(),
            "sens": sens_rel.as_posix(),
            "view": view_rel.as_posix(),
            "physical_status": pair["physical_status"],
            "source_status": pair["source_status"],
            "view_status": "NOT_CHECKED",
            "uk_projection_status": "ORACLE_NOT_VERIFIED",
            "executable_semantics_admitted": False,
        }
        if pair["physical_status"] != "PASS":
            row["view_status"] = "BLOCKED_PHYSICAL"
            row["reason"] = pair.get("error", "not a verified physical T5 pair")
            rows.append(row)
            continue
        row.update({
            "physical_sha256": pair["physical_sha256"],
            "source_sha256": pair["source_sha256"],
            "typed_word_sha256": pair["typed_word_sha256"],
            "physical_bytes": pair["physical_bytes"],
            "semantic_word_count": pair["semantic_word_count"],
        })
        path = root / sens_rel
        view = root / view_rel
        try:
            if view.is_symlink():
                raise ValueError("extensionless view is a symlink")
            physical = path.read_bytes()
            words = decode_bytes(physical)
            if encode_words(words) != physical or typed_sha256(words) != row["typed_word_sha256"]:
                raise ValueError("pair audit versus re-encoded typed T5 disagree")
            canonical_view = expected_ascii_view(words)
            row["expected_view_sha256"] = sha256(canonical_view)
            if not view.exists():
                row["view_status"] = "MISSING_VIEW"
                row["reason"] = "same-stem extensionless human bit-view is absent"
            elif not view.is_file():
                raise ValueError("extensionless view is not a regular file")
            else:
                actual = view.read_bytes()
                row["view_sha256"] = sha256(actual)
                if actual != canonical_view:
                    raise ValueError(
                        "view bytes are not the exact canonical ASCII bit words with one final LF"
                    )
                if encode_words(actual.decode("ascii")[:-1].split(" ")) != physical:
                    raise ValueError("view -> canonical physical T5 byte roundtrip failed")
                row["view_status"] = "VIEW_PASS"
        except (OSError, ValueError, UnicodeError, SensT5Error) as exc:
            row["view_status"] = "INVALID_VIEW"
            row["reason"] = str(exc)
        rows.append(row)
    counts = {status: sum(x["view_status"] == status for x in rows)
              for status in ("VIEW_PASS", "MISSING_VIEW", "INVALID_VIEW", "BLOCKED_PHYSICAL")}
    has_invalid = counts["INVALID_VIEW"] or counts["BLOCKED_PHYSICAL"]
    status = (
        "BLOCKED" if has_invalid else
        "NO_PAIRS" if not rows else
        "PARTIAL_TRIPLES" if counts["MISSING_VIEW"] else
        "ALL_PHYSICAL_VIEWS_MATCH_PENDING_UK_ORACLE"
    )
    return {
        "schema": SCHEMA,
        "mode": base["mode"],
        "status": status,
        "release_semantic_status": "NOT_CERTIFIED",
        "summary": {
            "tracked_physical_pairs": len(rows),
            "views_verified": counts["VIEW_PASS"],
            "views_missing": counts["MISSING_VIEW"],
            "views_invalid": counts["INVALID_VIEW"],
            "physical_pairs_blocked": counts["BLOCKED_PHYSICAL"],
            "uk_semantic_oracles_certified_by_this_audit": 0,
            "original_executables_migrated_by_this_audit": 0,
        },
        "files": rows,
        "warning": (
            "One byte-identical T5/view pair is not Ukrainian .lisp semantics "
            "or an independent historical/current executable oracle. "
            "Missing view never authorizes replacing source or .sens."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--output", type=Path, help="JSON evidence; never modifies corpus")
    parser.add_argument("--include-untracked", action="store_true",
                        help="for external preview fixture directories only")
    parser.add_argument("--require-all-views", action="store_true",
                        help="opt-in physical/view completeness gate; not a UK/oracle gate")
    args = parser.parse_args(argv)
    try:
        report = inspect(args.root, include_untracked=args.include_untracked)
        if args.output:
            destination = args.output.resolve(strict=False)
            base = args.root.resolve(strict=True)
            if destination.is_relative_to(base) or args.output.is_symlink():
                raise ValueError("inventory report output must stay outside source repository")
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                raise ValueError("inventory report output exists; never overwrite")
            destination.write_text(json.dumps(report, ensure_ascii=False, indent=2,
                                              sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], **report["summary"]},
                         ensure_ascii=False, sort_keys=True))
        if report["status"] in ("BLOCKED", "NO_PAIRS"):
            return 2
        if args.require_all_views and report["summary"]["views_missing"]:
            return 2
        return 0
    except (OSError, ValueError) as exc:
        print("TRIPLET INVENTORY BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
