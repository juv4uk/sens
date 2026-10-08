#!/usr/bin/env python3
"""SENS: one practical, fail-closed .lisp -> packed physical .sens entry point.

This command does not redefine language semantics. It delegates conversion,
three-pass legacy resolution and atomic publication to the canonical
scripts/migrate-approved-t5.py. It only creates an SHA-pinned source manifest,
runs that existing transaction, and *independently verifies* every published
T5 byte stream before reporting success.

Example:
  python3 scripts/migrate-sens.py \
    --source tests/fixtures/migration-d1-cond-cohort/branch.lisp \
    --out /tmp/sens-stage --report /tmp/sens-migration.json

Repeat --source for an atomic batch, or pass --manifest approved.json.\nEvery manifest entry is independently SHA-pinned before execution; supplied\nSHA256 values must match actual source bytes or the whole run is BLOCKED.
Eight-bit W8 source is ambiguous between old SID8 and ratified current D8.
Use --source-era auto (default; BLOCK), or --source-era legacy/current only
when source provenance proves that era.
Use --dry-run to classify without writing. The original .lisp never changes.
For protected publication, use an output directory outside the source tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sens_t5_codec import decode_bytes, encode_words, typed_sha256

TRANSACTION = SCRIPT_DIR / "migrate-approved-t5.py"
ARCHIVE_POLICY = "migration-benchmark-snapshot-2026-10-08.json"


class MigrationBlocked(ValueError):
    pass


def archived_program_path(path: PurePosixPath) -> bool:
    parts = path.parts
    return (
        len(parts) == 6
        and parts[:3] == ("benchmarks", "sens-surface", "results")
        and re.fullmatch(r"[0-9]{8}-[A-Za-z0-9._-]+", parts[3]) is not None
        and parts[4] == "programs"
        and path.suffix == ".lisp"
    )


def _proof_gated_archive_sources(root: Path) -> set[str]:
    approved: set[str] = set()
    directory = root / "knowledge" / "migration-admissions"
    if not directory.is_dir():
        return approved
    for manifest in sorted(directory.glob("*.json")):
        try:
            document = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeError):
            continue
        if document.get("schema") != "sens-t5-proof-admission/v1":
            continue
        source = document.get("source")
        source_sha = document.get("source_sha256")
        if not isinstance(source, str) or not isinstance(source_sha, str):
            continue
        try:
            rel = PurePosixPath(source)
            if rel.is_absolute() or "\\" in source or rel.suffix != ".lisp":
                continue
            candidate = root.joinpath(*rel.parts)
            if not archived_program_path(rel) or not candidate.is_file() or candidate.is_symlink():
                continue
            if hashlib.sha256(candidate.read_bytes()).hexdigest() != source_sha.lower():
                continue
        except (OSError, ValueError):
            continue
        approved.add(rel.as_posix())
    return approved


def outside(candidate: Path, root: Path, what: str) -> None:
    if candidate == root or root in candidate.parents:
        raise MigrationBlocked(f"{what} must be outside source root: {candidate}")


def pin_sources(sources: list[str], root: Path) -> dict:
    if not sources:
        raise MigrationBlocked("give at least one --source or --manifest")
    seen: set[str] = set()
    entries: list[dict[str, str]] = []
    for raw in sources:
        if "\\" in raw:
            raise MigrationBlocked(f"source path must use forward slashes: {raw}")
        p = PurePosixPath(raw)
        if p.is_absolute() or ".." in p.parts or p.suffix != ".lisp":
            raise MigrationBlocked(f"source must be a relative .lisp, without '..': {raw}")
        rel = p.as_posix()
        if rel in seen:
            raise MigrationBlocked(f"duplicate source: {rel}")
        seen.add(rel)
        candidate = root.joinpath(*p.parts)
        if candidate.is_symlink() or not candidate.is_file():
            raise MigrationBlocked(f"missing file or symlink source: {rel}")
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root):
            raise MigrationBlocked(f"source escapes root: {rel}")
        # Immutable content provenance: the downstream transactional tool
        # verifies this SHA again before publishing. Never silently trust names.
        sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
        entries.append({"path": rel, "sha256": sha})
    approved_archive = _proof_gated_archive_sources(root)
    for row in entries:
        rel = PurePosixPath(row["path"])
        if archived_program_path(rel) and rel.as_posix() not in approved_archive:
            raise MigrationBlocked(
                f"NONPROGRAM archived benchmark measurement; "
                f"no proof-gated executable .sens: {row['path']}"
            )
    return {"files": sorted(entries, key=lambda item: item["path"])}


def pin_manifest(path: Path, root: Path) -> dict:
    """Validate an approved manifest and SHA-pin EVERY source before execution.

    Both supported manifest shapes are accepted, but the forwarded temporary
    manifest always carries a verified content SHA for every entry. Explicit
    caller SHAs are treated as immutable preconditions, never overwritten.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("files") if isinstance(raw, dict) else raw
    if not isinstance(rows, list) or not rows:
        raise MigrationBlocked("manifest requires a non-empty files list")
    names: list[str] = []
    expected: dict[str, str] = {}
    for row in rows:
        if isinstance(row, str):
            name = row
        elif isinstance(row, dict):
            if set(row) - {"path", "sha256"}:
                raise MigrationBlocked("manifest contains unsupported fields")
            name = row.get("path")
            digest = row.get("sha256")
            if digest is not None:
                if not isinstance(digest, str) or len(digest) != 64 or any(
                    char not in "0123456789abcdefABCDEF" for char in digest
                ):
                    raise MigrationBlocked(f"invalid source SHA256 for {name!r}")
                if not isinstance(name, str):
                    raise MigrationBlocked("manifest path must be a string")
                expected[name] = digest.lower()
        else:
            raise MigrationBlocked("manifest row must be a path or path/SHA object")
        if not isinstance(name, str):
            raise MigrationBlocked("manifest path must be a string")
        names.append(name)
    pinned = pin_sources(names, root)
    for row in pinned["files"]:
        wanted = expected.get(row["path"])
        if wanted is not None and wanted != row["sha256"]:
            raise MigrationBlocked(f"source changed from approved SHA256: {row['path']}")
    return pinned


