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
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sens_t5_codec import decode_bytes, encode_words, typed_sha256

TRANSACTION = SCRIPT_DIR / "migrate-approved-t5.py"


class MigrationBlocked(ValueError):
    pass


# Source classification is NOT inferred from whether three-pass can emit
# physical bytes. These previously reviewed manifests pin non-program records
# to their exact immutable Git object, not merely to a filename glob.
NONPROGRAM_MANIFESTS = (
    "migration-nonprogram-isa-manifest-2026-10-08.json",
    "migration-nonprogram-schema-manifest-2026-10-08.json",
    "migration-nonprogram-evidence-manifest-2026-10-08.json",
    "migration-nonprogram-expr-records-2026-10-08.json",
)
ARCHIVE_POLICY = "migration-benchmark-snapshot-2026-10-08.json"


def _git_blob_sha(content: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + bytes([0]) + content
    ).hexdigest()


def _nonprogram_manifest_paths(root: Path) -> dict[str, str]:
    """Load reviewed path/blob records; fail closed if the contract drifts."""
    indexed: dict[str, str] = {}
    for filename in NONPROGRAM_MANIFESTS:
        manifest = root / "knowledge" / filename
        if manifest.is_symlink() or not manifest.is_file():
            raise MigrationBlocked(f"missing/unsafe nonprogram authority: {filename}")
        try:
            document = json.loads(manifest.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise MigrationBlocked(f"invalid nonprogram authority: {filename}") from exc
        if (not isinstance(document, dict)
                or document.get("schema") != "sens-migration-nonprogram-manifest/1"
                or document.get("automatic_sens_companion") is not False
                or not isinstance(document.get("entries"), list)
                or not document["entries"]):
            raise MigrationBlocked(f"invalid nonprogram authority contract: {filename}")
        for row in document["entries"]:
            if not isinstance(row, dict) or set(row) != {"path", "git_blob_sha1"}:
                raise MigrationBlocked(f"invalid SHA-locked nonprogram row: {filename}")
            name, blob = row["path"], row["git_blob_sha1"]
            if not isinstance(name, str) or chr(92) in name:
                raise MigrationBlocked("nonprogram source path must be relative POSIX")
            posix = PurePosixPath(name)
            if (posix.is_absolute() or ".." in posix.parts or posix.suffix != ".lisp"
                    or posix.as_posix() != name):
                raise MigrationBlocked(f"unsafe nonprogram path: {name}")
            if (not isinstance(blob, str) or len(blob) != 40
                    or any(c not in "0123456789abcdef" for c in blob)):
                raise MigrationBlocked(f"invalid Git source blob pin for {name}")
            if name in indexed:
                raise MigrationBlocked(f"duplicate nonprogram authority path: {name}")
            indexed[name] = blob
    return indexed


def _is_archived_benchmark(path: PurePosixPath, root: Path) -> bool:
    """Frozen measurement programs are archived evidence, not active SENS."""
    parts = path.parts
    if not (len(parts) == 6 and parts[:3] ==
            ("benchmarks", "sens-surface", "results") and
            parts[4] == "programs" and path.suffix == ".lisp"):
        return False
    source = root / "knowledge" / ARCHIVE_POLICY
    if source.is_symlink() or not source.is_file():
        raise MigrationBlocked("missing benchmark archive authority")
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise MigrationBlocked("invalid benchmark archive authority") from exc
    if (document.get("schema") != "sens-t5-archive-evidence/v1"
            or document.get("status") != "NONPROGRAM_ARCHIVED_BENCHMARK_EVIDENCE"
            or document.get("allow_bulk_conversion") is not False
            or document.get("admitted_as_executable") != 0):
        raise MigrationBlocked("benchmark archive authority contract changed")
    return True


def reject_classified_nonprogram(sources: list[str], root: Path) -> None:
    """Early all-or-nothing embargo before any conversion or T5 publication."""
    classified = _nonprogram_manifest_paths(root)
    for name in sources:
        rel = PurePosixPath(name)
        if _is_archived_benchmark(rel, root):
            raise MigrationBlocked(
                f"NONPROGRAM archived benchmark measurement; no executable .sens: {name}"
            )
        expected = classified.get(name)
        if expected is None:
            continue
        data = (root / name).read_bytes()
        actual = _git_blob_sha(data)
        if actual != expected:
            raise MigrationBlocked(
                f"NONPROGRAM source authority drift: {name}; "
                f"expected original Git blob {expected}, actual {actual}; independent review required"
            )
        raise MigrationBlocked(
            f"NONPROGRAM Git-blob-locked data/record; no executable .sens: {name}"
        )


def actual_reader(root: Path, configured: Path | None = None) -> Path:
    """Return a real Rust sens-trit reader for physical publication."""
    env = os.environ.get("SENS_TRIT_BIN")
    reader = (Path(env) if env else configured if configured else root / "target" / "debug" / "sens-trit").resolve()
    if not reader.is_file():
        process = subprocess.run(
            ["cargo", "build", "-q", "-p", "sens-cli", "--bin", "sens-trit"],
            cwd=root, capture_output=True, text=True, timeout=240,
        )
        if process.returncode != 0:
            reason = process.stderr.strip() or process.stdout.strip()
            raise MigrationBlocked(f"unable to build real Rust sens-trit reader: {reason[:1000]}")
    if not reader.is_file():
        raise MigrationBlocked(f"real Rust sens-trit reader not found: {reader}")
    return reader


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
    # Every selected path is checked as one atomic batch. A source may be
    # mechanically convertible while being reviewed NONPROGRAM archive/data.
    reject_classified_nonprogram([row["path"] for row in entries], root)
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
    ap.add_argument("--reader", type=Path, help="real built Rust sens-trit; auto-built for physical publication")
    ap.add_argument("--source-era", choices=("auto", "legacy", "current"), default="auto",
                    help="auto blocks W8 ambiguity; specify a proven historical/current source era")
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
        reader = None if args.dry_run else actual_reader(root, args.reader)
        with tempfile.TemporaryDirectory(prefix="sens-admission-") as directory:
            manifest = Path(directory) / "pinned.json"
            manifest.write_text(json.dumps(pinned, sort_keys=True) + "\n", encoding="utf-8")
            invoke(manifest, root, output, report, args.dry_run, args.source_era, reader)

        result = json.loads(report.read_text(encoding="utf-8"))
        verified = verify_published(result, output, args.dry_run)
        print(json.dumps({"status": "DRY_RUN_READY" if args.dry_run else "VERIFIED",
                          "files": verified, "report": str(report)}, ensure_ascii=False))
        return 0
    except (MigrationBlocked, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2


def invoke(manifest: Path, root: Path, output: Path, report: Path,
           dry_run: bool, source_era: str = "auto", reader: Path | None = None) -> None:
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
