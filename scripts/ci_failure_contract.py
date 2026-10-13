#!/usr/bin/env python3
"""CI diagnostic transport for SENS-owned binary verdicts. NOT a semantic oracle."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
LAYER = {"parse", "eval", "encode", "transport"}
STAMP = {"REGRESSION", "TRANSITIONAL", "FLAKE"}
FIELDS = (
    "test_id", "layer", "fixture", "fixture_sha256", "expected_sha256",
    "actual_sha256", "first_difference", "first_bad_sha", "reproduce",
    "stamp", "observed_at", "first_observed_bad_sha",
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc)


def parse_time(value):
    if not isinstance(value, str):
        raise ValueError("missing ISO-8601 UTC time")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp needs timezone")
    return parsed.astimezone(dt.timezone.utc)


def validate_manifest(manifest):
    if manifest.get("schema") != "sens-red-v1" or not isinstance(manifest.get("cases"), list):
        raise ValueError("manifest must have schema=sens-red-v1 and cases[]")
    seen = set()
    for item in manifest["cases"]:
        tid = item.get("test_id", "")
        if not isinstance(tid, str) or not tid or tid in seen:
            raise ValueError("duplicate/empty quarantine test_id")
        seen.add(tid)
        stamp = item.get("stamp")
        if stamp not in STAMP:
            raise ValueError(tid + ": invalid/missing classification")
        for field in ("owner", "first_seen_at", "reason"):
            if not item.get(field):
                raise ValueError(tid + ": missing " + field)
        begin = parse_time(item["first_seen_at"])
        if begin > now() + dt.timedelta(minutes=5):
            raise ValueError(tid + ": future first_seen_at")
        if stamp in {"TRANSITIONAL", "FLAKE"}:
            if not re.fullmatch(r"#\d+", item.get("ticket", "")):
                raise ValueError(tid + ": quarantine needs ticket #N")
            expiry = parse_time(item.get("expires_at"))
            if expiry <= begin:
                raise ValueError(tid + ": invalid expiry")
            if not item.get("investigation"):
                raise ValueError(tid + ": named investigation required")
    return manifest


def check_report(record):
    errors = []
    for key in FIELDS:
        if key not in record or record[key] in ("", None):
            errors.append("missing:" + key)
    if record.get("layer") not in LAYER:
        errors.append("invalid:layer")
    if record.get("stamp") not in STAMP:
        errors.append("invalid:stamp")
    for key in ("fixture_sha256", "expected_sha256", "actual_sha256"):
        if not DIGEST.fullmatch(str(record.get(key, ""))):
            errors.append("invalid:" + key)
    if not SHA.fullmatch(str(record.get("first_bad_sha", ""))):
        errors.append("UNRESOLVED_FIRST_BAD_SHA")
    if not SHA.fullmatch(str(record.get("first_observed_bad_sha", ""))):
        errors.append("invalid:first_observed_bad_sha")
    try:
        parse_time(record.get("observed_at"))
    except (ValueError, TypeError):
        errors.append("invalid:observed_at")
    difference = record.get("first_difference")
    if not isinstance(difference, dict) or not (
        ("byte_offset" in difference and "bit_offset" in difference)
        or ("exit_expected" in difference and "exit_actual" in difference)
    ):
        errors.append("invalid:first_difference")
    if not record.get("fixture", "").startswith("tests/") or not Path(record["fixture"]).is_file():
        errors.append("invalid:fixture_path")
    elif digest(Path(record["fixture"]).read_bytes()) != record.get("fixture_sha256"):
        errors.append("invalid:fixture_digest")
    if not isinstance(record.get("reproduce"), str) or not record.get("reproduce").strip():
        errors.append("invalid:reproduce")
    if record.get("stamp") in {"TRANSITIONAL", "FLAKE"}:
        if not re.fullmatch(r"#\d+", str(record.get("ticket", ""))):
            errors.append("invalid:ticket")
        for key in ("owner", "first_seen_at", "expires_at", "investigation"):
            if not record.get(key):
                errors.append("missing:" + key)
        try:
            if parse_time(record["expires_at"]) <= now():
                errors.append("EXPIRED_QUARANTINE")
        except (KeyError, ValueError, TypeError):
            errors.append("invalid:expires_at")
    return errors


def difference(expected, actual, status):
    for offset in range(max(len(expected), len(actual))):
        e = expected[offset] if offset < len(expected) else None
        a = actual[offset] if offset < len(actual) else None
        if e != a:
            if e is None or a is None:
                return {"byte_offset": offset, "bit_offset": 0,
                        "expected_byte": e, "actual_byte": a, "kind": "length"}
            xor = e ^ a
            bit = next(i for i in range(8) if xor & (1 << (7 - i)))
            return {"byte_offset": offset, "bit_offset": bit,
                    "expected_byte": e, "actual_byte": a, "kind": "content"}
    return {"exit_expected": 0, "exit_actual": status}


def run(args):
    manifest = validate_manifest(json.loads(Path(args.manifest).read_text()))
    fixture = Path(args.fixture)
    if not fixture.is_file() or not args.command:
        raise ValueError("fixture and command are required")
    cmd = list(args.command)
    if cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        raise ValueError("missing subprocess command")
    expected = Path(args.expected_file).read_bytes() if args.expected_file else b""
    completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    actual = completed.stdout
    if args.output_file:
        Path(args.output_file).write_bytes(actual)
    if completed.returncode == 0 and (not args.expected_file or actual == expected):
        print("PASS test_id=" + args.test_id + " layer=" + args.layer)
        return 0
    item = next((x for x in manifest["cases"] if x["test_id"] == args.test_id), None)
    stamp = item["stamp"] if item else "REGRESSION"
    observed = os.environ.get("GITHUB_SHA", "")
    record = {
        "test_id": args.test_id, "layer": args.layer,
        "fixture": args.fixture, "fixture_sha256": digest(fixture.read_bytes()),
        "expected_sha256": digest(expected), "actual_sha256": digest(actual),
        "first_difference": difference(expected, actual, completed.returncode),
        "first_bad_sha": (item or {}).get("first_bad_sha") or os.environ.get("SENS_FIRST_BAD_SHA", "UNRESOLVED"),
        "first_observed_bad_sha": observed if SHA.fullmatch(observed) else "UNRESOLVED",
        "observed_at": now().isoformat(), "reproduce": shlex.join(cmd),
        "stamp": stamp, "stderr_tail": completed.stderr.decode("utf-8", errors="replace")[-1500:],
        "exit_code": completed.returncode,
    }
    if item:
        for key in ("ticket", "owner", "reason", "first_seen_at", "expires_at", "investigation"):
            if key in item:
                record[key] = item[key]
    errors = check_report(record)
    print("SENS_FAILURE_REPORT=" + json.dumps(record, ensure_ascii=False, sort_keys=True))
    if args.report_file:
        with open(args.report_file, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    if errors:
        print("::error::UNINFORMATIVE-OUTPUT test=" + args.test_id + " " + ",".join(errors))
        return 1
    if item and now() - parse_time(item["first_seen_at"]) > dt.timedelta(hours=24):
        print("::warning::ESCALATION-24H " + args.test_id + " owner=" + item["owner"])
    if stamp == "REGRESSION":
        print("::error::REGRESSION " + args.test_id + " — semantic/release blocker")
        return 1
    print("::warning::NAMED-QUARANTINE " + stamp + " " + args.test_id
          + " ticket=" + item["ticket"] + " expires=" + item["expires_at"])
    return 0


def scan(args):
    validate_manifest(json.loads(Path(args.manifest).read_text()))
    path = Path(args.report_file)
    if not path.is_file() or not path.read_text().strip():
        if args.allow_empty:
            print("PASS no failed tests; nothing silently skipped")
            return 0
        print("UNINFORMATIVE-OUTPUT no diagnostic report")
        return 1
    failures = []
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        try:
            errors = check_report(json.loads(line))
        except (ValueError, TypeError) as exc:
            errors = ["invalid:json:" + str(exc)]
        failures += [str(line_number) + ":" + e for e in errors]
    if failures:
        print("UNINFORMATIVE-OUTPUT " + ", ".join(failures))
        return 1
    print("PASS diagnostic shape for " + str(len(path.read_text().splitlines())) + " failed test(s)")
    return 0


def self_test():
    fixture = Path("tests/semantic/narrate-d3-atom-eq-law.bits")
    if not fixture.exists():
        raise ValueError("run from repo root")
    record = {
        "test_id": "diagnostic-self-test", "layer": "eval",
        "fixture": str(fixture), "fixture_sha256": digest(fixture.read_bytes()),
        "expected_sha256": digest(b"1\n"), "actual_sha256": digest(b"0\n"),
        "first_difference": difference(b"1\n", b"0\n", 0),
        "first_bad_sha": "a" * 40, "first_observed_bad_sha": "b" * 40,
        "observed_at": now().isoformat(), "reproduce": "sens fixture.sens",
        "stamp": "REGRESSION",
    }
    if check_report(record):
        raise RuntimeError("valid mechanical report rejected")
    for field in FIELDS:
        mutant = dict(record)
        mutant.pop(field)
        if not check_report(mutant):
            raise RuntimeError("missing field passed: " + field)
    for field in ("first_bad_sha", "fixture_sha256", "actual_sha256"):
        mutant = dict(record, **{field: "UNKNOWN"})
        if not check_report(mutant):
            raise RuntimeError("invalid digest/SHA passed: " + field)
    for fake in (b"", b"0", b"1", b"1\nextra"):
        if fake != b"1\n" and "byte_offset" not in difference(b"1\n", fake, 0):
            raise RuntimeError("missing first difference")
    validate_manifest({"schema": "sens-red-v1", "cases": []})
    for stamp in ("TRANSITIONAL", "FLAKE"):
        try:
            validate_manifest({"schema": "sens-red-v1", "cases": [
                {"test_id": "x", "stamp": stamp, "owner": "worker",
                 "first_seen_at": now().isoformat(), "reason": "needs investigation"}
            ]})
        except ValueError:
            pass
        else:
            raise RuntimeError("unnamed quarantine was accepted")
    print("PASS diagnostic contract + missing-field mutants + quarantine guards")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("run")
    p.add_argument("--test-id", required=True)
    p.add_argument("--layer", required=True, choices=sorted(LAYER))
    p.add_argument("--fixture", required=True)
    p.add_argument("--manifest", default="knowledge/red-test-quarantine.json")
    p.add_argument("--report-file")
    p.add_argument("--expected-file")
    p.add_argument("--output-file")
    p.add_argument("command", nargs=argparse.REMAINDER)
    c = sub.add_parser("scan")
    c.add_argument("--manifest", default="knowledge/red-test-quarantine.json")
    c.add_argument("--report-file", required=True)
    c.add_argument("--allow-empty", action="store_true")
    sub.add_parser("self-test")
    args = parser.parse_args()
    try:
        return {"run": run, "scan": scan, "self-test": lambda a: self_test()}[args.action](args)
    except (OSError, ValueError, RuntimeError) as exc:
        print("UNINFORMATIVE-OUTPUT diagnostic transport error: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
