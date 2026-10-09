#!/usr/bin/env python3
"""Канонічний людський перегляд T5: фізичний .sens <-> слова 0/1.

Це НЕ новий семантичний reader і НЕ доказ українського .lisp oracle.
Використовується лише чинний scripts/sens_t5_codec.py. #4694.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

from sens_t5_codec import SensT5Error, decode_bytes, encode_words, typed_sha256

VIEW_PATTERN = re.compile(rb"[01]{1,9}(?: [01]{1,9})*\n")
MAX_VIEW_BYTES = 32 * 1024 * 1024


class ViewError(ValueError):
    """Блокувальна помилка: невірне джерело, шлях або неканонічний перегляд."""


def parse_view(blob: bytes) -> list[str]:
    """Лише ASCII 0/1, один SP між точними словами, один кінцевий LF."""
    if not blob or len(blob) > MAX_VIEW_BYTES or VIEW_PATTERN.fullmatch(blob) is None:
        raise ViewError("noncanonical 0/1 view: expected single-space words and one LF")
    return [item.decode("ascii") for item in blob[:-1].split(b" ")]


def render_view(words: list[str]) -> bytes:
    """Не виводити текстового транспортного трита 2 чи ширинних префіксів."""
    if not words:
        raise ViewError("cannot render empty word sequence")
    candidate = (" ".join(words) + "\n").encode("ascii")
    if parse_view(candidate) != words:
        raise ViewError("view render did not preserve exact domain word boundaries")
    return candidate


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative_sens(raw: str) -> PurePosixPath:
    if "\\" in raw:
        raise ViewError("backslash path is forbidden")
    rel = PurePosixPath(raw)
    if (not raw or rel.is_absolute() or "." in rel.parts or ".." in rel.parts
            or rel.suffix != ".sens" or rel.name in (".sens", "..sens")):
        raise ViewError("requires safe repository-relative name.sens path")
    return rel


def _source_path(root: Path, rel: PurePosixPath) -> Path:
    if not root.is_dir() or root.is_symlink():
        raise ViewError("source root must be a real directory")
    path = root
    for part in rel.parts:
        path = path / part
        if path.is_symlink():
            raise ViewError("symlink in source path")
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ViewError("physical .sens missing or outside source root")
    return path


def _source_lisp(source: Path) -> tuple[str, bytes]:
    lisp = source.with_suffix(".lisp")
    if lisp.is_symlink() or not lisp.is_file():
        raise ViewError("matching .lisp missing or unsafe: not a valid triple")
    data = lisp.read_bytes()
    try:
        data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ViewError("source .lisp must be valid UTF-8") from error
    return str(lisp), data


def _atomic_new_view(output: Path, view: bytes, staging_root: Path) -> None:
    """Тимчасовий файл + hardlink без overwrite, перевірка symlink-компонентів."""
    if output.exists() or output.is_symlink():
        raise ViewError("view already exists; never overwrite")
    parent = staging_root
    for part in output.relative_to(staging_root).parts[:-1]:
        parent = parent / part
        if parent.is_symlink():
            raise ViewError("symlink in staging output")
        parent.mkdir(exist_ok=True)
        if not parent.is_dir():
            raise ViewError("non-directory staging component")
    name = None
    try:
        with tempfile.NamedTemporaryFile(dir=parent, prefix=".sens-view-", delete=False) as tmp:
            name = tmp.name
            tmp.write(view)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.link(name, output)  # atomic publication only when output absent
    except FileExistsError as error:
        raise ViewError("view exists; no-clobber") from error
    finally:
        if name is not None:
            Path(name).unlink(missing_ok=True)


def verify_actual_rust_d2(reader: Path, source: Path, canonical_view: bytes) -> None:
    """Ask EXISTING compiled Rust reader; typed transport != D2 executable syntax.

    This is an additional structural gate only, never an independent source
    semantic oracle. The reader must echo exactly the physically decoded words.
    """
    reader = reader.resolve(strict=True)
    if not reader.is_file():
        raise ViewError("Rust D2 reader is not a real file")
    try:
        response = subprocess.run(
            [str(reader), "open", str(source)], capture_output=True,
            timeout=30, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ViewError(f"Rust D2 reader failed to run: {error}") from error
    if response.returncode or response.stderr or response.stdout != canonical_view:
        raise ViewError("Rust D2 reader rejected physical T5 or typed-word projection")


def check_or_stage(root: Path, relative: str, *, stage: Path | None = None,
                   preview: bool = False, reader: Path | None = None) -> dict:
    rel = _relative_sens(relative)
    source = _source_path(root, rel)
    lisp_name, lisp_bytes = _source_lisp(source)
    packed = source.read_bytes()
    words = decode_bytes(packed)  # includes canonical padding and byte range
    if encode_words(words) != packed:
        raise ViewError("T5 decode/encode failed exact physical byte parity")
    view = render_view(words)
    if encode_words(parse_view(view)) != packed:
        raise ViewError("view -> T5 did not reproduce source bytes")
    if preview and stage is None:
        raise ViewError("preview requires a staging target")
    if reader is not None:
        verify_actual_rust_d2(reader, source, view)
    if stage is None:
        target = source.with_suffix("")
        if target.is_symlink() or not target.is_file():
            raise ViewError("missing same-stem readable view")
        observed = target.read_bytes()
        if parse_view(observed) != words or observed != view:
            raise ViewError("stale or modified view does not match physical T5")
        mode = "VERIFY"
    else:
        if not stage.is_dir() or stage.is_symlink():
            raise ViewError("staging root must already exist and not be symlink")
        staging_root = stage.resolve()
        if staging_root == root.resolve() or staging_root.is_relative_to(root.resolve()):
            raise ViewError("staging must be outside source tree")
        target = staging_root.joinpath(*rel.with_suffix("").parts)
        if not target.resolve().is_relative_to(staging_root):
            raise ViewError("staging output escaped root")
        if source.read_bytes() != packed or Path(lisp_name).read_bytes() != lisp_bytes:
            raise ViewError("source changed during verification")
        if preview:
            # Validate the same write target without touching the filesystem.
            if target.exists() or target.is_symlink():
                raise ViewError("view already exists; never overwrite")
            parent = staging_root
            for part in rel.with_suffix("").parts[:-1]:
                parent = parent / part
                if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                    raise ViewError("unsafe staging ancestor")
            mode = "PREVIEW_NO_WRITE"
        else:
            _atomic_new_view(target, view, staging_root)
            mode = "STAGED_NO_CLOBBER"
    return {
        "schema": "sens-t5-spaced-view/v1",
        "status": mode,
        "source": str(rel.with_suffix(".lisp")),
        "binary": str(rel),
        "view": str(rel.with_suffix("")),
        "words": len(words),
        "physical_bytes": len(packed),
        "source_sha256": _sha256(lisp_bytes),
        "sens_sha256": _sha256(packed),
        "view_sha256": _sha256(view),
        "typed_word_sha256": typed_sha256(words),
        "d2_reader": "PASS" if reader is not None else "NOT_CHECKED",
        "semantic_oracle": "NOT_VERIFIED_BY_VIEW_TOOL",
        "release_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--sens", required=True, help="one explicit relative file.sens; no bulk scan")
    commands = parser.add_mutually_exclusive_group(required=True)
    commands.add_argument("--verify", action="store_true", help="read-only check committed triple")
    commands.add_argument("--stage", type=Path, help="existing OUTSIDE-repo staging directory; no overwrite")
    commands.add_argument("--preview-stage", type=Path,
                          help="inspect external target without creating directories or files")
    parser.add_argument("--reader", type=Path,
                        help="optional real Rust sens-trit binary; D2 open must echo exact view")
    args = parser.parse_args(argv)
    try:
        target = args.stage if args.stage is not None else args.preview_stage
        record = check_or_stage(args.root, args.sens, stage=target,
                                preview=args.preview_stage is not None,
                                reader=args.reader)
    except (ViewError, SensT5Error, OSError, ValueError, UnicodeError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
