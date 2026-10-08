#!/usr/bin/env python3
"""Manifest-driven transactional .lisp -> physical T5 .sens migration.

The three-pass migrator is the semantic engine. This command is the
operational boundary for a real approved cohort:

  manifest -> source integrity -> semantic migration -> T5 roundtrip ->
  collision check -> publish the complete batch atomically, or publish none.

Manifest formats:
  {"files": ["path/to/file.lisp", ...]}
  {"files": [{"path": "...", "sha256": "..."}, ...]}

No repository-wide traversal, no partial publication, no source rewrite, no
overwrite, no extensionless output, and no success on an incomplete batch.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "scripts" / "migrate-three-pass.py"

spec = importlib.util.spec_from_file_location("sens_three_pass", ENGINE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load migration engine: {ENGINE_PATH}")
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)


def load_manifest(path: Path, root: Path) -> list[tuple[Path, str | None]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("files") if isinstance(data, dict) else data
    if not isinstance(entries, list) or not entries:
        raise ValueError("manifest must contain a non-empty 'files' list")

    root = root.resolve()
    seen: set[Path] = set()
    result: list[tuple[Path, str | None]] = []

    for entry in entries:
        expected_sha = None
        if isinstance(entry, dict):
            raw_path = entry.get("path")
            expected_sha = entry.get("sha256")
            if expected_sha is not None:
                if not isinstance(expected_sha, str) or len(expected_sha) != 64:
                    raise ValueError(f"sha256 must be 64 hex characters: {raw_path}")
                int(expected_sha, 16)
        else:
            raw_path = entry

        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError("manifest entries must name a non-empty path")

        rel = Path(raw_path)
        if rel.is_absolute() or rel.suffix.lower() != ".lisp":
            raise ValueError(f"manifest entry must be a relative .lisp path: {raw_path}")

        normalized = Path(os.path.normpath(rel.as_posix()))
        if normalized in seen:
            raise ValueError(f"duplicate manifest entry: {raw_path}")
        seen.add(normalized)

        candidate = root / normalized
        if candidate.is_symlink():
            raise ValueError(f"manifest source must not be a symlink: {raw_path}")

        source = candidate.resolve()
        try:
            source.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"manifest path escapes root: {raw_path}") from exc
        if not source.is_file():
            raise ValueError(f"manifest source is not a regular file: {raw_path}")

        result.append((normalized, expected_sha))

    return sorted(result)


def source_sha256(source: Path) -> str:
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_engine_maps(root: Path):
    data = engine.load_foundation(root / "knowledge/d1-d9-foundation.json")
    legacy, my, upper = engine.build_three_pass_maps(
        data,
        root / "crates/sens/src/domain_surface_registry_generated.rs",
        root / "crates/sens/src/semantic_registry_generated.rs",
        root / "crates/sens/src/semantic_registry.rs",
        root / "crates/sens/src/eval/necessary_forms_generated.rs",
        root / "contracts/core1-historical-sid-map.lisp",
    )
    text7 = engine.build_text7(
        data, root / "crates/sens/src/text7_projection_generated.rs"
    )
    return legacy, my, upper, text7


def migrate_one(source: Path, root: Path, maps):
    legacy, my, upper, text7 = maps
    resolver = engine.Resolver(legacy, my, upper)
    source_text = source.read_text(encoding="utf-8")

    signal.signal(signal.SIGALRM, engine._timeout_handler)
    signal.alarm(5)
    try:
        projection = engine.migrate_file(source_text, resolver, text7)
    finally:
        signal.alarm(0)

    words = engine.parse_words(projection)
    payload = engine.encode_projection(projection)
    if engine.decode_bytes(payload) != words:
        raise engine.SensT5Error("T5 roundtrip changed typed source words")

    rel = source.relative_to(root)
    dest = engine.sens_destination(rel)
    return dest, payload, {
        "path": rel.as_posix(),
        "output": dest.as_posix(),
        "source_sha256": source_sha256(source),
        "physical_sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "semantic_word_count": len(words),
        "passes": resolver.counts,
        "status": "ready",
    }


def publish_batch(staged: list[tuple[Path, bytes]], output_root: Path) -> None:
    created: list[Path] = []
    try:
        for rel, payload in staged:
            target = output_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() or target.is_symlink():
                raise engine.SensT5Error(
                    f"target already exists; refusing overwrite: {rel.as_posix()}"
                )

            fd, tmp_name = tempfile.mkstemp(
                prefix=".sens-t5-", suffix=".tmp", dir=target.parent
            )
            tmp = Path(tmp_name)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.link(tmp, target)
                created.append(target)
            finally:
                tmp.unlink(missing_ok=True)
    except Exception:
        for target in reversed(created):
            target.unlink(missing_ok=True)
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path, nargs="?", default=ROOT)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = args.root.resolve()
    manifest = args.manifest.resolve()
    output = args.out.resolve()
    report_path = args.report.resolve()

    rows: list[dict] = []
    staged: list[tuple[Path, bytes]] = []
    requested = 0

    try:
        entries = load_manifest(manifest, root)
        requested = len(entries)
        maps = load_engine_maps(root)
        destinations: set[Path] = set()

        for rel, expected_sha in entries:
            source = root / rel
            dest = engine.sens_destination(rel)

            if dest in destinations:
                raise engine.SensT5Error(f"duplicate output destination: {dest}")
            destinations.add(dest)

            target = output / dest
            if target.exists() or target.is_symlink():
                rows.append({
                    "path": rel.as_posix(),
                    "output": dest.as_posix(),
                    "status": "blocked",
                    "reason": "target already exists; refusing overwrite",
                })
                continue

            try:
                actual_sha = source_sha256(source)
                if expected_sha is not None and actual_sha != expected_sha:
                    raise engine.SensT5Error(
                        f"source sha256 mismatch: expected {expected_sha}, got {actual_sha}"
                    )
                dest_path, payload, row = migrate_one(source, root, maps)
                if expected_sha is not None:
                    row["manifest_sha256"] = expected_sha
                if dest_path != dest:
                    raise engine.SensT5Error("destination derivation changed")
                staged.append((dest_path, payload))
                rows.append(row)
            except (engine.MigrationError, engine.SensT5Error, UnicodeError, OSError) as exc:
                rows.append({
                    "path": rel.as_posix(),
                    "output": dest.as_posix(),
                    "status": "blocked",
                    "reason": getattr(exc, "message", str(exc)),
                })

        blocked = [row for row in rows if row.get("status") == "blocked"]
        if blocked:
            staged.clear()
        elif not args.dry_run:
            publish_batch(staged, output)
    except Exception as exc:
        rows.append({"status": "error", "reason": str(exc)})
        staged.clear()

    ready = sum(row.get("status") == "ready" for row in rows)
    blocked = sum(row.get("status") == "blocked" for row in rows)
    errors = sum(row.get("status") == "error" for row in rows)
    published = 0 if args.dry_run or blocked or errors else ready

    report = {
        "schema": "sens-approved-t5-migration/v2",
        "mode": "dry-run" if args.dry_run else "write-transaction",
        "manifest": str(manifest),
        "root": str(root),
        "out": str(output),
        "summary": {
            "files_requested": requested,
            "files_ready": ready,
            "files_blocked": blocked,
            "files_error": errors,
            "published": published,
        },
        "files": rows,
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], ensure_ascii=False))

    return 1 if blocked or errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
