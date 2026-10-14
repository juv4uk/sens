#!/usr/bin/env python3
"""CI source-hygiene guard for one Zig reference module, not a language-role ban.

The owner permits any language for any task. Only research/zig-codecs is the
designated clean reference for physical carrier compatibility. Other Zig code
may implement anything; normative domain meaning comes from SENS contracts.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "research" / "zig-codecs"
BANNED = {
    "retired-eight-bit-identity": re.compile(
        r"(?i)(?:(?:sens|sid|function|func)[\s._/-]*8(?![0-9])|(?<![a-z0-9])w[\s._/-]*8(?![0-9]))"
    ),
    "retired-language-surface": re.compile(
        r"(?i)(?<![a-z0-9])(?:my[\s._/-]*lisp|core[\s._/-]*1)\b"
    ),
    "retired-dispatch": re.compile(
        r"(?i)\b(?:old|flat)[\s._-]*(?:opcode|registry|dispatch|identity)\b"
    ),
}


def scan(path, content):
    issues = []
    for line_number, line in enumerate(content.splitlines(), 1):
        for reason, marker in BANNED.items():
            match = marker.search(line)
            if match:
                issues.append({
                    "path": str(path), "line": line_number,
                    "reason": reason, "marker": match.group(0),
                })
    return issues


def self_test():
    path = Path("research/zig-codecs/selftest.zig")
    for bad in ("Sens8", "sid_8", "SID-8", "Function8", "W8",
                "KernelSid8", "ContaminatedSens8Alias", "Function8Old",
                "my-lisp", "core1", "flat dispatch"):
        assert scan(path, bad), f"undetected retired identifier: {bad!r}"
    for good in ('const std = @import("std");',
                 'const evaluator = @import("../../compiler/eval.zig");',
                 "D8:10000000 differs from D9:010000000",
                 "// historical Rust comparison using lib/core.lisp",
                 "// physical byte parity, SENS exact-domain semantic tests"):
        assert not scan(path, good), f"unexpected role restriction: {good!r}"
    print("ZIG_PURITY_SELF_TEST_PASS: retired IDs rejected; imports and language roles unrestricted")


def audit(report_path):
    raw = subprocess.check_output(["git", "ls-files", "-z", "--", "*.zig"], cwd=ROOT)
    tracked = sorted({Path(p.decode("utf-8")) for p in raw.split(b"\0") if p})
    # Owner order 2026-10-14: historical identities must not enter ANY Zig
    # source, regardless of directory or whether Zig handles codegen or IO.
    # No runtime/domain law is inferred from this mechanical source scan.
    scoped = tracked
    failures = []
    digest = hashlib.sha256()
    if not scoped:
        failures.append({
            "path": "*.zig", "line": 0,
            "reason": "missing-reference-module", "marker": "",
        })
    for path in scoped:
        raw_bytes = (ROOT / path).read_bytes()
        digest.update(path.as_posix().encode("utf-8") + b"\0" + raw_bytes + b"\0")
        try:
            failures.extend(scan(path, raw_bytes.decode("utf-8")))
        except UnicodeDecodeError:
            failures.append({
                "path": str(path), "line": 0,
                "reason": "non-utf8-zig-reference", "marker": "",
            })
    record = {
        "schema": "sens-zig-ladder-cleanliness/v3",
        "kind": "source-hygiene-not-semantic-oracle",
        "scope": "all git-tracked *.zig",
        "language_roles_restricted": False,
        "all_tracked_zig_files": len(tracked),
        "reference_zig_files": len([p for p in tracked if (ROOT / p).resolve().is_relative_to(REFERENCE.resolve())]),
        "source_sha256": digest.hexdigest(),
        "contamination_count": len(failures),
        "violations": failures,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    for failure in failures:
        print(f"::error file={failure['path']},line={failure['line']}::"
              f"ZIG_PURITY_FAIL reason={failure['reason']} marker={failure['marker']}")
    status = "PASS" if not failures else "FAIL"
    print(f"ZIG_PURITY_{status} files={len(scoped)} contamination={len(failures)} "
          f"source_sha256={digest.hexdigest()} authority=SENS_CONTRACT roles=UNRESTRICTED")
    return 0 if not failures else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        raise SystemExit(audit(args.report))
