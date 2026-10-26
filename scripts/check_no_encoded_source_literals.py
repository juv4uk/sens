#!/usr/bin/env python3
"""Reject numeric and encoded literals newly added to executable Lisp sources.

The public projection uses named Ukrainian forms and named D24+ values.
Numeric function heads are distinct from scalar numeric literals so
diagnostics show whether a coordinate or operand leaked into live source.
Comments, strings, explicitly quoted data, canonical domain-table keys,
frozen donor snapshots, and legacy signature metadata are handled as data,
not as executable SENS expressions.
The gate checks changed Lisp lines in a Git range so historical debt can be
removed incrementally without disguising new numeric literals as clean.
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
NUMBER = r"[+-]?(?:\d+(?:/[+-]?\d+)?(?:[.,]\d+)?(?:[eE][+-]?\d+)?)"
NUMERIC_CALL_HEAD = re.compile(rf"\(\s*({NUMBER})(?=\s|\)|$)")

# Domain-table coordinates are declarative keys, not Lisp call heads.
# Exemption is limited to complete canonical rows at their exact file width.
DOMAIN_TABLE_PATH = re.compile(r"^lib/domains/d(?P<width>10|11|[1-9])\.lisp$")
DOMAIN_TOKEN = r'(?:\(\)|"(?:\\.|[^"\\])*"|[^()\s]+)'
DOMAIN_TABLE_ROW = re.compile(
    r"^\s*\((?P<bits>[01]{1,11})\s+"
    + rf"\(ук\s+{DOMAIN_TOKEN}\)\s+"
    + rf"\(укр\s+{DOMAIN_TOKEN}\)\s+"
    + rf"\(san\s+{DOMAIN_TOKEN}\)\s+"
    + rf"\(en\s+{DOMAIN_TOKEN}\)\s+"
    + rf"\(LISP\s+{DOMAIN_TOKEN}\)\s+"
    + rf"\(sym\s+{DOMAIN_TOKEN}\)\)\s*$"
)


def _is_domain_table_key_head(source: str, path: str | Path | None, offset: int) -> bool:
    if path is None:
        return False
    path_match = DOMAIN_TABLE_PATH.fullmatch(Path(path).as_posix())
    if path_match is None:
        return False
    line_start = source.rfind("\n", 0, offset) + 1
    line_end = source.find("\n", offset)
    if line_end < 0:
        line_end = len(source)
    row_match = DOMAIN_TABLE_ROW.fullmatch(source[line_start:line_end].rstrip("\r"))
    return bool(
        row_match
        and len(row_match.group("bits")) == int(path_match.group("width"))
        and line_start + row_match.start("bits") == offset
    )


# Only complete historical signature metadata records (never Lisp calls).
LEGACY_SIGNATURE_PATH = "lib/surface/function-signatures.lisp"
LEGACY_SIGNATURE_ROW = re.compile(
    r'^\s*\((?P<bits>[01]{8})\s+\(kind\s+(?:builtin|syntax|macro)\)\s+'
    r'(?:\(form\s+(?:lambda|define)\)\s+)?'
    r'\(arity\s+(?:[0-9]+|\(at-least\s+[0-9]+\)|\(between\s+[0-9]+\s+[0-9]+\))\)\s+'
    r'\(surfaces\s+(?:stable|admitted)\)\s+'
    r'\(sig\s+"(?:\\.|[^"\\])*"\)\s+'
    r'\(doc\s+"(?:\\.|[^"\\])*"\)\)\s*$'
)


def _is_legacy_signature_key(source: str, path: str | Path | None, offset: int) -> bool:
    if path is None or Path(path).as_posix() != LEGACY_SIGNATURE_PATH:
        return False
    line_start = source.rfind("\n", 0, offset) + 1
    line_end = source.find("\n", offset)
    if line_end < 0:
        line_end = len(source)
    match = LEGACY_SIGNATURE_ROW.fullmatch(source[line_start:line_end].rstrip("\r"))
    return bool(match and line_start + match.start("bits") == offset)

MACHINE_FACT_NUMERIC_PATHS = {
    "lib/machine/encoding/coverage.lisp",
    "lib/machine/encoding/admitted-iclass-index.lisp",
    "lib/machine/dispatch/native-first-coverage.lisp",
}
MACHINE_ISA_FACT_PATH = re.compile(r"^lib/machine/isa/[^/]+\.lisp$")


def _source_line_bounds(source: str, offset: int) -> tuple[int, int]:
    start = source.rfind("\n", 0, offset) + 1
    end = source.find("\n", offset)
    return start, len(source) if end < 0 else end


def _is_domain_table_data_row(source: str, path: str | Path | None, offset: int) -> bool:
    if path is None:
        return False
    path_match = DOMAIN_TABLE_PATH.fullmatch(Path(path).as_posix())
    if path_match is None:
        return False
    start, end = _source_line_bounds(source, offset)
    row = DOMAIN_TABLE_ROW.fullmatch(source[start:end].rstrip("\r"))
    return bool(row and len(row.group("bits")) == int(path_match.group("width")))


def _is_legacy_signature_metadata_row(
    source: str, path: str | Path | None, offset: int,
) -> bool:
    if path is None or Path(path).as_posix() != LEGACY_SIGNATURE_PATH:
        return False
    start, end = _source_line_bounds(source, offset)
    return LEGACY_SIGNATURE_ROW.fullmatch(source[start:end].rstrip("\r")) is not None


CONFORMANCE_PATH = "tests/fixtures/conformance.lisp"
# Fixture records store executable source as strings and tier as record metadata.
# Only the numeric value of the explicit (tier . N) field is metadata; numbers
# elsewhere in this file must still be checked by the live-source guard.
CONFORMANCE_TIER_VALUE = re.compile(
    r'^\\s*\\(\\(expr \\. "(?:\\\\.|[^"\\\\])*".*?'
    r'\\(tier \\. (?P<value>[0-9]+)\\)'
)


def _is_conformance_tier_metadata(
    source: str, path: str | Path | None, offset: int,
) -> bool:
    if path is None or Path(path).as_posix() != CONFORMANCE_PATH:
        return False
    start, end = _source_line_bounds(source, offset)
    line = source[start:end].rstrip("\\r")
    match = CONFORMANCE_TIER_VALUE.match(line)
    return bool(match and start + match.start("value") == offset)


def _is_numeric_data_exemption(source: str, path: str | Path | None, offset: int) -> bool:
    if path is None:
        return False
    relative = Path(path).as_posix()
    return bool(
        _is_domain_table_data_row(source, relative, offset)
        or _is_legacy_signature_metadata_row(source, relative, offset)
        or _is_frozen_source_snapshot(relative)
        or _is_conformance_tier_metadata(source, relative, offset)
        or relative in MACHINE_FACT_NUMERIC_PATHS
        or MACHINE_ISA_FACT_PATH.fullmatch(relative)
    )


# Frozen donor snapshots: content is byte-pinned by the filename's Git blob
# hash (knowledge/d10-source-snapshots/<sha>.lisp). They are immutable evidence,
# not live code, and cannot be edited to satisfy the live-code ban -- the donor
# checker asserts sha1(content) == filename, so any edit breaks it.
FROZEN_SNAPSHOT_PATH = re.compile(r"^knowledge/d10-source-snapshots/[0-9a-f]{40}\.lisp$")


def _is_frozen_source_snapshot(path: str | Path | None) -> bool:
    return path is not None and FROZEN_SNAPSHOT_PATH.fullmatch(Path(path).as_posix()) is not None


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


def _quoted_data_numeric_head_offsets(code: str) -> set[int]:
    """Return every numeric atom inside an explicit D3 QUOTE operand.

    A numeric atom in quoted data is inert. Only the first operand of the
    Ukrainian QUOTE form is data; extra operands remain executable.
    """
    quoted: set[int] = set()
    stack: list[list] = []
    for match in re.finditer(r"\(|\)|[^\s()]+", code):
        token = match.group()
        if token == "(":
            parent = stack[-1] if stack else None
            inside_data = bool(parent and (
                parent[0] or (parent[1] in ("як-є", "001", "quote", "QUOTE") and parent[2] == 1)
            ))
            if parent:
                parent[2] += 1
            stack.append([inside_data, None, 0])
        elif token == ")":
            if stack:
                stack.pop()
        else:
            frame = stack[-1] if stack else None
            if frame is None:
                continue
            in_data = frame[0] or (
                frame[1] in ("як-є", "001", "quote", "QUOTE") and frame[2] == 1
            )
            if in_data and re.fullmatch(NUMBER, token):
                quoted.add(match.start())
            if frame[2] == 0:
                frame[1] = token
            frame[2] += 1
    return quoted

def find_forbidden_literals(source: str, path: str | Path | None = None) -> list[Finding]:
    """Find raw typed-wire spellings, numeric call heads and scalar literals."""
    code = _mask_comments_and_strings(source)
    findings: list[Finding] = []
    for match in ENCODED_WORD.finditer(code):
        line = code.count("\n", 0, match.start()) + 1
        column = match.start() - code.rfind("\n", 0, match.start())
        findings.append(Finding(line, column, match.group(), "encoded domain/wire word"))
    quoted_numeric_heads = _quoted_data_numeric_head_offsets(code)
    numeric_heads = {match.start(1): match for match in NUMERIC_CALL_HEAD.finditer(code)}
    # Ban numeric atoms in live source, not merely numeric function heads.
    # A numeric call head gets the more specific diagnostic below.
    for match in re.finditer(r"[^\s()]+", code):
        token = match.group()
        start = match.start()
        if not re.fullmatch(NUMBER, token):
            continue
        # Numeric atoms anywhere in a human program are forbidden, including
        # atoms inside QUOTE/як-є data. Only actual executable call heads below
        # receive the more specific head diagnostic.
        if start in numeric_heads and start not in quoted_numeric_heads:
            continue
        if _is_numeric_data_exemption(source, path, start):
            continue
        line = code.count("\n", 0, start) + 1
        column = start - code.rfind("\n", 0, start)
        findings.append(Finding(line, column, token, "numeric source literal"))
    for start, match in numeric_heads.items():
        if start in quoted_numeric_heads:
            continue
        if (_is_domain_table_key_head(source, path, start)
                or _is_legacy_signature_key(source, path, start)
                or _is_frozen_source_snapshot(path)):
            continue
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



def paired_replacement_lines_from_diff(diff: str) -> dict[tuple[str, int], int]:
    """Pair old/new lines only within equal-size contiguous Git edit blocks.

    New files, line reflows and unmatched additions are never exempt.
    """
    path: str | None = None
    pairs: dict[tuple[str, int], int] = {}
    removed: list[int] = []
    added: list[int] = []
    old_line = new_line = 0
    hunk = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")

    def flush() -> None:
        if path is not None and len(removed) == len(added):
            for before, after in zip(removed, added):
                pairs[(path, after)] = before
        removed.clear()
        added.clear()

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            flush()
            path = None
        elif line.startswith("+++ b/"):
            flush()
            path = line[6:] if line[6:].endswith(".lisp") else None
        elif line.startswith("--- "):
            continue
        elif line.startswith("@@"):
            flush()
            match = hunk.match(line)
            if match is None:
                path = None
            else:
                old_line, new_line = map(int, match.groups())
        elif line.startswith("-"):
            removed.append(old_line)
            old_line += 1
        elif line.startswith("+"):
            added.append(new_line)
            new_line += 1
        elif line.startswith(" "):
            flush()
            old_line += 1
            new_line += 1
    flush()
    return pairs


def _base_encoded_tokens_by_line(
    root: Path, base: str | None, path: str,
) -> dict[int, list[str]]:
    """Look up actual old CODE tokens, with full string/comment context."""
    try:
        previous = subprocess.run(
            ["git", "show", f"{base or 'HEAD'}:{path}"],
            cwd=root, check=True, text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
    except (OSError, UnicodeError, subprocess.CalledProcessError):
        return {}
    tokens: dict[int, list[str]] = {}
    for finding in find_forbidden_literals(previous, path=path):
        if finding.reason == "encoded domain/wire word":
            tokens.setdefault(finding.line, []).append(finding.token)
    return tokens




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

    # A projected call head can share a line with an UNCHANGED D24 operand.
    # Admit only the same ordered code tokens verified in a paired Git-base row.
    paired = paired_replacement_lines_from_diff(diff)
    violations: list[tuple[str, Finding]] = []
    for path, added_lines in additions.items():
        source = (root / path).read_text(encoding="utf-8")
        findings = find_forbidden_literals(source, path=path)
        current_encoded: dict[int, list[str]] = {}
        for item in findings:
            if item.reason == "encoded domain/wire word":
                current_encoded.setdefault(item.line, []).append(item.token)
        needs_base = any(
            item.line in added_lines
            and item.reason == "encoded domain/wire word"
            and (path, item.line) in paired
            for item in findings
        )
        previous_encoded = (
            _base_encoded_tokens_by_line(root, base, path) if needs_base else {}
        )
        for finding in findings:
            if finding.line not in added_lines:
                continue
            old_line = paired.get((path, finding.line))
            if (
                finding.reason == "encoded domain/wire word"
                and old_line is not None
                and previous_encoded.get(old_line)
                and previous_encoded[old_line] == current_encoded.get(finding.line)
            ):
                # No new typed token: still reject new/changed encoded words,
                # numeric heads, missing base rows, and multiline quoted data.
                continue
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
