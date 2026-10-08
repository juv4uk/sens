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

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts/migrate-three-pass.py"
ARTIFACT_ARGS = [
    "--foundation", "knowledge/d1-d7-foundation.json",
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
        ]
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=180)
        if not report.is_file():
            raise RuntimeError(f"migrator produced no report\n{completed.stdout}\n{completed.stderr}")
        state = json.loads(report.read_text(encoding="utf-8"))
        summary = state["summary"]
        reasons = collections.Counter(classify(row.get("reason", "")) for row in state["files"])
        written = list(output.rglob("*.sens")) if output.exists() else []
        result = {
            "schema": "sens-t5-migration-readiness/v1",
            "authority": "research-only; no source or .sens artifact is written",
            "mode": "original unpaired .lisp only; full-repository dry-run",
            "skipped_existing_sens_pairs": state.get("skipped_paired_paths", []),
            "migrator_exit_code": completed.returncode,
            "migrator_summary": summary,
            "reason_counts": dict(reasons.most_common()),
            "physical_outputs_created": [str(path.relative_to(output)) for path in written],
            "gate": {
                "pass": (
                    completed.returncode == 2
                    and summary["files_written"] == 0
                    and summary["files_would_write"] == 0
                    and summary["files_blocked"] == summary["files_seen"]
                    and not written
                ),
                "rule": "every ORIGINAL UNPAIRED .lisp remains BLOCKED until separate oracle proof; no .sens emitted",
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
    print(json.dumps({"summary": result["migrator_summary"], "reason_counts": result["reason_counts"], "gate": result["gate"]}, ensure_ascii=False))
    if not result["gate"]["pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
