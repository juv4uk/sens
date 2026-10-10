#!/usr/bin/env python3
"""Temporary foreign Git-delta adapter for the SENS-owned file policy.

No assert, no shell pipeline, no silent fallback. Git provides untrusted path
metadata only; SENS owns the policy and must replace this adapter after the
physical-T5 positive/negative witness has independent hosted parity.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import PurePosixPath

IMPORTANT = ("lib/", "knowledge/", "witnesses/")
NATIVE_EXTENSIONS = (".lisp", ".sens")
CENSUS_PATH = "knowledge/foreign-tools-census.lisp"
CENSUS_SCHEMA = "(schema . foreign-tools-census/1)"
ENTRY = re.compile(
    r'^\(\(path\s+\.\s*"([^"\\]+)"\)\s*'
    r'\(independence_status\s+\.\s*foreign\)\s*'
    r'\(owner-issue\s+\.\s*"#([0-9]+)"\)\s*'
    r'\(migration_plan\s+\.\s*"([^"\\]+)"\)\s*\)$'
)
PATH_FIELD = re.compile(r'\(path\s+\.\s*"([^"\\]+)"\)')


class PolicyError(ValueError):
    """A named, fail-closed input or evidence error."""


def fail(message: str) -> None:
    raise PolicyError(message)


def command(*args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        fail("GIT_COMMAND_FAILED: " + " ".join(args) + ": " + detail)
    return result.stdout


def nul_paths(data: bytes) -> list[str]:
    """Decode a Git -z stream strictly; an incomplete stream is never PASS."""
    if not data:
        return []
    if not data.endswith(b"\x00"):
        fail("UNTERMINATED_GIT_NUL_STREAM")
    parts = data[:-1].split(b"\x00")
    if any(not part for part in parts):
        fail("EMPTY_FIELD_IN_GIT_NUL_STREAM")
    try:
        return [part.decode("utf-8", "strict") for part in parts]
    except UnicodeDecodeError as error:
        fail("GIT_PATH_ENCODING_INVALID: " + str(error))


def census_entries(source: str) -> dict[str, str]:
    if CENSUS_SCHEMA not in source:
        fail("CENSUS_SCHEMA_MISSING: " + CENSUS_PATH)
    start = source.find("(new-foreign-tools .")
    end = source.find("(new-python-without-entry . blocked)", start)
    if start < 0 or end < 0 or end <= start:
        fail("CENSUS_FOREIGN_TOOL_SECTION_MISSING: " + CENSUS_PATH)

    section = source[start:end]
    rows = [
        line.strip()
        for line in section.splitlines()
        if "(path ." in line
    ]
    if not rows:
        fail("CENSUS_HAS_NO_FOREIGN_TOOL_ROWS: " + CENSUS_PATH)

    entries: dict[str, str] = {}
    for line_number, row in enumerate(rows, start=1):
        match = ENTRY.fullmatch(row)
        if match is None:
            fail(f"CENSUS_ENTRY_INVALID: {CENSUS_PATH}:row={line_number}")
        path, issue_number, plan = match.groups()
        if path in entries:
            fail("CENSUS_DUPLICATE_PATH: " + path)
        if not path.startswith("tools/") or not path.endswith(".py"):
            fail("CENSUS_PATH_NOT_ALLOWED: " + path)
        if not issue_number.isdigit():
            fail("CENSUS_OWNER_ISSUE_MISSING: " + path)
        plan = plan.strip()
        if len(plan) < 60 or not any(term in plan.lower() for term in ("sens", "t5")):
            fail("CENSUS_MIGRATION_PLAN_MISSING_OR_VAGUE: " + path)
        entries[path] = plan

    declared_rows = PATH_FIELD.findall(section)
    if len(declared_rows) != len(entries):
        fail("CENSUS_DUPLICATE_OR_MALFORMED_ROW: " + CENSUS_PATH)
    return entries


def introduced_paths(status_stream: bytes) -> list[str]:
    """Parse --name-status -z and inspect add/rename/copy destinations."""
    if status_stream and not status_stream.endswith(b"\x00"):
        fail("UNTERMINATED_GIT_NAME_STATUS")
    parts = status_stream[:-1].split(b"\x00") if status_stream else []
    paths: list[str] = []
    index = 0
    while index < len(parts):
        try:
            status = parts[index].decode("ascii", "strict")
        except UnicodeDecodeError as error:
            fail("GIT_STATUS_ENCODING_INVALID: " + str(error))
        index += 1
        if status == "A":
            if index >= len(parts):
                fail("GIT_STATUS_TRUNCATED_ADDITION")
            destination = parts[index]
            index += 1
        elif status.startswith(("R", "C")) and status[1:].isdigit():
            if index + 1 >= len(parts):
                fail("GIT_STATUS_TRUNCATED_RENAME_OR_COPY")
            destination = parts[index + 1]
            index += 2
        else:
            fail("GIT_STATUS_UNEXPECTED_CHANGE: " + status)
        try:
            paths.append(destination.decode("utf-8", "strict"))
        except UnicodeDecodeError as error:
            fail("GIT_PATH_ENCODING_INVALID: " + str(error))
    return paths


def path_is_canonical(path: str) -> bool:
    parts = path.split("/")
    return (
        bool(path)
        and not path.startswith("/")
        and "\\" not in path
        and all(part not in ("", ".", "..") for part in parts)
    )


def violations(paths: list[str], entries: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        if not path_is_canonical(path):
            errors.append("BAD_GIT_PATH: " + repr(path))
            continue
        if path.startswith(IMPORTANT) and not path.endswith(NATIVE_EXTENSIONS):
            errors.append("IMPORTANT_FILE_MUST_BE_LISP_OR_SENS: " + path)
        if path.endswith(".py"):
            if not path.startswith("tools/"):
                errors.append("NEW_PYTHON_OUTSIDE_TOOLS: " + path)
            elif path not in entries:
                errors.append("FOREIGN_PYTHON_WITHOUT_CENSUS_AND_PLAN: " + path)
    return errors


def census_coverage(tracked_tools: list[str], entries: dict[str, str]) -> list[str]:
    errors: list[str] = []
    tracked_python: set[str] = set()
    for path in tracked_tools:
        if not path_is_canonical(path) or not path.startswith("tools/"):
            errors.append("BAD_TRACKED_TOOLS_PATH: " + repr(path))
        elif path.endswith(".py"):
            tracked_python.add(path)
    for path in sorted(tracked_python - entries.keys()):
        errors.append("TRACKED_TOOLS_PYTHON_WITHOUT_CENSUS: " + path)
    for path in sorted(entries.keys() - tracked_python):
        errors.append("CENSUS_PATH_NOT_TRACKED: " + path)
    return errors


def verify_case(label: str, actual: object, expected: object) -> None:
    if actual != expected:
        fail(f"SELF_TEST_FAIL {label}: actual={actual!r} expected={expected!r}")


def catches(callback) -> bool:
    try:
        callback()
    except PolicyError:
        return True
    return False


def sample_census(plan: str | None = None) -> str:
    migration = plan or (
        "Replace mechanical Git path decisions with an executable physical SENS T5 "
        "witness, keep Git only as untrusted transport, prove hosted positive and "
        "negative parity, and remove Python only after that proof."
    )
    return "\n".join((
        "(00001001 *foreign-tools-census*",
        "  (00000001",
        "    ((schema . foreign-tools-census/1)",
        "     (new-foreign-tools .",
        "       (",
        '        ((path . "tools/guard.py") (independence_status . foreign) '
        '(owner-issue . "#5397") (migration_plan . "' + migration + '"))',
        "       ))",
        "     (new-python-without-entry . blocked)))",
    ))


def self_test() -> None:
    entries = census_entries(sample_census())
    verify_case(
        "native_extensions",
        violations(
            ["lib/a.lisp", "lib/a.sens", "knowledge/правило.lisp", "witnesses/proof.sens"],
            entries,
        ),
        [],
    )
    verify_case(
        "new_knowledge_json",
        violations(["knowledge/new.json"], entries),
        ["IMPORTANT_FILE_MUST_BE_LISP_OR_SENS: knowledge/new.json"],
    )
    verify_case(
        "new_lisp_fasl_is_not_native_source",
        violations(["lib/new.lisp.fasl"], entries),
        ["IMPORTANT_FILE_MUST_BE_LISP_OR_SENS: lib/new.lisp.fasl"],
    )
    verify_case(
        "python_outside_tools",
        violations(["scripts/new.py"], entries),
        ["NEW_PYTHON_OUTSIDE_TOOLS: scripts/new.py"],
    )
    verify_case(
        "uncensused_python_in_tools",
        violations(["tools/uncensused.py"], entries),
        ["FOREIGN_PYTHON_WITHOUT_CENSUS_AND_PLAN: tools/uncensused.py"],
    )
    verify_case(
        "tracked_python_must_be_censused",
        census_coverage(["tools/guard.py", "tools/uncensused.py"], entries),
        ["TRACKED_TOOLS_PYTHON_WITHOUT_CENSUS: tools/uncensused.py"],
    )
    verify_case(
        "census_must_match_tracked_tools",
        census_coverage([], entries),
        ["CENSUS_PATH_NOT_TRACKED: tools/guard.py"],
    )
    verify_case(
        "rename_destination",
        introduced_paths(b"R100\x00docs/old.json\x00knowledge/new.json\x00"),
        ["knowledge/new.json"],
    )
    verify_case(
        "copy_destination",
        introduced_paths(b"C100\x00tools/old.py\x00tools/new.py\x00"),
        ["tools/new.py"],
    )
    verify_case("empty_nul_stream", nul_paths(b""), [])
    verify_case("valid_nul_stream", nul_paths(b"tools/a.py\x00"), ["tools/a.py"])
    if not catches(lambda: nul_paths(b"tools/a.py")):
        fail("SELF_TEST_FAIL unterminated_nul_stream_admitted")
    for invalid in (
        "wrong schema",
        "(schema . foreign-tools-census/1) (new-python-without-entry . blocked)",
        sample_census("short plan"),
        sample_census().replace('(independence_status . foreign)', '(independence_status . local)'),
        sample_census().replace('(owner-issue . "#5397")', '(owner-issue . "unknown")'),
        sample_census().replace(
            '     (new-python-without-entry . blocked)))',
            '        ((path . "tools/guard.py") (independence_status . foreign) '
            '(owner-issue . "#5397") (migration_plan . "Replace mechanical Git path '
            'decisions with executable physical SENS T5 proof; retain Git paths only as '
            'untrusted transport, prove hosted positive and negative parity, then remove Python."))\\n'
            '     (new-python-without-entry . blocked)))',
        ),
    ):
        if not catches(lambda invalid=invalid: census_entries(invalid)):
            fail("SELF_TEST_FAIL malformed_census_admitted")
    print("FILE_GUARD_SELFTEST_OK: 13 positive/negative mechanical checks")


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        self_test()
        return 0
    if len(argv) != 2:
        print("NAMED_FAIL: EXPECTED_BASE_AND_HEAD_SHA", file=sys.stderr)
        return 2
    base, head = argv
    for label, sha in (("BASE", base), ("HEAD", head)):
        if not re.fullmatch(r"[0-9a-f]{40}", sha) or set(sha) == {"0"}:
            print("NAMED_FAIL: INVALID_" + label + "_SHA", file=sys.stderr)
            return 2
    try:
        command("cat-file", "-e", f"{base}^{{commit}}")
        command("cat-file", "-e", f"{head}^{{commit}}")
        command("merge-base", "--is-ancestor", base, head)
        with open(CENSUS_PATH, encoding="utf-8") as census_file:
            entries = census_entries(census_file.read())
        changes = command(
            "diff", "--name-status", "-z", "--diff-filter=ACR",
            "--find-renames", "--find-copies", "--find-copies-harder", base, head,
        )
        new_paths = introduced_paths(changes)
        tracked_tools = nul_paths(command("ls-files", "-z", "--", "tools/"))
        errors = violations(new_paths, entries)
        errors.extend(census_coverage(tracked_tools, entries))
        print(f"FILE_GUARD_AUDIT introduced={len(new_paths)} foreign_census={len(entries)}")
        if errors:
            for error in errors:
                print("NAMED_FAIL: " + error, file=sys.stderr)
            return 1
        print("FILE_GUARD_PASS: new important paths are .lisp/.sens; foreign Python is registered")
        return 0
    except (OSError, PolicyError, UnicodeError) as error:
        print("NAMED_FAIL: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
