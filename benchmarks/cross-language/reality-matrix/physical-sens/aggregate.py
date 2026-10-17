#!/usr/bin/env python3
"""Aggregate independent physical-SENS pilot runs into Reality Matrix schema."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics


PHASES = (
    ("full_decode_parse_execute", "full_decode_compile_execute",
     "cold_full_decode_parse_execute_ns_per_op"),
    ("warm_eval_hot", "warm_compiled_slot_replay",
     "warm_prepared_execution_ns_per_op"),
)


def p95(values: list[int]) -> int:
    ordered = sorted(values)
    return ordered[(95 * len(ordered) + 99) // 100 - 1]


def build_comparison(reports: list[dict]) -> dict:
    if len(reports) < 3:
        raise ValueError("at least three independent process reports are required")
    invariant_keys = (
        "repository_head", "contract_version", "cpu", "platform", "architecture", "python",
        "rustc", "zig_version_pin", "sens_cli_sha256", "phase_probe_sha256",
    )
    base = reports[0]
    for report in reports:
        if any(report.get(key) != base.get(key) for key in invariant_keys):
            raise ValueError("process reports disagree on source, binary, or environment")
        if set(report.get("cases", {})) != set(base.get("cases", {})):
            raise ValueError("process reports contain different physical workloads")
    if base.get("contract_version") != "11.9":
        raise ValueError("current Reality Matrix comparison requires Contract 11.9")

    workloads = []
    for workload_id, first in base["cases"].items():
        source_path = first["path"]
        source_sha = first["physical_sha256"]
        for report in reports:
            case = report["cases"][workload_id]
            if case["path"] != source_path or case["physical_sha256"] != source_sha:
                raise ValueError(f"physical input drift for {workload_id}")
            if not case["parity"].get("equal"):
                raise ValueError(f"parity is not PASS for {workload_id}")

        measurements = []
        for native_phase, python_phase, axis in PHASES:
            sens_samples = []
            competitor_samples = []
            for report in reports:
                case = report["cases"][workload_id]
                sens_samples.extend(case["native_sens"][native_phase]["raw_ns_per_operation"])
                competitor_samples.extend(case["python_microcpu"][python_phase]["raw_ns_per_operation"])
            measurements.append({
                "axis": axis, "status": "measured", "unit": "ns/operation",
                "sens_samples": sens_samples,
                "competitor_samples": competitor_samples,
                "sens_median": statistics.median(sens_samples),
                "competitor_median": statistics.median(competitor_samples),
                "sens_p95": p95(sens_samples),
                "competitor_p95": p95(competitor_samples),
                "notes": (
                    f"Native phase={native_phase}; Python phase={python_phase}. "
                    "Both use the same physical bytes, but internal representations "
                    "differ; this is not a language-level speed claim."
                ),
            })
        workloads.append({
            "id": workload_id,
            "parity": "pass",
            "params": {
                "physical_path": source_path, "physical_sha256": source_sha,
                "physical_bytes": first["physical_bytes"],
                "exact_word_count": first["word_count"],
                "microcpu_slot_count": first["microcpu_slot_count"],
                "process_replications": len(reports),
                "samples_per_process": base["samples_per_process"],
                "loops_per_sample": base["loops_per_sample"],
                "warmup_samples": base["warmup_samples"],
            },
            "measurements": measurements,
        })

    return {
        "system": "native-sens-vs-python-microcpu-physical-t5",
        "sens": {
            "commit": base["repository_head"], "contract": base["contract_version"],
            "ratified_domains": "D1-D7", "binary_sha256": base["sens_cli_sha256"],
            "phase_probe_sha256": base["phase_probe_sha256"],
        },
        "competitor": {
            "name": "Python-hosted µCPU research slot VM",
            "version": base["python"], "commit": base["repository_head"],
            "source_scope": "bounded D1-D3 slot execution; not general Python",
        },
        "environment": {
            "os": base["platform"].split("-")[0],
            "arch": base["architecture"],
            "cpu": base["cpu"], "load_context": "unknown",
            "evidence_mode": "pilot",
            "toolchain": {
                "python": base["python"], "rustc": base["rustc"],
                "zig_pin": base["zig_version_pin"],
            },
        },
        "workloads": workloads,
        "verdicts": [{
            "axis": "language_level_performance",
            "verdict": "inconclusive",
            "evidence": (
                "Three local WSL2 process replications with matching physical-input "
                "parity; phase boundaries and representations differ, so no general "
                "language ranking or speedup is supported."
            ),
        }],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in args.reports]
    comparison = build_comparison(reports)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(comparison, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"wrote {args.out}: {len(comparison['workloads'])} workloads; verdict=inconclusive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
