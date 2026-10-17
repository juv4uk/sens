#!/usr/bin/env python3
"""Fail-closed aggregation of independent paired fresh-process pilot reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics


SCHEMA = "sens-physical-d3-paired-fresh-process-wall/v1"
IMPLEMENTATIONS = ("native_sens", "python_microcpu")
INVARIANTS = (
    "repository_head", "contract_version", "native_sens_binary_sha256",
    "python_executable_sha256", "python_version", "source_sha256", "cpu",
    "platform", "architecture", "cpu_affinity", "reps_per_workload",
    "warmup_pairs",
)


def percentile95(values: list[int]) -> int:
    ordered = sorted(values)
    return ordered[(95 * len(ordered) + 99) // 100 - 1]


def validate_report(report: dict) -> None:
    if report.get("schema") != SCHEMA:
        raise ValueError("report schema is not the paired fresh-process schema")
    if report.get("research_status") != "RESEARCH_NON_GATE":
        raise ValueError("report must remain explicitly RESEARCH_NON_GATE")
    if report.get("tracked_worktree_status"):
        raise ValueError("timing report was measured with tracked worktree changes")
    reps = report.get("reps_per_workload")
    if not isinstance(reps, int) or reps < 15:
        raise ValueError("each report must contain at least 15 paired measurements")
    cases = report.get("cases")
    if not isinstance(cases, dict) or not cases:
        raise ValueError("report has no workloads")
    for name, case in cases.items():
        if case.get("parity") != "pass":
            raise ValueError(f"parity is not PASS for workload {name}")
        expected = case.get("expected_result")
        if case.get("correctness_gate_outputs") != {
            "native_sens": expected, "python_microcpu": expected,
        }:
            raise ValueError(f"pre-timing correctness gate mismatch for {name}")
        pair_rows = case.get("pairs")
        if not isinstance(pair_rows, list) or len(pair_rows) != reps:
            raise ValueError(f"raw pair count mismatch for workload {name}")
        for implementation in IMPLEMENTATIONS:
            samples = case.get(implementation, {}).get("samples_ns")
            if not isinstance(samples, list) or len(samples) != reps:
                raise ValueError(f"sample count mismatch for {name}/{implementation}")
            if any(not isinstance(sample, int) or sample <= 0 for sample in samples):
                raise ValueError(f"non-positive timing sample for {name}/{implementation}")
        for index, pair in enumerate(pair_rows):
            if pair.get("index") != index:
                raise ValueError(f"pair order/index mismatch for workload {name}")
            if set(pair.get("order", [])) != set(IMPLEMENTATIONS):
                raise ValueError(f"paired implementations missing for workload {name}")
            if pair.get("outputs") != {
                "native_sens": expected, "python_microcpu": expected,
            }:
                raise ValueError(f"timed invocation parity mismatch for workload {name}")
            if any(
                pair.get("elapsed_ns", {}).get(implementation)
                != case[implementation]["samples_ns"][index]
                for implementation in IMPLEMENTATIONS
            ):
                raise ValueError(f"raw pair/sample data disagree for workload {name}")


def aggregate_reports(reports: list[dict], *, source_names: list[str]) -> dict:
    if len(reports) < 3:
        raise ValueError("at least three independent parent-process reports are required")
    if len(source_names) != len(reports):
        raise ValueError("one source name is required for every report")
    for report in reports:
        validate_report(report)
    base = reports[0]
    for report in reports[1:]:
        if any(report.get(key) != base.get(key) for key in INVARIANTS):
            raise ValueError("independent process reports disagree on source or environment")
        if set(report["cases"]) != set(base["cases"]):
            raise ValueError("independent process reports contain different workloads")

    cases = {}
    for name, first in base["cases"].items():
        for report in reports:
            case = report["cases"][name]
            for key in ("physical_path", "physical_bytes", "physical_sha256",
                        "expected_result"):
                if case.get(key) != first.get(key):
                    raise ValueError(f"physical workload provenance differs for {name}")

        native = [
            sample for report in reports
            for sample in report["cases"][name]["native_sens"]["samples_ns"]
        ]
        python = [
            sample for report in reports
            for sample in report["cases"][name]["python_microcpu"]["samples_ns"]
        ]
        paired_ratios = [
            pair["elapsed_ns"]["python_microcpu"] / pair["elapsed_ns"]["native_sens"]
            for report in reports for pair in report["cases"][name]["pairs"]
        ]
        per_replication = []
        for source_name, report in zip(source_names, reports):
            case = report["cases"][name]
            native_p50 = statistics.median(case["native_sens"]["samples_ns"])
            python_p50 = statistics.median(case["python_microcpu"]["samples_ns"])
            per_replication.append({
                "source": source_name,
                "native_sens_p50_ns": native_p50,
                "python_microcpu_p50_ns": python_p50,
                "python_over_native_p50_ratio": python_p50 / native_p50,
            })
        cases[name] = {
            "physical_path": first["physical_path"],
            "physical_bytes": first["physical_bytes"],
            "physical_sha256": first["physical_sha256"],
            "expected_result": first["expected_result"],
            "parity": "pass",
            "independent_parent_processes": len(reports),
            "sample_pairs": len(native),
            "native_sens": {
                "p50_ns": statistics.median(native),
                "p95_ns": percentile95(native),
                "samples_ns": native,
            },
            "python_microcpu": {
                "p50_ns": statistics.median(python),
                "p95_ns": percentile95(python),
                "samples_ns": python,
            },
            "python_over_native_p50_ratio": statistics.median(python) / statistics.median(native),
            "paired_python_over_native_ratio_p50": statistics.median(paired_ratios),
            "per_replication": per_replication,
        }
    return {
        "schema": "sens-physical-d3-paired-fresh-process-wall-aggregate/v1",
        "research_status": "RESEARCH_NON_GATE",
        "interpretation": (
            "Descriptive end-to-end implementation comparison only. Fresh process "
            "startup through output/exit is included; no language-level speed claim."
        ),
        "provenance": {key: base[key] for key in INVARIANTS},
        "source_reports": source_names,
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in args.reports]
    summary = aggregate_reports(reports, source_names=[path.name for path in args.reports])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    for name, case in summary["cases"].items():
        print(f"{name}: pairs={case['sample_pairs']} "
              f"native-p50={case['native_sens']['p50_ns']:.0f}ns "
              f"python-p50={case['python_microcpu']['p50_ns']:.0f}ns "
              f"python/native-p50={case['python_over_native_p50_ratio']:.2f}x")
    print(f"wrote {args.out}; RESEARCH_NON_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
