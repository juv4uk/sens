#!/usr/bin/env python3
"""Перевірка Git-об'єктів .lisp за українською клавіатурною розкладкою.

Не виконує та не тлумачить SENS. Читає staged/pushed Git-об'єкт, а не
робочу копію, щоб незастейджені зміни не приховували некоректний коміт.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from report_ukr_projection_progress import ALLOWED


def git(*args: str) -> bytes:
    result = subprocess.run(
        ["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        diagnostic = result.stderr.decode("utf-8", "replace").strip()
        raise ValueError(f"git {' '.join(args[:3])}: {diagnostic}")
    return result.stdout


def paths_from_diff(*args: str) -> set[str]:
    raw = git(*args, "--", "*.lisp")
    return {path.decode("utf-8") for path in raw.split(b"\0") if path}


def staged_paths() -> set[str]:
    return paths_from_diff(
        "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMRT"
    )


def modified_paths(base: str, head: str) -> set[str]:
    return paths_from_diff(
        "diff", "--name-only", "-z", "--diff-filter=ACMRT", base, head
    )


def object_bytes(revision: str, path: str) -> bytes:
    if revision == ":":
        entries = git("ls-files", "--stage", "-z", "--", path)
    else:
        entries = git("ls-tree", "-z", revision, "--", path)
    entries = [row for row in entries.split(b"\0") if row]
    if (len(entries) != 1 or
            entries[0].split(b"\t", 1)[-1].decode("utf-8") != path):
        raise ValueError("Git-об'єкт відсутній або неоднозначний")
    mode = entries[0].split(b" ", 1)[0]
    if mode not in (b"100644", b"100755"):
        raise ValueError(
            f"не звичайний файл (Git mode {mode.decode('ascii', 'replace')})"
        )
    spec = f":{path}" if revision == ":" else f"{revision}:{path}"
    return git("show", spec)


def first_bad(data: bytes) -> str | None:
    try:
        source = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        return f"неправильний UTF-8: байт {exc.start + 1}"
    if not source.strip():
        return "порожній файл"
    for index, char in enumerate(source):
        if char not in ALLOWED:
            line = source.count("\n", 0, index) + 1
            column = index - source.rfind("\n", 0, index)
            return f"{line}:{column}: U+{ord(char):04X} {char!r}"
    return None


def validate(paths: set[str], revision: str) -> int:
    failures = 0
    paths = {p for p in paths if p.endswith(".lisp")}
    for path in sorted(paths):
        try:
            issue = first_bad(object_bytes(revision, path))
        except (ValueError, UnicodeError) as exc:
            issue = str(exc)
        if issue:
            failures += 1
            print(
                f"SENS_UKR_KEYBOARD_BLOCK {path}: {issue}", file=sys.stderr
            )
    if failures:
        print(
            f"SENS_UKR_KEYBOARD_FAIL files={failures} scope=changed-lisp",
            file=sys.stderr,
        )
        return 1
    print(f"SENS_UKR_KEYBOARD_PASS files={len(paths)} scope=changed-lisp")
    return 0


def validate_push() -> int:
    for line in sys.stdin:
        fields = line.rstrip("\n").split()
        if len(fields) != 4:
            raise ValueError("пошкоджений pre-push протокол Git")
        _local_ref, local_sha, _remote_ref, remote_sha = fields
        if set(local_sha) == {"0"}:  # видалення ref нічого не додає
            continue
        if set(remote_sha) == {"0"}:
            try:
                base = git(
                    "merge-base", local_sha, "refs/remotes/origin/main"
                ).decode("ascii").strip()
            except ValueError as exc:
                raise ValueError(
                    "новий ref без доступної бази origin/main"
                ) from exc
        else:
            base = remote_sha
        if validate(modified_paths(base, local_sha), local_sha):
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--pre-push", action="store_true")
    mode.add_argument("--paths-from", type=Path)
    mode.add_argument("--range", nargs=2, metavar=("BASE", "HEAD"))
    parser.add_argument("--ref", default="HEAD")
    args = parser.parse_args(argv)
    try:
        if args.staged:
            return validate(staged_paths(), ":")
        if args.pre_push:
            return validate_push()
        if args.range:
            return validate(modified_paths(*args.range), args.range[1])
        if not args.paths_from.is_file():
            raise ValueError("відсутній список змінених Git-файлів")
        names = args.paths_from.read_text(encoding="utf-8").splitlines()
        return validate(set(names), args.ref)
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"SENS_UKR_KEYBOARD_ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
