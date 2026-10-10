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
import re
import subprocess


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



# Git-owned machine layer contract.  These are structural lower bounds, not
# immutable blob pins: reviewed changes may extend the existing definitions.
# They must be checked against the committed HEAD blob, not only the checkout.
MACHINE_SOURCES = {
    "lib/machine/admission/x86-64.lisp": (
        30_000, 15, (
            "x86-admitted-instruction-patterns",
            "x86-admission-pattern-match?",
            "x86-first-unadmitted-form",
            "x86-admitted-program?",
            "x86-encode-admitted-program-or-reject",
        ),
    ),
    "lib/machine/encoding/x86-64.lisp": (
        50_000, 200, (
            "x86-reg-code",
            "x86-disp8-byte",
            "x86-imm32-bytes",
            "x86-rel32-bytes",
            "x86-encode-mov-mem-disp8-r64",
            "x86-encode-program",
        ),
    ),
    "lib/machine/lowering/semantic-x86-64.lisp": (
        20_000, 30, (
            "x86-lower-add-u64-forms",
            "x86-lower-cons-car-u64-forms",
            "x86-call-semantic-car-u64",
            "x86-encode-current-eq-cond-u64",
        ),
    ),
}
MACHINE_MARKERS = (
    "SEE_LOCAL_FIX_", "LOAD_FROM_FILE:", "RESTORED_FULL_FILE",
    "PLACEHOLDER", "; see next",
)
MACHINE_DEF = re.compile(r"(?m)^[ \t]*\(00001001[ \t]+")


def machine_blob_errors(path: str, payload: bytes) -> list[str]:
    """Check *bytes* of a machine source independently of its filename/diff."""
    minimum_bytes, minimum_defs, entry_points = MACHINE_SOURCES[path]
    problems: list[str] = []
    if len(payload) < minimum_bytes:
        problems.append(f"blob too short: {len(payload)} < {minimum_bytes} bytes")
    if b"\x00" in payload:
        problems.append("NUL byte in source blob")
    try:
        source = payload.decode("utf-8")
    except UnicodeDecodeError:
        return problems + ["blob is not UTF-8"]
    for marker in MACHINE_MARKERS:
        if marker in source:
            problems.append(f"forbidden producer marker {marker!r}")
    definitions = len(MACHINE_DEF.findall(source))
    if definitions < minimum_defs:
        problems.append(f"too few top-level definitions: {definitions} < {minimum_defs}")
    for name in entry_points:
        # Must be an active, top-level definition, not a name in a comment.
        pattern = rf"(?m)^[ \t]*\(00001001[ \t]+{re.escape(name)}(?=[\s()])"
        if re.search(pattern, source) is None:
            problems.append(f"missing executable entry point {name}")
    valid, depth, first_negative = scan(source)
    if not valid:
        problems.append(f"unbalanced machine blob: depth={depth}, negative-line={first_negative}")
    return problems


def machine_head_blob(root: pathlib.Path, path: str) -> tuple[bytes | None, str]:
    """Read actual HEAD:path bytes from Git, failing closed on missing/non-blobs."""
    command = ["git", "-C", str(root)]
    try:
        top = subprocess.run(command + ["rev-parse", "--show-toplevel"],
                             capture_output=True, check=False)
        if top.returncode != 0:
            return None, "Git root unavailable"
        if pathlib.Path(top.stdout.decode("utf-8").strip()).resolve() != root:
            return None, "requested root is not repository root"
        object_path = f"HEAD:{path}"
        kind = subprocess.run(command + ["cat-file", "-t", object_path],
                              capture_output=True, check=False)
        if kind.returncode != 0 or kind.stdout.strip() != b"blob":
            return None, f"missing or non-blob Git HEAD object {object_path}"
        blob = subprocess.run(command + ["show", object_path],
                              capture_output=True, check=False)
        if blob.returncode != 0:
            return None, f"cannot read Git HEAD blob {object_path}"
        return blob.stdout, ""
    except (FileNotFoundError, OSError, UnicodeDecodeError) as exc:
        return None, f"Git HEAD read failed: {exc}"


