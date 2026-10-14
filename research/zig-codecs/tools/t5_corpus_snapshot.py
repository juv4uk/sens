#!/usr/bin/env python3
"""#5767: pin one exact physical .sens corpus for independent Zig/Rust runs.

This tool does not encode, decode, interpret, or authorize SENS functions.
It verifies only repo-relative names and SHA-256 of unchanged physical bytes.
Run write before BOTH implementations, check after EACH implementation.
The resulting common corpus SHA is necessary, not sufficient, for byte parity.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import hashlib
import json
from pathlib import Path
import sys

MAX_T5_BYTES = 4 * 1024 * 1024
SCHEMA = "t5-corpus-physical-sha256-v1"


class SnapshotError(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def snapshot(root: Path, file_list: Path) -> dict:
    if not file_list.is_file():
        raise SnapshotError(f"missing-list:{file_list}")
    root = root.resolve(strict=True)
    rows = []
    seen = set()
    # The producer and Zig parity reader preserve path characters verbatim.
    # Only LF separates records; CR is removable solely as a CRLF terminator.
    for line_no, raw in enumerate(file_list.read_text(encoding="utf-8").split("\n"), 1):
        name = raw.removesuffix("\r")
        if not name:
            continue
        path = Path(name)
        if not path.is_absolute():
            path = root / path
        # Preserve the physical witness: do not hash a symlink's target as .sens.
        if path.is_symlink():
            raise SnapshotError(f"symlink:line={line_no}:{name}")
        path = path.resolve(strict=False)
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError as exc:
            raise SnapshotError(f"outside-repository:line={line_no}:{name}") from exc
        if path.suffix != ".sens":
            raise SnapshotError(f"not-sens:line={line_no}:{rel}")
        if rel in seen:
            raise SnapshotError(f"duplicate:line={line_no}:{rel}")
        seen.add(rel)
        if not path.is_file():
            raise SnapshotError(f"missing-file:line={line_no}:{rel}")
        size = path.stat().st_size
        if size > MAX_T5_BYTES:
            raise SnapshotError(f"oversized:line={line_no}:{rel}:bytes={size}")
        body = path.read_bytes()
        if len(body) != size:
            raise SnapshotError(f"changed-during-read:line={line_no}:{rel}")
        rows.append({"path": rel, "bytes": size, "sha256": sha(body)})
    if not rows:
        raise SnapshotError("empty-corpus")
    rows.sort(key=lambda row: row["path"])
    core = {"schema": SCHEMA, "files": rows, "count": len(rows)}
    return {**core, "corpus_sha256": sha(canonical(core))}


def verify_git_index_membership(root: Path, current: dict) -> None:
    """For strict real-corpus receipts: the manifest must cover every tracked .sens.

    This is physical inventory only, never SENS semantic or executable admission.
    """
    proc = subprocess.run(
        ["git", "-C", str(root.resolve(strict=True)), "ls-files", "-z", "--", "*.sens"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if proc.returncode:
        raise SnapshotError(
            "git-index-unavailable:"
            + proc.stderr.decode("utf-8", errors="replace").strip()
        )
    if proc.stdout and not proc.stdout.endswith(b"\0"):
        raise SnapshotError("git-index-incomplete-nul-stream")
    indexed = [os.fsdecode(part) for part in proc.stdout.split(b"\0") if part]
    if len(indexed) != len(set(indexed)):
        raise SnapshotError("git-index-duplicate-or-unmerged")
    expected, observed = set(indexed), {row["path"] for row in current["files"]}
    if expected != observed:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise SnapshotError(
            f"git-index-mismatch:missing={missing[:3]!r}:untracked={extra[:3]!r}"
        )


def first_difference(before: dict, after: dict) -> str:
    a = {r["path"]: r for r in before["files"]}
    b = {r["path"]: r for r in after["files"]}
    for path in sorted(set(a) | set(b)):
        if path not in a:
            return f"unexpected:{path}"
        if path not in b:
            return f"missing:{path}"
        if a[path] != b[path]:
            changes = [key for key in ("bytes", "sha256") if a[path][key] != b[path][key]]
            return f"changed:{path}:{','.join(changes)}"
    return "metadata-only"


def run(root: Path, file_list: Path, manifest: Path, mode: str,
        *, require_git_index: bool = False) -> int:
    current = snapshot(root, file_list)
    if require_git_index:
        verify_git_index_membership(root, current)
    if mode == "write":
        if manifest.exists():
            raise SnapshotError(f"manifest-already-exists:{manifest}; choose a fresh path")
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_bytes(json.dumps(current, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n")
        print(f"T5_CORPUS_SNAPSHOT_WRITTEN count={current['count']} sha256={current['corpus_sha256']} manifest={manifest}")
        return 0
    expected = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(expected, dict) or expected.get("schema") != SCHEMA:
        raise SnapshotError("invalid-manifest-schema")
    if expected.get("corpus_sha256") != sha(canonical({key: expected[key] for key in ("schema", "files", "count")})):
        raise SnapshotError("invalid-manifest-digest")
    if current != expected:
        print("FAIL test_id=t5-corpus-snapshot layer=transport "
              f"expected_sha={expected['corpus_sha256']} actual_sha={current['corpus_sha256']} "
              f"first_diff={first_difference(expected, current)} reproduce='python3 research/zig-codecs/tools/t5_corpus_snapshot.py check --root . --list parity_accept.txt --manifest SNAPSHOT.json'",
              file=sys.stderr)
        return 1
    print(f"T5_CORPUS_SNAPSHOT_OK count={current['count']} sha256={current['corpus_sha256']}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("write", "check"))
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--list", type=Path, required=True, dest="file_list")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--require-git-index", action="store_true",
                   help="reject omitted or untracked .sens against git ls-files -z")
    args = p.parse_args()
    try:
        return run(args.root, args.file_list, args.manifest, args.mode,
                   require_git_index=args.require_git_index)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print("FAIL test_id=t5-corpus-snapshot layer=transport "
              f"expected=READABLE_CONSISTENT_CORPUS actual=HARNESS_ERROR error={error} "
              f"reproduce='python3 research/zig-codecs/tools/t5_corpus_snapshot.py {args.mode} --root . --list parity_accept.txt --manifest SNAPSHOT.json'",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
