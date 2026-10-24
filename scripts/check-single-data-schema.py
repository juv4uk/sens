#!/usr/bin/env python3
"""Механічний контроль однієї кореневої Lisp-схеми; не оракул мови SENS.

0 — рівно одна коренева форма DATA; 1 — не доведено (скерувати до SENS);
2 — некоректний виклик. Невідомий reader-синтаксис не стає DATA_ONLY.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCHEMAS = frozenset({
    "silent-fallback-inventory", "ft-2", "uk-surface-audit-2",
    "uk-sa-coverage", "machine-profile-1", "machine-domain-profile-3",
})
MAX_BYTES = 1048576


def is_single_data_schema(source: str, expected: str) -> bool:
    if "\x00" in source or source.startswith("\ufeff"):
        return False
    depth = 0
    roots = 0
    root_name = None
    token = ""
    need_root = False
    in_string = False
    escape = False
    in_comment = False

    def finish_token() -> bool:
        nonlocal token, need_root, root_name
        if not token:
            return True
        if token[0] in ("#", "'", chr(96), ",", "|", "\\"):
            return False  # Reader-конструкція: не здогадуватися про семантику.
        if need_root:
            if token != expected:
                return False
            root_name = token
            need_root = False
        token = ""
        return True

    for ch in source:
        if in_comment:
            if ch == "\n":
                in_comment = False
            continue
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch in " \t\r\n\v\f":
            if not finish_token():
                return False
            continue
        if ch == ";":
            if not finish_token():
                return False
            in_comment = True
            continue
        if ch == '"':
            if not finish_token() or need_root or depth == 0:
                return False
            in_string = True
            continue
        if ch == "(":
            if not finish_token() or need_root:
                return False
            if depth == 0:
                if roots:
                    return False
                roots += 1
                need_root = True
            depth += 1
            continue
        if ch == ")":
            if not finish_token() or depth == 0 or need_root:
                return False
            depth -= 1
            continue
        if depth == 0:
            return False
        token += ch
        if len(token) > 65536:
            return False
    return (not in_string and not escape and not need_root
            and finish_token() and depth == 0 and roots == 1
            and root_name == expected)


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in SCHEMAS:
        print("SENS_SCHEMA_CLASSIFIER_INVALID_ARGUMENT", file=sys.stderr)
        return 2
    path = Path(argv[2])
    if path.is_symlink() or not path.is_file():
        return 1
    try:
        if path.stat().st_size > MAX_BYTES:
            return 1
        raw = path.read_bytes()
        if len(raw) > MAX_BYTES:
            return 1
        return 0 if is_single_data_schema(raw.decode("utf-8"), argv[1]) else 1
    except (OSError, UnicodeError, ValueError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
