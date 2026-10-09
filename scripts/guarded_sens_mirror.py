#!/usr/bin/env python3
"""All-or-nothing safety wrapper for legacy --sens-mirror migration.

The legacy manifest migrator may return success even if it wrote only some
.sens files and BLOCKED other inputs. Never expose that partial output as
a finished corpus. Run that existing converter in a private temporary tree,
verify EVERY discovered .lisp has one canonical physical same-stem .sens,
then publish the whole directory with Linux renameat2(RENAME_NOREPLACE).

Not a new converter or oracle. This is staging/commit infrastructure only.
No original sources or other authors' files are changed.
"""
from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from sens_t5_codec import decode_bytes, typed_sha256, SensT5Error

DEFAULT_DRIVER = SCRIPTS / "migrate-to-sens-codes.py"
SKIP = {".git", ".hg", ".svn", ".venv", "venv", "target",
        "__pycache__", "dist", "build", "node_modules"}
MAX_SOURCES = 100_000
AT_FDCWD = -100
RENAME_NOREPLACE = 1


class TransactionBlocked(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_relative(raw: object) -> Path:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise TransactionBlocked("invalid source/output relative path")
    value = PurePosixPath(raw)
    if value.is_absolute() or any(p in ("..", ".", "") for p in raw.split("/")):
        raise TransactionBlocked("absolute or unsafe traversal in report")
    path = Path(*value.parts)
    if path.suffix != ".lisp" and path.suffix != ".sens":
        raise TransactionBlocked("expected .lisp or .sens suffix")
    return path


def no_symlinks(path: Path, root: Path) -> None:
    if path.is_symlink():
        raise TransactionBlocked(f"symlink not allowed: {path}")
    for parent in [path, *path.parents]:
        if parent == root.parent:
            break
        if parent.is_symlink():
            raise TransactionBlocked(f"symlink component not allowed: {parent}")


def original_sources(root: Path) -> dict[Path, str]:
    if not root.is_dir() or root.is_symlink():
        raise TransactionBlocked("source root absent or symbolic link")
    found: dict[Path, str] = {}
    for path in sorted(root.rglob("*.lisp")):
        rel = path.relative_to(root)
        if any(part in SKIP for part in rel.parts):
            continue
        if path.is_symlink() or not path.is_file():
            raise TransactionBlocked(f"unsafe original source: {rel}")
        if len(found) >= MAX_SOURCES:
            raise TransactionBlocked("source limit exceeded")
        found[rel] = digest(path.read_bytes())
    if not found:
        raise TransactionBlocked("empty migration corpus")
    return found


def canonical_stage(stage: Path, report: dict,
                    sources: dict[Path, str]) -> dict:
    rows = report.get("files")
    if not isinstance(rows, list):
        raise TransactionBlocked("missing canonical conversion rows")
    if not isinstance(report.get("summary"), dict):
        raise TransactionBlocked("missing conversion summary")
    summary = report["summary"]
    if (summary.get("files_seen") != len(sources)
            or summary.get("files_blocked") != 0
            or summary.get("files_written") != len(sources)
            or len(rows) != len(sources)):
        raise TransactionBlocked(
            f"non-atomic batch: {summary.get('files_blocked')} blocked, "
            f"{summary.get('files_written')}/{len(sources)} converted"
        )
    expected: set[Path] = set()
    verified = []
    for row in rows:
        if not isinstance(row, dict) or row.get("status") != "sens-written":
            raise TransactionBlocked("one or more source rows not admitted")
        source = checked_relative(row.get("path"))
        if source.suffix != ".lisp" or source not in sources:
            raise TransactionBlocked("unrecognized source row")
        target = source.with_suffix(".sens")
        if row.get("output") != target.as_posix():
            raise TransactionBlocked("filename contract violation in report")
        if target in expected:
            raise TransactionBlocked("duplicate source/result row")
        expected.add(target)
        filename = stage / target
        no_symlinks(filename, stage)
        if not filename.is_file():
            raise TransactionBlocked(f"missing staged bytes: {target}")
        data = filename.read_bytes()
        try:
            words = decode_bytes(data)
        except SensT5Error as e:
            raise TransactionBlocked(f"invalid physical T5 {target}: {e}") from e
        if digest(data) != row.get("physical_sha256"):
            raise TransactionBlocked("physical SHA mismatch")
        if typed_sha256(words) != row.get("typed_word_sha256"):
            raise TransactionBlocked("typed word SHA mismatch")
        verified.append({
            "source": source.as_posix(), "target": target.as_posix(),
            "source_sha256": sources[source], "physical_sha256": digest(data),
            "typed_word_sha256": typed_sha256(words),
            "semantic_word_count": len(words),
            "physical_bytes": len(data),
            "admission": "PHYSICAL_ONLY_NOT_SEMANTIC_ORACLE",
        })
    actual = {p.relative_to(stage) for p in stage.rglob("*") if p.is_file()}
    if actual != expected:
        raise TransactionBlocked("staged directory contains unexpected/missing files")
    if expected != {src.with_suffix(".sens") for src in sources}:
        raise TransactionBlocked("not every source has matching .sens")
    return {
        "schema": "sens-guarded-sens-mirror/v1",
        "status": "PREPARED_PHYSICAL_ONLY",
        "semantics": "NOT_VERIFIED",
        "files": verified,
        "summary": {
            "sources": len(sources), "physical_files": len(verified),
            "blocked": 0, "semantic_oracle_verified": 0,
        },
    }


def atomic_new_directory(source: Path, destination: Path) -> None:
    """Linux-only atomic no-replace commit. Never overwrite an existing tree."""
    libc = ctypes.CDLL(None, use_errno=True)
    if not hasattr(libc, "renameat2"):
        raise TransactionBlocked("OS lacks atomic RENAME_NOREPLACE support")
    rename = libc.renameat2
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p,
                       ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    result = rename(AT_FDCWD, os.fsencode(source),
                    AT_FDCWD, os.fsencode(destination), RENAME_NOREPLACE)
    if result != 0:
        code = ctypes.get_errno()
        if code == errno.EEXIST:
            raise TransactionBlocked("destination already exists; no overwrite")
        raise OSError(code, os.strerror(code), str(destination))


def transaction(*, root: Path, out: Path, driver: Path = DEFAULT_DRIVER,
                foundation: Path = REPO / "knowledge/d1-d9-foundation.json",
                timeout: int = 180) -> dict:
    root = root.absolute()
    out = out.absolute()
    driver = driver.absolute()
    foundation = foundation.absolute()
    if out.exists() or out.is_symlink():
        raise TransactionBlocked("destination already exists; no overwrite")
    if out == root or root in out.parents or out in root.parents:
        raise TransactionBlocked("source and destination trees must be separate")
    if out.parent.is_symlink() or not out.parent.is_dir():
        raise TransactionBlocked("destination parent must exist, not a symlink")
    if not driver.is_file():
        raise TransactionBlocked("missing source migration driver")
    if not foundation.is_file():
        raise TransactionBlocked("missing ratified foundation")
    before = original_sources(root)
    with tempfile.TemporaryDirectory(prefix=".t5-transaction-", dir=out.parent) as temp:
        stage = Path(temp) / "payload"
        stage.mkdir()
        local_report = Path(temp) / "conversion.json"
        cmd = [sys.executable, str(driver), str(root), "--foundation",
               str(foundation), "--sens-mirror", str(stage),
               "--report", str(local_report)]
        try:
            done = subprocess.run(cmd, cwd=REPO, capture_output=True,
                                  text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as e:
            raise TransactionBlocked("converter timed out; nothing published") from e
        if not local_report.is_file():
            raise TransactionBlocked(
                "converter failed without report: " + done.stderr[-400:]
            )
        report = json.loads(local_report.read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            raise TransactionBlocked("invalid converter report")
        if done.returncode not in (0, 2):
            raise TransactionBlocked(
                f"converter error {done.returncode}: {done.stderr[-300:]}"
            )
        # A legacy driver can return 0 even if 1 of N files got blocked.
        proof = canonical_stage(stage, report, before)
        if done.returncode != 0:
            raise TransactionBlocked("converter nonzero exit despite apparent success")
        if original_sources(root) != before:
            raise TransactionBlocked("source bytes changed during migration")
        # Manifest lives INSIDE the same atomic directory as its .sens files.
        (stage / "_physical-migration-report.json").write_text(
            json.dumps(proof, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        atomic_new_directory(stage, out)
        return proof


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True,
                    help="NEW output directory that must not exist")
    ap.add_argument("--foundation", type=Path,
                    default=REPO / "knowledge/d1-d9-foundation.json")
    args = ap.parse_args(argv)
    try:
        proof = transaction(root=args.root, out=args.out,
                            foundation=args.foundation)
    except (TransactionBlocked, OSError, ValueError) as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 2
    print(json.dumps(proof["summary"], ensure_ascii=False))
    print("NOTICE: physical T5 only, NO semantic oracle admission")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
