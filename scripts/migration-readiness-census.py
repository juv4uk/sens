#!/usr/bin/env python3
"""Summarize full-repository T5 migration readiness without writing .sens files.

This is a coordination/evidence gate, not a semantic authority. A source may
become migratable only after its exact-domain, host-effect, and oracle evidence
are independently admitted.
"""
from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from migration_source_scope import source_scope, blocker_cohort

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts/migrate-three-pass.py"
ARTIFACT_ARGS = [
    "--foundation", "knowledge/d1-d9-foundation.json",
    "--domain-surfaces", "crates/sens/src/domain_surface_registry_generated.rs",
    "--semantic-generated", "crates/sens/src/semantic_registry_generated.rs",
    "--semantic-registry", "crates/sens/src/semantic_registry.rs",
    "--necessary-forms", "crates/sens/src/eval/necessary_forms_generated.rs",
    "--historical-map", "contracts/core1-historical-sid-map.lisp",
    "--text7", "crates/sens/src/text7_projection_generated.rs",
]


def classify(reason: str) -> str:
    if not reason:
        return "missing-reason"
    return reason.split(":", 1)[0]


def build_report() -> dict:
    with tempfile.TemporaryDirectory(prefix="sens-t5-readiness-") as td:
        work = Path(td)
        output = work / "sens-mirror"
        report = work / "migration.json"
        command = [
            sys.executable, str(MIGRATOR), str(ROOT),
            "--out", str(output), *ARTIFACT_ARGS,
            "--report", str(report), "--dry-run", "--unpaired-only",
            "--source-era", "auto",
        ]
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=180)
        if not report.is_file():
            raise RuntimeError(f"migrator produced no report\n{completed.stdout}\n{completed.stderr}")
        state = json.loads(report.read_text(encoding="utf-8"))
        summary = state["summary"]
        reasons = collections.Counter(classify(row.get("reason", "")) for row in state["files"])
        written = list(output.rglob("*.sens")) if output.exists() else []
        rows = state["files"]
        if len(rows) != summary["files_seen"]:
            raise RuntimeError("full-source census row count differs from summary")
        if summary["files_written"] or any(row["status"] not in ("blocked", "would-write") for row in rows):
            raise RuntimeError("unexpected write-capable or unknown source status")
        mechanical = [row for row in rows if row["status"] == "would-write"]
        if len(mechanical) != summary["files_would_write"]:
            raise RuntimeError("mechanical candidate count differs from summary")
        archived_candidates = [row for row in mechanical
                               if source_scope(row["path"]) == "ARCHIVED_BENCHMARK_NONPROGRAM"]
        nonarchive_candidates = [row for row in mechanical
                                 if source_scope(row["path"]) != "ARCHIVED_BENCHMARK_NONPROGRAM"]
        nonarchive_blockers = [row for row in rows if row["status"] == "blocked"
                               and source_scope(row["path"]) != "ARCHIVED_BENCHMARK_NONPROGRAM"]
        work_counts = collections.Counter(blocker_cohort(row.get("reason", ""))
                                          for row in nonarchive_blockers)
        work_queue = [
            {"cohort": cohort, "blocked_count": count,
             "examples": [
                 {"path": row["path"], "reason": row.get("reason", "")}
                 for row in nonarchive_blockers
                 if blocker_cohort(row.get("reason", "")) == cohort
             ][:10]}
            for cohort, count in sorted(work_counts.items(), key=lambda item: (-item[1], item[0]))
        ]
        result = {
            "schema": "sens-t5-migration-readiness/v1",
            "authority": "research-only; ratified D1-D9, W8 auto fail-closed; no .sens written",
            "foundation_path": "knowledge/d1-d9-foundation.json",
            "source_era": "auto",
            "ratified_foundation_sha256": state.get("authority", {}).get("foundation_sha256"),
            "mode": "original unpaired .lisp only; full-repository dry-run",
            "skipped_existing_sens_pairs": state.get("skipped_paired_paths", []),
            "migrator_exit_code": completed.returncode,
            "migrator_summary": summary,
            "reason_counts": dict(reasons.most_common()),
            "source_scope": {
                "archived_benchmark_mechanically_eligible": len(archived_candidates),
                "active_or_unclassified_mechanically_eligible": len(nonarchive_candidates),
                "active_or_unclassified_blocked": len(nonarchive_blockers),
                "archived_candidate_paths": [r["path"] for r in archived_candidates],
                "active_or_unclassified_candidate_paths": [r["path"] for r in nonarchive_candidates],
                "executable_originals_semantically_certified": 0,
            },
            "agent_work_queue": work_queue,
            "physical_outputs_created": [str(path.relative_to(output)) for path in written],
            "gate": {
                "pass": (
                    completed.returncode in (0, 2)
                    and summary["files_written"] == 0
                    and len(nonarchive_candidates) == 0
                    and summary["files_blocked"] + summary["files_would_write"] == summary["files_seen"]
                    and not written
                ),
                "rule": "no unproved ACTIVE/UNCLASSIFIED original is mechanically admitted; archival benchmark candidates are NOT executable migrations; no .sens emitted",
            },
        }
        return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "summary": result["migrator_summary"],
        "source_scope": result["source_scope"],
        "agent_work_queue": result["agent_work_queue"],
        "gate": result["gate"],
    }, ensure_ascii=False))
    if not result["gate"]["pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
