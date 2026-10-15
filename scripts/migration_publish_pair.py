"""Fail-closed two-projection publication for an already Zig-certified T5 candidate.

This is a filesystem transaction helper, never an encoder, oracle, or semantic
authority. The caller must verify the candidate through the Zig corridor first.
"""
from __future__ import annotations

from pathlib import Path
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
    for path in (carrier_path, view_path):
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"PAIR_OUTPUT_EXISTS path={path}")

    write_new(carrier_path, carrier)
    try:
        write_new(view_path, view)
    except BaseException:
        try:
            # Do not destroy a replaced/mutated artifact or follow a symlink.
            if carrier_path.is_symlink() or carrier_path.read_bytes() != carrier:
                raise OSError("PAIR_CARRIER_CHANGED_DURING_ROLLBACK")
            carrier_path.unlink()
        except OSError as exc:
            raise OSError(
                f"PAIR_ROLLBACK_BLOCKED path={carrier_path}: {exc}"
            ) from exc
        raise
