#!/usr/bin/env python3
"""SENS CI failure-output contract observer; never a semantic oracle.

One scanner invocation corresponds to one independently executed SENS test.
The SENS witness alone owns meaning, expectations and its result.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys

PREFIX = "SENS-FAILURE "
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
ISSUE = re.compile(r"#[1-9][0-9]*\Z")
LAYERS = frozenset(("parse", "eval", "encode", "transport"))
CLASSES = frozenset(("REGRESSION", "TRANSITIONAL", "FLAKE", "UNCLASSIFIED"))


class Invalid(Exception):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise Invalid(reason)


def iso_time(value: object) -> datetime:
    require(isinstance(value, str), "observed_at requires timezone")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Invalid("invalid observed_at") from exc
    require(stamp.tzinfo is not None, "observed_at timezone is mandatory")
    return stamp.astimezone(timezone.utc)


def validate(record: object, *, now: datetime) -> dict:
    require(isinstance(record, dict), "SENS-FAILURE must be JSON object")
    r = record
    require(isinstance(r.get("id"), str) and r["id"].strip() and "\n" not in r["id"], "missing/invalid id")
    require(isinstance(r.get("layer"), str) and r["layer"] in LAYERS, "missing/invalid layer")
    inp = r.get("input")
    require(isinstance(inp, dict), "missing input")
    if set(inp) == {"program"}:
        require(isinstance(inp["program"], str) and bool(inp["program"]), "empty input.program")
    elif set(inp) == {"fixture", "sha256"}:
        require(isinstance(inp["fixture"], str) and bool(inp["fixture"].strip()), "missing fixture path")
        require(isinstance(inp["sha256"], str) and bool(HEX64.fullmatch(inp["sha256"])), "invalid fixture sha256")
    else:
        raise Invalid("input requires program OR fixture+sha256")
    for key in ("expected_sha256", "actual_sha256"):
        require(isinstance(r.get(key), str) and bool(HEX64.fullmatch(r[key])), "missing/invalid " + key)
    require(r["expected_sha256"] != r["actual_sha256"], "expected and actual digests are equal")
    diff = r.get("first_difference")
    require(isinstance(diff, dict), "missing first_difference")
    require(set(diff) == {"offset", "unit"}, "first_difference requires offset and unit")
    require(type(diff["offset"]) is int and diff["offset"] >= 0, "first_difference.offset invalid")
    require(isinstance(diff["unit"], str) and diff["unit"] in ("bit", "byte"), "first_difference.unit invalid")
    require(isinstance(r.get("first_bad_sha"), str) and bool(HEX40.fullmatch(r["first_bad_sha"])),
            "missing/invalid first_bad_sha; do not invent SHA")
    require(isinstance(r.get("reproduce"), str) and r["reproduce"].strip() and "\n" not in r["reproduce"],
            "missing or multiline reproduce")
    require(isinstance(r.get("classification"), str) and r["classification"] in CLASSES,
            "missing/invalid classification")
    observed = iso_time(r.get("observed_at"))
    require(observed <= now + timedelta(minutes=5), "future observed_at")
    return r


def validate_quarantine(manifest: object, *, now: datetime) -> dict:
    require(isinstance(manifest, dict) and set(manifest) == {"entries"}, "manifest requires entries only")
    require(isinstance(manifest["entries"], list), "manifest.entries must be array")
    result: dict[str, dict] = {}
    for entry in manifest["entries"]:
        require(isinstance(entry, dict), "quarantine entry is not object")
        for key in ("id", "classification", "issue", "owner", "since", "expires", "reason"):
            require(isinstance(entry.get(key), str) and entry[key].strip(), "quarantine missing " + key)
        require(entry["classification"] in ("TRANSITIONAL", "FLAKE"), "REGRESSION cannot be quarantined")
        require(bool(ISSUE.fullmatch(entry["issue"])), "issue must be #N")
        try:
            start, end = date.fromisoformat(entry["since"]), date.fromisoformat(entry["expires"])
        except ValueError as exc:
            raise Invalid("invalid quarantine date") from exc
        require(end >= start, "quarantine expires before since")
        require(entry["id"] not in result, "duplicate quarantine id")
        require(end >= now.date(), "expired quarantine " + entry["id"])
        result[entry["id"]] = entry
    return result


def analyze(log: str, exit_code: int, manifest: object, *, now: datetime) -> tuple[int, str]:
    reports = [line[len(PREFIX):] for line in log.splitlines() if line.startswith(PREFIX)]
    if exit_code == 0:
        if reports:
            return 2, "UNINFORMATIVE-OUTPUT: hidden RED envelope in successful command"
        return 0, "PASS: SENS source test exited successfully"
    if len(reports) != 1:
        return 2, f"UNINFORMATIVE-OUTPUT: expected one SENS-FAILURE envelope, found {len(reports)}; raw_exit={exit_code}"
    try:
        report = validate(json.loads(reports[0]), now=now)
        quarantined = validate_quarantine(manifest, now=now)
    except (ValueError, Invalid) as exc:
        return 2, f"UNINFORMATIVE-OUTPUT: {exc}; raw_exit={exit_code}"
    cls = report["classification"]
    label = f"id={report['id']} layer={report['layer']} first_bad_sha={report['first_bad_sha']} reproduce={report['reproduce']}"
    if cls == "REGRESSION":
        return 1, f"REGRESSION BLOCK: {label}; raw_exit={exit_code}"
    if cls == "UNCLASSIFIED":
        age = now - iso_time(report["observed_at"])
        if age > timedelta(hours=24):
            return 3, f"ESCALATE-24H owner=juv4uk: unclassified RED age={age}; {label}"
        return 1, f"UNCLASSIFIED RED: pending <24h triage; {label}"
    item = quarantined.get(report["id"])
    if item is None or item["classification"] != cls:
        return 2, f"UNINFORMATIVE-OUTPUT: no matching named quarantine for {cls}; {label}"
    if report.get("ticket") != item["issue"]:
        return 2, f"UNINFORMATIVE-OUTPUT: quarantine ticket mismatch; {label}"
    return 0, (f"QUARANTINED RED [{cls}] id={item['id']} issue={item['issue']} "
               f"owner={item['owner']} since={item['since']} expires={item['expires']} "
               f"reason={item['reason']}; {label}; raw_exit={exit_code}")


def emit(message: str, code: int) -> None:
    print(message, file=sys.stderr if code else sys.stdout)
    if os.getenv("GITHUB_ACTIONS") == "true":
        safe = message.replace("%", "%25").replace("\r", " ").replace("\n", " ")
        if code:
            print("::error::" + safe)
        elif message.startswith("QUARANTINED"):
            print("::warning::" + safe)
        summary = os.getenv("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as stream:
                stream.write("\n### SENS red-test contract\n\n" + message.replace("|", "\\|") + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scan", choices=["scan"])
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("data/ci-test-quarantine.json"))
    args = parser.parse_args(argv)
    try:
        log = args.log.read_text(encoding="utf-8", errors="replace")
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        code, message = analyze(log, args.exit_code, manifest, now=datetime.now(timezone.utc))
    except (OSError, ValueError, Invalid) as exc:
        code, message = 2, f"UNINFORMATIVE-OUTPUT: cannot load log/manifest: {exc}"
    emit(message, code)
    return code


if __name__ == "__main__":
    sys.exit(main())