def machine_mutation_errors(path: str, original: bytes) -> list[str]:
    """Negative witnesses: each poisoned but balanced blob MUST be rejected."""
    broken = (
        ("local-pointer", b"SEE_LOCAL_FIX_B4j\n"),
        ("tmp-pointer", b"LOAD_FROM_FILE:/tmp/sem_join.lisp\n"),
        ("fake-restore", b"; RESTORED_FULL_FILE_SEE_CD5C362\n"),
        ("balanced-stub", b"(00001001 stub (00001000 (x) x))\n"),
        # Keep intact size, definitions and parentheses; only add a marker.
        ("full-size-marker", original + b"\n; SEE_LOCAL_FIX_B4j\n"),
    )
    missed: list[str] = []
    for label, payload in broken:
        if not machine_blob_errors(path, payload):
            missed.append(f"mutation {label} was accepted")
    # Preserve size and balance; remove exactly one required entry point.
    name = MACHINE_SOURCES[path][2][0]
    needle = ("(00001001 " + name).encode("utf-8")
    if needle not in original:
        missed.append(f"cannot build missing-entry-point mutation for {name}")
    elif not machine_blob_errors(path, original.replace(needle, b"(00001001 invalid-mutant", 1)):
        missed.append(f"missing-entry-point mutation was accepted for {name}")
    return missed


def main() -> int:
    ap = argparse.ArgumentParser(description="Static Lisp paren-balance guard.")
    ap.add_argument("--root", default=".", help="repository root")
    ap.add_argument("--paths", nargs="*", default=["lib"],
                    help="files or directories (relative to --root) to scan")
    ap.add_argument("--self-test", action="store_true",
                    help="verify rejection of balanced stubs and producer markers")
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
    encoder_relative_path = pathlib.Path("lib/machine/encoding/x86-64.lisp")
    required_encoder_forms = (
        "(00001001 x86-reg-code",
        "(00001001 x86-disp8-byte",
        "(00001001 x86-imm32-bytes",
        "(00001001 x86-rel32-bytes",
        "(00001001 x86-encode-mov-mem-disp8-r64",
        "(00001001 x86-encode-program",
    )
    forbidden_source_markers = (
        "PLACEHOLDER",
        "RESTORED_FULL_FILE",
        "LOAD_FROM_FILE:",
        "/tmp/sem_join.lisp",
        "see next",
    )
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

        if rel == encoder_relative_path.as_posix():
            byte_length = len(text.encode("utf-8"))
            if byte_length < 50_000:
                integrity_errors.append((f, f"critical encoder source unexpectedly short ({byte_length} bytes)"))
            for marker in forbidden_source_markers:
                if marker in text:
                    integrity_errors.append((f, f"forbidden intermediate marker {marker!r}"))
            for form in required_encoder_forms:
                if form not in text:
                    integrity_errors.append((f, f"missing required encoder entry point {form}"))

    # Critical inputs are mandatory even if --paths selects a smaller subtree.
    # Validate BOTH actual disk bytes and Git HEAD bytes. A producer cannot
    # stage a pointer and leave a complete implementation only in /tmp.
    for rel in MACHINE_SOURCES:
        disk = root / rel
        if not disk.is_file() or disk.is_symlink():
            integrity_errors.append((disk, "missing, non-file or symlink machine source"))
        else:
            try:
                disk_payload = disk.read_bytes()
                for problem in machine_blob_errors(rel, disk_payload):
                    integrity_errors.append((disk, f"checkout: {problem}"))
            except OSError as exc:
                integrity_errors.append((disk, f"cannot read checkout source: {exc}"))
        blob, error = machine_head_blob(root, rel)
        if blob is None:
            integrity_errors.append((disk, f"Git HEAD: {error}"))
        else:
            for problem in machine_blob_errors(rel, blob):
                integrity_errors.append((disk, f"Git HEAD: {problem}"))
            if args.self_test:
                for problem in machine_mutation_errors(rel, blob):
                    integrity_errors.append((disk, f"mutation witness: {problem}"))
                if not machine_blob_errors(rel, blob):
                    print(f"  MUTATIONS-REJECTED {rel}: 6 negative witnesses")

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
