#!/usr/bin/env python3
"""Mint Nirbhaya law carriers from current SENS source using canonical Zig/T5M.

Archived *.b64 files are historical evidence only. This script never restores
them as runtime artifacts: every pair is regenerated from the current .lisp.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

STEMS = (
    "d9-f6-object-addresses-law",
    "d9-fs-binding-map-strict-law",
    "result-status-d7-label-law",
    "d5-member-total-list-law",
    "d5-assoc-total-list-law",
)


def repo_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=Path(__file__).resolve().parent,
            check=True,
            capture_output=True,
            text=True,
        )
        return Path(result.stdout.strip()).resolve()
    except (OSError, subprocess.CalledProcessError):
        return Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_regular_file(path: Path, *, executable: bool = False) -> None:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"NIRBHAYA_INPUT_NOT_REGULAR path={path}")
    if executable and os.name != "nt" and not os.access(path, os.X_OK):
        raise RuntimeError(f"NIRBHAYA_EXECUTABLE_NOT_EXECUTABLE path={path}")


def target_snapshot(target: Path) -> bytes | None:
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise RuntimeError(f"NIRBHAYA_TARGET_NOT_REGULAR path={target}")
    return target.read_bytes() if target.exists() else None


def publish_pairs(
    sem: Path,
    staged_pairs: list[dict[str, Any]],
    original_targets: dict[Path, bytes | None],
) -> None:
    """Publish a fully minted batch and restore prior bytes after a write error."""
    targets: list[Path] = []
    for pair in staged_pairs:
        targets.extend((pair["target_sens"], pair["target_view"]))

    # Fail closed if another writer changed or replaced any target while mint
    # was running. Do not overwrite a newer native pair with an older staging.
    for target in targets:
        observed = target_snapshot(target)
        if observed != original_targets[target]:
            raise RuntimeError(f"NIRBHAYA_CONCURRENT_TARGET_UPDATE path={target}")

    published: list[Path] = []
    try:
        for pair in staged_pairs:
            # Recheck immediately before each pair's two-file replacement.
            for target in (pair["target_sens"], pair["target_view"]):
                if target_snapshot(target) != original_targets[target]:
                    raise RuntimeError(f"NIRBHAYA_CONCURRENT_TARGET_UPDATE path={target}")
            for staged_key, target_key in (
                ("staged_sens", "target_sens"),
                ("staged_view", "target_view"),
            ):
                staged = pair[staged_key]
                target = pair[target_key]
                os.replace(staged, target)
                published.append(target)
    except Exception:
        for index, target in enumerate(reversed(published)):
            previous = original_targets[target]
            if previous is None:
                target.unlink(missing_ok=True)
            else:
                rollback = sem / f".nirbhaya-rollback-{index}.tmp"
                rollback.write_bytes(previous)
                os.replace(rollback, target)
        raise


def mint_all(
    root: Path,
    sens_binary: Path,
    sens_trit_binary: Path,
) -> list[dict[str, Any]]:
    root = Path(root).resolve()
    sem = root / "tests" / "semantic"
    if sem.is_symlink() or not sem.is_dir():
        raise RuntimeError(f"NIRBHAYA_SEMANTIC_DIRECTORY_INVALID path={sem}")

    sens_binary = Path(sens_binary)
    if not sens_binary.is_absolute():
        sens_binary = root / sens_binary
    sens_trit_binary = Path(sens_trit_binary)
    if not sens_trit_binary.is_absolute():
        sens_trit_binary = root / sens_trit_binary
    # Do not resolve away a symlink before the fail-closed file check.
    require_regular_file(sens_binary, executable=True)
    require_regular_file(sens_trit_binary, executable=True)

    sources: list[tuple[str, Path, str]] = []
    original_targets: dict[Path, bytes | None] = {}
    for stem in STEMS:
        source = sem / f"{stem}.lisp"
        require_regular_file(source)
        sources.append((stem, source, sha256_file(source)))
        for target in (sem / f"{stem}.sens", sem / stem):
            original_targets[target] = target_snapshot(target)

    results: list[dict[str, Any]] = []
    # Staging lives on the target filesystem, so publication uses atomic
    # single-file renames. No target changes until all five pairs verify.
    with tempfile.TemporaryDirectory(prefix=".nirbhaya-mint-", dir=sem) as temp:
        scratch = Path(temp)
        staged_pairs: list[dict[str, Any]] = []

        for stem, source, source_sha in sources:
            staged_sens = scratch / f"{stem}.sens"
            staged_view = scratch / f"{stem}.view"
            subprocess.run(
                [
                    str(sens_binary),
                    "--t5m-mint",
                    str(source),
                    str(staged_sens),
                ],
                cwd=root,
                check=True,
            )
            if not staged_sens.is_file() or staged_sens.stat().st_size == 0:
                raise RuntimeError(f"NIRBHAYA_MINT_EMPTY stem={stem}")

            with staged_view.open("wb") as output:
                subprocess.run(
                    [str(sens_trit_binary), "view", str(staged_sens)],
                    cwd=root,
                    stdout=output,
                    check=True,
                )
            if not staged_view.is_file() or staged_view.stat().st_size == 0:
                raise RuntimeError(f"NIRBHAYA_VIEW_EMPTY stem={stem}")

            subprocess.run(
                [str(sens_trit_binary), "verify-view", str(staged_sens)],
                cwd=root,
                stdout=subprocess.DEVNULL,
                check=True,
            )
            if sha256_file(source) != source_sha:
                raise RuntimeError(f"NIRBHAYA_SOURCE_CHANGED_DURING_MINT stem={stem}")

            staged_pairs.append(
                {
                    "stem": stem,
                    "source": source,
                    "source_sha256": source_sha,
                    "staged_sens": staged_sens,
                    "staged_view": staged_view,
                    "target_sens": sem / f"{stem}.sens",
                    "target_view": sem / stem,
                }
            )

        for pair in staged_pairs:
            if sha256_file(pair["source"]) != pair["source_sha256"]:
                raise RuntimeError(
                    f"NIRBHAYA_SOURCE_CHANGED_BEFORE_PUBLISH stem={pair['stem']}"
                )

        publish_pairs(sem, staged_pairs, original_targets)

        for pair in staged_pairs:
            result = {
                "stem": pair["stem"],
                "source_sha256": pair["source_sha256"],
                "sens_bytes": pair["target_sens"].stat().st_size,
                "view_bytes": pair["target_view"].stat().st_size,
            }
            results.append(result)
            print(
                "NIRBHAYA_CANONICAL_T5M_PAIR_PASS"
                f" stem={result['stem']}"
                f" source_sha256={result['source_sha256']}"
                f" sens_bytes={result['sens_bytes']}"
                f" view_bytes={result['view_bytes']}"
                " native_semantics=NOT_CERTIFIED_BY_MINT"
            )
    return results


def main(argv: list[str] | None = None) -> int:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Mint five law pairs from current SENS source using SENS/Zig/T5M."
    )
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument("--sens", type=Path, default=Path("target/debug/sens"))
    parser.add_argument("--sens-trit", type=Path, default=Path("target/debug/sens-trit"))
    args = parser.parse_args(argv)
    try:
        mint_all(args.root, args.sens, args.sens_trit)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"NIRBHAYA_CANONICAL_MINT_FAILED error={error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
