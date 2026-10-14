#!/usr/bin/env python3
"""CI_GLUE_NO_SEMANTICS — fail-closed lexical + dependency scan of Zig.

Every git-tracked Zig file, including future paths, is checked.  This tool
NEVER determines SENS domain meaning, execution admission or truth.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TRANSPORT_ROOT = Path("research/zig-codecs")
ALLOWED_BUILTINS = frozenset(("std", "builtin", "root"))

# Read the whole source, including comments and literals.  Exact D8/W8 widths
# are valid mechanical coordinates; an old identity must not be smuggled
# through a compound/CamelCase identifier or alternative punctuation.
FORBIDDEN = (
    re.compile(r"(?i)(?:sid|sens|function|func)[\s._/-]*8(?![0-9])"),
    re.compile(r"(?i)(?:legacy|historical)"),
    re.compile(r"(?i)(?:decimal|parseint|parseunsigned|atoi|strtol|fromdecimal|asdecimal)"),
    re.compile(r"(?i)(?:\.lisp\b|crates/sens|contracts/|knowledge/|research/framed3/)"),
    re.compile(r"(?i)(?:old|flat)[\s._/-]*(?:opcode|registry|dispatch|identity)"),
    re.compile(r"@cImport\s*\("),
)
IMPORT = re.compile(r'@import\s*\(\s*"([^"]+)"\s*\)')
EMBED = re.compile(r'@embedFile\s*\(\s*"([^"]+)"\s*\)')
IMPORT_CALL = re.compile(r"@import\s*\(")
EMBED_CALL = re.compile(r"@embedFile\s*\(")
SINGLE_LITERAL = re.compile(r'\s*"([^"\\]*)"\s*\)')



def violations(path: Path, contents: str, *, root: Path = ROOT) -> list[str]:
    findings: list[str] = []
    relative_root = (root / TRANSPORT_ROOT).resolve()
    source_path = root / path
    for number, line in enumerate(contents.splitlines(), 1):
        for pattern in FORBIDDEN:
            found = pattern.search(line)
            if found:
                findings.append(
                    f"{path}:{number}: forbidden Zig transport vocabulary {found.group()!r}"
                )
        # Reject any compile-time concatenation or nonliteral path. A Zig
        # import name must appear as a single visible, auditable string.
        for function, calls in (("@import", IMPORT_CALL), ("@embedFile", EMBED_CALL)):
            for call in calls.finditer(line):
                if SINGLE_LITERAL.match(line[call.end():]) is None:
                    findings.append(
                        f"{path}:{number}: nonliteral {function} forbidden in Zig corridor"
                    )
        for call in IMPORT.finditer(line):
            name = call.group(1)
            if name in ALLOWED_BUILTINS:
                continue
            target = (source_path.parent / name).resolve()
            if not name.endswith(".zig") or not target.is_relative_to(relative_root):
                findings.append(f"{path}:{number}: forbidden Zig import {name!r}")
        # Embedded documents are a hidden route for importing old registries.
        # Embeds inside the Zig-only subtree remain allowed for physical tests.
        for call in EMBED.finditer(line):
            name = call.group(1)
            target = (source_path.parent / name).resolve()
            if not target.is_relative_to(relative_root):
                findings.append(f"{path}:{number}: forbidden Zig embed {name!r}")
    return findings


def scan(root: Path = ROOT) -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "ls-files", "-z", "--", "*.zig"],
            cwd=root,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        return [f"cannot enumerate tracked Zig sources: {exc}"]
    paths = sorted({Path(value.decode("utf-8")) for value in output.split(b"\0") if value})
    if not paths:
        return ["no tracked Zig sources found: cannot confirm cleanroom"]
    allowed = (root / TRANSPORT_ROOT).resolve()
    errors: list[str] = []
    for path in paths:
        physical = root / path
        if not physical.resolve().is_relative_to(allowed):
            errors.append(f"{path}:0: Zig source outside transport subtree")
        if physical.is_symlink():
            errors.append(f"{path}:0: symlinked Zig source is not allowed")
            continue
        try:
            contents = physical.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{path}:0: unreadable Zig source: {exc}")
            continue
        errors.extend(violations(path, contents, root=root))
    return errors


def self_test() -> None:
    good = (
        '// D8:00000001 is not D9:000000001',
        'const std = @import("std");',
        'const t5 = @import("../t5.zig");',
        'const a = DomainWord(8).init(0b0000_0001);',
        'const bits = @embedFile("../t5.zig");',
    )
    bad = (
        "const SID8 = 0;",
        "const KernelSid8Alias = 0;",
        'const RootSens_8Stage = 0;',
        "const Function8Old = 0;",
        "// legacy code",
        "// historically supported",
        "parseInt(bytes)",
        "const old_registry = 8;",
        'const bytes = @embedFile("../../../contracts/core.lisp");',
        'const foreign = @import("../../../crates/sens/src/lib.zig");',
        "const x = @cImport({});",
        'const src = "lib/core.lisp";',
        'const exploit = @import("crates/" ++ "sens.zig");',
        'const hidden = @embedFile(prefix ++ "registry");',
        'const escape = @import("../\\x2e/engine.zig");',
    )
    path = Path("research/zig-codecs/t5/sterile/probe.zig")
    for src in good:
        assert not violations(path, src), f"false positive for {src!r}"
    for src in bad:
        assert violations(path, src), f"failed to reject {src!r}"
    print("CLEANROOM_LEXICAL_GUARD_SELFTEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = scan()
    if errors:
        for error in errors:
            print(f"ZIG_CLEANROOM_RED: {error}", file=sys.stderr)
        return 1
    print("ZIG_CLEANROOM_LEXICAL_PASS: all tracked Zig sources, comments, imports, embeds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
