#!/usr/bin/env python3
"""Read-only audit of SHA-pinned nonprogram Lisp manifests.

A changed blob is TRANSITIONAL(#4460), NEVER silently repinned, skipped, or
credited as a migrated executable. This diagnostic is not a release gate.
Use --strict for the existing independent nonprogram review lane.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
from report_original_migration_candidates import NONPROGRAM_MANIFESTS, git_blob_sha
from report_ukr_projection_progress import tokenize_lisp

SCHEMA = "sens-nonprogram-source-pin-drift/v1"


def scan(root: Path, manifests=NONPROGRAM_MANIFESTS, *, limit: int = 10) -> dict:
    if limit < 0:
        raise ValueError("limit must be nonnegative")
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root is not a directory")
    discrepancies = []
    seen = set()
    checked = 0
    for cohort, manifest_name, expected_count in manifests:
        rel_manifest = Path(manifest_name)
        if rel_manifest.is_absolute() or ".." in rel_manifest.parts:
            raise ValueError("unsafe manifest path")
        manifest = root / rel_manifest
        if not manifest.is_file() or manifest.is_symlink():
            raise ValueError("missing/unsafe manifest: " + manifest_name)
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if (payload.get("schema") != "sens-migration-nonprogram-manifest/1"
                or payload.get("automatic_sens_companion") is not False
                or payload.get("issue") != 4460):
            raise ValueError("invalid reviewed manifest authority: " + manifest_name)
        entries = payload.get("entries")
        if not isinstance(entries, list) or len(entries) != expected_count:
            raise ValueError("reviewed manifest cardinality changed: " + manifest_name)
        for item in entries:
            if not isinstance(item, dict):
                raise ValueError("malformed reviewed entry")
            path, expected = item.get("path"), item.get("git_blob_sha1")
            if (not isinstance(path, str) or not path.endswith(".lisp")
                    or path.startswith("/") or "\\" in path
                    or any(p in ("", ".", "..") for p in path.split("/"))
                    or path in seen):
                raise ValueError("unsafe or duplicated source path in manifest")
            if (not isinstance(expected, str) or len(expected) != 40
                    or any(c not in "0123456789abcdef" for c in expected)):
                raise ValueError("invalid pinned SHA: " + path)
            seen.add(path)
            source = root / path
            checked += 1
            reason = None
            actual = None
            if source.is_symlink() or not source.is_file():
                reason = "MISSING_OR_SYMLINK_SOURCE"
            elif any((root / Path(*Path(path).parts[:i])).is_symlink()
                     for i in range(1, len(Path(path).parts))):
                reason = "SYMLINK_ANCESTOR"
            else:
                actual = git_blob_sha(source)
                if actual != expected:
                    reason = "SOURCE_BLOB_DRIFT"
                if source.with_suffix(".sens").exists() or source.with_suffix(".sens").is_symlink():
                    reason = "UNAPPROVED_PHYSICAL_PAIR"
                if cohort == "comment-only-loader":
                    # Чинний Lisp допускає ; та вкладені #| ... |#
                    # як коментарі. Старий построковий евристичний
                    # розбір створює штучний NO_LONGER_COMMENT_ONLY.
                    try:
                        tokens = tokenize_lisp(source.read_text(encoding="utf-8"))
                    except UnicodeError:
                        reason = "INVALID_UTF8_COMMENT_ONLY_SOURCE"
                    except ValueError:
                        reason = "INVALID_LISP_COMMENT_SYNTAX"
                    else:
                        if tokens:
                            reason = "NO_LONGER_COMMENT_ONLY"
            if reason:
                discrepancies.append({
                    "path": path, "cohort": cohort, "reason": reason,
                    "pinned_blob_sha": expected, "current_blob_sha": actual,
                })
    return {
        "schema": SCHEMA,
        "status": "TRANSITIONAL(#4460)_NEEDS_SOURCE_REVIEW"
                  if discrepancies else "PINNED_SOURCE_BLOBS_MATCH",
        "sources_checked": checked,
        "discrepancies": len(discrepancies),
        "unreviewed_drift_cannot_authorize_release": True,
        "automatic_repin": False,
        "sample": discrepancies[:limit],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--strict", action="store_true",
                        help="fail closed on any SHA drift or changed source class")
    args = parser.parse_args(argv)
    try:
        report = scan(args.root, limit=args.limit)
    except (OSError, ValueError, KeyError) as exc:
        print("NONPROGRAM_PIN_AUDIT_BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["discrepancies"]:
        print("::warning::TRANSITIONAL(#4460): "
              + str(report["discrepancies"])
              + " nonprogram source pins require per-file review; "
              "no automatic repinning or SENS semantic credit")
    return 2 if args.strict and report["discrepancies"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
