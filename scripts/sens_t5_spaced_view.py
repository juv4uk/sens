#!/usr/bin/env python3
"""Verified physical .sens <-> canonical extensionless ASCII bit-word view.

This is a PRESENTATION tool, never a new language parser, semantic authority
or executable SENS file. D2 grammar and Ukrainian/oracle parity are separate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from sens_t5_codec import (
    SensT5Error, decode_bytes, encode_words, typed_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
VIEW_PATTERN = re.compile(rb"[01]{1,9}(?: [01]{1,9})*\n\Z")
SCHEMA = "sens-t5-exact-spaced-view/v1"


def canonical_view(words: list[str]) -> bytes:
    """One ASCII space between exact words, exactly one terminal LF."""
    encode_words(words)  # owner codec validates exact bit widths
    return (" ".join(words) + "\n").encode("ascii")


def parse_view(data: bytes) -> list[str]:
    """Strict inverse view grammar: no LF padding/whitespace normalization."""
    if not data or not VIEW_PATTERN.fullmatch(data):
        raise SensT5Error(
            "noncanonical view: expected [01]{1,9} with single ASCII spaces "
            "and one final LF; no width tags, 2, tabs or CRLF"
        )
    words = data[:-1].decode("ascii").split(" ")
    if canonical_view(words) != data:
        raise SensT5Error("view differs from canonical exact-width rendering")
    return words


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parts(relative: Path, ending: str) -> None:
    if (relative.is_absolute() or relative.suffix != ending
            or not relative.parts or any(p in ("..", ".", ".git") for p in relative.parts)):
        raise ValueError("unsafe or non-.sens input path: " + str(relative))


def _no_link_components(root: Path, relative: Path) -> None:
    if root.is_symlink():
        raise ValueError("symlink source/view root is forbidden")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symlink source/view path is forbidden: " + str(relative))


def _ensure_outside(source_root: Path, output: Path) -> None:
    if output == source_root or output.is_relative_to(source_root):
        raise ValueError("output staging must be outside source repository")


def _atomic_no_clobber(path: Path, payload: bytes) -> None:
    """Commit an already-validated view exactly once, without truncation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _no_link_components(path.anchor and Path(path.anchor) or path.parent, 
                        Path(*path.parts[1:]))  # refuse symlink components
    if path.exists() or path.is_symlink():
        raise FileExistsError("view exists: never overwrite " + str(path))
    fd, scratch = tempfile.mkstemp(prefix=".sens-view-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(scratch, path)  # atomic publish, fails if destination exists
    finally:
        os.unlink(scratch)


def inspect(root: Path, rel: Path, mode: str, view_root: Path) -> dict:
    _parts(rel, ".sens")
    _no_link_components(root, rel)
    source = root / rel
    lisp = root / rel.with_suffix(".lisp")
    _no_link_components(root, rel.with_suffix(".lisp"))
    if not source.is_file() or not lisp.is_file():
        raise ValueError("must provide existing same-stem .lisp and physical .sens")
    old = source.read_bytes()
    original = lisp.read_bytes()
    words = decode_bytes(old)
    if encode_words(words) != old:
        raise SensT5Error("noncanonical physical T5 bytes")
    visible = canonical_view(words)
    if encode_words(parse_view(visible)) != old:
        raise SensT5Error("view -> T5 inverse identity failed")
    target_rel = rel.with_suffix("")
    target = view_root / target_rel
    _no_link_components(view_root, target_rel)
    receipt = {
        "path": rel.as_posix(),
        "source": rel.with_suffix(".lisp").as_posix(),
        "view": target_rel.as_posix(),
        "source_sha256": sha(original),
        "physical_sha256": sha(old),
        "typed_word_sha256": typed_sha256(words),
        "view_sha256": sha(visible),
        "physical_bytes": len(old),
        "view_bytes": len(visible),
        "word_count": len(words),
        "physical_and_view_roundtrip": "PASS",
        "uk_source_bidirectional_oracle": "NOT_VERIFIED",
        "semantic_observable_parity": "NOT_VERIFIED",
    }
    if mode == "verify":
        actual = target.read_bytes()
        if actual != visible:
            raise ValueError("stale/tampered/noncanonical extensionless view")
        if encode_words(parse_view(actual)) != old:
            raise ValueError("stored view -> physical T5 byte mismatch")
        receipt["status"] = "PASS_VIEW_ONLY"
    elif mode == "create":
        # The original files may have changed between validation and writing.
        if source.read_bytes() != old or lisp.read_bytes() != original:
            raise ValueError("source or physical SENS changed during verification")
        _atomic_no_clobber(target, visible)
        receipt["status"] = "CREATED_VIEW_ONLY"
    else:
        receipt["status"] = "WOULD_CREATE_VIEW_ONLY"
    return receipt


def run(args: argparse.Namespace) -> dict:
    untrusted_root = args.root.absolute()
    if untrusted_root.is_symlink():
        raise ValueError("symlink repository root is forbidden")
    root = untrusted_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("not a source repository")
    if args.mode == "create":
        if args.out is None:
            raise ValueError("--out is required for create")
        if args.out.is_symlink():
            raise ValueError("symlink output root is forbidden")
        view_root = args.out.resolve()
        _ensure_outside(root, view_root)
    elif args.out is not None:
        if args.out.is_symlink():
            raise ValueError("symlink view root is forbidden")
        view_root = args.out.resolve()
    else:
        view_root = root
    if args.mode == "preview" and args.out is None:
        view_root = root
    rows = []
    seen = set()
    for raw in args.paths:
        item = {"path": raw}
        try:
            rel = Path(raw)
            _parts(rel, ".sens")
            if rel.as_posix() in seen:
                raise ValueError("duplicate physical source path")
            seen.add(rel.as_posix())
            item = inspect(root, rel, args.mode, view_root)
        except (OSError, SensT5Error, ValueError) as error:
            item.update({"status": "BLOCKED", "reason": str(error)})
        rows.append(item)
    result = {
        "schema": SCHEMA, "mode": args.mode,
        "summary": {
            "seen": len(rows),
            "passed": sum(r["status"] != "BLOCKED" for r in rows),
            "blocked": sum(r["status"] == "BLOCKED" for r in rows),
            "created": sum(r["status"] == "CREATED_VIEW_ONLY" for r in rows),
            "semantic_oracle_passed": 0,
        },
        "files": rows,
        "warning": (
            "T5/view roundtrip alone does not admit the program: independent D2, "
            "canonical Ukrainian source renderer and historical/current oracle "
            "are separate release blockers."
        ),
    }
    if args.report is not None:
        if args.report.resolve().is_relative_to(root):
            raise ValueError("receipt must be written outside source repository")
        if args.report.is_symlink():
            raise ValueError("symlink report forbidden")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preview", "create", "verify"))
    parser.add_argument("paths", nargs="+", help="explicit repo-relative .sens files")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path,
                        help="external staging mirror (create) or view root (verify)")
    parser.add_argument("--report", type=Path, help="optional JSON receipt outside repo")
    try:
        data = run(parser.parse_args())
    except (OSError, ValueError, SensT5Error) as exc:
        print("T5 VIEW BLOCKED: " + str(exc), file=sys.stderr)
        return 3
    print(json.dumps(data, ensure_ascii=False))
    return 2 if data["summary"]["blocked"] or not data["summary"]["passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
