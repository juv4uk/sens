#!/usr/bin/env python3
"""Static Lisp paren-balance guard.

Catches the class of defect where a `.lisp` file is committed with an unclosed
(or over-closed) list. Such a file still fails at load time inside the language
runtime, but only in whatever lane happens to load it — so the failure surfaces
late, as an unnamed `exit code 1` in a large gate step.

This guard is deliberately dumb and fast: it does not parse Lisp, it only counts
parens while skipping `;` comments and "..." strings (with backslash escapes).
That is exactly the check that would have caught the #4375 projection syntax
repair before a wasted CI run.

Usage:
    python3 scripts/check-lisp-paren-balance.py [--root .] [--paths lib]

Exit code 0 when every scanned file is balanced, 1 otherwise.
"""
from __future__ import annotations

import argparse
import pathlib


def scan(text: str) -> tuple[bool, int, int]:
    """Return (balanced, final_depth, first_line_where_depth_goes_negative).

    Skips `;` comments and "..." strings (honouring backslash escapes).
    """
    depth = 0
    line = 1
    first_neg = 0
    in_str = False
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        else:
            if c == ";":
                j = text.find("\n", i)
                i = n if j < 0 else j  # loop counts the newline
                continue
            if c == '"':
                in_str = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth < 0 and not first_neg:
                    first_neg = line
        i += 1
    return (depth == 0 and not in_str), depth, first_neg


def main() -> int:
    ap = argparse.ArgumentParser(description="Static Lisp paren-balance guard.")
    ap.add_argument("--root", default=".", help="repository root")
    ap.add_argument("--paths", nargs="*", default=["lib"],
                    help="files or directories (relative to --root) to scan")
    args = ap.parse_args()

    root = pathlib.Path(args.root).resolve()
    files: list[pathlib.Path] = []
    for p in args.paths:
        base = root / p
        if base.is_file():
            files.append(base)
        elif base.is_dir():
            files.extend(sorted(base.rglob("*.lisp")))

    bad: list[tuple[pathlib.Path, str, int, int]] = []
    integrity_errors: list[tuple[pathlib.Path, str]] = []
    required_lowering_forms = (
        "(00001001 x86-lower-add-u64-forms",
        "(00001001 x86-lower-cons-car-u64-forms",
        "(00001001 x86-call-semantic-car-u64",
        "(00001001 x86-encode-current-eq-cond-u64",
    )
    lowering_relative_path = pathlib.Path("lib/machine/lowering/semantic-x86-64.lisp")
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            bad.append((f, "invalid utf-8", 0, 0))
            continue
        ok, depth, neg = scan(text)
        if not ok:
            bad.append((f, "", depth, neg))

        # Paren balance alone accepts a tiny but formally balanced placeholder.
        # The active native composition authority must keep its required entry
        # points and cannot be replaced by an in-progress merge marker.
        try:
            rel = f.resolve().relative_to(root).as_posix()
        except ValueError:
            rel = ""
        if rel == lowering_relative_path.as_posix():
            if len(text.encode("utf-8")) < 20_000:
                integrity_errors.append((f, f"critical source unexpectedly short ({len(text.encode('utf-8'))} bytes)"))
            for marker in ("PLACEHOLDER", "RESTORED_FULL_FILE", "LOAD_FROM_FILE:", "/tmp/sem_join.lisp"):
                if marker in text:
                    integrity_errors.append((f, f"forbidden intermediate marker {marker!r}"))
            for form in required_lowering_forms:
                if form not in text:
                    integrity_errors.append((f, f"missing required lowering entry point {form}"))
            if "00100010" in text:
                integrity_errors.append((f, "legacy W8 EQ head remains in the current exact-D3 lowering projection"))

    print(f"lisp-paren-balance: scanned {len(files)} file(s) under {args.paths}")
    for f, why, depth, neg in bad:
        try:
            rel = f.relative_to(root)
        except ValueError:
            rel = f
        if why:
            detail = why
        else:
            detail = f"final depth {depth}"
            if neg:
                detail += f", first ')' below zero at line {neg}"
        print(f"  UNBALANCED {rel}: {detail}")

    for f, reason in integrity_errors:
        try:
            rel = f.relative_to(root)
        except ValueError:
            rel = f
        print(f"  INTEGRITY-FAIL {rel}: {reason}")

    if bad or integrity_errors:
        print(f"lisp-paren-balance: FAIL ({len(bad)} syntax / {len(integrity_errors)} integrity)")
        return 1
    print("lisp-paren-balance: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
