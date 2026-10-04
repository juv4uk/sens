#!/usr/bin/env python3
"""Paired memory/working-set preflight for current English vs canonical D1-D8.

This lane deliberately reuses the #3113 CPU helper and semantic preflight.
Peak RSS is measured per helper process via POSIX wait4/rusage, which means it
is a phase-command working-set ceiling, not a subtractive "phase delta".

Allocation count/bytes remain null until one equal instrumentation mechanism is
available for both candidates.  No ratio or winner is computed.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CPU_RUNNER_PATH = HERE / "cpu_runner.py"

SPEC = importlib.util.spec_from_file_location("current_en_vs_d1d8_cpu_runner", CPU_RUNNER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load shared CPU runner")
cpu = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cpu
SPEC.loader.exec_module(cpu)

SCHEMA = "sens-current-en-vs-d1d8/v1"
SUMMARY_SCHEMA = "sens-current-en-vs-d1d8-memory-summary/v1"
CANDIDATES = ("english-surface", "canonical-d1d8")
DEFAULT_PHASES = ("session", "ingest", "lower", "execute", "full")
VALID_PHASES = set(DEFAULT_PHASES) | {"repeated"}


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    grouped: dict[tuple[str, str], list[int]] = {}
    for row in rows:
        candidate = str(row["candidate"])
        phase = str(row["phase"])
        metrics = row["metrics"]
        if not isinstance(metrics, dict):
            raise ValueError("metrics must be an object")
        rss = metrics.get("peak_rss_kb")
        if not isinstance(rss, int) or rss < 0:
            raise ValueError(f"missing POSIX peak RSS for {candidate}/{phase}")
        grouped.setdefault((candidate, phase), []).append(rss)

    summary_rows = []
    for (candidate, phase), values in sorted(grouped.items()):
        ordered = sorted(values)
        summary_rows.append(
            {
                "candidate": candidate,
                "phase": phase,
                "samples": len(ordered),
                "peak_rss_kb_median": statistics.median(ordered),
                "peak_rss_kb_min": ordered[0],
                "peak_rss_kb_max": ordered[-1],
                "peak_rss_kb_spread": ordered[-1] - ordered[0],
                "allocation_count": None,
                "allocated_bytes": None,
            }
        )
    return {"schema": SUMMARY_SCHEMA, "rows": summary_rows}


def memory_row(
    *,
    pair_id: str,
    case_id: str,
    candidate: str,
    workload: str,
    phase: str,
    rep: int,
    current_git_sha: str,
    binary_sha: str,
    corpus_sha: str,
    common_provenance: dict[str, object],
    resources: dict[str, int],
) -> dict[str, object]:
    peak = resources["process_peak_rss_kb"]
    if peak < 0:
        raise RuntimeError(
            "peak RSS unavailable: this bounded preflight requires POSIX wait4/rusage"
        )
    return {
        "schema": SCHEMA,
        "pair_id": pair_id,
        "case_id": case_id,
        "lane": "memory",
        "candidate": candidate,
        "workload": workload,
        "phase": phase,
        "rep": rep,
        "language_model": "D1-D8",
        "legacy_identity_used": False,
        "oracle_ok": True,
        "git_sha": current_git_sha,
        "binary_sha256": binary_sha,
        "corpus_sha256": corpus_sha,
        "provenance": {
            **common_provenance,
            "memory_method": "posix-wait4-rusage-ru_maxrss",
            "rss_semantics": "per-process phase-command peak; not phase delta",
            "allocation_method": None,
        },
        "metrics": {
            "peak_rss_kb": peak,
            "allocation_count": None,
            "allocated_bytes": None,
            # Keep process CPU/wall only as context for the same child sample.
            "process_wall_ns": resources["process_wall_ns"],
            "process_user_ns": resources["process_user_ns"],
            "process_sys_ns": resources["process_sys_ns"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=HERE / "fixtures" / "d3-smoke.json",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--summary-out", type=Path, required=True)
    parser.add_argument("--blocked-out", type=Path)
    parser.add_argument("--helper", type=Path)
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--repeat-n", type=int, default=10)
    parser.add_argument(
        "--phases",
        default=",".join(DEFAULT_PHASES),
        help="comma-separated subset of session,ingest,lower,execute,full,repeated",
    )
    args = parser.parse_args()

    if args.reps < 3:
        raise ValueError("--reps must be >= 3 for memory spread evidence")
    phases = tuple(part.strip() for part in args.phases.split(",") if part.strip())
    if not phases or any(phase not in VALID_PHASES for phase in phases):
        raise ValueError(f"invalid --phases: {args.phases}")

    repo = HERE.parents[1]
    manifest_path = args.manifest.resolve()
    manifest_bytes = manifest_path.read_bytes()
    manifest = cpu.load_manifest(manifest_path)
    corpus_sha = cpu.sha256_bytes(manifest_bytes)
    current_git_sha = cpu.git_sha(repo)

    helper = args.helper.resolve() if args.helper else cpu.build_helper(repo)
    if not helper.is_file():
        raise FileNotFoundError(helper)
    binary_sha = cpu.sha256_file(helper)
    common_provenance = cpu.provenance(args.repeat_n)

    rows: list[dict[str, object]] = []
    blocked: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="sens-current-en-vs-d1d8-mem-") as tmp_name:
        tmp = Path(tmp_name)
        for workload_obj in manifest["workloads"]:
            workload = dict(workload_obj)
            workload_id = str(workload["id"])
            if workload["status"] == "blocked":
                blocked.append(
                    {
                        "workload": workload_id,
                        "reason": workload.get("reason", "not ready"),
                        "blockers": workload.get("blockers", []),
                    }
                )
                continue

            paths, oracle = cpu.preflight_pair(helper, tmp, workload, args.repeat_n)

            for phase in phases:
                for rep in range(args.reps):
                    pair_id = f"{workload_id}:{phase}:{rep}"
                    for candidate in CANDIDATES:
                        result, resources = cpu.run_helper(
                            helper,
                            candidate,
                            phase,
                            paths[candidate],
                            args.repeat_n,
                        )
                        if phase in {"execute", "full", "repeated"}:
                            if result["value"] != oracle["value"] or result["output"] != oracle["output"]:
                                raise ValueError(
                                    f"{workload_id}: {candidate}/{phase} changed oracle result"
                                )
                        rows.append(
                            memory_row(
                                pair_id=pair_id,
                                case_id=f"{pair_id}:{candidate}",
                                candidate=candidate,
                                workload=workload_id,
                                phase=phase,
                                rep=rep,
                                current_git_sha=current_git_sha,
                                binary_sha=binary_sha,
                                corpus_sha=corpus_sha,
                                common_provenance=common_provenance,
                                resources=resources,
                            )
                        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    summary = summarize(rows)
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    args.summary_out.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    blocked_path = args.blocked_out or args.out.with_suffix(".blocked.json")
    blocked_path.write_text(
        json.dumps(
            {
                "schema": cpu.BLOCKED_SCHEMA,
                "git_sha": current_git_sha,
                "corpus_sha256": corpus_sha,
                "blocked": blocked,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"wrote {len(rows)} paired memory rows to {args.out}")
    print(f"wrote memory summary to {args.summary_out}")
    print(f"blocked workloads: {len(blocked)} -> {blocked_path}")
    print("allocation_count and allocated_bytes remain null")
    print("no memory ratio or winner is computed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
