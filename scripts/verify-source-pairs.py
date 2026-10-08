#!/usr/bin/env python3
"""Fail-closed, read-only audit for SENS canonical binary / Ukrainian source pairs.

This is a verification seam, NOT a translator. Canonical encode/decode must be
supplied as independent stdin->stdout executables. Without both bridges the
release-critical check fails; --inventory-only is strictly non-release evidence.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import unicodedata

UKRAINIAN_LETTERS = frozenset(
    "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
)
# Conservative Ukrainian layout contract: expand only with a tested keyboard
# mapping. In particular ASCII English A-Z, confusables, BOM and invisible
# format characters are forbidden, not silently normalized or transliterated.
KEYBOARD_PUNCTUATION = frozenset("0123456789 ()[]{}.,;:!?'-+*/=<>%_\"№₴\n\t")
ADMITTED = UKRAINIAN_LETTERS | KEYBOARD_PUNCTUATION


class PairError(ValueError):
    pass


def validate_binary(data: bytes, name: str) -> None:
    if not data or any(byte not in (48, 49) for byte in data):
        raise PairError(f"{name}: expected nonempty exact visible-binary 0/1 stream (no whitespace)")


def validate_ukrainian(data: bytes, name: str) -> None:
    try:
        value = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise PairError(f"{name}: invalid UTF-8: {exc}") from exc
    if not value or value != unicodedata.normalize("NFC", value):
        raise PairError(f"{name}: projection must be nonempty canonical NFC")
    for offset, ch in enumerate(value):
        if ch not in ADMITTED:
            raise PairError(f"{name}: forbidden/non-keyboard character U+{ord(ch):04X} at offset {offset}")


def bridge(path: Path, source: bytes, name: str) -> bytes:
    if not path.is_file():
        raise PairError(f"{name}: bridge not found: {path}")
    command = [sys.executable, str(path)] if path.suffix == ".py" else [str(path)]
    try:
        result = subprocess.run(command, input=source, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PairError(f"{name}: failed bridge: {exc}") from exc
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()[:300]
        raise PairError(f"{name}: bridge exit {result.returncode}: {message}")
    return result.stdout


def verify_pair(source: Path, encoder: Path | None, decoder: Path | None,
                inventory_only: bool = False) -> None:
    twin = source.with_suffix("")
    if source.is_symlink() or twin.is_symlink():
        raise PairError(f"{source}: source and twin must not be symlinks")
    if not twin.is_file():
        raise PairError(f"{source}: missing adjacent binary twin {twin}")
    u = source.read_bytes()
    b = twin.read_bytes()
    validate_ukrainian(u, str(source))
    validate_binary(b, str(twin))
    if inventory_only:
        return
    if encoder is None or decoder is None:
        raise PairError("missing --encoder/--decoder; inventory-only is not release evidence")
    # Direct equality plus both compositions catches accidental formatting,
    # aliases, padding, comment dropping, and noncanonical transport output.
    if bridge(encoder, u, "encode(U)") != b:
        raise PairError(f"{source}: encode(U) differs byte-for-byte from {twin}")
    if bridge(decoder, b, "decode(B)") != u:
        raise PairError(f"{source}: decode(B) differs byte-for-byte from {source}")
    du = bridge(decoder, bridge(encoder, u, "encode(U)"), "decode(encode(U))")
    eb = bridge(encoder, bridge(decoder, b, "decode(B)"), "encode(decode(B))")
    if du != u or eb != b:
        raise PairError(f"{source}: canonical two-way composition is not identity")


def check(root: Path, globs: list[str], encoder: Path | None,
          decoder: Path | None, inventory_only: bool = False) -> tuple[int, list[str]]:
    root = root.resolve()
    if not globs:
        return 0, ["no --include patterns: scope cannot be empty"]
    sources = sorted({p for pattern in globs for p in root.glob(pattern)
                      if p.is_file() and p.suffix == ".lisp"})
    errors = []
    if not sources:
        errors.append("no .lisp source matched --include patterns (fail closed)")
    # Probe only source-bearing directories: unrelated extensionless build files
    # are not SENS source, but any bit-only orphan in a source directory is.
    expected_twins = {src.with_suffix("") for src in sources}
    for directory in sorted({src.parent for src in sources}):
        for item in sorted(directory.iterdir()):
            if item in expected_twins or item.suffix or not item.is_file():
                continue
            # Reading other extensionless files is limited; this is a narrow
            # orphan detector, not a repo-wide content classification.
            if item.stat().st_size > 10_000_000:
                continue
            payload = item.read_bytes()
            if payload and all(c in (48, 49) for c in payload):
                errors.append(f"{item}: bit-only binary orphan with no adjacent .lisp")
    for src in sources:
        if root not in src.parents:
            errors.append(f"{src}: outside requested root")
            continue
        try:
            verify_pair(src, encoder, decoder, inventory_only)
        except (PairError, OSError) as exc:
            errors.append(str(exc))
    return len(sources), errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--include", action="append", default=[],
                        help="repo-relative glob of active .lisp sources; repeatable")
    parser.add_argument("--encoder", type=Path, help="Ukrainian UTF-8 stdin -> exact binary stdout")
    parser.add_argument("--decoder", type=Path, help="exact binary stdin -> Ukrainian UTF-8 stdout")
    parser.add_argument("--inventory-only", action="store_true",
                        help="validate pairing/characters only; NOT release proof")
    args = parser.parse_args(argv)
    count, errors = check(args.root, args.include, args.encoder, args.decoder,
                          args.inventory_only)
    for error in errors:
        print(f"PAIR-FAIL: {error}", file=sys.stderr)
    status = "FAIL" if errors else ("INVENTORY-ONLY" if args.inventory_only else "PASS")
    print(f"PAIR-{status}: checked {count} active Ukrainian/binary source pairs")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
