#!/usr/bin/env python3
"""#2536 — orthogonal PHASE guard for governed binary-domain task records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from task_schema_record import parse_record

ALLOWED = ("HISTORICAL-INGEST", "STRUCTURAL-DISCOVERY", "SENS-DERIVATION")

_PHASE_LINE = re.compile(
    r"^\s*(?:[-*]\s*)?\**PHASE\**\s*[:=]\s*(.*?)\s*$", re.I
)
_ALLOCATE = re.compile(
    r"\b(?:allocate|allocates|allocated|assign|assigns|assigned|place|places|placed|"
    r"ratify|ratifies|ratified)\w*\b.{0,80}"
    r"\b(?:coordinate|resident|slot|address)\w*\b",
    re.I,
)
_DELETE_HISTORICAL = re.compile(
    r"(?:\b(?:delete|drop|omit|erase|remove)\w*\b.{0,100}"
    r"\b(?:historical|observation|row)\w*\b.{0,100}"
    r"\b(?:derived|derivable|derivation)\w*\b)"
    r"|(?:\b(?:derived|derivable|derivation)\w*\b.{0,100}"
    r"\b(?:delete|drop|omit|erase|remove)\w*\b.{0,100}"
    r"\b(?:historical|observation|row)\w*\b)",
    re.I,
)
_NEGATION = re.compile(
    r"\b(?:no|not|never|without|forbid|forbidden|must\s+not|may\s+not|"
    r"cannot|can't|do\s+not|does\s+not)\b",
    re.I,
)


def phase_occurrences(body: str) -> list[str]:
    out: list[str] = []
    for raw in (body or "").splitlines():
        m = _PHASE_LINE.match(raw)
        if m:
            out.append(m.group(1).strip().strip(chr(96)).strip())
    return out


def _single_law(body: str) -> str | None:
    record = parse_record(body or "")
    rows = record.occurrences.get("LAW", ())
    if len(rows) != 1:
        return None
    return rows[0].value.strip()


def _positive_allocation_claim(law: str) -> bool:
    return bool(_ALLOCATE.search(law)) and _NEGATION.search(law) is None


def _historical_deletion_claim(law: str) -> bool:
    return bool(_DELETE_HISTORICAL.search(law)) and _NEGATION.search(law) is None


def judge_issue(issue: dict) -> dict | None:
    if str(issue.get("state", "open")).lower() != "open":
        return None

    body = issue.get("body") or ""
    record = parse_record(body)
    if not record.marked:
        return None

    phases = phase_occurrences(body)
    base = {
        "issue": int(issue["number"]),
        "title": str(issue.get("title") or ""),
        "phase_values": phases,
    }

    if not phases:
        return {**base, "verdict": "MISSING-PHASE", "detail": ""}
    if len(phases) > 1:
        return {**base, "verdict": "DUPLICATE-PHASE", "detail": f"count={len(phases)}"}

    phase = phases[0].upper()
    if phase not in ALLOWED:
        return {**base, "verdict": "INVALID-PHASE", "detail": phases[0]}

    law = _single_law(body)
    if law:
        if phase == "HISTORICAL-INGEST" and _historical_deletion_claim(law):
            return {
                **base,
                "phase": phase,
                "verdict": "PHASE-MIXING-HISTORICAL-DELETION",
                "detail": law,
            }
        if phase in {"HISTORICAL-INGEST", "STRUCTURAL-DISCOVERY"} and _positive_allocation_claim(law):
            return {
                **base,
                "phase": phase,
                "verdict": "PHASE-MIXING-EARLY-PLACEMENT",
                "detail": law,
            }

    return {**base, "phase": phase, "verdict": "OK", "detail": ""}


def audit(issues: list[dict]) -> dict:
    rows = []
    skipped = 0
    for issue in issues:
        row = judge_issue(issue)
        if row is None:
            skipped += 1
        else:
            rows.append(row)

    violations = [row for row in rows if row["verdict"] != "OK"]
    counts: dict[str, int] = {}
    for row in violations:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1

    return {
        "schema": "task-phase-audit/v1",
        "allowed_phases": list(ALLOWED),
        "judged": len(rows),
        "skipped": skipped,
        "ok": len(rows) - len(violations),
        "violations": violations,
        "violation_counts": counts,
    }


def load_issues(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["issues"] if isinstance(data, dict) else data


def self_test() -> int:
    def record(phase: str | None, law: str = "observe capability relation") -> str:
        prefix = "" if phase is None else f"PHASE: {phase}\n"
        return (
            "Parent: #1\n"
            + prefix
            + "## BINARY-DOMAIN RECORD\n"
            + "DOMAIN: Core.Test [carrier=UNKNOWN]\n"
            + "BINARY OBJECT: UNPLACED\n"
            + f"LAW: {law}\n"
            + "WITNESS: #1\n"
            + "FALSIFIER: fails if counterexample exists\n"
            + "STATUS: hypothesis\n"
            + "RELATION: Core-only\n"
        )

    fixtures = [
        {"number": 1, "state": "open", "body": record("HISTORICAL-INGEST")},
        {"number": 2, "state": "open", "body": record("STRUCTURAL-DISCOVERY")},
        {"number": 3, "state": "open", "body": record("SENS-DERIVATION", "allocate coordinate after proved placement law")},
        {"number": 4, "state": "open", "body": record(None)},
        {"number": 5, "state": "open", "body": record("DISCOVERY")},
        {"number": 6, "state": "open", "body": record("HISTORICAL-INGEST") + "\nPHASE: STRUCTURAL-DISCOVERY\n"},
        {"number": 7, "state": "open", "body": record("HISTORICAL-INGEST", "delete historical row because the capability is derivable later")},
        {"number": 8, "state": "open", "body": record("HISTORICAL-INGEST", "allocate resident coordinate from historical chronology")},
        {"number": 9, "state": "open", "body": record("STRUCTURAL-DISCOVERY", "assign coordinate to each discovered factor")},
        {"number": 10, "state": "open", "body": record("STRUCTURAL-DISCOVERY", "factor observables; no coordinate allocation or resident promotion")},
        {"number": 11, "state": "open", "body": "PHASE: HISTORICAL-INGEST\nno marker"},
        {"number": 12, "state": "closed", "body": record("STRUCTURAL-DISCOVERY")},
    ]

    result = audit(fixtures)
    got = {row["issue"]: row["verdict"] for row in result["violations"]}
    assert 1 not in got and 2 not in got and 3 not in got and 10 not in got
    assert got[4] == "MISSING-PHASE"
    assert got[5] == "INVALID-PHASE"
    assert got[6] == "DUPLICATE-PHASE"
    assert got[7] == "PHASE-MIXING-HISTORICAL-DELETION"
    assert got[8] == "PHASE-MIXING-EARLY-PLACEMENT"
    assert got[9] == "PHASE-MIXING-EARLY-PLACEMENT"
    assert 11 not in got and 12 not in got

    print("TASK-PHASE-GUARD=PASS")
    print("PHASE-ENUM=3")
    print("ORTHOGONAL-TO-SEVEN-FIELDS=PASS")
    print("MISSING-PHASE=PASS")
    print("DUPLICATE-PHASE=PASS")
    print("INVALID-PHASE=PASS")
    print("HISTORICAL-DELETION-FALSIFIER=PASS")
    print("EARLY-PLACEMENT-FALSIFIER=PASS")
    print("NEGATIVE-GUARD-NOT-FLAGGED=PASS")
    print("UNMARKED-LEGACY-SKIPPED=PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.issues:
        ap.error("--issues required or use --self-test")

    result = audit(load_issues(args.issues))
    print(
        f"(task-phase-audit (judged {result['judged']}) "
        f"(ok {result['ok']}) (violations {len(result['violations'])}))"
    )
    for verdict, count in sorted(result["violation_counts"].items()):
        print(f"  ({verdict} {count})")
    for row in result["violations"]:
        phase = row.get("phase", row["phase_values"])
        print(
            f"  #{row['issue']} {row['verdict']} "
            f"phase={phase!r} detail={row['detail']!r}"
        )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if result["violations"] and not args.report_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
