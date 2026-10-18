"""Fail-closed two-projection publication for an already Zig-certified T5 candidate.

This is a filesystem transaction helper, never an encoder, oracle, or semantic
authority. The caller must verify the candidate through the Zig corridor first.
"""
from __future__ import annotations

from pathlib import Path
import os
import stat
import tempfile
from typing import Callable


def publish_pair(
    write_new: Callable[[Path, bytes], None],
    carrier_path: Path,
    carrier: bytes,
    view_path: Path,
    view: bytes,
) -> None:
    """Publish same-stem carrier and view, or remove our carrier on view failure.

    Preflight prevents a known view collision from leaving an orphan `.sens`.
    An unexpected second-write failure also rolls back only the physical bytes
    this call has just created. No pre-existing file is overwritten or deleted.
    """
    if carrier_path == view_path:
        raise ValueError("PAIR_IDENTICAL_DESTINATIONS")
    # The only machine carrier is name.sens; the extensionless view belongs
    # to precisely that same stem. A mismatched pair is never published.
    if carrier_path.suffix != ".sens" or carrier_path.with_suffix("") != view_path:
        raise ValueError("PAIR_NONCANONICAL_SAME_STEM")
    for path in (carrier_path, view_path):
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"PAIR_OUTPUT_EXISTS path={path}")

    write_new(carrier_path, carrier)
    # Byte parity alone is not provenance: an unrelated file can contain
    # identical bytes. Record the freshly created inode before second publish.
    created = carrier_path.lstat()
    try:
        write_new(view_path, view)
    except BaseException:
        try:
            # Do not destroy a replaced/mutated artifact or follow a symlink.
            current = carrier_path.lstat()
            if (not stat.S_ISREG(current.st_mode)
                    or (current.st_dev, current.st_ino) != (created.st_dev, created.st_ino)
                    or carrier_path.read_bytes() != carrier):
                raise OSError("PAIR_CARRIER_CHANGED_DURING_ROLLBACK")
            carrier_path.unlink()
        except OSError as exc:
            raise OSError(
                f"PAIR_ROLLBACK_BLOCKED path={carrier_path}: {exc}"
            ) from exc
        raise

def _snapshot(path: Path) -> dict | None:
    """Read a regular destination and bind bytes to the observed inode."""
    if path.is_symlink():
        raise ValueError(f"PAIR_OUTPUT_SYMLINK path={path}")
    try:
        before = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f"PAIR_OUTPUT_NOT_REGULAR path={path}")
    data = path.read_bytes()
    after = path.lstat()
    first = (before.st_dev, before.st_ino, before.st_mode,
             before.st_size, before.st_mtime_ns)
    second = (after.st_dev, after.st_ino, after.st_mode,
              after.st_size, after.st_mtime_ns)
    if first != second or len(data) != after.st_size:
        raise OSError(f"PAIR_OUTPUT_CHANGED_DURING_SNAPSHOT path={path}")
    return {
        "dev": after.st_dev, "ino": after.st_ino, "mode": after.st_mode,
        "size": after.st_size, "mtime_ns": after.st_mtime_ns, "bytes": data,
    }


def _matches_snapshot(path: Path, expected: dict | None) -> bool:
    try:
        actual = _snapshot(path)
    except (OSError, ValueError):
        return False
    return actual == expected


def _stage(path: Path, data: bytes, mode: int) -> Path:
    """Stage bytes on the destination filesystem and fsync before publication."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".sens-pair-", suffix=".tmp", dir=path.parent)
    staged = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            os.fchmod(stream.fileno(), stat.S_IMODE(mode))
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        staged.unlink(missing_ok=True)
        raise
    return staged


def replace_pair(
    carrier_path: Path,
    carrier: bytes,
    view_path: Path,
    view: bytes,
) -> None:
    """Explicitly refresh a same-stem pair, restoring the old pair on failure.

    This is separate from publish_pair: normal conversion remains write-new-only.
    Existing files are snapshotted by inode and content; rollback changes a path
    only while it still contains the exact artifact installed by this call.
    """
    if carrier_path == view_path:
        raise ValueError("PAIR_IDENTICAL_DESTINATIONS")
    if carrier_path.suffix != ".sens" or carrier_path.with_suffix("") != view_path:
        raise ValueError("PAIR_NONCANONICAL_SAME_STEM")

    paths = (carrier_path, view_path)
    payloads = (carrier, view)
    originals: dict[Path, dict | None] = {}
    staged_new: dict[Path, Path] = {}
    staged_old: dict[Path, Path] = {}
    installed: dict[Path, dict] = {}
    try:
        for path in paths:
            originals[path] = _snapshot(path)

        # Prepare both new artifacts and rollback copies before replacing either
        # canonical file. Keep existing file permissions on replacement.
        for path, payload in zip(paths, payloads):
            original = originals[path]
            mode = original["mode"] if original is not None else 0o644
            staged_new[path] = _stage(path, payload, mode)
            if original is not None:
                staged_old[path] = _stage(path, original["bytes"], original["mode"])

        # Catch changes between snapshot and publication.
        for path in paths:
            if not _matches_snapshot(path, originals[path]):
                raise OSError(f"PAIR_OUTPUT_CHANGED_BEFORE_REPLACE path={path}")

        try:
            for path, payload in zip(paths, payloads):
                if originals[path] is None:
                    # Missing outputs keep no-clobber behavior if another writer
                    # creates the path after preflight.
                    os.link(staged_new[path], path)
                    staged_new[path].unlink(missing_ok=True)
                else:
                    os.replace(staged_new[path], path)
                current = _snapshot(path)
                if current is None or current["bytes"] != payload:
                    raise OSError(f"PAIR_PUBLISHED_BYTES_MISMATCH path={path}")
                installed[path] = current
        except BaseException as publish_error:
            rollback_errors = []
            for path in reversed(paths):
                if path not in installed:
                    continue
                try:
                    if not _matches_snapshot(path, installed[path]):
                        raise OSError(f"PAIR_ROLLBACK_CHANGED path={path}")
                    original = originals[path]
                    if original is None:
                        path.unlink()
                    else:
                        if not _matches_snapshot(path, installed[path]):
                            raise OSError(f"PAIR_ROLLBACK_CHANGED path={path}")
                        os.replace(staged_old[path], path)
                except OSError as rollback_error:
                    rollback_errors.append(str(rollback_error))
            if rollback_errors:
                raise OSError(
                    "PAIR_ROLLBACK_FAILED; original publication error="
                    + str(publish_error) + "; " + "; ".join(rollback_errors)
                ) from publish_error
            raise
    finally:
        for staged in (*staged_new.values(), *staged_old.values()):
            staged.unlink(missing_ok=True)

