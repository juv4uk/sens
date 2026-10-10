#!/usr/bin/env python3
"""Analyze measured rows only. BLOCKED is never counted as a zero runtime."""
from __future__ import annotations
import argparse
import collections
import csv
import json
import math
import os
import platform
import statistics
import subprocess
from pathlib import Path

LANES = {"interpreter-source", "native-admitted-cpu", "physical-t5-inprocess"}

def summarize(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source, delimiter="\t")
        if reader.fieldnames != ["case", "lane", "iteration", "elapsed_ns", "value", "status"]:
            raise ValueError("invalid native-machine raw-data header")
        rows = list(reader)
    if not rows:
        raise ValueError("empty benchmark output is not evidence")
    all_rows = collections.defaultdict(list)
    for row in rows:
        if not row["case"] or row["lane"] not in LANES:
            raise ValueError(f"invalid measured lane: {row}")
        all_rows[(row["case"], row["lane"])].append(row)
    results = []
    for (case, lane), data in sorted(all_rows.items()):
        blocks = [row for row in data if row["status"].startswith("BLOCKED:")]
        passes = [row for row in data if row["status"] == "PASS"]
        if len(blocks) + len(passes) != len(data) or blocks and passes:
            raise ValueError(f"mixed/unknown outcome: {case}/{lane}")
        if blocks and (len(blocks) != 1 or int(blocks[0]["iteration"]) != -1):
            raise ValueError(f"invalid BLOCKED record: {case}/{lane}")
        ns = []
        values = set()
        for row in passes:
            if int(row["iteration"]) < 0 or int(row["elapsed_ns"]) <= 0:
                raise ValueError(f"invalid PASS timing: {row}")
            ns.append(int(row["elapsed_ns"]))
            values.add(row["value"])
        if len(values) > 1:
            raise ValueError(f"unstable value: {case}/{lane}")
        ns.sort()
        results.append({
            "case": case, "lane": lane, "status": "BLOCKED" if blocks else "PASS",
            "samples": len(ns), "median_ns": statistics.median(ns) if ns else None,
            "p95_ns": ns[math.ceil(len(ns) * 0.95) - 1] if ns else None,
            "result": next(iter(values)) if values else None,
            "blocker": blocks[0]["status"][8:] if blocks else None,
        })
    groups = collections.defaultdict(dict)
    for item in results:
        groups[item["case"]][item["lane"]] = item
    ratios = []
    for case, group in sorted(groups.items()):
        if "interpreter-source" not in group or "native-admitted-cpu" not in group:
            continue
        interp = group["interpreter-source"]
        native = group["native-admitted-cpu"]
        if interp["status"] == native["status"] == "PASS":
            if interp["result"] != native["result"] or interp["samples"] != native["samples"]:
                raise ValueError(f"native result/sample mismatch in {case}")
            ratio = interp["median_ns"] / native["median_ns"]
        else:
            ratio = None
        ratios.append({"case": case, "interpreter_over_native_median": ratio,
                       "status": "PASS" if ratio is not None else "BLOCKED"})
    return {"schema": "sens-native-machine-1/v1", "cases": results, "ratios": ratios}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.raw)
    args.out.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[2]
    def cmd(argv: list[str]) -> str:
        try:
            return subprocess.check_output(argv, cwd=root, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            return "unknown"
    cpuinfo = Path("/proc/cpuinfo")
    cpuline = next((line.partition(":")[2].strip() for line in cpuinfo.read_text().splitlines()
                    if line.startswith("model name")), platform.processor()) if cpuinfo.exists() else platform.processor()
    result["environment"] = {
        "commit": cmd(["git", "rev-parse", "HEAD"]),
        "cpu": cpuline,
        "rustc": cmd(["rustc", "-V"]),
        "platform": platform.platform(),
        "runner": os.getenv("RUNNER_NAME", "local"),
    }
    (args.out / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    lines = ["# SENS Native Machine №1", "",
             "CPU: " + cpuline, "SHA: " + result["environment"]["commit"], "",
             "| Workload | Lane | State | Samples | Median (µs) | p95 (µs) |",
             "| --- | --- | --- | ---: | ---: | ---: |"]
    for row in result["cases"]:
        def fmt(n):
            return f"{n / 1000:.3f}" if n is not None else "—"
        lines.append(f"| {row['case']} | {row['lane']} | {row['status']} | "
                     f"{row['samples']} | {fmt(row['median_ns'])} | {fmt(row['p95_ns'])} |")
        if row["blocker"]:
            lines.append(f"\nBlocked {row['case']} / {row['lane']}: {row['blocker']}\n")
    lines += ["", "## Within-workload interpreter/native result", ""]
    for case in result["ratios"]:
        if case["status"] == "PASS":
            lines.append(f"- {case['case']}: {case['interpreter_over_native_median']:.3f}x interpreter/native, including parser/admission/host overhead")
        else:
            lines.append(f"- {case['case']}: BLOCKED — **no speed ratio**")
    lines += ["", "Physical T5 uses different programs and data: it is NOT a third implementation of the u64 pair workload.",
              "Actual benchmark green means measurements ran; it does NOT imply native admission or broad semantic migration passed."]
    report = "\n".join(lines) + "\n"
    (args.out / "report.md").write_text(report)
    print(report)

if __name__ == "__main__":
    main()
