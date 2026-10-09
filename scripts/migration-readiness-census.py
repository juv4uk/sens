#!/usr/bin/env python3
"""Summarize full-repository T5 migration readiness without writing .sens files.

This is a coordination/evidence gate, not a semantic authority. A source may
become migratable only after its exact-domain, host-effect, and oracle evidence
are independently admitted.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts/migrate-three-pass.py"
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
from migration_source_scope import scope
# Reuse the existing SHA-pinned original-data registry; never infer a
# nonprogram classification from a filename or an unfamiliar Lisp head.
from report_original_migration_candidates import load_nonprogram_classification, git_blob_sha
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


def _checked_rows(state: dict, era: str) -> dict[str, dict]:
    summary = state["summary"]
    rows = state["files"]
    if len(rows) != summary["files_seen"]:
        raise RuntimeError(f"{era}: missing source rows in migration report")
    result: dict[str, dict] = {}
    for row in rows:
        name = row.get("path")
        if not isinstance(name, str) or not name.endswith(".lisp"):
            raise RuntimeError(f"{era}: invalid .lisp source row {name!r}")
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts or name in result:
            raise RuntimeError(f"{era}: invalid or duplicate source path {name!r}")
        result[name] = row
    if summary["files_written"] != 0 or summary["files_blocked"] + summary["files_would_write"] != len(rows):
        raise RuntimeError(f"{era}: migration dry-run accounting disagrees")
    return result


def _candidate_class(statuses: dict[str, str]) -> str:
    # A mechanical candidate is NOT an admitted program. Only D2 + semantic
    # oracle proof may promote a candidate to a committed physical .sens pair.
    if statuses["auto"] == "would-write":
        return "auto-mechanical-candidate-needs-oracle"
    l = statuses["legacy"] == "would-write"
    c = statuses["current"] == "would-write"
    if l and c:
        return "both-eras-mechanical-needs-provenance-and-oracle"
    if l:
        return "legacy-mechanical-needs-provenance-and-oracle"
    if c:
        return "current-mechanical-needs-provenance-and-oracle"
    return "blocked-in-all-eras-needs-semantic-or-nonprogram-triage"


def build_report() -> dict:
    """Report THREE independent source-era projections without publishing.

    The existing release gate still judges only the fail-closed AUTO scan.
    Historical/current passes are diagnostics, not an instruction to pick a
    convenient meaning for an 8-bit word; neither can write any .sens bytes.
    """
    with tempfile.TemporaryDirectory(prefix="sens-t5-readiness-") as td:
        work = Path(td)
        views: dict[str, dict] = {}
        by_era: dict[str, dict[str, dict]] = {}
        for era in ("auto", "legacy", "current"):
            output = work / f"physical-{era}"
            report_path = work / f"migration-{era}.json"
            command = [
                sys.executable, str(MIGRATOR), str(ROOT),
                "--out", str(output), *ARTIFACT_ARGS,
                "--report", str(report_path), "--dry-run", "--unpaired-only",
                "--source-era", era,
            ]
            completed = subprocess.run(
                command, cwd=ROOT, text=True, capture_output=True, timeout=180
            )
            if not report_path.is_file():
                raise RuntimeError(
                    f"{era}: migrator produced no report\n{completed.stdout}\n{completed.stderr}"
                )
            state = json.loads(report_path.read_text(encoding="utf-8"))
            if completed.returncode not in (0, 2):
                raise RuntimeError(f"{era}: migrator returned error {completed.returncode}")
            if state.get("source_era") != era:
                raise RuntimeError(f"{era}: report era mismatch")
            rows = _checked_rows(state, era)
            written = list(output.rglob("*.sens")) if output.exists() else []
            if written:
                raise RuntimeError(f"{era}: dry-run unexpectedly published physical .sens")
            views[era] = {
                "state": state, "exit": completed.returncode,
                "paired": state.get("skipped_paired_paths", []),
            }
            by_era[era] = rows

        original_paths = set(by_era["auto"])
        original_paired = set(views["auto"]["paired"])
        for era in ("legacy", "current"):
            if set(by_era[era]) != original_paths:
                raise RuntimeError(f"{era}: original source set changed between scans")
            if set(views[era]["paired"]) != original_paired:
                raise RuntimeError(f"{era}: paired-source set changed between scans")
        if original_paths.intersection(original_paired):
            raise RuntimeError("a source was both paired and unpaired")

        # 25 ISA + 21 schema + 8 evidence + 13 expr-record DATA sources have
        # already been reviewed and Git-blob-pinned in original-corpus work.
        # Check them against this EXACT three-era unpaired source set, or fail.
        reviewed = load_nonprogram_classification(ROOT)
        if not set(reviewed).issubset(original_paths):
            missing = sorted(set(reviewed) - original_paths)
            raise RuntimeError(f"reviewed nonprogram missing from unpaired source set: {missing[:5]}")
        queues: collections.Counter[str] = collections.Counter()
        queue_rows: list[dict] = []
        for path in sorted(original_paths):
            source = (ROOT / path).resolve()
            if not source.is_relative_to(ROOT) or source.is_symlink() or not source.is_file():
                raise RuntimeError(f"unsafe/missing source in original census: {path}")
            reviewed_row = reviewed.get(path)
            if reviewed_row is not None:
                if git_blob_sha(source) != reviewed_row["source_git_blob_sha"]:
                    raise RuntimeError(f"reviewed source SHA mismatch: {path}")
                if reviewed_row["semantic_oracle_admitted"] or reviewed_row["automatic_sens_companion"]:
                    raise RuntimeError(f"nonprogram incorrectly granted executable admission: {path}")
            states = {era: by_era[era][path].get("status", "") for era in views}
            if not all(v in ("blocked", "would-write") for v in states.values()):
                raise RuntimeError(f"unrecognized migration status on {path}: {states}")
            cohort = _candidate_class(states)
            queues[cohort] += 1
            queue_rows.append({
                "path": path,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "queue": cohort,
                "source_scope": (reviewed_row["source_class"] if reviewed_row
                                 else scope(path)),
                "reviewed_nonprogram_cohort": (reviewed_row["cohort"] if reviewed_row
                                               else None),
                "reviewed_nonprogram_git_blob": (reviewed_row["source_git_blob_sha"] if reviewed_row
                                                 else None),
                "status": states,
                "blocker_by_era": {
                    era: by_era[era][path].get("reason") if states[era] == "blocked" else None
                    for era in ("auto", "legacy", "current")
                },
                "semantic_oracle_admitted": False,
                "physical_published": False,
            })

        archived_auto = [
            row for row in queue_rows
            if row["source_scope"] == "ARCHIVED_BENCHMARK_NONPROGRAM"
            and row["status"]["auto"] == "would-write"
        ]
        reviewed_auto = [
            row for row in queue_rows
            if row["source_scope"] == "NONPROGRAM_DATA_REVIEWED"
            and row["status"]["auto"] == "would-write"
        ]
        nonarchive_auto = [
            row for row in queue_rows
            if row["source_scope"] not in ("ARCHIVED_BENCHMARK_NONPROGRAM",
                                          "NONPROGRAM_DATA_REVIEWED")
            and row["status"]["auto"] == "would-write"
        ]
        actionable_rows = [
            row for row in queue_rows
            if row["source_scope"] not in ("ARCHIVED_BENCHMARK_NONPROGRAM",
                                          "NONPROGRAM_DATA_REVIEWED")
        ]
        actionable_queues = collections.Counter(row["queue"] for row in actionable_rows)
        if len(actionable_rows) + len(reviewed) + sum(
                row["source_scope"] == "ARCHIVED_BENCHMARK_NONPROGRAM"
                for row in queue_rows) != len(queue_rows):
            raise RuntimeError("source class partitions overlap or omit originals")

        # First-error visibility is insufficient: the initial AUTO W8 error
        # often masks a deeper value/number/binder blocker. Summarize the
        # second error exposed by each explicit-era diagnostic run, WITHOUT
        # treating that run as semantic authorization.
        reasons_by_era = {
            era: dict(collections.Counter(
                classify(row.get("reason", ""))
                for row in views[era]["state"]["files"]
                if row.get("status") == "blocked"
            ).most_common())
            for era in ("auto", "legacy", "current")
        }
        transitions: collections.Counter[tuple[str, str, str]] = collections.Counter()
        transition_paths: dict[tuple[str, str, str], list[str]] = collections.defaultdict(list)
        for row in queue_rows:
            reasons = row["blocker_by_era"]
            transition = tuple(
                classify(reasons.get(era) or "mechanical-candidate")
                for era in ("auto", "legacy", "current")
            )
            transitions[transition] += 1
            if len(transition_paths[transition]) < 5:
                transition_paths[transition].append(row["path"])
        top_transitions = [
            {"auto": reasons[0], "legacy": reasons[1], "current": reasons[2],
             "files": count, "example_original_paths": transition_paths[reasons]}
            for reasons, count in transitions.most_common(40)
        ]

        auto = views["auto"]["state"]
        summary = auto["summary"]
        reasons = collections.Counter(
            classify(row.get("reason", "")) for row in auto["files"]
        )
        result = {
            "schema": "sens-t5-migration-readiness/v2",
            "authority": "research-only; ratified D1-D9; no candidate is oracle-certified",
            "foundation_path": "knowledge/d1-d9-foundation.json",
            "source_era": "auto",
            "ratified_foundation_sha256": auto.get("authority", {}).get("foundation_sha256"),
            "mode": "original unpaired .lisp only; three separate physical-free dry-runs",
            "skipped_existing_sens_pairs": sorted(original_paired),
            "migrator_exit_code": views["auto"]["exit"],
            "migrator_summary": summary,
            "reason_counts": dict(reasons.most_common()),
            "physical_outputs_created": [],
            "per_era_summary": {
                era: views[era]["state"]["summary"] for era in ("auto", "legacy", "current")
            },
            "candidate_queues": dict(queues.most_common()),
            "actionable_executable_unknown_queues": dict(actionable_queues.most_common()),
            "reviewed_nonprogram_sources": sorted(reviewed.values(),
                                                 key=lambda item: item["path"]),
            "blocker_by_era_reason_counts": reasons_by_era,
            "top_blocker_transitions": top_transitions,
            "candidate_rows": queue_rows,
            "source_scope": {
                "reviewed_nonprogram_originals": len(reviewed),
                "reviewed_nonprogram_auto_mechanical_only": len(reviewed_auto),
                "reviewed_nonprogram_by_cohort": {
                    cohort: sum(x["cohort"] == cohort for x in reviewed.values())
                    for cohort in sorted({x["cohort"] for x in reviewed.values()})
                },
                "active_or_unknown_originals": len(actionable_rows),
                "archived_benchmark_mechanical_only": len(archived_auto),
                "nonarchive_mechanical_unproved": len(nonarchive_auto),
                "archived_candidate_paths": [row["path"] for row in archived_auto],
                "nonarchive_candidate_paths": [row["path"] for row in nonarchive_auto],
                "semantically_admitted_executable_originals": 0,
            },
            "gate": {
                "pass": (
                    views["auto"]["exit"] in (0, 2)
                    and summary["files_written"] == 0
                    and summary["files_would_write"] == len(archived_auto) + len(reviewed_auto)
                    and not nonarchive_auto
                    and summary["files_blocked"] + summary["files_would_write"] == summary["files_seen"]
                ),
                "rule": "every ACTIVE/UNCLASSIFIED original remains BLOCKED until independent oracle proof; Git-SHA reviewed DATA and archived mechanical candidates are NONPROGRAM, never executable credit; no .sens emitted",
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
    print(json.dumps({"summary": result["migrator_summary"], "per_era_summary": result["per_era_summary"], "candidate_queues": result["candidate_queues"], "actionable_queues": result["actionable_executable_unknown_queues"], "source_scope": result["source_scope"], "top_blocker_transitions": result["top_blocker_transitions"][:12], "per_era_top_reasons": {era: dict(list(rows.items())[:12]) for era, rows in result["blocker_by_era_reason_counts"].items()}, "gate": result["gate"]}, ensure_ascii=False))
    if not result["gate"]["pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
