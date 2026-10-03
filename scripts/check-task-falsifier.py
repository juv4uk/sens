#!/usr/bin/env python3
"""#2532 — conservative FALSIFIER quality audit over canonical task records.

Consumes task_schema_record.py. It never reparses Markdown independently and
never guesses domain semantics. Ambiguous prose is UNKNOWN, not OK.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from task_schema_record import parse_record, structural_verdict

SCHEMA = "task-falsifier-baseline/v1"

_SPACE = re.compile(r"\s+")
_PUNCT = re.compile(r"[\x60*_#]+")
_PLACEHOLDER = re.compile(
    r"^(?:todo|tbd|fixme|test more|more testing|check ci|verify law|"
    r"needs testing|pending|explicit counter-test|counter-test placeholder)$",
    re.I,
)
_EXPLICIT_UNKNOWN = re.compile(
    r"^(?:unknown|unresolved|not yet known|not yet determined|pending evidence)$",
    re.I,
)
_COMMAND_ONLY = re.compile(
    r"^(?:(?:run|execute|check)\s+)?(?:cargo\s+test|pytest|python3?\b.*|"
    r"gh\s+workflow\b.*|ci|tests?)\s*[.;]?$",
    re.I,
)
_POSITIVE_ONLY = re.compile(
    r"^(?:positive\s+example|example|witness)\s*:\s*.+$",
    re.I,
)
_DISPROOF_SIGNAL = re.compile(
    r"\b(?:falsif(?:y|ied|ies)|counterexample|fails?\s+if|"
    r"reject(?:ed)?\s+if|breaks?\s+if|would\s+fail\s+if|"
    r"disproved?\s+if|must\s+fail(?:\s+when)?|must\s+not\b|must\s+make\b|"
    r"if\b.+\bthen\b.+\bfail|"
    r"if\b.+(?:!=|≠|changes?|collides?|diverges?|becomes?|accepts?|rejects?)|"
    r"\b(?:rejects?|invalidates?|violates?|contradicts?)\b.{0,80}\b(?:model|law|claim|bridge|placement|coordinate|hypothesis)\b)",
    re.I,
)

def _norm(text: str) -> str:
    text = _PUNCT.sub("", text or "")
    text = text.strip(" \t\r\n.;:")
    return _SPACE.sub(" ", text).lower()

def falsifier_verdict(law: str, falsifier: str) -> str:
    raw = (falsifier or "").strip()
    if not raw:
        return "empty"
    norm = _norm(raw)
    law_norm = _norm(law or "")
    if _EXPLICIT_UNKNOWN.fullmatch(norm):
        return "unknown"
    if _PLACEHOLDER.fullmatch(norm):
        return "placeholder"
    if law_norm and norm == law_norm:
        return "restatement"
    if law_norm and norm in {
        f"not {law_norm}",
        f"law fails {law_norm}",
        f"the law fails {law_norm}",
        f"falsify {law_norm}",
    }:
        return "restatement"
    if _COMMAND_ONLY.fullmatch(norm):
        return "non-falsifying"
    if _POSITIVE_ONLY.fullmatch(raw) and not _DISPROOF_SIGNAL.search(raw):
        return "non-falsifying"
    if _DISPROOF_SIGNAL.search(raw):
        return "ok"
    return "unknown"

def judge_issue(issue: dict) -> dict | None:
    if str(issue.get("state", "open")).lower() != "open":
        return None
    body = issue.get("body") or ""
    record = parse_record(body)
    if not record.marked:
        return None

    structure = structural_verdict(record, "FALSIFIER")
    rows = record.occurrences.get("FALSIFIER", ())
    law_rows = record.occurrences.get("LAW", ())

    # Missing/duplicate structure belongs to #2531, not this semantic judge.
    if structure in {"MISSING-FIELD", "DUPLICATE-FIELD"}:
        return None
    if len(rows) != 1:
        return None

    law = law_rows[0].value if len(law_rows) == 1 else ""
    value = rows[0].value
    verdict = falsifier_verdict(law, value)
    return {
        "issue": int(issue["number"]),
        "title": str(issue.get("title") or ""),
        "verdict": verdict,
        "falsifier": value.strip(),
    }

def audit(issues: list[dict]) -> dict:
    rows: list[dict] = []
    skipped = 0
    for issue in issues:
        row = judge_issue(issue)
        if row is None:
            skipped += 1
        else:
            rows.append(row)
    debt = [row for row in rows if row["verdict"] != "ok"]
    counts: dict[str, int] = {}
    for row in debt:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    return {
        "schema": "task-falsifier-audit/v1",
        "judged": len(rows),
        "skipped": skipped,
        "ok": len(rows) - len(debt),
        "debt": debt,
        "debt_counts": counts,
    }

def baseline_from_audit(result: dict) -> dict:
    items = [
        {"issue": row["issue"], "verdict": row["verdict"]}
        for row in result["debt"]
    ]
    items.sort(key=lambda row: (row["issue"], row["verdict"]))
    return {"schema": SCHEMA, "debt": items}

def baseline_keys(data: dict) -> set[tuple[int, str]]:
    if data.get("schema") != SCHEMA:
        raise ValueError("unsupported FALSIFIER baseline schema")
    out: set[tuple[int, str]] = set()
    for row in data.get("debt", []):
        key = (int(row["issue"]), str(row["verdict"]))
        if key in out:
            raise ValueError(f"duplicate baseline debt key: {key}")
        out.add(key)
    return out

def load_issues(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["issues"] if isinstance(data, dict) else data

def self_test() -> int:
    cases = [
        ("x -> y", "", "empty"),
        ("x -> y", "TBD", "placeholder"),
        ("x -> y", "test more", "placeholder"),
        ("x -> y", "check CI", "placeholder"),
        ("x -> y", "x -> y", "restatement"),
        ("x -> y", "not x -> y", "restatement"),
        ("x -> y", "run cargo test", "non-falsifying"),
        ("x -> y", "example: x=1 gives y=2", "non-falsifying"),
        ("x -> y", "UNKNOWN", "unknown"),
        ("axis refinements commute", "FALSIFIED if swapping refinement order changes the endpoint", "ok"),
        ("same bits do not imply same domain law", "counterexample: cross-domain apply accepts instead of DOMAIN-MISMATCH", "ok"),
        ("coordinate law is permutation-stable", "reject if an admissible relabel changes the claimed invariant", "ok"),
        ("x -> y", "compare three implementations", "unknown"),
        ("x -> y", "explicit counter-test", "placeholder"),
        (
            "exact-Q coordinates obey normalization",
            "Noncanonical raw coordinate, skipped gcd normalization, or width collapse reject the model.",
            "ok",
        ),
        (
            "cross-domain laws stay separated",
            "Cross-domain law application must fail DOMAIN-MISMATCH; shared helpers must not authorize semantic equality.",
            "ok",
        ),
    ]
    failures = 0
    for law, fal, expected in cases:
        got = falsifier_verdict(law, fal)
        passed = got == expected
        failures += 0 if passed else 1
        print(f"  [{'ok' if passed else 'FAIL'}] {got:15} expected={expected:15} {fal!r}")

    body = """## BINARY-DOMAIN RECORD
