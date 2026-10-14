#!/usr/bin/env python3
"""SHA-256 receipt for #5767/#5770 real T5 files; transport, NOT SENS semantics.

Consumes the existing parity_corpus.py accept-list, verifies that the paths are
exactly the git-tracked .sens inventory, and emits checkout-independent hashes.
Run alongside the existing Zig parity test; do not add a CI workflow or codec.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys


def tracked_paths(root: Path) -> list[str]:
    process = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "*.sens"],
        capture_output=True, check=False,
    )
    if process.returncode:
        raise ValueError("git index unavailable: " + process.stderr.decode("utf-8", "replace"))
    result = [os.fsdecode(raw) for raw in process.stdout.split(b"\0") if raw]
    if not result:
        raise ValueError("empty git-tracked .sens inventory")
    return sorted(result, key=os.fsencode)


def accepted_paths(root: Path, accept: Path) -> list[str]:
    lines = accept.read_text(encoding="utf-8").splitlines()
    if not lines or any(not line for line in lines):
        raise ValueError("empty or malformed parity accept list")
    paths = []
    for line in lines:
        path = Path(line)
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            raise ValueError(f"missing/nonregular/relative accept entry: {line!r}")
        try:
            rel = path.resolve().relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError(f"accept entry outside repo: {line!r}") from exc
        if any(char in rel for char in ("\t", "\n", "\r")):
            raise ValueError(f"unsafe manifest filename: {rel!r}")
        paths.append(rel)
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate accept entry")
    return sorted(paths, key=os.fsencode)


def sha_file(path: Path) -> tuple[int, str]:
    before = path.stat()
    h = hashlib.sha256()
    length = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            length += len(block)
            h.update(block)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or length != after.st_size:
        raise ValueError(f"changed during fingerprint: {path}")
    return length, h.hexdigest()


def receipt(root: Path, accept: Path) -> tuple[bytes, str, int]:
    tracked = tracked_paths(root)
    present = accepted_paths(root, accept)
    if tracked != present:
        omitted = sorted(set(tracked) - set(present), key=os.fsencode)
        extra = sorted(set(present) - set(tracked), key=os.fsencode)
        raise ValueError(f"accept != git index: omitted={omitted[:3]!r} extra={extra[:3]!r}")
    records = []
    for rel in tracked:
        path = root / rel
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing/nonregular tracked file: {rel!r}")
        if any(char in rel for char in ("\t", "\n", "\r")):
            raise ValueError(f"unsafe tracked filename: {rel!r}")
        length, sha = sha_file(path)
        records.append(f"{rel}\t{length}\t{sha}\n".encode("utf-8"))
    manifest = b"".join(records)
    return manifest, hashlib.sha256(manifest).hexdigest(), len(tracked)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path, help="git repository root")
    p.add_argument("--accept", required=True, type=Path, help="parity_accept.txt produced by existing generator")
    p.add_argument("--manifest", default="parity_manifest.tsv", type=Path)
    p.add_argument("--expect-sha256", help="expected manifest SHA-256 for paired Zig↔Rust runs")
    args = p.parse_args()
    root = args.root.resolve()
    manifest, got, count = receipt(root, args.accept)
    if args.expect_sha256 and got != args.expect_sha256.lower():
        expected = args.expect_sha256.lower()
        first = next((i for i, (a, b) in enumerate(zip(expected, got)) if a != b),
                     min(len(expected), len(got)))
        print(f"FAIL test_id=t5-corpus-sha layer=transport "
              f"expected_sha256={expected} actual_sha256={got} first_diff={first} "
              "reproduce='python3 research/zig-codecs/tools/t5_corpus_receipt.py "
              "--root . --accept parity_accept.txt --expect-sha256 <expected>'",
              file=sys.stderr)
        return 1
    args.manifest.write_bytes(manifest)
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    print(f"T5_CORPUS_RECEIPT files={count} sha256={got} git_head={head} "
          f"manifest={args.manifest} layer=transport semantic_status=NOT_VERIFIED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"FAIL test_id=t5-corpus-receipt layer=transport cause={exc}") from exc