def verify_published(report: dict, output: Path, dry_run: bool) -> int:
    summary = report.get("summary", {})
    rows = report.get("files", [])
    count = int(summary.get("files_requested", -1))
    ready = int(summary.get("files_ready", -1))
    blocked = int(summary.get("files_blocked", -1))
    errors = int(summary.get("files_error", -1))
    published = int(summary.get("published", -1))
    if count <= 0 or len(rows) != count or blocked or errors or ready != count:
        raise MigrationBlocked(f"not all requested files admitted: {summary}")
    if published != (0 if dry_run else count):
        raise MigrationBlocked(f"publication count mismatch: {summary}")
    if dry_run:
        return count

    verified = 0
    for row in rows:
        if row.get("status") != "ready":
            raise MigrationBlocked(f"unadmitted result: {row}")
        raw = row.get("output")
        if not isinstance(raw, str) or "\\" in raw:
            raise MigrationBlocked("missing or unsafe output path")
        relative = PurePosixPath(raw)
        if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".sens":
            raise MigrationBlocked(f"invalid T5 destination: {raw}")
        dest = output.joinpath(*relative.parts)
        if dest.is_symlink() or not dest.is_file() or not dest.resolve().is_relative_to(output):
            raise MigrationBlocked(f"physical .sens missing / unsafe: {raw}")
        data = dest.read_bytes()
        words = decode_bytes(data)
        if encode_words(words) != data:
            raise MigrationBlocked(f"T5 physical round-trip failed: {raw}")
        digest = hashlib.sha256(data).hexdigest()
        if digest != row.get("physical_sha256"):
            raise MigrationBlocked(f"T5 content hash mismatch: {raw}")
        if len(words) != row.get("semantic_word_count") or len(data) != row.get("bytes"):
            raise MigrationBlocked(f"exact word count / byte length mismatch: {raw}")
        if row.get("typed_word_sha256") is not None and typed_sha256(words) != row["typed_word_sha256"]:
            raise MigrationBlocked(f"typed-word digest mismatch: {raw}")
        verified += 1
    return verified


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=ROOT, help="source SENS repo (default: script repo)")
    selection = ap.add_mutually_exclusive_group(required=True)
    selection.add_argument("--source", action="append", help="source .lisp path; repeat for atomic batch")
    selection.add_argument("--manifest", type=Path, help="existing approved file manifest")
    ap.add_argument("--out", type=Path, required=True, help="separate artifact staging root")
    ap.add_argument("--report", type=Path, required=True, help="JSON admission/blocker report")
    ap.add_argument("--dry-run", action="store_true", help="admission only, no .sens files")
    ap.add_argument("--source-era", choices=("auto", "legacy", "current"), default="auto",
                    help="auto blocks W8 ambiguity; specify a proven historical/current source era")
    ap.add_argument("--reader", type=Path,
                    default=ROOT / "target" / "debug" / "sens-trit",
                    help="real Rust sens-trit reader used for physical-T5 publication")
    args = ap.parse_args(argv)

    try:
        root = args.root.resolve(strict=True)
        output = args.out.resolve()
        report = args.report.resolve()
        if not root.is_dir():
            raise MigrationBlocked(f"source root is not a directory: {root}")
        outside(output, root, "--out")
        outside(report, root, "--report")
        if output == report or output in report.parents:
            raise MigrationBlocked("--report must not be inside --out")
        if args.manifest:
            approved = args.manifest.resolve(strict=True)
            outside(approved, output, "--manifest")
            if not approved.is_file():
                raise MigrationBlocked("manifest must be an existing regular file")
            pinned = pin_manifest(approved, root)
        else:
            pinned = pin_sources(args.source, root)
        # One SHA-locked transaction path for BOTH entry modes. Never pass a
        # raw, unpinned approved manifest directly into the publisher.
        with tempfile.TemporaryDirectory(prefix="sens-admission-") as directory:
            manifest = Path(directory) / "pinned.json"
            manifest.write_text(json.dumps(pinned, sort_keys=True) + "\n", encoding="utf-8")
            invoke(manifest, root, output, report, args.dry_run, args.source_era, args.reader)

        result = json.loads(report.read_text(encoding="utf-8"))
        verified = verify_published(result, output, args.dry_run)
        print(json.dumps({"status": "DRY_RUN_READY" if args.dry_run else "VERIFIED",
                          "files": verified, "report": str(report)}, ensure_ascii=False))
        return 0
    except (MigrationBlocked, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2


def invoke(manifest: Path, root: Path, output: Path, report: Path,
           dry_run: bool, source_era: str = "auto",
           reader: Path | None = None) -> None:
    command = [sys.executable, str(TRANSACTION), str(root), "--manifest",
               str(manifest), "--out", str(output), "--report", str(report),
               "--source-era", source_era]
    if dry_run:
        command.append("--dry-run")
    elif reader is not None:
        command.extend(["--reader", str(reader)])
    process = subprocess.run(command, cwd=root, capture_output=True, text=True)
    if process.returncode != 0:
        # Keep the original tool's precise per-file blocker manifest.
        reason = process.stderr.strip() or process.stdout.strip()
        raise MigrationBlocked(f"admission transaction failed ({process.returncode}); "
                               f"{reason[:1000]}; report={report}")


if __name__ == "__main__":
    raise SystemExit(main())
