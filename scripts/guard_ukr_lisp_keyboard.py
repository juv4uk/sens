#!/usr/bin/env python3
"""Перевірка Git-об'єктів .lisp за українською клавіатурною розкладкою.

Не виконує та не тлумачить SENS. Читає staged/pushed Git-об'єкт, а не
робочу копію, щоб незастейджені зміни не приховували некоректний коміт.
"""
from __future__ import annotations

import argparse
import re
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


def ensure_remote_revision(revision: str, remote_ref: str) -> None:
    """Fetch a just-advertised push base when this clone has not seen it yet."""
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{revision}^{{commit}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if probe.returncode == 0:
        return

    try:
        fetched = subprocess.run(
            ["git", "fetch", "--no-tags", "origin", remote_ref],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=20,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(
            f"не вдалося за 20 с отримати push-базу {remote_ref}"
        ) from exc
    if fetched.returncode:
        detail = fetched.stderr.decode("utf-8", "replace").strip()
        raise ValueError(
            f"не вдалося отримати push-базу {remote_ref}: {detail}"
        )

    try:
        git("cat-file", "-e", f"{revision}^{{commit}}")
    except ValueError as exc:
        raise ValueError(
            f"push-база {revision} відсутня після bounded fetch {remote_ref}"
        ) from exc


def _mask_exempt(source: str) -> str:
    """Маскувати те, що не є кодом укр-проєкції, зберігаючи довжину:
    - коментарі `;` і вкладені `#| |#` (коментарі НЕ кодуються у носій — див.
      strip_comments у scripts/migrate-three-pass.py, тож у Д7 їх не перевіряємо);
    - дані D7 у цитатах `(як-є …)` (вміст фактів може бути латиницею);
    - зовнішні URL (історичні джерела).
    """
    chars = list(source)

    def blank(start: int, end: int) -> None:
        for i in range(start, end):
            if chars[i] != "\n":
                chars[i] = " "

    # 1) Коментарі — не код і не носій: ; до кінця рядка, вкладені #| |#,
    #    зі збереженням рядків і лапок (дзеркало strip_comments мінтера).
    n = len(chars)
    i = 0
    state = "normal"
    depth = 0
    while i < n:
        ch = chars[i]
        if state == "string":
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == '"':
                state = "normal"
            i += 1
            continue
        if state == "line":
            if ch == "\n":
                state = "normal"
            else:
                chars[i] = " "
            i += 1
            continue
        if state == "block":
            if source.startswith("#|", i):
                depth += 1
                chars[i] = " "
                chars[i + 1] = " "
                i += 2
                continue
            if source.startswith("|#", i):
                depth -= 1
                chars[i] = " "
                chars[i + 1] = " "
                i += 2
                if depth == 0:
                    state = "normal"
                continue
            if ch != "\n":
                chars[i] = " "
            i += 1
            continue
        if ch == '"':
            state = "string"
            i += 1
            continue
        if ch == ";":
            chars[i] = " "
            state = "line"
            i += 1
            continue
        if source.startswith("#|", i):
            chars[i] = " "
            chars[i + 1] = " "
            state = "block"
            depth = 1
            i += 2
            continue
        i += 1

    masked = "".join(chars)

    # 2) (як-є …) з балансуванням дужок
    i = 0
    while True:
        j = masked.find("(як-є", i)
        if j == -1:
            break
        depth2 = 0
        k = j
        while k < n:
            if masked[k] == "(":
                depth2 += 1
            elif masked[k] == ")":
                depth2 -= 1
                if depth2 == 0:
                    k += 1
                    break
            k += 1
        blank(j, k)
        i = k

    # 3) URL
    for m in re.finditer(r"https?://\S+", masked):
        blank(m.start(), m.end())
    return "".join(chars)


def first_bad(data: bytes) -> str | None:
    try:
        source = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        return f"неправильний UTF-8: байт {exc.start + 1}"
    if not source.strip():
        return "порожній файл"
    for index, char in enumerate(_mask_exempt(source)):
        if char not in ALLOWED:
            line = source.count("\n", 0, index) + 1
            column = index - source.rfind("\n", 0, index)
            return f"{line}:{column}: U+{ord(char):04X} {char!r}"
    return None


# Шари із законною латиницею: декларативні доменні таблиці (колонки
# san/en/LISP/sym не перейменовуються), машинний шар (назви ISA/регістрів),
# згенеровані та поверхневі файли. Це не програми укр-проєкції.
EXCLUDED_PREFIXES = (
    "lib/domains/",
    "lib/machine/",
    "lib/generated/",
    "lib/surface/",
    "docs/",
    "evidence/",
    "contracts/",
    "experiments/",
    "knowledge/",
    "research/",
)
# Не програми укр-проєкції: статус, контракти, згенеровані зведення.
EXCLUDED_FILES = frozenset((
    "my-lisp-constitution.lisp",
    "ecosystem-status.lisp",
    "memory-layout-contract.lisp",
    "machine-lowering-boundary.lisp",
    "repo.lisp",
    "tasks.lisp",
    "language-contract.lisp",
    "typed-buffer-proposal.lisp",
    "contract-consumers.lisp",
))


def validate(paths: set[str], revision: str) -> int:
    failures = 0
    paths = {
        p for p in paths
        if p.endswith(".lisp")
        and not p.startswith(EXCLUDED_PREFIXES)
        and p not in EXCLUDED_FILES
    }
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
        _local_ref, local_sha, remote_ref, remote_sha = fields
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
            ensure_remote_revision(base, remote_ref)
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
