#!/usr/bin/env python3
"""#4819: immutable ORIGINAL Core1 executable migration frontier, no publication.

The 11 observed values live in the independent old S0 runner workflow.
This command does NOT claim to rerun that private oracle and does NOT emit T5.

Execute the existing canonical 3-pass as a scoped --dry-run on an unchanged
historical .lisp Git blob, first with fail-closed AUTO provenance and then with
an explicitly proven historical legacy W8 era. Retain precise first blocking
token and source byte integrity. A mechanical candidate is NOT an admission.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
SOURCE = Path("lib/core1-compiler-sid-resolver.lisp")
SOURCE_GIT_BLOB = "b3f976ef456cc6033ef34984c6d5b557101811d4"
HISTORICAL_S0_COMMIT = "6031f92652066825a245c806c0773e9e524257bd"
SCHEMA = "sens-core1-original-frontier/v1"


class FrontierBlocked(ValueError):
    pass


def git_source_sha(root: Path, rel: Path = SOURCE) -> str:
    path = root / rel
    if path.is_symlink() or not path.is_file():
        raise FrontierBlocked("SOURCE: immutable .lisp missing or symlink")
    result = subprocess.run(
        ["git", "hash-object", "--", str(path)], cwd=root,
        capture_output=True, timeout=15, check=False, text=True,
    )
    if result.returncode:
        raise FrontierBlocked("SOURCE: git hash-object failed: " + result.stderr[-250:])
    return result.stdout.strip()


def canonical_probe(root: Path, era: str) -> dict:
    assert era in {"auto", "legacy"}
    with tempfile.TemporaryDirectory(prefix="sens-core1-original-proof-") as tmp:
        temp = Path(tmp)
        out = temp / "stage"
        receipt = temp / "canonical-report.json"
        args = [
            sys.executable, str(root / "scripts/migrate-three-pass.py"),
            str(root / SOURCE), "--out", str(out),
            "--report", str(receipt), "--source-era", era, "--dry-run",
        ]
        try:
            run = subprocess.run(args, cwd=root, capture_output=True,
                                 timeout=90, check=False, text=True)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise FrontierBlocked(f"CANONICAL: {era}: cannot probe: {exc}") from exc
        if not receipt.is_file():
            raise FrontierBlocked(f"CANONICAL: {era}: no report, exit {run.returncode}: {run.stderr[-250:]}")
        report = json.loads(receipt.read_text(encoding="utf-8"))
        summary = report.get("summary", {})
        rows = report.get("files", [])
        if (
            report.get("schema") != "sens-three-pass-t5-migration/v3"
            or report.get("mode") != "dry-run"
            or report.get("source_era") != era
            or summary.get("files_seen") != 1
            or summary.get("files_written") != 0
            or len(rows) != 1
            or rows[0].get("path") != SOURCE.name
            or rows[0].get("output") != SOURCE.with_suffix(".sens").name
            or rows[0].get("status") not in {"blocked", "would-write"}
            or summary.get("files_blocked") + summary.get("files_would_write") != 1
            or any(out.rglob("*")) if out.exists() else False
        ):
            raise FrontierBlocked(f"CANONICAL: {era}: inconsistent/no-write receipt")
        row = rows[0]
        if row["status"] == "blocked" and run.returncode != 2:
            raise FrontierBlocked(f"CANONICAL: {era}: blocked result was masked as success")
        if row["status"] == "would-write" and run.returncode != 0:
            raise FrontierBlocked(f"CANONICAL: {era}: mechanical candidate incorrectly returned error")
        return {
            "source_era": era,
            "classification": ("MECHANICAL_ONLY_NOT_ADMITTED" if row["status"] == "would-write"
                               else "BLOCKED_WITH_REASON"),
            "first_blocker": row.get("reason") if row["status"] == "blocked" else None,
            "first_token": row.get("token"),
            "line": row.get("line"),
            "column": row.get("column"),
            "passes": row.get("passes"),
            "proposed_physical_bytes": row.get("bytes") if row["status"] == "would-write" else 0,
            "published_physical_bytes": 0,
            "historical_executable_admitted": False,
        }


def audit(root: Path = REPO) -> dict:
    root = root.resolve(strict=True)
    file = root / SOURCE
    if file.with_suffix(".sens").exists() or file.with_suffix(".sens").is_symlink():
        raise FrontierBlocked("SOURCE: physical .sens already exists; cannot count new original")
    before = file.read_bytes()
    actual = git_source_sha(root)
    if actual != SOURCE_GIT_BLOB:
        raise FrontierBlocked("PROVENANCE: original source Git blob changed; owner review required")
    if not before or not before.decode("utf-8").strip():
        raise FrontierBlocked("SOURCE: empty/invalid historical program")
    probes = [canonical_probe(root, era) for era in ("auto", "legacy")]
    after = file.read_bytes()
    if before != after or git_source_sha(root) != SOURCE_GIT_BLOB:
        raise FrontierBlocked("SOURCE: canonical dry-run changed immutable .lisp")
    if file.with_suffix(".sens").exists():
        raise FrontierBlocked("SOURCE: dry-run wrote physical T5 into repo")
    return {
        "schema": SCHEMA,
        "status": "RESEARCH_FRONTIER_NOT_SEMANTIC_ADMISSION",
        "source": SOURCE.as_posix(),
        "historical_original_git_blob_sha1": SOURCE_GIT_BLOB,
        "original_sha256": hashlib.sha256(before).hexdigest(),
        "historical_oracle": {
            "workflow": ".github/workflows/core1-compiler-sid-resolver.yml",
            "pinned_old_s0_commit": HISTORICAL_S0_COMMIT,
            "expected_observations": 11,
            "replayed_here": False,
        },
        "canonical_no_write_probes": probes,
        "new_physical_sens_files": 0,
        "new_historically_certified_executables": 0,
        "current_physical_11_observables": "NOT_VERIFIED",
        "next_admission_requires": (
            "11/11 old-S0 vs actual Rust physical .sens observables, "
            "current D2+Text7 exact symbol/Global/Local law, "
            "approved source SHA/typed/physical/view manifest"
        ),
        "d10_residents_added": 0,
        "d10_is_not_a_transport_workaround": True,
    }


def main() -> int:
    try:
        print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))
    except (FrontierBlocked, OSError, UnicodeError, ValueError, TypeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
