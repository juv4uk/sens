#!/usr/bin/env python3
"""CI_GLUE_NO_SEMANTICS — lexical sterility guard for production Zig sources.

This checker does NOT interpret SENS, recognize callable functions, or accept
an executable program. It only prevents forbidden historical vocabulary and
host-text identity coercions inside the Zig transport implementation.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ZIG_ROOTS = (Path("research/zig-codecs"), Path("zig"))
FORBIDDEN = (
    re.compile(r"(?i)\b(?:sid|sens)[_-]?8\b"),
    re.compile(r"(?i)\b(?:legacy|historical|decimal)\b"),
    re.compile(r"(?i)\b(?:parseint|parseunsigned|atoi|strtol|fromdecimal|asdecimal)\b"),
)


def violations(path: Path, contents: str) -> list[str]:
    findings: list[str] = []
    for number, line in enumerate(contents.splitlines(), 1):
        for pattern in FORBIDDEN:
            match = pattern.search(line)
            if match:
                findings.append(f"{path}:{number}: forbidden Zig transport vocabulary {match.group()!r}")
    return findings


def scan(root: Path = ROOT) -> list[str]:
    files = sorted(
        p for relative in ZIG_ROOTS
        if (root / relative).is_dir()
        for p in (root / relative).rglob("*.zig")
        if p.is_file()
    )
    if not files:
        return ["no Zig transport sources found: cannot confirm cleanroom"]
    errors: list[str] = []
    for path in files:
        errors.extend(violations(path.relative_to(root), path.read_text(encoding="utf-8")))
    return errors


def self_test() -> None:
    assert not violations(Path("sample.zig"), "// physical length is transport metadata")
    assert violations(Path("sample.zig"), "const SID8 = 0;")
    assert violations(Path("sample.zig"), "// legacy code")
    assert violations(Path("sample.zig"), "parseInt(bytes)")
    assert violations(Path("sample.zig"), "const Sens_8 = 1;")
    assert violations(Path("sample.zig"), "// decimal bridge")
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
    print("ZIG_CLEANROOM_LEXICAL_PASS: production Zig source and comments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
