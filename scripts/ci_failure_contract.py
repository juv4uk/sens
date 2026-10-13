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
CLASSIFICATION_HOURS = 24  # applies to UNCLASSIFIED RED, not valid named quarantine
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
        if stamp not in STAMP | {"UNCLASSIFIED"}:
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
    fixture_path = record.get("fixture")
    if not isinstance(fixture_path, str) or not fixture_path.startswith("tests/") or not Path(fixture_path).is_file():
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
    """Execute the named process; Python only reports mechanics, never truth."""
    manifest = validate_manifest(json.loads(Path(args.manifest).read_text()))
    fixture = Path(args.fixture)
    if not fixture.is_file() or not args.command:
        raise ValueError("fixture and command are required")
    cmd = list(args.command)
    if cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        raise ValueError("missing subprocess command")

    native = args.layer == "eval"
    executor = Path("target/debug/sens")
    if native:
        if (len(cmd) != 2 or Path(cmd[0]).resolve() != executor.resolve()
                or cmd[1] != args.fixture or not args.fixture.endswith(".sens")
                or not executor.is_file() or not os.access(executor, os.X_OK)):
            print("::error::UNINFORMATIVE-EXECUTOR semantic test must execute "
                  "target/debug/sens <same-physical-fixture.sens> directly")
            return 1
        if (bool(args.expected_file) == bool(args.expect_error_substring)
                or not args.executor_report_file):
            print("::error::UNINFORMATIVE-EXECUTOR require exactly one positive expected-file "
                  "or negative stderr matcher, and executor receipt output")
            return 1
    elif args.expect_error_substring or args.executor_report_file:
        print("::error::UNINFORMATIVE-EXECUTOR native receipts are for eval only")
        return 1

    expected = Path(args.expected_file).read_bytes() if args.expected_file else b""
    negative = bool(args.expect_error_substring)
    expected_evidence = (b"stderr-contains:" + args.expect_error_substring.encode("utf-8")
                         if negative else expected)
    binary_sha = digest(executor.read_bytes()) if native else None
    version = None
    if native:
        manifest_text = Path("crates/sens-cli/Cargo.toml").read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', manifest_text, re.M)
        if not match:
            print("::error::UNINFORMATIVE-EXECUTOR missing executable package version")
            return 1
        version = match.group(1)

    reproduce = shlex.join(cmd)
    kind = "NATIVE_SENS_ORACLE" if native else "CI_GLUE_NO_SEMANTICS"
    print("TEST_EXECUTOR_START kind=" + kind + " test_id=" + args.test_id
          + " command=" + reproduce, flush=True)
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as child:
        print("TEST_EXECUTOR_PID kind=" + kind + " test_id=" + args.test_id +
              " pid=" + str(child.pid), flush=True)
        stdout, stderr = child.communicate()
        completed = subprocess.CompletedProcess(cmd, child.returncode, stdout, stderr)
    actual = completed.stderr if negative else completed.stdout
    passed = ((completed.returncode != 0
               and args.expect_error_substring.encode("utf-8").lower() in completed.stderr.lower()
               and not completed.stdout)
              if negative else
              (completed.returncode == 0 and
               (bool(args.expected_file) and completed.stdout == expected if native
                else not args.expected_file or completed.stdout == expected)))
    fixture_sha = digest(fixture.read_bytes())
    receipt = {
        "test_id": args.test_id, "layer": args.layer, "kind": kind,
        "executor": str(executor) if native else cmd[0],
        "executor_sha256": binary_sha, "package_version": version,
        "fixture": str(fixture), "fixture_sha256": fixture_sha,
        "expected_sha256": digest(expected_evidence),
        "actual_sha256": digest(actual),
        "stdout_sha256": digest(completed.stdout),
        "stderr_sha256": digest(completed.stderr),
        "exit_code": completed.returncode, "verdict": "PASS" if passed else "FAIL",
        "reproduce": reproduce, "mode": "negative" if negative else "positive",
        "observed_sha": os.environ.get("GITHUB_SHA", "LOCAL"),
    }
    print("TEST_EXECUTOR_RECEIPT=" + json.dumps(receipt, ensure_ascii=False, sort_keys=True),
          flush=True)
    if native:
        print("NATIVE_EXECUTOR_END test_id=" + args.test_id +
              " binary=" + str(executor) + " package_version=" + version +
              " binary_sha256=" + binary_sha +
              " exit=" + str(completed.returncode), flush=True)
        if args.executor_report_file:
            with open(args.executor_report_file, "a", encoding="utf-8") as stream:
                stream.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n")
    if passed:
        print("PASS test_id=" + args.test_id + " layer=" + args.layer +
              " executor=" + kind, flush=True)
        return 0

    if completed.stderr:
        print("TEST_EXECUTOR_STDERR_TAIL=" +
              completed.stderr.decode("utf-8", errors="replace")[-1500:],
              flush=True)
    item = next((x for x in manifest["cases"] if x["test_id"] == args.test_id), None)
    stamp = item["stamp"] if item else "UNCLASSIFIED"
    observed = os.environ.get("GITHUB_SHA", "")
    record = {
        "test_id": args.test_id, "layer": args.layer,
        "fixture": args.fixture, "fixture_sha256": fixture_sha,
        "expected_sha256": digest(expected_evidence), "actual_sha256": digest(actual),
        "first_difference": difference(expected_evidence, actual, completed.returncode),
        "first_bad_sha": (item or {}).get("first_bad_sha") or
                         os.environ.get("SENS_FIRST_BAD_SHA", "UNRESOLVED"),
        "first_observed_bad_sha": observed if SHA.fullmatch(observed) else "UNRESOLVED",
        "observed_at": now().isoformat(), "reproduce": reproduce,
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
    if stamp == "REGRESSION":
        print("::error::REGRESSION " + args.test_id + " — semantic/release blocker")
        return 1
    print("::warning::NAMED-QUARANTINE " + stamp + " " + args.test_id
          + " ticket=" + item["ticket"] + " expires=" + item["expires_at"])
    return 0


def scan_executors(args):
    """Fail closed if any claimed SENS law lacks a real, hash-bound native receipt."""
    path = Path(args.report_file)
    if not path.is_file():
        print("::error::UNINFORMATIVE-EXECUTOR missing native process evidence log")
        return 1
    seen = {}
    problems = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            tid = record["test_id"]
            if tid in seen:
                raise ValueError("duplicate test receipt: " + tid)
            seen[tid] = record
            if record.get("kind") != "NATIVE_SENS_ORACLE" or record.get("layer") != "eval":
                raise ValueError(tid + ": Python/mechanical executor mislabelled semantic")
            if record.get("verdict") != "PASS":
                raise ValueError(tid + ": actual SENS verdict not PASS")
            binary = Path("target/debug/sens")
            fixture = Path(record["fixture"])
            version = re.search(
                r'^version\s*=\s*"([^"]+)"',
                Path("crates/sens-cli/Cargo.toml").read_text(encoding="utf-8"), re.M
            )
            if not binary.is_file() or not os.access(binary, os.X_OK):
                raise ValueError(tid + ": native binary absent")
            if not fixture.is_file() or not fixture.name.endswith(".sens"):
                raise ValueError(tid + ": physical SENS input absent")
            if (record["executor"] != str(binary)
                    or record["executor_sha256"] != digest(binary.read_bytes())
                    or record["fixture_sha256"] != digest(fixture.read_bytes())
                    or not version or record["package_version"] != version.group(1)
                    or record["reproduce"] != shlex.join([str(binary), str(fixture)])):
                raise ValueError(tid + ": binary/input/version/command proof mismatch")
            for key in ("expected_sha256", "actual_sha256", "stdout_sha256", "stderr_sha256"):
                if not DIGEST.fullmatch(str(record.get(key, ""))):
                    raise ValueError(tid + ": missing " + key)
            if record.get("mode") == "positive" and record.get("exit_code") != 0:
                raise ValueError(tid + ": positive process had nonzero exit")
            if record.get("mode") == "negative" and record.get("exit_code") == 0:
                raise ValueError(tid + ": negative process was admitted")
            if record.get("mode") not in ("positive", "negative"):
                raise ValueError(tid + ": unknown verdict mode")
        except (KeyError, ValueError, TypeError, OSError) as exc:
            problems.append(str(exc))
    for required in args.require:
        if required not in seen:
            problems.append("missing native SENS process for " + required)
    if problems:
        for problem in problems:
            print("::error::UNINFORMATIVE-EXECUTOR " + problem)
        return 1
    print("NATIVE_EXECUTOR_RATCHET_PASS verified=" + str(len(seen)) +
          " required=" + ",".join(args.require))
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


def audit(args):
    """Escalate unclassified RED at 24h; honor valid named quarantine until expiry."""
    raw = json.loads(Path(args.manifest).read_text())
    problematic = []
    for item in raw.get("cases", []):
        test_id = item.get("test_id", "UNNAMED")
        owner = item.get("owner", "UNASSIGNED")
        try:
            seen = parse_time(item["first_seen_at"])
        except (KeyError, ValueError, TypeError):
            problematic.append(test_id + ":MISSING_FIRST_SEEN owner=" + owner)
            continue
        stamp = item.get("stamp")
        if stamp == "UNCLASSIFIED":
            if now() - seen > dt.timedelta(hours=CLASSIFICATION_HOURS):
                problematic.append(test_id + ":ESCALATE_24H_UNCLASSIFIED owner=" + owner)
            else:
                problematic.append(test_id + ":UNCLASSIFIED_RED owner=" + owner)
        elif stamp == "REGRESSION":
            problematic.append(test_id + ":REGRESSION_BLOCKER owner=" + owner)
        if stamp in {"TRANSITIONAL", "FLAKE"}:
            try:
                if parse_time(item["expires_at"]) <= now():
                    problematic.append(test_id + ":EXPIRED_QUARANTINE owner=" + owner)
            except (KeyError, ValueError, TypeError):
                problematic.append(test_id + ":MISSING_QUARANTINE_EXPIRY owner=" + owner)
    try:
        validate_manifest(raw)
    except (ValueError, TypeError) as exc:
        problematic.append("INVALID_MANIFEST:" + str(exc))
    for issue in problematic:
        print("::error::" + issue)
    if problematic:
        return 1
    print("PASS named red registry: count=" + str(len(raw["cases"])))
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
    p.add_argument("--expect-error-substring")
    p.add_argument("--executor-report-file")
    p.add_argument("command", nargs=argparse.REMAINDER)
    e = sub.add_parser("scan-executors")
    e.add_argument("--report-file", required=True)
    e.add_argument("--require", action="append", required=True)
    c = sub.add_parser("scan")
    c.add_argument("--manifest", default="knowledge/red-test-quarantine.json")
    c.add_argument("--report-file", required=True)
    c.add_argument("--allow-empty", action="store_true")
    sub.add_parser("self-test")
    a = sub.add_parser("audit")
    a.add_argument("--manifest", default="knowledge/red-test-quarantine.json")
    args = parser.parse_args()
    try:
        return {"run": run, "scan": scan, "scan-executors": scan_executors, "audit": audit, "self-test": lambda a: self_test()}[args.action](args)
    except (OSError, ValueError, RuntimeError) as exc:
        print("UNINFORMATIVE-OUTPUT diagnostic transport error: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
