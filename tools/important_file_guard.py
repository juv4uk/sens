#!/usr/bin/env python3
"""Temporary foreign Git-delta boundary for SENS-owned important files.

Only new paths are restricted: historical files remain migration debt.
No assert, shell pipeline, silent fallback, or third-party dependency.
"""
from __future__ import annotations

import re
import tempfile
import subprocess
import sys
from pathlib import Path, PurePosixPath

IMPORTANT = ("lib/", "knowledge/", "witnesses/")
NATIVE = (".lisp", ".sens")
CENSUS_PATH = "tools/foreign-census.lisp"
ENTRY = re.compile(
    r'^\(foreign-tool "(tools/[^"\\]+\.py)" '
    r'\(independence_status foreign\) '
    r'\(migration_plan "([^"\\]+)"\)\)$'
)


def census_entries(source: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, raw in enumerate(source.splitlines(), start=1):
        row = raw.strip()
        if not row or row.startswith(";"):
            continue
        match = ENTRY.fullmatch(row)
        if match is None:
            raise ValueError(f"{CENSUS_PATH}:{line_number}: INVALID_CENSUS_ENTRY")
        path, plan = match.groups()
        if path in entries:
            raise ValueError(f"{CENSUS_PATH}:{line_number}: DUPLICATE_FOREIGN_ENTRY: {path}")
        if not plan.strip() or len(plan.strip()) < 15:
            raise ValueError(f"{CENSUS_PATH}:{line_number}: MISSING_MIGRATION_PLAN: {path}")
        entries[path] = plan
    return entries


def introduced_paths(status_stream: bytes) -> list[str]:
    """Parse git diff --name-status -z --diff-filter=ARC, incl. rename targets."""
    items = status_stream.split(b"\0")
    if items[-1] != b"":
        raise ValueError("UNTERMINATED_GIT_NAME_STATUS")
    items.pop()
    result: list[str] = []
    i = 0
    while i < len(items):
        status = items[i].decode("ascii", "strict")
        i += 1
        if status == "A":
            if i >= len(items):
                raise ValueError("TRUNCATED_ADDITION")
            path = items[i]
            i += 1
        elif status.startswith(("R", "C")) and status[1:].isdigit():
            if i + 1 >= len(items):
                raise ValueError("TRUNCATED_RENAME_OR_COPY")
            path = items[i + 1]
            i += 2
        else:
            raise ValueError(f"UNEXPECTED_CHANGE_STATUS: {status}")
        result.append(path.decode("utf-8", "surrogateescape"))
    return result


def violations(paths: list[str], entries: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        parts = PurePosixPath(path).parts
        if not path or path.startswith("/") or "\\" in path or ".." in parts:
            errors.append(f"BAD_GIT_PATH: {path!r}")
            continue
        if path.startswith(IMPORTANT) and not path.endswith(NATIVE):
            errors.append(f"IMPORTANT_FILE_MUST_BE_SENS: {path}")
        if path.endswith(".py"):
            if not path.startswith("tools/"):
                errors.append(f"NEW_PYTHON_OUTSIDE_TOOLS: {path}")
            elif path not in entries:
                errors.append(f"FOREIGN_PYTHON_WITHOUT_CENSUS_AND_PLAN: {path}")
    return errors




def parse_tree_mode(raw: bytes, expected_path: str) -> str:
    """Validate one exact Git tree entry, never a guessed path or truncated record."""
    if raw.count(b"\0") != 1 or not raw.endswith(b"\0"):
        raise ValueError(f"INVALID_GIT_TREE_RECORD: {expected_path}")
    line = raw[:-1]
    if line.count(b"\t") != 1:
        raise ValueError(f"INVALID_GIT_TREE_FIELDS: {expected_path}")
    metadata, encoded_path = line.split(b"\t", 1)
    fields = metadata.split(b" ")
    if len(fields) != 3:
        raise ValueError(f"INVALID_GIT_TREE_METADATA: {expected_path}")
    mode, kind, oid = fields
    actual_path = encoded_path.decode("utf-8", "strict")
    if actual_path != expected_path:
        raise ValueError(f"GIT_TREE_PATH_MISMATCH: expected={expected_path} actual={actual_path}")
    if not re.fullmatch(rb"[0-9a-f]{40,64}", oid):
        raise ValueError(f"INVALID_GIT_OBJECT_ID: {expected_path}")
    if kind not in (b"blob", b"commit", b"tree"):
        raise ValueError(f"INVALID_GIT_OBJECT_TYPE: {expected_path}")
    return mode.decode("ascii", "strict") + ":" + kind.decode("ascii", "strict")


def new_source_mode_failures(paths: list[str], head: str, cwd: str | None = None) -> list[str]:
    """A suffix cannot admit Git symlink 120000 or submodule/gitlink 160000."""
    errors: list[str] = []
    for path in paths:
        if not (path.startswith(IMPORTANT) or (path.startswith("tools/") and path.endswith(".py"))):
            continue
        record = subprocess.run(
            ["git", "ls-tree", "-z", "--full-tree", head, "--", path],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd,
        )
        if record.returncode != 0:
            raise ValueError(f"GIT_TREE_LOOKUP_FAILED: {path}: " +
                             record.stderr.decode("utf-8", "replace"))
        mode = parse_tree_mode(record.stdout, path)
        if mode not in ("100644:blob", "100755:blob"):
            errors.append(f"NON_REGULAR_NEW_SOURCE: {path}: Git mode={mode}")
    return errors

def verify_case(label: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise RuntimeError(f"GUARD_SELFTEST_FAIL {label}: actual={actual!r} expected={expected!r}")


def self_test() -> None:
    entries = census_entries(
        '(foreign-tool "tools/important_file_guard.py" '
        '(independence_status foreign) '
        '(migration_plan "Replace with direct executable T5 SENS guardian once bounded path ingress is proven"))\n'
    )
    verify_case("native", violations(["lib/a.lisp", "knowledge/a.sens", "witnesses/приклад.lisp"], entries), [])
    verify_case("old_non_native_becomes_new", violations(["knowledge/new.json"], entries),
                ["IMPORTANT_FILE_MUST_BE_SENS: knowledge/new.json"])
    verify_case("fasl_not_exempt", violations(["lib/other.lisp.fasl"], entries),
                ["IMPORTANT_FILE_MUST_BE_SENS: lib/other.lisp.fasl"])
    verify_case("python_foreign", violations(["tools/important_file_guard.py"], entries), [])
    verify_case("python_without_census", violations(["tools/other.py"], entries),
                ["FOREIGN_PYTHON_WITHOUT_CENSUS_AND_PLAN: tools/other.py"])
    verify_case("python_elsewhere", violations(["scripts/other.py"], entries),
                ["NEW_PYTHON_OUTSIDE_TOOLS: scripts/other.py"])
    verify_case("rename", introduced_paths(b"R100\0docs/legacy.json\0knowledge/new.json\0"),
                ["knowledge/new.json"])
    verify_case("add_null", introduced_paths(b"A\0lib/a.lisp\0A\0tools/important_file_guard.py\0"),
                ["lib/a.lisp", "tools/important_file_guard.py"])
    try:
        census_entries('(foreign-tool "tools/b.py" (independence_status foreign) (migration_plan "short"))')
    except ValueError:
        pass
    else:
        raise RuntimeError("GUARD_SELFTEST_FAIL missing migration plan must be rejected")
    object_id = b"a" * 40
    verify_case("regular_blob", parse_tree_mode(
        b"100644 blob " + object_id + b"\tlib/example.sens\0", "lib/example.sens"), "100644:blob")
    verify_case("symlink_must_not_be_source", parse_tree_mode(
        b"120000 blob " + object_id + b"\tlib/example.sens\0", "lib/example.sens"), "120000:blob")
    verify_case("gitlink_must_not_be_source", parse_tree_mode(
        b"160000 commit " + object_id + b"\tlib/example.sens\0", "lib/example.sens"), "160000:commit")
    for invalid in (
        b"120000 blob " + object_id + b"\tlib/example.sens",
        b"100644 blob " + object_id + b"\tlib/different.sens\0",
    ):
        try:
            parse_tree_mode(invalid, "lib/example.sens")
        except ValueError:
            continue
        raise RuntimeError("GUARD_SELFTEST_FAIL: invalid Git tree evidence admitted")
    # End-to-end mode witness: Git itself must report a real symlink,
    # not only a handcrafted ls-tree row. No mutation of the user's repo.
    with tempfile.TemporaryDirectory(prefix="sens-file-guard-") as scratch:
        repo_root = Path(scratch)
        (repo_root / "lib").mkdir()
        (repo_root / "lib" / "good.sens").write_bytes(b"\x00")
        (repo_root / "lib" / "shadow.sens").symlink_to("good.sens")
        for arguments in (
            ["git", "init", "-q", scratch],
            ["git", "-C", scratch, "add", "lib/good.sens", "lib/shadow.sens"],
        ):
            subprocess.run(arguments, check=True, capture_output=True)
        tree = subprocess.run(
            ["git", "-C", scratch, "write-tree"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        verify_case("git_regular_allowed",
                    new_source_mode_failures(["lib/good.sens"], tree, cwd=scratch), [])
        verify_case("git_symlink_rejected",
                    new_source_mode_failures(["lib/shadow.sens"], tree, cwd=scratch),
                    ["NON_REGULAR_NEW_SOURCE: lib/shadow.sens: Git mode=120000:blob"])
    print("FILE_GUARD_SELFTEST_OK: actual Git tree regular/symlink parity")
    print("FILE_GUARD_SELFTEST_OK: regular/symlink/gitlink/truncated/path-substitution")
    print("FILE_GUARD_SELFTEST_OK: 9 existing mechanical checks")


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        self_test()
        return 0
    if len(argv) != 2:
        print("NAMED_FAIL: EXPECTED_BASE_AND_HEAD_SHA", file=sys.stderr)
        return 2
    base, head = argv
    if not re.fullmatch(r"[0-9a-f]{40}", base) or not re.fullmatch(r"[0-9a-f]{40}", head):
        print("NAMED_FAIL: INVALID_GIT_COMMIT_SHA", file=sys.stderr)
        return 2
    with open(CENSUS_PATH, encoding="utf-8") as source:
        entries = census_entries(source.read())
    completed = subprocess.run(
        ["git", "diff", "--name-status", "-z", "--diff-filter=ARC", "--find-renames", base, head],
        check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        print("NAMED_FAIL: GIT_DIFF_FAILED: " + completed.stderr.decode("utf-8", "replace"), file=sys.stderr)
        return 2
    new_paths = introduced_paths(completed.stdout)
    failures = violations(new_paths, entries)
    failures.extend(new_source_mode_failures(new_paths, head))
    print(f"FILE_GUARD_AUDIT introduced={len(new_paths)} foreign_census={len(entries)}")
    for failure in failures:
        print("NAMED_FAIL: " + failure, file=sys.stderr)
    if failures:
        return 1
    print("FILE_GUARD_PASS: all introduced protected paths are .lisp/.sens; Python debt is registered")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (OSError, ValueError, UnicodeError) as error:
        print(f"NAMED_FAIL: GUARD_INPUT_ERROR: {error}", file=sys.stderr)
        sys.exit(2)
