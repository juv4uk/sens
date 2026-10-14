#!/usr/bin/env python3
"""CI_GLUE_NO_SEMANTICS: fail-closed purity audit of EVERY tracked Zig source."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIG_ROOT = ROOT / "research" / "zig-codecs"
BANNED = {
    "retired-eight-bit-identity": re.compile(
        r"(?i)(?:(?:sens|sid|function|func)[\s._/-]*8(?![0-9])|(?<![a-z0-9])w[\s._/-]*8(?![0-9]))"),
    "retired-language-surface": re.compile(
        r"(?i)(?<![a-z0-9])(?:my[\s._/-]*lisp|core[\s._/-]*1)\b"),
    "historical-authority": re.compile(r"(?i)\b(?:legacy|historical)\b"),
    "retired-dispatch": re.compile(
        r"(?i)\b(?:old|flat)[\s._-]*(?:opcode|registry|dispatch|identity)\b"),
    "semantic-source-dependency": re.compile(
        r"(?i)(?:\.lisp\b|crates/sens|research/framed3/rust_codec|contracts/|knowledge/)"),
}
IMPORT = re.compile(r'@import\s*\(\s*"([^"]+)"\s*\)')


def scan(path, source):
    violations = []
    for line_no, line in enumerate(source.splitlines(), 1):
        for reason, expr in BANNED.items():
            match = expr.search(line)
            if match:
                violations.append({
                    "path": str(path), "line": line_no,
                    "reason": reason, "marker": match.group(0),
                })
        for match in IMPORT.finditer(line):
            name = match.group(1)
            if name in ("std", "builtin", "root"):
                continue
            dest = (ROOT / path).parent.joinpath(name).resolve()
            if not name.endswith(".zig") or not dest.is_relative_to(ZIG_ROOT.resolve()):
                violations.append({
                    "path": str(path), "line": line_no,
                    "reason": "foreign-import", "marker": name,
                })
    return violations


def self_test():
    path = Path("research/zig-codecs/selftest.zig")
    for bad in ("Sens8", "sid_8", "SID-8", "Function8", "W8",
                "KernelSid8", "ContaminatedSens8Alias", "Function8Old",
                "my-lisp", "core1", "historical opcode",
                "legacy registry", "flat dispatch", "lib/core.lisp",
                'const x = @import("../../lib/law.zig");'):
        assert scan(path, bad), f"guard failed to detect {bad!r}"
    for clean in ('const std = @import("std");',
                  'const t5 = @import("t5/t5.zig");',
                  "D8:10000000 is not D9:010000000",
                  "T5 / F3C / E1 exact-width physical wire"):
        assert not scan(path, clean), f"false positive: {clean!r}"
    print("ZIG_PURITY_SELF_TEST_PASS")


def audit(report):
    output = subprocess.check_output(
        ["git", "ls-files", "-z", "--", "*.zig"], cwd=ROOT)
    paths = sorted({Path(p.decode("utf-8")) for p in output.split(b"\0") if p})
    violations = []
    digest = hashlib.sha256()
    if not paths:
        violations.append({"path": "*", "line": 0,
                           "reason": "missing-zig-source", "marker": ""})
    for path in paths:
        if not (ROOT / path).resolve().is_relative_to(ZIG_ROOT.resolve()):
            violations.append({"path": str(path), "line": 0,
                               "reason": "outside-transport-module", "marker": str(path)})
        data = (ROOT / path).read_bytes()
        digest.update(path.as_posix().encode() + b"\0" + data + b"\0")
        try:
            violations.extend(scan(path, data.decode("utf-8")))
        except UnicodeDecodeError:
            violations.append({"path": str(path), "line": 0,
                               "reason": "non-utf8-zig", "marker": ""})
    evidence = {
        "schema": "sens-zig-clean-reference/v1",
        "authority": "CI_GLUE_NO_SEMANTICS",
        "scope": "all-tracked-zig",
        "semantic_authority": "SENS_ONLY",
        "zig_files_scanned": len(paths),
        "zig_source_sha256": digest.hexdigest(),
        "contamination_count": len(violations),
        "violations": violations,
    }
    if report:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    for item in violations:
        print(f"::error file={item['path']},line={item['line']}::"
              f"ZIG_PURITY_FAIL reason={item['reason']} marker={item['marker']}")
    state = "PASS" if not violations else "FAIL"
    print(f"ZIG_PURITY_{state} files={len(paths)} contamination={len(violations)} "
          f"source_sha256={digest.hexdigest()} authority=SENS")
    return 0 if not violations else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        raise SystemExit(audit(args.report))
