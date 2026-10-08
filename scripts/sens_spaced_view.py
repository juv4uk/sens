#!/usr/bin/env python3
"""Exact-width extensionless ASCII view of admitted physical SENS T5.

T5 codec stays the sole transport authority. This tool does NOT translate
Ukrainian surface/legacy aliases and does NOT certify executable semantics.
View files are generated only in staging; existing repository triples are
read-only verified. Never write .lisp, .sens, or the publication branch.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import SensT5Error, decode_bytes, encode_words, typed_sha256  # noqa: E402

VIEW = re.compile(rb"[01]{1,9}(?: [01]{1,9})*\n\Z")
SCHEMA = "sens-spaced-view/v1"


class ViewBlocked(ValueError):
    pass


def parse_view(data: bytes) -> list[str]:
    """Demand exact ASCII bits, single spaces, one LF and 1..9-bit words."""
    if not VIEW.fullmatch(data):
        raise ViewBlocked(
            "noncanonical ASCII view: require exact 0/1 words separated by one SP "
            "and exactly one trailing LF"
        )
    return [word.decode("ascii") for word in data[:-1].split(b" ")]


def render_view(words: list[str]) -> bytes:
    """Width is identity: '0', '00' and '000' MUST remain distinct."""
    raw = (" ".join(words) + "\n").encode("ascii")
    if parse_view(raw) != words:
        raise ViewBlocked("typed-word / text view round-trip failed")
    return raw


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative_source(source: str, root: Path) -> tuple[Path, Path]:
    if chr(92) in source:
        raise ViewBlocked("source path must use forward slashes")
    path = PurePosixPath(source)
    if (path.is_absolute() or ".." in path.parts or
            path.as_posix() != source or path.suffix != ".sens" or
            path.stem in ("", ".", "..")):
        raise ViewBlocked("source must be a relative same-stem .sens path")
    source_path = root.joinpath(*path.parts)
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ViewBlocked("source symlink/redirect forbidden")
    if not source_path.is_file() or not source_path.resolve().is_relative_to(root):
        raise ViewBlocked("missing or unsafe original physical .sens")
    human = source_path.with_suffix(".lisp")
    if human.is_symlink() or not human.is_file():
        raise ViewBlocked("same-stem Ukrainian .lisp source missing or unsafe")
    return Path(*path.parts), source_path


def rust_open(source: Path, reader: Path, words: list[str]) -> None:
    if reader.is_symlink() or not reader.is_file():
        raise ViewBlocked("missing or unsafe real Rust sens-trit")
    try:
        result = subprocess.run(
            [str(reader.resolve()), "open", str(source)],
            capture_output=True, text=True, timeout=40, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ViewBlocked(f"real Rust D2 reader failed: {exc}") from exc
    if result.returncode:
        raise ViewBlocked(
            "Rust D2 syntax rejected physical T5: " + result.stderr.strip()[:350]
        )
    if result.stdout != " ".join(words) + "\n":
        raise ViewBlocked("Rust D2 opener typed-word boundaries differ from Python codec")


def safe_stage(out_root: Path, source_root: Path, relative: Path, payload: bytes) -> Path:
    root = out_root.resolve()
    if root == source_root or root.is_relative_to(source_root):
        raise ViewBlocked("view staging must be outside the source repository")
    if root.is_symlink():
        raise ViewBlocked("unsafe staging root symlink")
    destination = root / relative.with_suffix("")
    # Refuse symlink components before creating any path.
    cur = root
    for part in destination.relative_to(root).parts:
        cur = cur / part
        if cur.is_symlink():
            raise ViewBlocked("unsafe destination symlink")
    if destination.exists() or destination.is_symlink():
        raise ViewBlocked("generated view already exists: never overwrite")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.parent.resolve().is_relative_to(root):
        raise ViewBlocked("staging directory redirected outside approved root")
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".sens-view-", dir=destination.parent, delete=False
        ) as staged:
            temp_name = Path(staged.name)
            staged.write(payload)
            staged.flush()
            os.fsync(staged.fileno())
        # The hard link is atomic, failing if ANY file exists already.
        os.link(temp_name, destination, follow_symlinks=False)
    finally:
        if temp_name is not None:
            temp_name.unlink(missing_ok=True)
    if destination.read_bytes() != payload:
        raise ViewBlocked("staged view differs from physical T5 rendering")
    return destination


def inspect(root: Path, original: str, reader: Path | None = None) -> tuple[dict, bytes, Path]:
    path, physical_path = relative_source(original, root)
    binary = physical_path.read_bytes()
    words = decode_bytes(binary)
    view = render_view(words)
    # Real inverse, including canonical T5 tail padding and typed widths.
    if encode_words(parse_view(view)) != binary:
        raise ViewBlocked("ASCII view cannot regenerate byte-identical canonical T5")
    if reader is not None:
        rust_open(physical_path, reader, words)
    human = physical_path.with_suffix(".lisp").read_bytes()
    record = {
        "schema": SCHEMA, "status": "PREVIEW_ONLY",
        "source": path.as_posix(), "uk_source": path.with_suffix(".lisp").as_posix(),
        "extensionless_view": path.with_suffix("").as_posix(),
        "source_sha256": sha256(human),
        "physical_t5_sha256": sha256(binary),
        "typed_word_sha256": typed_sha256(words),
        "spaced_ascii_sha256": sha256(view),
        "typed_word_count": len(words), "physical_size": len(binary),
        "view_size": len(view), "t5_roundtrip": "PASS",
        "rust_d2_syntax": "PASS" if reader is not None else "NOT_VERIFIED",
        "canonical_uk_surface": "NOT_VERIFIED",
        "semantic_oracle": "NOT_VERIFIED", "release_admitted": False,
        "files_written": 0,
    }
    return record, view, path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, help="repo-relative .sens file")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--reader", type=Path, help="actual built Rust sens-trit; mandatory for staging")
    ap.add_argument("--out-root", type=Path, help="external staging dir for extensionless view")
    ap.add_argument("--report", type=Path, help="JSON proof receipt outside source repo")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--stage", action="store_true", help="write only NEW extensionless staged view")
    mode.add_argument("--verify", action="store_true", help="check EXISTING extensionless view, read-only")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.stage and (args.reader is None or args.out_root is None):
            raise ViewBlocked("--stage requires --reader and --out-root")
        if args.verify and args.out_root is not None:
            raise ViewBlocked("--verify uses original same-stem view, not an output root")
        if args.report is not None and args.report.resolve().is_relative_to(root):
            raise ViewBlocked("report must be outside source repository")
        record, expected, path = inspect(root, args.source, args.reader)
        if args.verify:
            original_view = root / path.with_suffix("")
            if original_view.is_symlink() or not original_view.is_file():
                raise ViewBlocked("missing verified same-stem extensionless view")
            if original_view.read_bytes() != expected:
                raise ViewBlocked("stale or tampered same-stem view (not canonical T5 projection)")
            if encode_words(parse_view(original_view.read_bytes())) != (
                    root / path).read_bytes():
                raise ViewBlocked("view inverse differs from physical T5")
            record["status"] = "VIEW_MATCHES_T5"
        if args.stage:
            destination = safe_stage(args.out_root, root, path, expected)
            record["status"] = "STAGED_VIEW_T5_ONLY"
            record["files_written"] = 1
            record["staged_path"] = str(destination)
    except (ValueError, OSError, SensT5Error, UnicodeError) as exc:
        record = {
            "schema": SCHEMA, "status": "BLOCKED", "source": args.source,
            "reason": str(exc)[:600], "files_written": 0,
            "semantic_oracle": "NOT_VERIFIED", "release_admitted": False,
        }
    if args.report is not None and not args.report.resolve().is_relative_to(root):
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 2 if record["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
