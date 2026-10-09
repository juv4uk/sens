#!/usr/bin/env python3
"""Safe, explicit file-by-file .lisp -> physical T5 .sens migration.

This is a batch driver, not a competing language implementation: semantic
conversion is delegated to migrate-three-pass.py and packing to sens_t5_codec.
Nothing is published unless --write is explicitly requested.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts/migrate-three-pass.py"

spec = importlib.util.spec_from_file_location("sens_migration_batch_impl", MIGRATOR)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load ratified SENS three-pass migrator")
mig = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mig
spec.loader.exec_module(mig)

INPUTS = {
    "foundation": ROOT / "knowledge/d1-d9-foundation.json",
    "domain_surfaces": ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
    "semantic_generated": ROOT / "crates/sens/src/semantic_registry_generated.rs",
    "semantic_registry": ROOT / "crates/sens/src/semantic_registry.rs",
    "necessary_forms": ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
    "historical_map": ROOT / "contracts/core1-historical-sid-map.lisp",
    "text7": ROOT / "crates/sens/src/text7_projection_generated.rs",
}
EXCLUDE = set(mig.SKIP_DIRS)
SCHEMA = "sens-t5-safe-batch/v1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def forbidden_components(path: Path) -> bool:
    return path.is_absolute() or not path.parts or ".." in path.parts or any(
        p in EXCLUDE for p in path.parts
    )


def assert_no_links(base: Path, relative: Path) -> None:
    current = base
    if current.is_symlink():
        raise ValueError("symlink repository/mirror root forbidden")
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink input/target component forbidden: {relative}")


def discover(repo: Path, requested: list[str]) -> tuple[list[Path], list[dict]]:
    found: set[Path] = set()
    failures: list[dict] = []
    for item in requested:
        relative = Path(item)
        if forbidden_components(relative):
            failures.append({"path": item, "status": "blocked",
                             "reason": "unsafe/excluded input path"})
            continue
        try:
            assert_no_links(repo, relative)
            path = repo / relative
            if path.is_dir():
                for child in sorted(path.rglob("*")):
                    rel = child.relative_to(repo)
                    if any(p in EXCLUDE for p in rel.parts):
                        continue
                    if child.is_symlink():
                        failures.append({"path": str(rel), "status": "blocked",
                                         "reason": "symlink in input tree"})
                    elif child.is_file() and child.suffix == ".lisp":
                        assert_no_links(repo, rel)
                        found.add(rel)
            elif path.is_file() and relative.suffix == ".lisp":
                found.add(relative)
            else:
                failures.append({"path": item, "status": "blocked",
                                 "reason": "expected existing .lisp source or directory"})
        except (ValueError, OSError) as exc:
            failures.append({"path": item, "status": "blocked", "reason": str(exc)})
    return sorted(found, key=lambda p: p.as_posix()), failures


def run(args: argparse.Namespace) -> dict:
    repo = args.root.resolve()
    out = args.out.resolve()
    report = args.report.resolve()
    if not repo.is_dir():
        raise ValueError("source repository must exist")
    # No source edits, including accidental reports or files under the source tree.
    if out == repo or out.is_relative_to(repo) or report.is_relative_to(repo):
        raise ValueError("output mirror and report must be OUTSIDE source root")
    if report == out or report.is_dir():
        raise ValueError("--report must name a JSON file, not the output directory")
    if out.is_symlink() or report.is_symlink():
        raise ValueError("symlink output/report is forbidden")
    paths, failures = discover(repo, args.paths)

    data = mig.load_foundation(INPUTS["foundation"])
    source_era = args.source_era
    admitted_d8 = data["domains"].get("D8", {}).get("residents", {})
    if source_era == "current" and "D8" not in data.get("current_domains", ()):
        raise ValueError("current D8 source requires owner-ratified D8 foundation")
    legacy, my, upper = mig.build_three_pass_maps(
        data, INPUTS["domain_surfaces"], INPUTS["semantic_generated"],
        INPUTS["semantic_registry"], INPUTS["necessary_forms"], INPUTS["historical_map"]
    )
    text7 = mig.build_text7(data, INPUTS["text7"])
    ledger = sorted(failures, key=lambda e: e["path"])
    # A cohort is all-or-none: retain physical candidates in memory until
    # every requested original has passed conversion and final source checks.
    staged: list[tuple[Path, Path, bytes, bytes, dict]] = []
    for rel in paths:
        source = repo / rel
        destination = mig.sens_destination(rel)
        target = out / destination
        row = {"path": rel.as_posix(), "output": destination.as_posix()}
        resolver = mig.Resolver(legacy, my, upper, source_era=source_era,
                                admitted_d8=admitted_d8,
                                strict_decisions=args.decision_table == "l1-l7")
        readable = ""  # never inherit another source on per-file error
        try:
            assert_no_links(repo, rel)
            assert_no_links(out, destination)
            if target.exists() or target.is_symlink():
                raise ValueError("existing .sens output: overwrite forbidden")
            original = source.read_bytes()
            row["source_sha256"] = digest(original)
            readable = original.decode("utf-8")
            projection = mig.migrate_file(readable, resolver, text7)
            words = mig.parse_words(projection)
            packed = mig.encode_projection(projection)
            if mig.decode_bytes(packed) != words:
                raise ValueError("exact typed T5 word roundtrip failed")
            # Disallow use of generated textual bytes as a misleading .sens file.
            if packed == projection.encode("ascii"):
                raise ValueError("invalid text disguised as physical .sens")
            row.update({
                "status": "would-write",
                "physical_bytes": len(packed),
                "source_words": len(words),
                "physical_sha256": digest(packed),
                "typed_word_sha256": mig.typed_sha256(words),
                "passes": dict(resolver.counts),
                "source_era": source_era,
                "decision_table": args.decision_table,
            })
            if args.write:
                staged.append((rel, destination, original, packed, row))
        except (mig.MigrationError, mig.SensT5Error, UnicodeError,
                ValueError, OSError) as exc:
            row.update({"status": "blocked", "reason": str(exc),
                        "passes": dict(resolver.counts), "source_era": source_era, "decision_table": args.decision_table})
            tok = getattr(exc, "tok", None)
            if tok is not None:
                row["token"] = tok.text
                row["line"], row["column"] = mig.line_col(readable, tok.offset)
        ledger.append(row)
    ledger.sort(key=lambda e: e["path"])

    # A single BLOCK (including discovery failures) forbids *all* writes.
    # A review may still inspect each mechanically feasible would-write row.
    if args.write and not any(row["status"] == "blocked" for row in ledger):
        for rel, destination, original, packed, row in staged:
            try:
                assert_no_links(repo, rel)
                assert_no_links(out, destination)
                if (out / destination).exists() or (out / destination).is_symlink():
                    raise ValueError("existing .sens output: overwrite forbidden")
                if (repo / rel).read_bytes() != original:
                    raise ValueError("source changed during migration")
            except (ValueError, OSError) as exc:
                row.update(status="blocked", reason=str(exc))
        if not any(row["status"] == "blocked" for row in ledger):
            created: list[Path] = []
            active: dict | None = None
            try:
                for rel, destination, original, packed, row in staged:
                    active = row
                    assert_no_links(repo, rel)
                    assert_no_links(out, destination)
                    if (repo / rel).read_bytes() != original:
                        raise ValueError("source changed during batch publication")
                    target = out / destination
                    mig.write_atomic_no_clobber(target, packed)
                    created.append(target)
            except (ValueError, OSError, mig.SensT5Error) as exc:
                # Only unlink OUR newly created targets, not existing targets.
                for target in reversed(created):
                    target.unlink(missing_ok=True)
                if active is not None:
                    active.update(status="blocked", reason="atomic batch aborted: " + str(exc))
            else:
                for _, _, _, _, row in staged:
                    row["status"] = "written"

    admitted = sum(e["status"] in ("would-write", "written") for e in ledger)
    blocked = sum(e["status"] == "blocked" for e in ledger)
    written = sum(e["status"] == "written" for e in ledger)
    candidates = sum(e["status"] == "would-write" for e in ledger)
    result = {
        "schema": SCHEMA, "mode": "write-new-only" if args.write else "dry-run",
        "root": str(repo), "output_mirror": str(out),
        "authority": {"foundation_sha256": digest(INPUTS["foundation"].read_bytes()),
                      "codec": "physical-T5-5-trits-per-byte",
                      "source_era": source_era,
                      "decision_table": args.decision_table,
                      "w8_policy": "auto blocks ambiguity; legacy and current require explicit choice"},
        "summary": {"files_seen": len(ledger), "files_admitted": admitted,
                    "files_written": written,
                    "files_would_write": candidates,
                    "files_blocked": blocked},
        "files": ledger,
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    stage = report.with_name(report.name + ".tmp")
    if stage.exists() or report.is_symlink():
        raise ValueError("report staging target already exists or is symlink")
    try:
        stage.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
        stage.replace(report)
    finally:
        stage.unlink(missing_ok=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+",
                        help="EXPLICIT repository-relative .lisp files or directories")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, required=True,
                        help="separate output mirror (never source root)")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--source-era", choices=("auto", "legacy", "current"),
                        default="auto",
                        help="auto FAILS on ambiguous W8; choose legacy/current only with provenance")
    parser.add_argument("--decision-table", choices=("legacy", "l1-l7"),
                        default="legacy", help="L1-L7 strict normalization; existing parser only")
    parser.add_argument("--write", action="store_true",
                        help="opt in to creating new physical .sens; never overwrite")
    args = parser.parse_args()
    try:
        result = run(args)
    except (OSError, ValueError, mig.MigrationError) as exc:
        print(f"FATAL migration setup: {exc}", file=sys.stderr)
        return 3
    print(json.dumps(result["summary"], ensure_ascii=False))
    return 2 if result["summary"]["files_blocked"] or not result["summary"]["files_admitted"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
