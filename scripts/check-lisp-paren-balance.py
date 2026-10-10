#!/usr/bin/env python3
"""Static Lisp paren-balance + critical-source integrity guard.

Two defect classes are caught at push time:

1. A `.lisp` file committed with an unclosed (or over-closed) list. Such a file
   still fails at load time inside the language runtime, but only in whatever
   lane happens to load it — so the failure surfaces late, as an unnamed
   `exit code 1` in a large gate step. (This is the #4375 class.)

2. A critical machine-authority source committed as a *formally balanced*
   one-line placeholder. The #5423 forensics proved that
   `lib/machine/{admission,encoding,lowering}/` sources were replaced by
   single-line pointers such as `SEE_LOCAL_FIX_B4j`,
   `LOAD_FROM_FILE:/tmp/sem_join.lisp`, `RESTORED_FULL_FILE_SEE_...`,
   `; PLACEHOLDER` and `; see next`. Paren balance alone accepts those.

The guard is deliberately dumb and fast: it does not parse Lisp, it only
counts parens while skipping `;` comments and "..." strings (with backslash
escapes). On top of that it applies path-specific size / required entry-point
/ forbidden-marker checks to the three critical machine sources.

Usage:
    python3 scripts/check-lisp-paren-balance.py [--root .] [--paths lib]

Exit code 0 when every scanned file is balanced and every critical source is
intact, 1 otherwise.
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


# The native composition authority: three full sources that must never be
# reduced to a pointer. Thresholds are well below the true sizes
# (admission ~42 KiB, encoder ~57 KiB, lowering ~26 KiB) and well above any
# balanced placeholder.
LOWERING = pathlib.Path("lib/machine/lowering/semantic-x86-64.lisp")
ENCODER = pathlib.Path("lib/machine/encoding/x86-64.lisp")
ADMISSION = pathlib.Path("lib/machine/admission/x86-64.lisp")

REQUIRED_LOWERING_FORMS = (
    "(00001001 x86-lower-add-u64-forms",
    "(00001001 x86-lower-cons-car-u64-forms",
    "(00001001 x86-call-semantic-car-u64",
    "(00001001 x86-encode-current-eq-cond-u64",
)
REQUIRED_ENCODER_FORMS = (
    "(00001001 x86-reg-code",
    "(00001001 x86-disp8-byte",
    "(00001001 x86-imm32-bytes",
    "(00001001 x86-rel32-bytes",
    "(00001001 x86-encode-mov-mem-disp8-r64",
    "(00001001 x86-encode-program",
)
REQUIRED_ADMISSION_FORMS = (
    "(00001001 x86-admitted-program?",
    "(00001001 x86-admitted-instruction?",
    "(00001001 x86-first-unadmitted-form",
    "(00001001 x86-encode-admitted-instruction",
    "(00001001 x86-encode-admitted-program-or-reject",
)

# Every marker the #5423 forensics observed being committed in place of real
# content. `SEE_LOCAL_FIX_` and `see next` were the two the old guard missed.
FORBIDDEN_SOURCE_MARKERS = (
    "PLACEHOLDER",
    "SEE_LOCAL_FIX_",
    "RESTORED_FULL_FILE",
    "LOAD_FROM_FILE:",
    "/tmp/sem_join.lisp",
    "see next",
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Static Lisp paren-balance + critical-source guard.")
    ap.add_argument("--root", default=".", help="repository root")
    ap.add_argument("--paths", nargs="*", default=["lib"],
                    help="files or directories (relative to --root) to scan")
    args = ap.parse_args()

    root = pathlib.Path(args.root).resolve()
    files: list[pathlib.Path] = []
    missing_scan_paths: list[pathlib.Path] = []
    for p in args.paths:
        base = root / p
        if base.is_file():
            files.append(base)
        elif base.is_dir():
            files.extend(sorted(base.rglob("*.lisp")))
        else:
            missing_scan_paths.append(base)

    bad: list[tuple[pathlib.Path, str, int, int]] = []
    integrity_errors: list[tuple[pathlib.Path, str]] = []

    for absent in missing_scan_paths:
        integrity_errors.append((absent, "requested scan path is missing or is not a regular file"))

    # A missing critical file must not be treated as an empty successful scan
    # when the whole `lib` tree (the repository default) is being checked.
    if any(pathlib.Path(p).as_posix().rstrip("/") in (".", "lib") for p in args.paths):
        for critical in (LOWERING, ENCODER, ADMISSION):
            candidate = root / critical
            if not candidate.is_file():
                integrity_errors.append((candidate, "mandatory machine authority file missing"))
            elif candidate.is_symlink():
                integrity_errors.append((candidate, "mandatory machine authority cannot be a symlink"))

    def check_critical(rel: pathlib.Path, text: str, min_bytes: int,
                       required_forms: tuple[str, ...]) -> None:
        byte_length = len(text.encode("utf-8"))
        if byte_length < min_bytes:
            integrity_errors.append((rel, f"critical source unexpectedly short ({byte_length} bytes)"))
        for marker in FORBIDDEN_SOURCE_MARKERS:
            if marker in text:
                integrity_errors.append((rel, f"forbidden intermediate marker {marker!r}"))
        for form in required_forms:
            if form not in text:
                integrity_errors.append((rel, f"missing required entry point {form}"))

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
        try:
            rel = f.resolve().relative_to(root).as_posix()
        except ValueError:
            rel = ""
        if rel == LOWERING.as_posix():
            check_critical(f, text, 20_000, REQUIRED_LOWERING_FORMS)
            if "00100010" in text:
                integrity_errors.append((f, "legacy W8 EQ head remains in the current exact-D3 lowering projection"))
        elif rel == ENCODER.as_posix():
            check_critical(f, text, 50_000, REQUIRED_ENCODER_FORMS)
        elif rel == ADMISSION.as_posix():
            check_critical(f, text, 20_000, REQUIRED_ADMISSION_FORMS)

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
