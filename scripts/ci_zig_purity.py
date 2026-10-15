#!/usr/bin/env python3
"""Check every tracked Zig source for retired pre-D8 semantic identities.

No restriction on what Zig can implement. The SENS ladder owns all semantic
identity; any Zig file may handle execution, compilation or physical transport
but may never import old flat eight-bit identity or historical dispatch.
Ratified current D8 began 2026-10-06 (#3960), not in the historical flat era.
"""
import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

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


class ZigSourceBlocked(ValueError):
    """Tracked Zig path cannot be trusted as a regular checkout source."""


def tracked_source_bytes(root: Path, relative: Path) -> bytes:
    """Reject missing Zig files and links, including links in parent paths.

    Scanning a link target would inspect bytes not belonging to the tracked
    Zig source path and could produce a misleading purity PASS.
    """
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ZigSourceBlocked("invalid-zig-source-path")
    source = root
    for part in relative.parts:
        source = source / part
        if source.is_symlink():
            raise ZigSourceBlocked("linked-zig-source")
    if not source.is_file():
        raise ZigSourceBlocked("missing-or-nonregular-zig-source")
    before = source.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ZigSourceBlocked("missing-or-nonregular-zig-source")
    # A hardlink passes is_file() and is_symlink() but aliases bytes that
    # can be modified through an untracked path. Do not certify that inode.
    if before.st_nlink != 1:
        raise ZigSourceBlocked("hardlinked-zig-source")
    with source.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        content = stream.read()
    after = source.lstat()
    if source.is_symlink():
        raise ZigSourceBlocked("linked-zig-source")
    # Bind the receipt to one unchanged regular inode, not a path swapped
    # between the symlink preflight and content read.
    if (not stat.S_ISREG(opened.st_mode) or not stat.S_ISREG(after.st_mode)
            or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
            or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
            or before.st_size != len(content) or after.st_size != len(content)
            or before.st_mtime_ns != after.st_mtime_ns
            or opened.st_nlink != 1 or after.st_nlink != 1):
        raise ZigSourceBlocked("changed-zig-source")
    return content


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
        if not scan(path, bad):
            raise AssertionError(f"undetected retired identifier: {bad!r}")
    for good in ('const std = @import("std");',
                 'const evaluator = @import("../../compiler/eval.zig");',
                 "D8:10000000 differs from D9:010000000",
                 "// historical Rust comparison using lib/core.lisp",
                 "// physical byte parity, SENS exact-domain semantic tests"):
        if scan(path, good):
            raise AssertionError(f"unexpected role restriction: {good!r}")
    # A tracked Zig symlink must never scan external/untracked target bytes.
    with TemporaryDirectory(prefix="sens-zig-purity-") as temp:
        root = Path(temp)
        regular = root / "valid.zig"
        regular.write_bytes(b"pub const width: u8 = 7;\n")
        if tracked_source_bytes(root, Path("valid.zig")) != regular.read_bytes():
            raise AssertionError("normal tracked Zig file became unreadable")
        (root / "linked.zig").symlink_to(regular)
        outside = root / "untracked-external-source"
        outside.write_bytes(b"ContaminatedSens8Alias")
        (root / "hardlinked.zig").hardlink_to(outside)
        (root / "source-dir").mkdir()
        (root / "source-dir" / "nested.zig").write_bytes(b"pub const x = 1;\n")
        (root / "linked-dir").symlink_to(root / "source-dir", target_is_directory=True)
        for relative, expected in (
            ("linked.zig", "linked-zig-source"),
            ("hardlinked.zig", "hardlinked-zig-source"),
            ("linked-dir/nested.zig", "linked-zig-source"),
            ("absent.zig", "missing-or-nonregular-zig-source"),
        ):
            try:
                tracked_source_bytes(root, Path(relative))
            except ZigSourceBlocked as exc:
                if str(exc) != expected:
                    raise AssertionError(f"wrong fail-closed reason for {relative}: {exc}") from exc
            else:
                raise AssertionError(f"tracked Zig source bypassed fail-closed: {relative}")
    print("ZIG_PURITY_SELF_TEST_PASS: retired IDs rejected; regular/symlink/hardlink/missing controls passed")


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
        digest.update(path.as_posix().encode("utf-8") + b"\0")
        try:
            raw_bytes = tracked_source_bytes(ROOT, path)
        except (ZigSourceBlocked, OSError) as exc:
            # Source unavailable: the receipt records a FAIL, not target bytes.
            digest.update(b"\0")
            failures.append({
                "path": str(path), "line": 0,
                "reason": str(exc) if isinstance(exc, ZigSourceBlocked) else "unreadable-zig-source",
                "marker": "",
            })
            continue
        digest.update(raw_bytes + b"\0")
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
