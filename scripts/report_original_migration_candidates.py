#!/usr/bin/env python3
"""Expose actual old-source candidates from the existing fail-closed T5 census.

Read-only. A parse/codec-admissible dry-run is NOT semantic admission:
only independent source-law and Rust oracle parity can authorize publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts/migrate-three-pass.py"
ARGS = [
    "--foundation", "knowledge/d1-d7-foundation.json",
    "--domain-surfaces", "crates/sens/src/domain_surface_registry_generated.rs",
    "--semantic-generated", "crates/sens/src/semantic_registry_generated.rs",
    "--semantic-registry", "crates/sens/src/semantic_registry.rs",
    "--necessary-forms", "crates/sens/src/eval/necessary_forms_generated.rs",
    "--historical-map", "contracts/core1-historical-sid-map.lisp",
    "--text7", "crates/sens/src/text7_projection_generated.rs",
]

def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def categorize(row: dict, root: Path) -> dict:
    rel = Path(row["path"])
    if rel.is_absolute() or ".." in rel.parts or rel.suffix != ".lisp":
        raise ValueError("untrusted migrator path")
    source = root / rel
    if not source.is_file() or source.is_symlink():
        raise ValueError("source is not a regular tracked file")
    pair = source.with_suffix(".sens")
    result = {
        "path": rel.as_posix(),
        "source_git_blob_sha": git_blob_sha(source),
        "same_stem_sens_already_exists": pair.exists() or pair.is_symlink(),
        "source_is_executable_proven": False,
        "independent_semantic_oracle_passed": False,
    }
    if row["status"] == "would-write":
        result.update(
            status="CANDIDATE_NOT_ADMITTED",
            destination=rel.with_suffix(".sens").as_posix(),
            proposed_physical_sha256=row["physical_sha256"],
            proposed_typed_word_sha256=row["typed_word_sha256"],
            proposed_bytes=row["bytes"],
            proposed_words=row["semantic_word_count"],
            passes=row["passes"],
        )
    elif row["status"] == "blocked":
        result.update(status="BLOCKED", reason=row.get("reason", "unknown"))
    else:
        raise ValueError(f"unexpected dry-run status {row['status']!r}")
    return result


def build_report(root: Path = ROOT) -> dict:
    with tempfile.TemporaryDirectory(prefix="sens-original-candidate-") as td:
        report_path = Path(td) / "migration.json"
        output_dir = Path(td) / "no-physical-output"
        proc = subprocess.run(
            [sys.executable, str(root / "scripts/migrate-three-pass.py"),
             str(root), "--out", str(output_dir), *ARGS,
             "--report", str(report_path), "--dry-run"],
            cwd=root, capture_output=True, text=True, timeout=210
        )
        if not report_path.exists():
            raise RuntimeError(f"no dry-run report: {proc.stderr[-2000:]}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if proc.returncode not in (0, 2):
            raise RuntimeError(f"dry-run crashed ({proc.returncode}): {proc.stderr[-2000:]}")
        if report["mode"] != "dry-run" or report["summary"]["files_written"] != 0:
            raise RuntimeError("unexpected write-capable migration report")
        if list(output_dir.rglob("*.sens")) if output_dir.exists() else []:
            raise RuntimeError("dry-run emitted physical output")
        rows = [categorize(row, root) for row in report["files"]]
        candidates = [r for r in rows if r["status"] == "CANDIDATE_NOT_ADMITTED"]
        unpaired = [r for r in candidates if not r["same_stem_sens_already_exists"]]
        blocked = len(rows) - len(candidates)
        if len(rows) != report["summary"]["files_seen"] or blocked != report["summary"]["files_blocked"]:
            raise RuntimeError("migrator report totals inconsistent")
        return {
            "schema": "sens-original-three-pass-eligibility/v1",
            "authority": "candidate discovery only; parser/codec parity is NOT oracle parity",
            "mode": "read-only canonical migrator dry-run",
            "summary": {
                "scanned": len(rows),
                "blocked": blocked,
                "mechanical_candidates": len(candidates),
                "already_paired_candidates": len(candidates)-len(unpaired),
                "unpaired_candidates_needing_original_oracle": len(unpaired),
                "original_unpaired_executables_migrated_by_this_tool": 0,
                "physical_outputs_created": 0,
            },
            "mechanical_candidates": candidates,
            "unpaired_blocker_sample": [r for r in rows if r["status"] == "BLOCKED" and not r["same_stem_sens_already_exists"]][:20],
            "required_evidence": [
                "prove original file is an executable SENS program, not an archive/catalogue",
                "prove exact historical function successor, D1/D2/w8 era and no host/IO effects",
                "run actual three-pass CLI to same-stem packed T5 without overwriting source",
                "Rust exact-domain oracle parity including wrong-domain negatives and digest",
                "merge only after focused and independent physical+syntax CI green",
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary":result["summary"],"candidates":result["mechanical_candidates"]},ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
