#!/usr/bin/env python3
"""Derive silicon witness coverage from one #4086 ledger artifact.

This script never owns ISA admission. It only summarizes the rows already
present in the supplied machine-readable ledger.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

CLASSES = (
    "execute-safe",
    "decode-only-safety",
    "platform-gated",
    "unsupported-current-grammar",
    "unknown",
)

ISSUE_RE = re.compile(r"(?:#\d+|https://github\.com/[^/]+/[^/]+/issues/\d+)$")


class CoverageError(RuntimeError):
    pass


def _classification(row: dict[str, Any], artifact: dict[str, Any]) -> str:
    value = row.get("classification", artifact.get("classification"))
    if not isinstance(value, str) or value not in CLASSES:
        raise CoverageError(f"row {row.get('id', '<missing-id>')} has invalid classification: {value!r}")
    return value


def _unknown_has_blocker(row: dict[str, Any]) -> bool:
    blocker = row.get("blocking_issue")
    return isinstance(blocker, str) and bool(ISSUE_RE.fullmatch(blocker.strip()))


def summarize(artifact: dict[str, Any]) -> dict[str, Any]:
    rows = artifact.get("rows")
    if not isinstance(rows, list):
        raise CoverageError("artifact.rows must be a list")

    counts: Counter[str] = Counter()
    for index, raw_row in enumerate(rows):
        if not isinstance(raw_row, dict):
            raise CoverageError(f"artifact.rows[{index}] must be an object")
        classification = _classification(raw_row, artifact)
        counts[classification] += 1
        if classification == "unknown" and not _unknown_has_blocker(raw_row):
            raise CoverageError(
                f"unknown row {raw_row.get('id', index)!r} must carry blocking_issue (#NNN or issue URL)"
            )

    total = len(rows)
    census_total = artifact.get("census_total")
    census_complete = artifact.get("census_complete") is True

    if census_total is not None:
        if not isinstance(census_total, int) or census_total < 0:
            raise CoverageError("census_total must be a non-negative integer when present")
        if census_complete and census_total != total:
            raise CoverageError(
                f"complete census mismatch: rows={total}, census_total={census_total}"
            )

    percentages = {
        name: (counts[name] * 100.0 / total if total else 0.0)
        for name in CLASSES
    }

    return {
        "schema": "sens-silicon-coverage-v1",
        "source_schema": artifact.get("schema", "unknown"),
        "sens_commit": artifact.get("sens_commit", "unknown"),
        "cpu_model": artifact.get("cpu_model", "unknown"),
        "target": artifact.get("target", "unknown"),
        "coverage_scope": "full-census" if census_complete else "artifact-rows-only",
        "census_complete": census_complete,
        "census_total": census_total,
        "classified_rows": total,
        "counts": {name: counts[name] for name in CLASSES},
        "percentages": {name: round(percentages[name], 6) for name in CLASSES},
        "health": {
            "unknown_zero": counts["unknown"] == 0,
            "full_census_accounted": bool(
                census_complete and census_total == total
            ),
        },
    }


def markdown(summary: dict[str, Any]) -> str:
    lines = [
        "### Silicon coverage",
        "",
        f"- commit: `{summary['sens_commit']}`",
        f"- CPU: `{summary['cpu_model']}`",
        f"- scope: **{summary['coverage_scope']}**",
        f"- classified rows: **{summary['classified_rows']}**",
        "",
        "| class | count | percent |",
        "|---|---:|---:|",
    ]
    for name in CLASSES:
        lines.append(
            f"| {name} | {summary['counts'][name]} | {summary['percentages'][name]:.2f}% |"
        )
    lines += [
        "",
        f"- unknown=0: **{'YES' if summary['health']['unknown_zero'] else 'NO'}**",
        f"- full census accounted: **{'YES' if summary['health']['full_census_accounted'] else 'NO / partial artifact'}**",
    ]
    return "\n".join(lines) + "\n"


def self_test() -> None:
    complete = {
        "schema": "test-ledger",
        "sens_commit": "deadbeef",
        "cpu_model": "test-cpu",
        "target": "test",
        "census_complete": True,
        "census_total": 5,
        "rows": [
            {"id": "a", "classification": "execute-safe"},
            {"id": "b", "classification": "decode-only-safety"},
            {"id": "c", "classification": "platform-gated"},
            {"id": "d", "classification": "unsupported-current-grammar"},
            {"id": "e", "classification": "unknown", "blocking_issue": "#999"},
        ],
    }
    result = summarize(complete)
    assert result["classified_rows"] == 5
    assert sum(result["counts"].values()) == 5
    assert result["coverage_scope"] == "full-census"
    assert result["health"]["full_census_accounted"] is True
    assert result["health"]["unknown_zero"] is False
    assert all(result["counts"][name] == 1 for name in CLASSES)

    top_level_v1 = {
        "schema": "sens-real-silicon-sweep-v1",
        "classification": "execute-safe",
        "rows": [{"id": "x"}, {"id": "y"}],
    }
    result = summarize(top_level_v1)
    assert result["counts"]["execute-safe"] == 2
    assert result["coverage_scope"] == "artifact-rows-only"

    bad_unknown = {
        "rows": [{"id": "u", "classification": "unknown"}],
    }
    try:
        summarize(bad_unknown)
    except CoverageError:
        pass
    else:
        raise AssertionError("unknown row without blocking_issue must fail")

    bad_total = {
        "census_complete": True,
        "census_total": 2,
        "rows": [{"id": "x", "classification": "execute-safe"}],
    }
    try:
        summarize(bad_total)
    except CoverageError:
        pass
    else:
        raise AssertionError("complete census mismatch must fail")

    print("silicon-coverage-self-test-ok")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", nargs="?", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    if args.artifact is None:
        parser.error("artifact is required unless --self-test is used")

    try:
        artifact = json.loads(args.artifact.read_text(encoding="utf-8"))
        if not isinstance(artifact, dict):
            raise CoverageError("artifact root must be an object")
        summary = summarize(artifact)
    except (OSError, json.JSONDecodeError, CoverageError) as exc:
        print(f"silicon-coverage-error: {exc}", file=sys.stderr)
        return 1

    payload = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)

    report = markdown(summary)
    github_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if github_summary:
        with open(github_summary, "a", encoding="utf-8") as handle:
            handle.write(report)

    # unknown=0 is a health target, not enough by itself to claim full coverage.
    if summary["census_complete"] and not summary["health"]["full_census_accounted"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
