#!/usr/bin/env python3
"""CI glue only: execute the native ELF sens oracle; never interpret SENS in Python."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

SCHEMA = "sens-native-executor-evidence/v1"
REQUIRED = {
    "sens-time-d1-predicate-law",
    "knowledge-exact-arity-structure",
    "sens-domain-logic-2040-mutant",
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()

def check_binary(path):
    p = Path(path)
    if p.name != "sens" or not p.is_file() or not os.access(p, os.X_OK):
        raise ValueError("UNINFORMATIVE-EXECUTOR: missing executable sens")
    with p.open("rb") as f:
        if f.read(4) != bytes([127, 69, 76, 70]):
            raise ValueError("UNINFORMATIVE-EXECUTOR: sens must be native ELF")
    return p

def verify(record):
    required = ("schema", "test_id", "binary", "binary_sha256", "version",
                "fixture", "fixture_sha256", "expected_sha256", "actual_sha256",
                "expectation", "actual_stream", "exit_code", "verdict", "reproduce")
    if any(key not in record for key in required):
        raise ValueError("UNINFORMATIVE-EXECUTOR: missing evidence fields")
    if record["schema"] != SCHEMA or record["test_id"] not in REQUIRED:
        raise ValueError("UNINFORMATIVE-EXECUTOR: invalid schema/test")
    if record["verdict"] != "PASS" or not record["version"].startswith("sens "):
        raise ValueError("UNINFORMATIVE-EXECUTOR: no actual native PASS/version")
    for key in ("binary_sha256", "fixture_sha256", "expected_sha256", "actual_sha256"):
        value = record[key]
        if not isinstance(value, str) or len(value) != 64 or any(x not in "0123456789abcdef" for x in value):
            raise ValueError("UNINFORMATIVE-EXECUTOR: invalid digest " + key)
    if file_sha(check_binary(record["binary"])) != record["binary_sha256"]:
        raise ValueError("UNINFORMATIVE-EXECUTOR: binary SHA mismatch")
    fixture = Path(record["fixture"])
    if not fixture.is_file() or fixture.suffix != ".sens" or file_sha(fixture) != record["fixture_sha256"]:
        raise ValueError("UNINFORMATIVE-EXECUTOR: fixture SHA mismatch")
    if record["reproduce"] != shlex.join([record["binary"], record["fixture"]]):
        raise ValueError("UNINFORMATIVE-EXECUTOR: opaque reproduction")
    if record["expectation"] == "stdout-exact":
        if record["exit_code"] != 0 or record["actual_stream"] != "stdout" or record["expected_sha256"] != record["actual_sha256"]:
            raise ValueError("UNINFORMATIVE-EXECUTOR: positive mismatch")
    elif record["expectation"] == "stderr-contains":
        match = record.get("expected_match", "")
        if record["exit_code"] == 0 or record["actual_stream"] != "stderr" or not match or sha(match.encode()) != record["expected_sha256"]:
            raise ValueError("UNINFORMATIVE-EXECUTOR: negative mismatch")
    else:
        raise ValueError("UNINFORMATIVE-EXECUTOR: unknown expected mode")

def run(args):
    if args.test_id not in REQUIRED:
        raise ValueError("UNINFORMATIVE-EXECUTOR: unknown native test")
    binary = check_binary(args.binary)
    fixture = Path(args.fixture)
    if not fixture.is_file() or fixture.suffix != ".sens":
        raise ValueError("UNINFORMATIVE-EXECUTOR: physical .sens file required")
    if (args.expected_file is None) == (args.expect_stderr is None):
        raise ValueError("UNINFORMATIVE-EXECUTOR: choose exactly one expected mode")
    version = subprocess.run([str(binary), "--version"], capture_output=True, check=False)
    v = version.stdout.decode("utf-8", errors="replace").strip()
    if version.returncode or not v.startswith("sens "):
        raise ValueError("UNINFORMATIVE-EXECUTOR: native sens --version failed")
    command = [str(binary), str(fixture)]
    expected = Path(args.expected_file).read_bytes() if args.expected_file else args.expect_stderr.encode()
    mode = "stdout-exact" if args.expected_file else "stderr-contains"
    print("SENS_EXECUTOR binary=" + str(binary) + " version=" + v + " sha256=" + file_sha(binary), flush=True)
    print("SENS_INPUT fixture=" + str(fixture) + " sha256=" + file_sha(fixture), flush=True)
    print("SENS_REPRODUCE " + shlex.join(command), flush=True)
    actual = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    selected = actual.stdout if args.expected_file else actual.stderr
    passed = ((actual.returncode == 0 and selected == expected)
              if args.expected_file else
              (actual.returncode != 0 and expected.lower() in selected.lower()))
    record = {
        "schema": SCHEMA, "test_id": args.test_id,
        "binary": str(binary), "binary_sha256": file_sha(binary),
        "version": v, "fixture": str(fixture), "fixture_sha256": file_sha(fixture),
        "expected_sha256": sha(expected), "actual_sha256": sha(selected),
        "actual_stream": "stdout" if args.expected_file else "stderr",
        "expectation": mode, "expected_match": args.expect_stderr,
        "exit_code": actual.returncode, "verdict": "PASS" if passed else "FAIL",
        "reproduce": shlex.join(command), "github_sha": os.getenv("GITHUB_SHA", "LOCAL"),
    }
    print("SENS_OUTPUT " + repr(selected.decode("utf-8", errors="replace")[-2048:]), flush=True)
    print("SENS_NATIVE_EVIDENCE " + json.dumps(record, ensure_ascii=False, sort_keys=True), flush=True)
    with open(args.evidence_file, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    if not passed:
        print("::error::UNINFORMATIVE-EXECUTOR expected_sha256=" + sha(expected) + " actual_sha256=" + sha(selected), file=sys.stderr)
        return 1
    verify(record)
    print("SENS_NATIVE_PASS " + args.test_id, flush=True)
    return 0

def scan(args):
    p = Path(args.evidence_file)
    if not p.is_file():
        raise ValueError("UNINFORMATIVE-EXECUTOR: evidence file missing")
    records = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [r.get("test_id") for r in records]
    if len(records) != len(REQUIRED) or set(ids) != REQUIRED or len(set(ids)) != len(ids):
        raise ValueError("UNINFORMATIVE-EXECUTOR: missing/extra/duplicate native proofs: " + repr(ids))
    for r in records:
        verify(r)
        print("SENS_NATIVE_RATCHET_PASS test_id=" + r["test_id"] +
              " fixture_sha256=" + r["fixture_sha256"] +
              " expected_sha256=" + r["expected_sha256"] +
              " actual_sha256=" + r["actual_sha256"], flush=True)
    return 0

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="action", required=True)
    a = sub.add_parser("run")
    a.add_argument("--test-id", required=True)
    a.add_argument("--binary", required=True)
    a.add_argument("--fixture", required=True)
    a.add_argument("--expected-file")
    a.add_argument("--expect-stderr")
    a.add_argument("--evidence-file", required=True)
    b = sub.add_parser("scan")
    b.add_argument("--evidence-file", required=True)
    args = p.parse_args()
    try:
        return {"run": run, "scan": scan}[args.action](args)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("::error::UNINFORMATIVE-EXECUTOR " + str(exc), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
