#!/usr/bin/env python3
"""Structural ratchet for the seven-field binary-domain task record (#2531).

Consumes a pinned/local issue snapshot.  No network access.

For every OPEN issue with an explicit BINARY-DOMAIN RECORD/FORMAT marker:
- each of the seven fields must occur exactly once;
- UNKNOWN counts as a value;
- semantic field quality is delegated to sibling checks.

Historical debt is keyed by (issue, field, verdict); baseline may shrink but a
new tuple fails closed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from task_schema_record import FIELD_LABELS, structural_rows


def load_issues(path: str):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["issues"] if isinstance(data, dict) else data


def findings(issues):
    out = []
    judged = 0
    skipped = 0
    for issue in issues:
        if str(issue.get("state", "open")).lower() != "open":
            skipped += 1
            continue
        rows = structural_rows(issue.get("body") or "")
        if not rows:
            skipped += 1
            continue
        judged += 1
        for row in rows:
            if row["verdict"] == "OK":
                continue
            out.append(
                {
                    "issue": int(issue["number"]),
                    "field": row["field"],
                    "verdict": row["verdict"],
                    "count": int(row["count"]),
                }
            )
    return out, judged, skipped


def key(row):
    return (int(row["issue"]), str(row["field"]), str(row["verdict"]))


def baseline_payload(rows):
    return {
        "schema": "task-record-structure-baseline/v1",
        "violations": sorted(
            [
                {
                    "issue": int(row["issue"]),
                    "field": str(row["field"]),
                    "verdict": str(row["verdict"]),
                }
                for row in rows
            ],
            key=lambda x: (x["issue"], x["field"], x["verdict"]),
        ),
    }


def run(path, baseline=None, emit_baseline=False, report_only=False):
    rows, judged, skipped = findings(load_issues(path))

    if emit_baseline:
        print(json.dumps(baseline_payload(rows), indent=2, sort_keys=True))
        return 0

    known = set()
    if baseline:
        raw = json.loads(Path(baseline).read_text(encoding="utf-8"))
        known = {key(x) for x in raw.get("violations", [])}

    new = [row for row in rows if key(row) not in known]

    counts = {}
    for row in rows:
        counts[row["field"]] = counts.get(row["field"], 0) + 1

    print(
        f"(task-record-structure (judged {judged}) (skipped {skipped}) "
        f"(violations {len(rows)}) (new {len(new)}))"
    )
    for label in FIELD_LABELS:
        print(f"  (field {json.dumps(label)} (violations {counts.get(label, 0)}))")
    for row in rows:
        mark = "NEW " if key(row) not in known else "    "
        print(
            f"  {mark}#{row['issue']} {row['field']}: "
            f"{row['verdict']} count={row['count']}"
        )

    if new and not report_only:
        print("\ntask-record-structure-violation: new structural debt")
        return 1

    print("(task-record-structure-ok)")
    return 0


def self_test():
    good_body = """## BINARY-DOMAIN RECORD

DOMAIN: D5
BINARY OBJECT: 00101
LAW: x
WITNESS: PR #1
FALSIFIER: remove law
STATUS: hypothesis
RELATION: Core-only
"""
    issues = [
        {"number": 1, "state": "open", "body": good_body},
        {
            "number": 2,
            "state": "open",
            "body": good_body.replace("LAW: x\n", ""),
        },
        {
            "number": 3,
            "state": "open",
            "body": good_body.replace(
                "RELATION: Core-only\n",
                "RELATION: Core-only\nRELATION: bridge-candidate\n",
            ),
        },
        {
            "number": 4,
            "state": "open",
            "body": good_body.replace("STATUS: hypothesis", "STATUS:"),
        },
        {
            "number": 5,
            "state": "open",
            "body": good_body.replace("DOMAIN: D5", "DOMAIN: UNKNOWN"),
        },
        {"number": 6, "state": "open", "body": "DOMAIN: D5\n"},
        {"number": 7, "state": "closed", "body": good_body},
    ]

    rows, judged, skipped = findings(issues)
    got = {key(row) for row in rows}
    assert (2, "LAW", "MISSING-FIELD") in got
    assert (3, "RELATION", "DUPLICATE-FIELD") in got
    assert (4, "STATUS", "EMPTY-FIELD") in got
    assert all(x[0] not in {1, 5, 6, 7} for x in got)
    assert judged == 5
    assert skipped == 2

    payload = baseline_payload(rows)
    assert payload["schema"] == "task-record-structure-baseline/v1"
    assert len(payload["violations"]) == 3

    print("TASK-RECORD-STRUCTURE-CHECKER=PASS")
    print("EXACT-ONCE=PASS")
    print("UNKNOWN-AS-VALUE=PASS")
    print("UNMARKED-LEGACY-SKIPPED=PASS")
    print("BASELINE-KEY=issue+field+verdict")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues")
    ap.add_argument("--baseline")
    ap.add_argument("--emit-baseline", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.issues:
        ap.error("--issues required or use --self-test")
    return run(
        args.issues,
        baseline=args.baseline,
        emit_baseline=args.emit_baseline,
        report_only=args.report_only,
    )


if __name__ == "__main__":
    sys.exit(main())
