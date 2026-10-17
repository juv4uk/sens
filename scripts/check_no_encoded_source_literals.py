#!/usr/bin/env python3
"""Reject machine/domain word literals newly added to textual Lisp sources.

Decimal values remain valid in the human projection and are lowered by T5M.
The gate checks every changed Lisp path in a Git range (or the working-tree
diff by default), while allowing the repository's pre-existing migration
corpus to be removed incrementally rather than making unrelated edits fail.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple


class Finding(NamedTuple):
    line: int
    column: int
    token: str
    reason: str


ENCODED_WORD = re.compile(
    r"(?<![\w#])#(?:d\d+:[01]+|b[01]+|q2:[01]+(?:/[01]+)?)",
    re.IGNORECASE,
)
NUMBER = r"[+-]?(?:\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?)"
NUMERIC_CALL_HEAD = re.compile(rf"\(\s*({NUMBER})(?=\s|\)|$)")


def _mask_comments_and_strings(source: str) -> str:
    """Keep offsets/newlines while removing comments and string contents."""
    out = list(source)
    in_string = False
    escaped = False
    in_comment = False
    for index, char in enumerate(source):
        if in_comment:
            if char == "\n":
                in_comment = False
            else:
                out[index] = " "
            continue
        if in_string:
            if char != "\n":
                out[index] = " "
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == ";":
            out[index] = " "
            in_comment = True
        elif char == '"':
            out[index] = " "
            in_string = True
    return "".join(out)


def find_forbidden_literals(source: str) -> list[Finding]:
    """Find raw typed-wire spellings and numeric call heads in Lisp code.

    A decimal number in argument/data position (for example ``(сума 235)``)
    is a human-projection value, not a domain-word literal, and is allowed.
    """
    code = _mask_comments_and_strings(source)
    findings: list[Finding] = []
    for match in ENCODED_WORD.finditer(code):
        line = code.count("\n", 0, match.start()) + 1
        column = match.start() - code.rfind("\n", 0, match.start())
        findings.append(Finding(line, column, match.group(), "encoded domain/wire word"))
    for match in NUMERIC_CALL_HEAD.finditer(code):
        start = match.start(1)
        line = code.count("\n", 0, start) + 1
        column = start - code.rfind("\n", 0, start)
        findings.append(Finding(line, column, match.group(1), "numeric function/opcode head"))
    return sorted(findings, key=lambda item: (item.line, item.column))


def added_lisp_lines_from_diff(diff: str) -> list[tuple[str, int, str]]:
    """Return added lines and new-file line numbers from a unified Git diff."""
    path: str | None = None
    new_line = 0
    rows: list[tuple[str, int, str]] = []
    hunk = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            continue
        if line.startswith("--- ") or line.startswith("diff --git "):
            continue
        if line.startswith("@@"):
            match = hunk.match(line)
            new_line = int(match.group(1)) if match else 0
            continue
        if line.startswith("+") and not line.startswith("+++"):
            if path is not None and path.endswith(".lisp"):
                rows.append((path, new_line, line[1:]))
            new_line += 1
        elif line.startswith(" "):
            new_line += 1
    return rows


def _git_diff(root: Path, base: str | None) -> str:
    command = ["git", "diff", "--no-ext-diff", "--no-renames", "--unified=0"]
    if base:
        # The caller supplies the exact push-before or PR-base snapshot. Use
        # direct tree comparison: shallow CI checkouts may have no merge-base.
        command.extend([base, "HEAD", "--"])
    else:
        command.extend(["HEAD", "--"])
    command.append("*.lisp")
    return subprocess.run(
        command, cwd=root, check=True, text=True, encoding="utf-8",
        stdout=subprocess.PIPE,
    ).stdout


def check(root: Path, base: str | None = None) -> tuple[int, list[tuple[str, Finding]]]:
    diff = _git_diff(root, base)
    additions: dict[str, set[int]] = {}
    for path, line_number, _source_line in added_lisp_lines_from_diff(diff):
        additions.setdefault(path, set()).add(line_number)

    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", "*.lisp"],
        cwd=root, check=True, text=True, encoding="utf-8",
        stdout=subprocess.PIPE,
    ).stdout.splitlines()
    for path in untracked:
        try:
            line_count = len((root / path).read_text(encoding="utf-8").splitlines())
        except (OSError, UnicodeError) as error:
            raise ValueError(f"cannot read new Lisp source {path}: {error}") from error
        additions[path] = set(range(1, line_count + 1))

    violations: list[tuple[str, Finding]] = []
    for path, added_lines in additions.items():
        source = (root / path).read_text(encoding="utf-8")
        for finding in find_forbidden_literals(source):
            if finding.line in added_lines:
                violations.append((path, finding))
    return sum(map(len, additions.values())), violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base", help="Git base SHA/ref; checks additions from base to HEAD")
    args = parser.parse_args(argv)
    try:
        added_lines, violations = check(args.root, args.base)
        for path, finding in violations:
            print(
                f"{path}:{finding.line}:{finding.column}: forbidden {finding.reason}: "
                f"{finding.token}",
                file=sys.stderr,
            )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"source-literal-guard error: {error}", file=sys.stderr)
        return 2
    if violations:
        print(f"SOURCE_ENCODED_LITERAL_GUARD_FAIL count={len(violations)}", file=sys.stderr)
        return 1
    print(
        "SOURCE_ENCODED_LITERAL_GUARD_PASS "
        f"added_lisp_lines={added_lines} forbidden=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