DOMAIN: D5
BINARY OBJECT: 00101
LAW: two axes commute
WITNESS: #1
FALSIFIER: fails if reversing axis order changes the endpoint
STATUS: hypothesis
RELATION: Core-only
"""
    row = judge_issue({"number": 1, "state": "open", "body": body})
    assert row and row["verdict"] == "ok"
    assert judge_issue({"number": 2, "state": "open", "body": "LAW: x\nFALSIFIER: fails if x changes\n"}) is None

    fake = {
        "schema": SCHEMA,
        "debt": [
            {"issue": 10, "verdict": "unknown"},
            {"issue": 11, "verdict": "placeholder"},
        ],
    }
    assert baseline_keys(fake) == {(10, "unknown"), (11, "placeholder")}

    if failures:
        print(f"FALSIFIER-QUALITY-SELFTEST=FAIL failures={failures}")
        return 1
    print("FALSIFIER-QUALITY-SELFTEST=PASS")
    print("AMBIGUOUS-PROSE=UNKNOWN")
    print("PARSER=task_schema_record.py")
    print("BASELINE-NON-GROWTH=PASS")
    return 0

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues", type=Path)
    ap.add_argument("--baseline", type=Path)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--emit-baseline", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.issues:
        ap.error("--issues required or use --self-test")

    result = audit(load_issues(args.issues))
    if args.emit_baseline:
        print(json.dumps(baseline_from_audit(result), indent=2, sort_keys=True))
        return 0

    print(
        f"(task-falsifier-audit (judged {result['judged']}) "
        f"(ok {result['ok']}) (debt {len(result['debt'])}))"
    )
    for verdict, count in sorted(result["debt_counts"].items()):
        print(f"  ({verdict} {count})")
    for row in result["debt"]:
        print(f"  #{row['issue']} {row['verdict']} {row['falsifier']!r}")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.baseline:
        current = {(row["issue"], row["verdict"]) for row in result["debt"]}
        known = baseline_keys(json.loads(args.baseline.read_text(encoding="utf-8")))
        new_debt = sorted(current - known)
        if new_debt:
            print("NEW-FALSIFIER-DEBT")
            for issue, verdict in new_debt:
                print(f"  #{issue} {verdict}")
            if not args.report_only:
                return 1
    elif result["debt"] and not args.report_only:
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
