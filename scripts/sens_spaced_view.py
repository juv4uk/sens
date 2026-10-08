#!/usr/bin/env python3
"""#4694 — safe generated ASCII view of REAL physical T5 .sens.

The extensionless file is NEVER an executable, wire format or new semantic
authority. This does not certify Ukrainian source parity or admit historical
programs; it only verifies physical/typed/view identity and the existing Rust
D2 reader when provided.

Commands:
    preview --root . --sens path/name.sens [--reader target/debug/sens-trit]
    verify  --root . --sens path/name.sens --reader target/debug/sens-trit
    stage   --root . --sens path/name.sens --reader target/debug/sens-trit \
            --mirror /tmp/sens-view-stage [--write]
Writes are restricted to a mirror OUTSIDE the source repo, never overwriting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from sens_t5_codec import (
    MAX_FILE_BYTES, SensT5Error, decode_bytes, encode_words, typed_sha256,
)

SCHEMA = "sens-t5-exact-spaced-view/v1"
VIEW = re.compile(rb"[01]{1,9}(?: [01]{1,9})*\n\Z")
MAX_VIEW_BYTES = MAX_FILE_BYTES * 6


class ViewBlocked(ValueError):
    pass


def canonical_view(words: list[str]) -> bytes:
    if not words or any(re.fullmatch(r"[01]{1,9}", x) is None for x in words):
        raise ViewBlocked("VIEW: exact 1..9-bit words required")
    rendered = (" ".join(words) + "\n").encode("ascii")
    if len(rendered) > MAX_VIEW_BYTES:
        raise ViewBlocked("VIEW: exceeds safe output size")
    return rendered


def parse_view(data: bytes) -> list[str]:
    if not isinstance(data, bytes) or not data or len(data) > MAX_VIEW_BYTES:
        raise ViewBlocked("VIEW: require nonempty bounded ASCII bytes")
    if VIEW.fullmatch(data) is None:
        raise ViewBlocked("VIEW: exact ASCII 0/1 words, one space and one final LF required")
    words = data[:-1].decode("ascii").split(" ")
    if canonical_view(words) != data:
        raise ViewBlocked("VIEW: byte-noncanonical projection")
    return words


def checked_path(root: Path, relative: Path, suffix: str | None) -> Path:
    if (relative.is_absolute() or not relative.parts
            or any(part in ("", ".", "..") for part in relative.parts)
            or (suffix is not None and relative.suffix != suffix)):
        raise ViewBlocked("PATH: unsafe or wrong-suffix relative path")
    candidate = root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ViewBlocked("PATH: symlink in source/view path")
    if not candidate.is_file():
        raise ViewBlocked("PATH: missing regular source or target: " + relative.as_posix())
    return candidate


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_d2(reader: Path, physical: Path, canonical: bytes) -> None:
    if not reader.is_file():
        raise ViewBlocked("D2: actual Rust sens-trit reader is required")
    try:
        process = subprocess.run(
            [str(reader), "open", str(physical)], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ViewBlocked("D2: Rust reader could not run: " + str(exc)) from exc
    if process.returncode or process.stderr or process.stdout != canonical:
        raise ViewBlocked("D2: Rust reader rejects exact physical program or word projection")


def inspect(root: Path, rel: Path, *, reader: Path | None = None,
            verify_existing: bool = False) -> tuple[dict, bytes]:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ViewBlocked("PATH: root must be a directory")
    physical_path = checked_path(root, rel, ".sens")
    source_rel = rel.with_suffix(".lisp")
    source_path = checked_path(root, source_rel, ".lisp")
    raw = physical_path.read_bytes()
    try:
        words = decode_bytes(raw)
        encoded = encode_words(words)
    except SensT5Error as exc:
        raise ViewBlocked("T5: " + str(exc)) from exc
    if encoded != raw:
        raise ViewBlocked("T5: noncanonical physical bytes including tail padding")
    rendered = canonical_view(words)
    if parse_view(rendered) != words or encode_words(parse_view(rendered)) != raw:
        raise ViewBlocked("VIEW: exact roundtrip differs from physical T5")
    if reader is not None:
        verify_d2(reader.resolve(strict=True), physical_path, rendered)
    elif verify_existing:
        raise ViewBlocked("D2: existing view verification requires real Rust reader")
    view_rel = rel.with_suffix("")
    if verify_existing:
        view_path = checked_path(root, view_rel, "")
        existing = view_path.read_bytes()
        if parse_view(existing) != words or existing != rendered:
            raise ViewBlocked("VIEW: stale or altered extensionless bytes")
        if encode_words(parse_view(existing)) != raw:
            raise ViewBlocked("VIEW: extensionless projection fails T5 byte parity")
    state = {
        "schema": SCHEMA,
        "status": "VIEW_PARITY_ONLY_NOT_RELEASE" if reader else "PHYSICAL_PREVIEW_NOT_RELEASE",
        "sens": rel.as_posix(),
        "source": source_rel.as_posix(),
        "view": view_rel.as_posix(),
        "source_sha256": sha256(source_path.read_bytes()),
        "physical_sha256": sha256(raw),
        "typed_word_sha256": typed_sha256(words),
        "view_sha256": sha256(rendered),
        "physical_bytes": len(raw),
        "typed_words": len(words),
        "view_bytes": len(rendered),
        "d2_reader": "PASS" if reader else "NOT_CHECKED",
        "source_semantic_oracle": "NOT_VERIFIED",
        "original_executable_migrations_admitted": 0,
        "release_certified": False,
    }
    return state, rendered


def safe_stage(root: Path, mirror: Path, rel: Path, view: bytes) -> Path:
    root = root.resolve(strict=True)
    mirror = mirror.resolve(strict=False)
    if mirror == root or root in mirror.parents:
        raise ViewBlocked("PATH: mirror must be outside repository; never write originals")
    if mirror.exists() and not mirror.is_dir():
        raise ViewBlocked("PATH: stage mirror is not a directory")
    dest = mirror / rel.with_suffix("")
    parent = mirror
    if parent.is_symlink():
        raise ViewBlocked("PATH: stage mirror symlink")
    for part in rel.parent.parts:
        parent = parent / part
        if parent.is_symlink():
            raise ViewBlocked("PATH: symlink stage ancestor")
    parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        raise ViewBlocked("NO_CLOBBER: staged view already exists")
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=".sens-view-",
                                          dir=parent, delete=False) as tmp:
            temp_path = Path(tmp.name)
            tmp.write(view)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.link(temp_path, dest)  # atomically fail if target exists
    except FileExistsError as exc:
        raise ViewBlocked("NO_CLOBBER: staged view already exists") from exc
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preview", "verify", "stage"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--sens", type=Path, required=True,
                        help="same-stem relative .sens path inside --root")
    parser.add_argument("--reader", type=Path,
                        help="actual compiled Rust sens-trit for D2 verification")
    parser.add_argument("--mirror", type=Path,
                        help="external staging root (required for stage)")
    parser.add_argument("--write", action="store_true",
                        help="atomic write-once to --mirror (stage only)")
    parser.add_argument("--report", type=Path,
                        help="optional JSON evidence report; not a semantic certificate")
    args = parser.parse_args(argv)
    try:
        if args.write and args.command != "stage":
            raise ViewBlocked("WRITE: --write valid only with stage")
        if args.command in ("stage", "verify") and args.reader is None:
            raise ViewBlocked("D2: stage/verify requires actual Rust reader")
        if args.command == "stage" and args.mirror is None:
            raise ViewBlocked("PATH: stage needs external --mirror")
        state, view = inspect(args.root, args.sens, reader=args.reader,
                              verify_existing=args.command == "verify")
        if args.command == "stage":
            # Check safety even in preview: never print a misleading would-write path.
            root = args.root.resolve(strict=True)
            mirror = args.mirror.resolve(strict=False)
            if mirror == root or root in mirror.parents:
                raise ViewBlocked("PATH: stage mirror must be outside repo")
            target = mirror / args.sens.with_suffix("")
            state["stage_target"] = str(target)
            if target.exists() or target.is_symlink():
                raise ViewBlocked("NO_CLOBBER: staged view already exists")
            if args.write:
                safe_stage(args.root, args.mirror, args.sens, view)
                state["stage_written"] = True
            else:
                state["stage_written"] = False
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(state, ensure_ascii=False,
                                               indent=2, sort_keys=True) + "\n",
                                   encoding="utf-8")
        print(json.dumps(state, ensure_ascii=False, sort_keys=True))
        return 0
    except (ViewBlocked, SensT5Error, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
